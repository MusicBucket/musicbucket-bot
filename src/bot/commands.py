import datetime
import logging
import random
from collections import defaultdict

from peewee import fn, SQL

from bot.logger import LoggerMixin
from bot.messages import UrlProcessor
from bot.models import SaveChatMixin, SaveUserMixin, Chat, Link, Album, LastFMUsername, User
from bot.music.lastfm import LastFMClient
from bot.music.music import LinkType, EntityType
from bot.music.spotify import SpotifyClient
from bot.responser import Responser

logger = logging.getLogger(__name__)


class CommandFactory:
    """Handles the execution of a command"""

    @staticmethod
    def run_music_command(bot, update, args):
        command = MusicCommand(bot, update, args)
        command.run()

    @staticmethod
    def run_music_from_beginning_command(bot, update, args):
        command = MusicFromBeginningCommand(bot, update, args)
        command.run()

    @staticmethod
    def run_recommendations_command(bot, update):
        command = RecommendationsCommand(bot, update)
        command.run()

    @staticmethod
    def run_now_playing_command(bot, update):
        command = RecommendationsCommand(bot, update)
        command.run()

    @staticmethod
    def run_lastfmset_command(bot, update, args):
        command = LastfmSetCommand(bot, update, args)
        command.run()

    @staticmethod
    def run_stats_command(bot, update):
        command = StatsCommand(bot, update)
        command.run()


class Command(LoggerMixin):
    COMMAND = None

    def __init__(self, bot, update, args=[]):
        self.bot = bot
        self.update = update
        self.args = args

    def run(self):
        self.log_command(self.COMMAND, self.args, self.update)


class MusicCommand(Command):
    """
    Command /music
    Gets the links sent by all the users of the chat in the last week
    and group them by user>links
    """
    COMMAND = 'music'
    DAYS = 7
    LAST_WEEK = datetime.datetime.now() - datetime.timedelta(days=DAYS)

    def __init__(self, bot, update, args=[]):
        super().__init__(bot, update, args)
        self.responser = Responser(self.bot, self.update)
        self.last_week_links = defaultdict(list)

    def run(self):
        # TODO: Test si el self.__class__ de super duu el nom de la classe fill o el de la pare
        super().run()
        if len(self.args) > 0:
            links = self._get_links_from_user()
        else:
            links = self._get_links()
        self.last_week_links = self._group_links_by_user(links)
        self.responser.reply_music(self.last_week_links)

    def _get_links(self):
        links = Link.select() \
            .join(Chat) \
            .where(Chat.id == self.update.message.chat_id) \
            .where((Link.created_at >= self.LAST_WEEK) | (Link.updated_at >= self.LAST_WEEK)) \
            .order_by(Link.updated_at.asc(), Link.created_at.asc())
        return links

    def _get_links_from_user(self):
        username = self.args[0]
        username = username.replace('@', '')
        links = Link.select() \
            .join(Chat, on=(Chat.id == Link.chat)) \
            .join(User, on=(User.id == Link.user)) \
            .where((Chat.id == self.update.message.chat_id) & (User.username == username)) \
            .where((Link.created_at >= self.LAST_WEEK) | (Link.updated_at >= self.LAST_WEEK)) \
            .order_by(Link.updated_at.asc(), Link.created_at.asc())
        return links

    def _group_links_by_user(self, links):
        for link in links:
            self.last_week_links[link.user].append(link)
        return dict(self.last_week_links)


class MusicFromBeginningCommand(Command):
    """
    Command /music_from_beginning @username
    Gets the links sent by an specific username of the chat from the beginning
    """
    COMMAND = 'music_from_beginning'

    def __init__(self, bot, update, args=[]):
        super().__init__(bot, update, args)
        self.responser = Responser(self.bot, self.update)
        self.all_time_links = defaultdict(list)

    def run(self):
        super().run()
        if len(self.args) > 0:
            links = self._get_links_from_user()
            self.all_time_links = self._group_links_by_user(links)
            self.responser.reply_music_from_beginning(self.all_time_links)
        else:
            self.responser.error_music_from_beginning_no_username()

    def _get_links_from_user(self):
        username = self.args[0]
        username = username.replace('@', '')
        links = Link.select() \
            .join(Chat, on=(Chat.id == Link.chat)) \
            .join(User, on=(User.id == Link.user)) \
            .where((Chat.id == self.update.message.chat_id) & (User.username == username)) \
            .order_by(Link.updated_at.asc(), Link.created_at.asc())
        return links

    def _group_links_by_user(self, links):
        for link in links:
            self.all_time_links[link.user].append(link)
        return dict(self.all_time_links)


