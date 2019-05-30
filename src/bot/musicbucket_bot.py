import datetime
import logging
import random
import re
from collections import defaultdict
from enum import Enum

from peewee import fn, SQL
from telegram import InlineQueryResultArticle, InputTextMessageContent

from bot.logger import Logger
from bot.models import User, Chat, Link, Track, Artist, Album, Genre, LastFMUsername
from bot.music.lastfm import LastFMClient
from bot.music.music import LinkType, EntityType
from bot.music.musicbrainz import MusicBrainzClient
from bot.music.spotify import SpotifyClient
from bot.responser import Responser

logger = logging.getLogger(__name__)


class Command(Enum):
    MUSIC = 'music'
    MUSIC_FROM_BEGINNING = 'music_from_beginning'
    RECOMMENDATIONS = 'recommendations'
    NOW_PLAYING = 'np'
    LASTFMSET = 'lastfmset'
    STATS = 'stats'


class Inline(Enum):
    SEARCH = 'search'


class MusicBucketBotFactory:
    """Handles the execution of a command"""

    @staticmethod
    def handle_save_link(bot, update):
        MusicBucketBotFactory._handle(bot, update)

    @staticmethod
    def handle_music_command(bot, update, args):
        command = Command.MUSIC
        MusicBucketBotFactory._handle(bot, update, command=command, command_args=args)

    @staticmethod
    def handle_music_from_beginning_command(bot, update, args):
        command = Command.MUSIC_FROM_BEGINNING
        MusicBucketBotFactory._handle(bot, update, command=command, command_args=args)

    @staticmethod
    def handle_recommendations_command(bot, update):
        command = Command.RECOMMENDATIONS
        MusicBucketBotFactory._handle(bot, update, command=command)

    @staticmethod
    def handle_now_playing_command(bot, update):
        command = Command.NOW_PLAYING
        MusicBucketBotFactory._handle(bot, update, command=command)

    @staticmethod
    def handle_lastfmset_command(bot, update, args):
        command = Command.LASTFMSET
        MusicBucketBotFactory._handle(bot, update, command=command, command_args=args)

    @staticmethod
    def handle_stats_command(bot, update):
        command = Command.STATS
        MusicBucketBotFactory._handle(bot, update, command=command)

    @staticmethod
    def handle_search(bot, update):
        inline = Inline.SEARCH
        MusicBucketBotFactory._handle(bot, update, inline=inline)

    @staticmethod
    def _handle(bot, update, command=None, inline=None, command_args=[]):
        args = []
        kwargs = {
            'bot': bot,
            'update': update,
            'command_args': command_args,
            'action': command or inline
        }
        musicbucket_bot = MusicBucketBot(*args, **kwargs)

        if command not in Command and inline not in Inline:
            musicbucket_bot.process_message()
        elif command:
            musicbucket_bot.execute_command()
        elif inline:
            musicbucket_bot.execute_inline()


