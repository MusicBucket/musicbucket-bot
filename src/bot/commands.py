import datetime
import logging
import random
from collections import defaultdict

from emoji import emojize
from peewee import fn, SQL

from bot.logger import LoggerMixin
from bot.messages import UrlProcessor
from bot.models import Chat, Link, Album, LastFMUsername, User, CreateOrUpdateMixin
from bot.music.lastfm import LastFMClient
from bot.music.music import LinkType, EntityType
from bot.music.spotify import SpotifyClient
from bot.reply import ReplyMixin

log = logging.getLogger(__name__)


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
        command = NowPlayingCommand(bot, update)
        command.run()

    @staticmethod
    def run_lastfmset_command(bot, update, args):
        command = LastfmSetCommand(bot, update, args)
        command.run()

    @staticmethod
    def run_stats_command(bot, update):
        command = StatsCommand(bot, update)
        command.run()


class Command(ReplyMixin, LoggerMixin):
    COMMAND = None

    def __init__(self, bot, update, args=[]):
        self.bot = bot
        self.update = update
        self.args = args

    def get_response(self):
        return ''

    def run(self):
        self.log_command(self.COMMAND, self.args, self.update)
        self.reply(self.bot, self.update, self.get_response())


class MusicCommand(Command):
    """
    Command /music
    Gets the links sent by all the users of the chat in the last week
    and group them by user>links
    """
    COMMAND = 'music'
    DAYS = 7
    LAST_WEEK = datetime.datetime.now() - datetime.timedelta(days=DAYS)

    def get_response(self):
        if self.args:
            links = self._get_links_from_user()
        else:
            links = self._get_links()
        last_week_links = self._group_links_by_user(links)
        return self._build_message(last_week_links)

    @staticmethod
    def _build_message(last_week_links):
        msg = '<strong>Music from the last week:</strong> \n'
        for user, links in last_week_links.items():
            msg += '- {} <strong>{}:</strong>\n'.format(emojize(':baby:', use_aliases=True),
                                                        user.username or user.first_name)
            for link in links:
                if link.link_type == LinkType.ARTIST.value:
                    msg += '    {} <a href="{}">{}</a> {}\n'.format(
                        emojize(':busts_in_silhouette:', use_aliases=True),
                        link.url,
                        link.artist.name,
                        '({})'.format(link.genres[0]) if link.genres else '')
                elif link.link_type == LinkType.ALBUM.value:
                    msg += '    {} <a href="{}">{} - {}</a> {}\n'.format(
                        emojize(':cd:', use_aliases=True),
                        link.url,
                        link.album.get_first_artist().name if link.album.get_first_artist() else '',
                        link.album.name,
                        '({})'.format(link.genres[0]) if link.genres else '')
                elif link.link_type == LinkType.TRACK.value:
                    msg += '    {} <a href="{}">{} by {}</a> {}\n'.format(
                        emojize(':musical_note:', use_aliases=True),
                        link.url,
                        link.track.name,
                        link.track.artists.first().name if link.track.get_first_artist() else '',
                        '({})'.format(link.genres[0]) if link.genres else '')
            msg += '\n'
        return msg

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

    @staticmethod
    def _group_links_by_user(links):
        last_week_links = defaultdict(list)
        for link in links:
            last_week_links[link.user].append(link)
        return dict(last_week_links)