class RecommendationsCommand(Command):
    """
    Command /recommendations
    Returns a recommendations list based on the links sent during the last week
    """
    COMMAND = 'recommendations'
    DAYS = 7
    LAST_WEEK = datetime.datetime.now() - datetime.timedelta(days=DAYS)

    def __init__(self, bot, update, args=[]):
        super().__init__(bot, update, args)
        self.spotify_client = SpotifyClient()
        self.responser = Responser(self.bot, self.update)
        self.artist_seeds = []
        self.track_recommendations = []

    def run(self):
        super().run()

        album_seeds = self._get_album_seeds()
        if len(album_seeds) > 0:
            if len(album_seeds) > SpotifyClient.MAX_RECOMMENDATIONS_SEEDS:
                album_seeds = self._get_random_album_seeds(album_seeds)
            self.artist_seeds = [album.artists.first() for album in album_seeds]
            self.track_recommendations = self.spotify_client.get_recommendations(self.artist_seeds)

        self.responser.reply_recommendations(self.track_recommendations, self.artist_seeds)

    def _get_album_seeds(self):
        album_seeds = Album.select() \
            .join(Link) \
            .join(Chat) \
            .where(Chat.id == self.update.message.chat_id) \
            .where((Link.created_at >= self.LAST_WEEK) | (Link.updated_at >= self.LAST_WEEK)) \
            .where(Link.link_type == LinkType.ALBUM.value) \
            .order_by(Link.updated_at.asc(), Link.created_at.asc())
        return album_seeds

    @staticmethod
    def _get_random_album_seeds(album_seeds):
        return random.sample(list(album_seeds), k=SpotifyClient.MAX_RECOMMENDATIONS_SEEDS)


class NowPlayingCommand(Command):
    """
    Command /np
    Shows which track is the user currently playing and saves it as a sent link
    """
    COMMAND = 'np'

    def __init__(self, bot, update, args=[]):
        super().__init__(bot, update, args)
        self.lastfm_client = LastFMClient()
        self.spotify_client = SpotifyClient()
        self.responser = Responser(self.bot, self.update)
        self.username = None
        self.now_playing = None

    def run(self):
        super().run()
        from_user = self.update.from_user
        lastfm_username = LastFMUsername.get_or_none(from_user.id)
        if lastfm_username:
            self.username = lastfm_username.username
            self.now_playing = self.lastfm_client.now_playing(self.username)
        self.responser.reply_now_playing(self.now_playing, self.username)

        if self.now_playing:
            url_candidate = self._search_for_url_candidate()
            if url_candidate:
                self._save_link(url_candidate)

    def _search_for_url_candidate(self):
        album = self.now_playing.get('album')
        track = self.now_playing.get('track')
        if album:
            results = self.spotify_client.search_link(album, EntityType.ALBUM.value)
        else:
            results = self.spotify_client.search_link(track, EntityType.TRACK.value)
        candidate = results[0] if len(results) > 0 else None
        if candidate:
            return candidate['external_urls']['spotify']
        return None, None

    def _save_link(self, url):
        url_processor = UrlProcessor(self.bot, self.update, url)
        url_processor.process()


class LastfmSetCommand(Command, SaveChatMixin, SaveUserMixin):
    """
    Command /lastfmset
    Sets the given Last.fm username to the current user
    """
    COMMAND = 'lastfmset'

    def __init__(self, bot, update, args=[]):
        super().__init__(bot, update, args)
        self.responser = Responser(self.bot, self.update)
        self.lastfm_username = None

    def run(self):
        super().run()

        if len(self.args) == 0:
            self.responser.error_lastfmset_username_no_username()
            return

        self.save_chat(self.update)
        user = self.save_user(self.update)

        self.lastfm_username = self._set_lastfm_username(user)
        self.responser.reply_lastfmset(self.lastfm_username)

    def _set_lastfm_username(self, user):
        username = self.args[0]
        username = username.replace('@', '')

        lastfm_username, created = LastFMUsername.get_or_create(
            user=user,
            defaults={
                'username': username
            }
        )
        if not created:
            lastfm_username.username = username
            lastfm_username.save()
        return username


class StatsCommand(Command):
    """
    Command /stats
    Shows the links sent count for every user in the current chat
    """
    COMMAND = 'stats'

    def __init__(self, bot, update, args=[]):
        super().__init__(bot, update, args)
        self.responser = Responser(self.bot, self.update)

    def run(self):
        super().run()
        stats_by_user = self._get_stats_by_user()
        self.responser.reply_stats(stats_by_user)

    def _get_stats_by_user(self):
        stats_by_user = User.select(User, fn.Count(Link.url).alias('links')) \
            .join(Link, on=Link.user) \
            .join(Chat, on=Link.chat) \
            .where(Link.chat.id == self.update.message.chat_id) \
            .group_by(User) \
            .order_by(SQL('links').desc())
        return stats_by_user
