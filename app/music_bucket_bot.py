import datetime
import logging
import random
import re
from collections import defaultdict
from enum import Enum

from peewee import fn, SQL
from telegram import InlineQueryResultArticle, InputTextMessageContent

from app.db.db import User, Chat, Link
from app.music.music import LinkType, EntityType
from app.music.spotify import SpotifyClient
from app.responser import Responser

logger = logging.getLogger(__name__)


class Commands(Enum):
    SAVE_LINK = 'save_link'
    MUSIC = 'music'
    MUSIC_FROM_BEGINNING = 'music_from_beginning'
    RECOMMENDATIONS = 'recommendations'
    STATS = 'stats'
    SEARCH = 'search'


class MusicBucketBotFactory:
    """Handles the execution of a command"""

    @staticmethod
    def handle_save_link(bot, update):
        command = Commands.SAVE_LINK
        MusicBucketBotFactory._handle(bot, update, command)

    @staticmethod
    def handle_music_command(bot, update):
        command = Commands.MUSIC
        MusicBucketBotFactory._handle(bot, update, command)

    @staticmethod
    def handle_music_from_beginning_command(bot, update, args):
        command = Commands.MUSIC_FROM_BEGINNING
        MusicBucketBotFactory._handle(bot, update, command, args)

    @staticmethod
    def handle_recommendations(bot, update):
        command = Commands.RECOMMENDATIONS
        MusicBucketBotFactory._handle(bot, update, command)

    @staticmethod
    def handle_stats_command(bot, update):
        command = Commands.STATS
        MusicBucketBotFactory._handle(bot, update, command)

    @staticmethod
    def handle_search_command(bot, update):
        command = Commands.SEARCH
        MusicBucketBotFactory._handle(bot, update, command)

    @staticmethod
    def _handle(bot, update, command, command_args=[]):
        args = []
        kwargs = {'bot': bot,
                  'update': update,
                  'command_args': command_args,
                  'command': command}
        music_bucket_bot = MusicBucketBot(*args, **kwargs)
        music_bucket_bot.execute()