class MusicBucketBot:
    """Command executor. Logic core."""

    class LinkProcessor:
        @staticmethod
        def extract_url_from_message(text):
            """Gets the first url of a message"""
            link = re.search("(?P<url>https?://[^\s]+)", text)
            if link is not None:
                url = link.group('url')
                return url
            return ''

    def __init__(self, *args, **kwargs):
        self.action = kwargs.get('action')
        self.command_args = kwargs.get('command_args')
        self.bot = kwargs.get('bot')
        self.update = kwargs.get('update')

        self.spotify_client = SpotifyClient()
        self.lastfm_client = LastFMClient()
        self.musicbrainz_client = MusicBrainzClient()
        self.responser = Responser(self.bot, self.update)

    def execute_inline(self):
        Logger.log_inline(self.action, self.update)

        self._search()

    def execute_command(self):
        Logger.log_command(self.action, self.command_args, self.update)

        if self.action == Command.MUSIC:
            self._music()
        elif self.action == Command.MUSIC_FROM_BEGINNING:
            self._music_from_beginning()
        elif self.action == Command.RECOMMENDATIONS:
            self._recommendations()
        elif self.action == Command.NOW_PLAYING:
            self._now_playing()
        elif self.action == Command.LASTFMSET:
            self._lastfmset_username()
        elif self.action == Command.STATS:
            self._stats()
        else:
            self.process_message()

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

        try:
            username = self.command_args[0]
            username = username.replace('@', '')
            links = Link.select() \
                .join(Chat, on=(Chat.id == Link.chat)) \
                .join(User, on=(User.id == Link.user)) \
                .where((Chat.id == self.update.message.chat_id) & (User.username == username)) \
                .where((Link.created_at >= now - last_week_timedelta) | (Link.updated_at >= now - last_week_timedelta)) \
                .order_by(Link.updated_at.asc(), Link.created_at.asc())

        except IndexError:
            links = Link.select() \
                .join(Chat) \
                .where(Chat.id == self.update.message.chat_id) \
                .where((Link.created_at >= now - last_week_timedelta) | (Link.updated_at >= now - last_week_timedelta)) \
                .order_by(Link.updated_at.asc(), Link.created_at.asc())

        for link in links:
            last_week_links[link.user].append(link)
        last_week_links = dict(last_week_links)

        self.responser.reply_music(last_week_links)

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

    def _recommendations(self):
        """
        Command /recommendations
        Returns a recommendations list based on the links sent during the last week
        """
        days = 7
        now = datetime.datetime.now()
        last_week_timedelta = datetime.timedelta(days=days)

        album_seeds = Album.select() \
            .join(Link) \
            .join(Chat) \
            .where(Chat.id == self.update.message.chat_id) \
            .where((Link.created_at >= (now - last_week_timedelta)) | (Link.updated_at >= (now - last_week_timedelta))) \
            .where(Link.link_type == LinkType.ALBUM.value) \
            .order_by(Link.updated_at.asc(), Link.created_at.asc())

        artist_seeds = []
        if len(album_seeds) == 0:
            track_recommendations = []
        else:
            if len(album_seeds) > SpotifyClient.MAX_RECOMMENDATIONS_SEEDS:
                album_seeds = random.sample(list(album_seeds), k=SpotifyClient.MAX_RECOMMENDATIONS_SEEDS)
            artist_seeds = [album.artists.first() for album in album_seeds]
            track_recommendations = self.spotify_client.get_recommendations(artist_seeds)
        self.responser.reply_recommendations(track_recommendations, artist_seeds)

    def _now_playing(self):
        """
        Command /np
        Shows which track is the user currently playing
        TODO: By getting MBID from the returned track artist, call MB API and get Spotify Link to save it in the database as a sent recommendation
        """
        from_user = self.update.message.from_user
        lastfm_username = LastFMUsername.get_or_none(from_user.id)
        if not lastfm_username:
            username = None
            now_playing = None
        else:
            username = lastfm_username.username
            now_playing = self.lastfm_client.now_playing(username)

        self.responser.reply_now_playing(now_playing, username)

    def _lastfmset_username(self):
        """
        Command /lastfmset
        Sets the given Last.fm username to the current user
        """
        try:
            username = self.command_args[0]
            username = username.replace('@', '')
        except IndexError:
            self.responser.error_lastfmset_username_no_username()
            return

        lastfm_username, created = LastFMUsername.get_or_create(
            user=self.update.message.from_user.id,
            defaults={
                'username': username
            }
        )
        if not created:
            lastfm_username.username = username
            lastfm_username.save()

        self.responser.reply_lastfmset(username)

    def _stats(self):
        """
        Command /stats
        Shows the links sent count for every user in the current chat
        """
        users = User.select(User, fn.Count(Link.url).alias('links')) \
            .join(Link, on=Link.user) \
            .join(Chat, on=Link.chat) \
            .where(Link.chat.id == self.update.message.chat_id) \
            .group_by(User) \
            .order_by(SQL('links').desc())

        self.responser.reply_stats(users)

    def _search(self):
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

        results = []
        if valid_entity_type and len(query) >= 3:
            search_result = self.spotify_client.search_link(query, entity_type)
            for result in search_result:
                thumb_url = ''
                description = ''

                if entity_type == EntityType.TRACK.value:
                    album = result['album']
                    artists = result['artists']
                    thumb_url = album['images'][0]['url']
                    description = '{} - {}'.format(', '.join(artist['name'] for artist in artists), album['name'])
                elif entity_type == EntityType.ALBUM.value:
                    thumb_url = result['images'][0]['url'] if len(result['images']) > 0 else ''
                    artists = result['artists']
                    description = ', '.join(artist['name'] for artist in artists)
                elif entity_type == EntityType.ARTIST.value:
                    thumb_url = result['images'][0]['url'] if len(result['images']) > 0 else ''
                    description = ', '.join(result['genres'])

                results.append(
                    InlineQueryResultArticle(
                        id=result['id'],
                        thumb_url=thumb_url,
                        title=result['name'],
                        description=description,
                        input_message_content=InputTextMessageContent(result['external_urls']['spotify'])
                    )
                )

        self.responser.show_search_results(results)

    def process_message(self):
        """
        Finds the streaming url, identifies the streaming service in the text and
        saves it to the database.
        It also saves the user and the chat if they don't exist @ database
        """
        url = self.LinkProcessor.extract_url_from_message(self.update.message.text)
        link_type = self.spotify_client.get_link_type(url)
        if url:
            if not self.spotify_client.is_valid_url(url) or not link_type:
                Logger.log_url_processing(url, False, self.update)
                return
            Logger.log_url_processing(url, True, self.update)
            self._process_url(url, link_type)

    def _process_url(self, url, link_type):
        cleaned_url = self.spotify_client.clean_url(url)
        entity_id = self.spotify_client.get_entity_id_from_url(cleaned_url)
        user = self._save_user()
        chat = self._save_chat()

        # Create or update the link
        link, was_updated = self._save_link(cleaned_url, link_type, user, chat)

        if link_type == LinkType.ARTIST:
            spotify_artist = self.spotify_client.client.artist(entity_id)
            artist = self._save_artist(spotify_artist)
            spotify_track = self.spotify_client.get_artist_top_track(artist)
            link.artist = artist
        elif link_type == LinkType.ALBUM:
            spotify_album = self.spotify_client.client.album(entity_id)
            album = self._save_album(spotify_album)
            spotify_track = self.spotify_client.get_album_first_track(album)
            link.album = album
        elif link_type == LinkType.TRACK:
            spotify_track = self.spotify_client.client.track(entity_id)
            track = self._save_track(spotify_track)
            link.track = track
        link.save()

        self.responser.reply_save_link(link, spotify_track, was_updated)

    # Operations
    def _save_artist(self, spotify_artist):
        image = spotify_artist['images'][0]['url'] if len(spotify_artist)['images'] > 0 else ''

        saved_artist, was_created = Artist.get_or_create(
            id=spotify_artist['id'],
            defaults={
                'name': spotify_artist['name'],
                'image': image,
                'popularity': spotify_artist['popularity'],
                'href': spotify_artist['href'],
                'spotify_url': spotify_artist['external_urls']['spotify'],
                'uri': spotify_artist['uri']})

        # Save or retrieve the genres
        if was_created:
            saved_genres = self._save_genres(spotify_artist['genres'])
            saved_artist.genres = saved_genres
            saved_artist.save()
            Logger.log_db_operation(Logger.DBOperation.CREATE, saved_artist)
        return saved_artist

    def _save_album(self, spotify_album):
        image = spotify_album['images'][0]['url'] if len(spotify_album)['images'] > 0 else ''

        saved_album, was_created = Album.get_or_create(
            id=spotify_album['id'],
            defaults={
                'name': spotify_album['name'],
                'label': spotify_album['label'],
                'image': image,
                'popularity': spotify_album['popularity'],
                'href': spotify_album['href'],
                'spotify_url': spotify_album['external_urls']['spotify'],
                'uri': spotify_album['uri']})

        if was_created:
            saved_artists = []
            for album_artist in spotify_album['artists']:
                artist_id = album_artist['id']
                artist = self.spotify_client.client.artist(artist_id)
                saved_artist = self._save_artist(artist)
                saved_artists.append(saved_artist)
            # Set the artists to the album
            saved_album.artists = saved_artist
            saved_album.save()

            saved_genres = self._save_genres(spotify_album['genres'])
            saved_album.genres = saved_genres
            saved_album.save()
            Logger.log_db_operation(Logger.DBOperation.CREATE, saved_album)
        return saved_album

    def _save_track(self, spotify_track):
        album_id = spotify_track['album']['id']
        album = self.spotify_client.client.album(album_id)
        saved_album = self._save_album(album)

        # Save the track (with the album)
        saved_track, was_created = Track.get_or_create(
            id=spotify_track['id'],
            defaults={
                'name': spotify_track['name'],
                'track_number ': spotify_track['track_number'],
                'duration_ms ': spotify_track['duration_ms'],
                'explicit': spotify_track['explicit'],
                'popularity ': spotify_track['popularity'],
                'href': spotify_track['href'],
                'spotify_url': spotify_track['external_urls']['spotify'],
                'preview_url ': spotify_track['preview_url'],
                'uri': spotify_track['uri'],
                'album': saved_album})

        if was_created:
            saved_artists = []
            for track_artist in spotify_track['artists']:
                artist_id = track_artist['id']
                artist = self.spotify_client.client.artist(artist_id)
                saved_artist = self._save_artist(artist)
                saved_artists.append(saved_artist)
            # Set the artists to the album
            saved_track.artists = saved_artists
            saved_track.save()
            Logger.log_db_operation(Logger.DBOperation.CREATE, saved_track)
        return saved_track

    def _save_genres(self, genres):
        saved_genres = []
        for genre in genres:
            saved_genre, was_created = Genre.get_or_create(name=genre)
            saved_genres.append(saved_genre)
            if was_created:
                Logger.log_db_operation(Logger.DBOperation.CREATE, saved_genre)
        return saved_genres

    def _save_user(self):
        # Create or get the user that sent the link
        user, was_created = User.get_or_create(
            id=self.update.message.from_user.id,
            defaults={
                'username': self.update.message.from_user.username,
                'first_name': self.update.message.from_user.first_name})
        if was_created:
            Logger.log_db_operation(Logger.DBOperation.CREATE, user)
        return user

    def _save_chat(self):
        # Create or get the chat where the link was sent
        chat, was_created = Chat.get_or_create(
            id=self.update.message.chat_id,
            defaults={
                'name': self.update.message.chat.title or self.update.message.chat.username or self.update.message.chat.first_name
            })
        if was_created:
            Logger.log_db_operation(Logger.DBOperation.CREATE, chat)
        return chat

    def _save_link(self, cleaned_url, link_type, user, chat):
        # Update the link if it exists for a chat, create if it doesn't exist
        link = Link.get_or_none((Link.url == cleaned_url) & (Link.chat == chat))
        was_updated = False
        if link is not None:
            # If link already exists, set updated_at and last_update_user to current
            link.apply_update(user)
            link.save()
            was_updated = True
            Logger.log_db_operation(Logger.DBOperation.UPDATE, link)
        else:
            link = Link.create(
                url=cleaned_url,
                link_type=link_type.value,
                created_at=datetime.datetime.now(),
                user=user,
                chat=chat)
            Logger.log_db_operation(Logger.DBOperation.CREATE, link)

        return link, was_updated