class MusicFromBeginningCommand(Command):
    """
    Command /music_from_beginning @username
    Gets the links sent by an specific username of the chat from the beginning
    """
    COMMAND = 'music_from_beginning'

    def get_response(self):
        if self.args:
            links = self._get_links_from_user()
            all_time_links = self._group_links_by_user(links)
            return self._build_message(all_time_links)
        else:
            msg = 'Command usage /music_from_beginning @username'
            return msg

    @staticmethod
    def _build_message(all_time_links):
        msg = '<strong>Music from the beginning of time:</strong> \n'
        for user, links in all_time_links.items():
            msg += '- {} <strong>{}:</strong>\n'.format(emojize(':baby:', use_aliases=True),
                                                        user.username or user.first_name)
            for link in links:
                if link.link_type == LinkType.ARTIST.value:
                    msg += '    {}  {} <a href="{}">{}</a> {}\n'.format(
                        emojize(':busts_in_silhouette:', use_aliases=True),
                        '[{}]'.format(link.created_at.strftime(
                            "%Y/%m/%d"),
                            ' | Updated @ {} by {}'.format(link.updated_at.strftime(
                                "%Y/%m/%d"),
                                link.last_update_user.username or link.last_update_user.first_name or '') if link.last_update_user else ''),
                        link.url,
                        link.artist.name,
                        '({})'.format(link.genres[0]) if link.genres else '')
                elif link.link_type == LinkType.ALBUM.value:
                    msg += '    {}  {} <a href="{}">{} - {}</a> {}\n'.format(
                        emojize(':cd:', use_aliases=True),
                        '[{}{}]'.format(link.created_at.strftime(
                            "%Y/%m/%d"),
                            ' | Updated @ {} by {}'.format(link.updated_at.strftime(
                                "%Y/%m/%d"),
                                link.last_update_user.username or link.last_update_user.first_name or '') if link.last_update_user else ''),
                        link.url,
                        link.album.artists[0].name,
                        link.album.name,
                        '({})'.format(link.genres[0]) if link.genres else '')
                elif link.link_type == LinkType.TRACK.value:
                    msg += '    {}  {} <a href="{}">{} by {}</a> {}\n'.format(
                        emojize(':musical_note:', use_aliases=True),
                        '[{}{}]'.format(link.created_at.strftime(
                            "%Y/%m/%d"),
                            ' | Updated @ {} by {}'.format(link.updated_at.strftime(
                                "%Y/%m/%d"),
                                link.last_update_user.username or link.last_update_user.first_name or '') if link.last_update_user else ''),
                        link.url,
                        link.track.name,
                        link.track.artists[0].name,
                        '({})'.format(link.genres[0]) if link.genres else '')
            msg += '\n'
        return msg

    def _get_links_from_user(self):
        username = self.args[0]
        username = username.replace('@', '')
        links = Link.select() \
            .join(Chat, on=(Chat.id == Link.chat)) \
            .join(User, on=(User.id == Link.user)) \
            .where((Chat.id == self.update.message.chat_id) & (User.username == username)) \
            .order_by(Link.updated_at.asc(), Link.created_at.asc())
        return links

    @staticmethod
    def _group_links_by_user(links):
        all_time_links = defaultdict(list)
        for link in links:
            all_time_links[link.user].append(link)
        return dict(all_time_links)


class RecommendationsCommand(Command):
    """
    Command /recommendations
    Returns a recommendations list based on the links sent during the last week
    """
    COMMAND = 'recommendations'
    DAYS = 7
    LAST_WEEK = datetime.datetime.now() - datetime.timedelta(days=DAYS)

    def __init__(self, bot, update):
        super().__init__(bot, update)
        self.spotify_client = SpotifyClient()

    def get_response(self):
        track_recommendations = {}
        artist_seeds = []
        album_seeds = self._get_album_seeds()
        if album_seeds:
            if len(album_seeds) > SpotifyClient.MAX_RECOMMENDATIONS_SEEDS:
                album_seeds = self._get_random_album_seeds(album_seeds)
            artist_seeds = [album.artists.first() for album in album_seeds]
            track_recommendations = self.spotify_client.get_recommendations(artist_seeds)
        return self._build_message(track_recommendations, artist_seeds)

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
    def _build_message(track_recommendations, artist_seeds):
        if not track_recommendations.get('tracks', []) or not artist_seeds:
            msg = 'There are not recommendations for this week yet. Send some music!'
            return msg

        artists_names = [artist.name for artist in artist_seeds]
        msg = 'Track recommendations of the week, based on the artists: <strong>{}</strong>\n'.format(
            '</strong>, <strong>'.join(artists_names))
        for track in track_recommendations['tracks']:
            msg += '{} <a href="{}">{}</a> by <strong>{}</strong>\n'.format(
                emojize(':musical_note:', use_aliases=True),
                track['external_urls']['spotify'],
                track['name'],
                track['artists'][0]['name'])
        return msg

    @staticmethod
    def _get_random_album_seeds(album_seeds):
        return random.sample(list(album_seeds), k=SpotifyClient.MAX_RECOMMENDATIONS_SEEDS)