class MusicBucketBot:
    """Command executor"""

    class LinkProcessor:
        def extract_url_from_message(self, text):
            """Gets the first url of a message"""
            link = re.search("(?P<url>https?://[^\s]+)", text)
            if link is not None:
                logger.info(f'Extracting url from message: {text}')
                return link.group('url')
            return ''

    def __init__(self, *args, **kwargs):
        self.command = kwargs.get('command')
        self.command_args = kwargs.get('command_args')
        self.bot = kwargs.get('bot')
        self.update = kwargs.get('update')

        self.spotify_client = SpotifyClient()
        self.link_processor = self.LinkProcessor()
        self.responser = Responser(self.bot, self.update)

    def execute(self):
        if self.command == Commands.MUSIC:
            self._music()
        elif self.command == Commands.MUSIC_FROM_BEGINNING:
            self._music_from_beginning()
        elif self.command == Commands.RECOMMENDATIONS:
            self._recommendations()
        elif self.command == Commands.STATS:
            self._stats()
        elif self.command == Commands.SEARCH:
            self._search()
        else:
            self._process_message()

    # Commands logic
    def _music(self):
        """
        Command /music
        Gets the links sent by all the users of the chat in the last week
        and group them by user>links
        """
        days = 7
        now = datetime.datetime.now()
        last_week_timedelta = datetime.timedelta(days=days)

        last_week_links = defaultdict(list)

        links = Link.select() \
            .join(Chat) \
            .where(Chat.id == self.update.message.chat_id) \
            .where((Link.created_at >= now - last_week_timedelta) | (Link.updated_at >= now - last_week_timedelta)) \
            .order_by(Link.updated_at.asc(), Link.created_at.asc())

        for link in links:
            last_week_links[link.user].append(link)
        last_week_links = dict(last_week_links)

        self.responser.reply_music(last_week_links)

        logger.info(
            f"'/music' command was called by user {self.update.message.from_user.id} in chat {self.update.message.chat_id}")

    def _music_from_beginning(self):
        """
        Command /music_from_beginning @username
        Gets the links sent by an specific username of the chat from the beginning
        """
        all_time_links = defaultdict(list)

        try:
            username = self.command_args[0]
            username = username.replace('@', '')
        except IndexError:
            self.responser.error_music_from_beginning_no_username()
            return

        links = Link.select() \
            .join(Chat, on=(Chat.id == Link.chat)) \
            .join(User, on=(User.id == Link.user)) \
            .where((Chat.id == self.update.message.chat_id) & (User.username == username)) \
            .order_by(Link.updated_at.asc(), Link.created_at.asc())

        if len(links) == 0:
            self.responser.error_no_links_found(username)
            return

        for link in links:
            all_time_links[link.user].append(link)
        all_time_links = dict(all_time_links)

        self.responser.reply_music_from_beginning(all_time_links)
        logger.info(
            f"'/music_from_beginning' command was called by user {self.update.message.from_user.id} \
                     in chat {self.update.message.chat_id} for the user {username}")

    def _recommendations(self):
        """
        Command /recommendations
        Returns a recommendations list based on the links sent during the last week
        """
        days = 7
        now = datetime.datetime.now()
        last_week_timedelta = datetime.timedelta(days=days)
        SpotifyClient.MAX_RECOMMENDATIONS_ARTISTS_SEEDS
        artists_ids = []

        seed_links = Link.select() \
            .join(Chat) \
            .where(Chat.id == self.update.message.chat_id) \
            .where((Link.created_at >= now - last_week_timedelta) | (Link.updated_at >= now - last_week_timedelta)) \
            .where(Link.link_type == LinkType.ARTIST.value) \
            .order_by(Link.updated_at.asc(), Link.created_at.asc())

        if len(seed_links) == 0:
            track_recommendations = []
        else:
            if len(seed_links) > SpotifyClient.MAX_RECOMMENDATIONS_ARTISTS_SEEDS:
                seed_links = random.sample(list(seed_links), k=SpotifyClient.MAX_RECOMMENDATIONS_ARTISTS_SEEDS)

            artists_ids = [self.spotify_client.get_entity_id_from_url(link.url) for link in seed_links]
            track_recommendations = self.spotify_client.get_recommendations(artists_ids)
        self.responser.reply_recommendations(track_recommendations, seed_links)

        logger.info(f"'/recommendations' command was called by user {self.update.message.from_user.id} "
                    f"in the chat {self.update.message.chat_id}")

    def _stats(self):
        """
        Command /stats
        Returns the number of links sent in a chat by every user
        """
        users = User.select(User, fn.Count(Link.url).alias('links')) \
            .join(Link, on=Link.user) \
            .join(Chat, on=Link.chat) \
            .where(Link.chat.id == self.update.message.chat_id) \
            .group_by(User) \
            .order_by(SQL('links').desc())

        self.responser.reply_stats(users)

        logger.info(
            f"'/stats' command was called by user {self.update.message.from_user.id} "
            f"in the chat {self.update.message.chat_id}")

    def _search(self):
        results = []

        user_input = self.update.inline_query.query

        entity_type = user_input.split(' ', 1)[0]
        query = user_input.replace(entity_type, '').strip()
        valid_entity_type = False

        if entity_type == EntityType.ARTIST.value:
            valid_entity_type = True
        elif entity_type == EntityType.ALBUM.value:
            valid_entity_type = True
        elif entity_type == EntityType.TRACK.value:
            valid_entity_type = True

        if valid_entity_type and len(query) >= 3:
            logger.info(f"Searching for entity:'{entity_type}' with query:'{query}'")
            search_result = self.spotify_client.search_link(query, entity_type)
            for result in search_result:
                thumb_url = ''
                description = ''

                # If the result are tracks, look for the album cover
                if entity_type == EntityType.TRACK.value:
                    album = result['album']
                    artists = result['artists']
                    thumb_url = album['images'][0]['url']
                    # [o.my_attr for o in my_list]
                    description = '{} - {}'.format(', '.join(artist['name'] for artist in artists), album['name'])
                elif entity_type == EntityType.ALBUM.value:
                    thumb_url = result['images'][0]['url'] if len(result['images']) > 0 else ''
                    artists = result['artists']
                    description = ', '.join(artist['name'] for artist in artists)
                elif entity_type == EntityType.ARTIST.value:
                    thumb_url = result['images'][0]['url'] if len(result['images']) > 0 else ''
                    description = ', '.join(result['genres'])

                results.append(InlineQueryResultArticle(
                    id=result['id'],
                    thumb_url=thumb_url,
                    title=result['name'],
                    description=description,
                    input_message_content=InputTextMessageContent(result['external_urls']['spotify'])))

        self.responser.show_search_results(results)

    def _process_message(self):
        """
       Finds the streaming url, identifies the streaming service in the text and
       saves it to the database.
       It also saves the user and the chat if they don't exist @ database
       """
        url = self.link_processor.extract_url_from_message(self.update.message.text)
        link_type = self.spotify_client.get_link_type(url)
        if not self.spotify_client.is_valid_url(url):
            return
        if not link_type:
            return

        cleaned_url = self.spotify_client.clean_url(url)
        user = self._save_user()
        chat = self._save_chat()

        link_info = self.spotify_client.get_link_info(cleaned_url, link_type)
        if link_info is None:
            logger.error("Error ocurred getting link info")
            return

        link_updated = self._save_link(link_info, user, chat)
        self.responser.reply_save_link(link_info, link_updated)

    # Operations
    def _save_user(self):
        # Create or get the user that sent the link
        user, user_created = User.get_or_create(
            id=self.update.message.from_user.id,
            username=self.update.message.from_user.username,
            first_name=self.update.message.from_user.first_name)
        if user_created:
            logger.info("User '{}' with id '{}' was created".format(
                user.username if user.username else user.first_name,
                user.id))
        return user

    def _save_chat(self):
        # Create or get the chat where the link was sent
        chat, chat_created = Chat.get_or_create(
            id=self.update.message.chat_id,
            name=self.update.message.chat.title or self.update.message.chat.username or self.update.message.chat.first_name)
        if chat_created:
            logger.info(f"Chat '{chat.name}' with id '{chat.id}' was created")

        return chat

    def _save_link(self, link_info, user, chat):
        # Update the link if it exists for a chat, create if it doesn't exist
        link = Link.get_or_none((Link.url == link_info.url) & (Link.chat == chat))
        link_updated = False
        if link is not None:
            # If link already exists, set updated_at and last_update_user to current
            link.apply_update(user)
            link.save()
            link_updated = True
        else:

            link = Link.create(
                url=link_info.url,
                link_type=link_info.link_type.value,
                created_at=datetime.datetime.now(),
                artist_name=link_info.artist,
                album_name=link_info.album,
                track_name=link_info.track,
                genre=link_info.genres[0] if len(link_info.genres) > 0 else None,
                user=user,
                chat=chat)

        # Log link operation
        link_operation = 'Saved' if not link_updated else 'Updated'

        if link_info.link_type == LinkType.ARTIST:
            logger.info("'{}' link '{}' of type '{}' in chat '{}'".format(
                link_operation, link.artist_name, link.link_type, link.chat.name))
        elif link_info.link_type == LinkType.ALBUM:
            logger.info("'{}' link '{}' of type '{}' in chat '{}'".format(
                link_operation, link.album_name, link.link_type, link.chat.name))
        elif link_info.link_type == LinkType.TRACK:
            logger.info("'{}' link '{}' of type '{}' in chat '{}'".format(
                link_operation, link.track_name, link.link_type, link.chat.name))

        return link_updated