class NowPlayingCommand(Command):
    """
    Command /np
    Shows which track is the user currently playing and saves it as a sent link
    """
    COMMAND = 'np'

    def __init__(self, bot, update):
        super().__init__(bot, update)
        self.lastfm_client = LastFMClient()
        self.spotify_client = SpotifyClient()

    def get_response(self):
        now_playing = None
        username = None
        from_user = self.update.message.from_user
        lastfm_username = LastFMUsername.get_or_none(from_user.id)
        if lastfm_username:
            username = lastfm_username.username
            now_playing = self.lastfm_client.now_playing(username)
        msg = self._build_message(now_playing, username)

        if now_playing:
            url_candidate = self._search_for_url_candidate(now_playing)
            if url_candidate:
                self._save_link(url_candidate)
        return msg

    @staticmethod
    def _build_message(now_playing, username):
        if not username:
            return f'There is no Last.fm username for your user. Please set your username with:\n' \
                f'<i>/lastfmset username</i>'
        if not now_playing:
            return f'<b>{username}</b> is not currently playing music'

        artist_emoji = emojize(':busts_in_silhouette:', use_aliases=True)
        album_emoji = emojize(':cd:', use_aliases=True)
        track_emoji = emojize(':musical_note:', use_aliases=True)
        artist = now_playing.get('artist')
        album = now_playing.get('album')
        track = now_playing.get('track')
        # cover = now_playing.get('cover')

        msg = f"<b>{username}</b>'s now playing:\n"
        msg += f"{track_emoji} {track.title}\n"
        if album:
            msg += f"{album_emoji} {album.title}\n"
        if artist:
            msg += f"{artist_emoji} {artist}\n"
        return msg

    def _search_for_url_candidate(self, now_playing):
        album = now_playing.get('album')
        track = now_playing.get('track')
        if album:
            results = self.spotify_client.search_link(album, EntityType.ALBUM.value)
        else:
            results = self.spotify_client.search_link(track, EntityType.TRACK.value)
        candidate = results[0] if results else None
        if candidate:
            return candidate['external_urls']['spotify']
        return None, None

    def _save_link(self, url):
        url_processor = UrlProcessor(self.bot, self.update, url)
        url_processor.process()


class LastfmSetCommand(Command, CreateOrUpdateMixin):
    """
    Command /lastfmset
    Sets the given Last.fm username to the current user
    """
    COMMAND = 'lastfmset'

    def get_response(self):
        self.save_chat(self.update)
        user = self.save_user(self.update)

        lastfm_username = self._set_lastfm_username(user)
        return self._build_message(lastfm_username)

    @staticmethod
    def _build_message(lastfm_username):
        if not lastfm_username:
            return 'Command usage /lastfmset username'
        return f"<b>{lastfm_username}</b>'s Last.fm username set correctly"

    def _set_lastfm_username(self, user):
        if not self.args == 0:
            return None

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

    def get_response(self):
        stats_by_user = self._get_stats_by_user()
        return self._build_message(stats_by_user)

    @staticmethod
    def _build_message(stats_by_user):
        msg = '<strong>Links sent by the users from the beginning in this chat:</strong> \n'
        for user in stats_by_user:
            msg += '- {} <strong>{}:</strong> {}\n'.format(emojize(':baby:', use_aliases=True),
                                                           user.username or user.first_name,
                                                           user.links)
        return msg

    def _get_stats_by_user(self):
        stats_by_user = User.select(User, fn.Count(Link.url).alias('links')) \
            .join(Link, on=Link.user) \
            .join(Chat, on=Link.chat) \
            .where(Link.chat.id == self.update.message.chat_id) \
            .group_by(User) \
            .order_by(SQL('links').desc())
        return stats_by_user
