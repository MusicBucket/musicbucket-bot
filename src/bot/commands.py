import datetime
import logging
import random
from collections import defaultdict

from emoji import emojize
from peewee import fn, SQL
from telegram import Update
from telegram.ext import CallbackContext

from bot.buttons import DeleteSavedLinkButton
from bot.logger import LoggerMixin
from bot.messages import UrlProcessor
from bot.models import Chat, Link, Album, LastFMUsername, User, CreateOrUpdateMixin, SavedLink, Track, Artist
from bot.music.lastfm import LastFMClient
from bot.music.music import LinkType, EntityType
from bot.music.spotify import SpotifyClient
from bot.reply import ReplyMixin

log = logging.getLogger(__name__)


class CommandFactory:
    """Handles the execution of the commands"""

    @staticmethod
    def run_music_command(update: Update, context: CallbackContext):
        command = MusicCommand(update, context)
        command.run()

    @staticmethod
    def run_music_from_beginning_command(update: Update, context: CallbackContext):
        command = MusicFromBeginningCommand(update, context)
        command.run()

    @staticmethod
    def run_my_music_command(update: Update, context: CallbackContext):
        if update.message.chat.type != 'group':
            command = MyMusicCommand(update, context)
            command.run()

    @staticmethod
    def run_recommendations_command(update: Update, context: CallbackContext):
        command = RecommendationsCommand(update, context)
        command.run()

    @staticmethod
    def run_now_playing_command(update: Update, context: CallbackContext):
        command = NowPlayingCommand(update, context)
        command.run()

    @staticmethod
    def run_lastfmset_command(update: Update, context: CallbackContext):
        command = LastfmSetCommand(update, context)
        command.run()

    @staticmethod
    def run_saved_links_command(update: Update, context: CallbackContext):
        command = SavedLinksCommand(update, context)
        command.run()

    @staticmethod
    def run_delete_saved_links_command(update: Update, context: CallbackContext):
        if update.message.chat.type != 'group':
            command = DeleteSavedLinksCommand(update, context)
            command.run()

    @staticmethod
    def run_stats_command(update: Update, context: CallbackContext):
        command = StatsCommand(update, context)
        command.run()


class Command(ReplyMixin, LoggerMixin):
    COMMAND = None
    WEB_PAGE_PREVIEW = False

    def __init__(self, update, context):
        self.update = update
        self.context = context
        self.args = context.args or []

    def run(self):
        self.log_command(self.COMMAND, self.args, self.update)
        response, reply_markup = self.get_response()
        self.reply(self.update, self.context, response, disable_web_page_preview=not self.WEB_PAGE_PREVIEW,
                   reply_markup=reply_markup)

    def get_response(self):
        raise NotImplementedError()


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
        return self._build_message(last_week_links), None

    @staticmethod
    def _build_message(last_week_links):
        msg = '<strong>Music from the last week:</strong> \n'
        for user, links in last_week_links.items():
            msg += '- {} <strong>{}:</strong>\n'.format(emojize(':baby:', use_aliases=True),
                                                        user.username or user.first_name)
            for link in links:
                msg += '    {} <a href="{}">{}</a> {}\n'.format(
                    link.get_emoji(),
                    link.url,
                    str(link),
                    '({})'.format(link.genres[0]) if link.genres else ''
                )
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
            return self._build_message(all_time_links), None
        else:
            msg = 'Command usage /music_from_beginning @username'
            return msg, None

    @staticmethod
    def _build_message(all_time_links):
        msg = '<strong>Music from the beginning of time:</strong> \n'
        for user, links in all_time_links.items():
            msg += '- {} <strong>{}:</strong>\n'.format(
                emojize(':baby:', use_aliases=True), user.username or user.first_name
            )
            for link in links:
                msg += '    {}  {} <a href="{}">{}</a> {}\n'.format(
                    link.get_emoji(),
                    '[{}]'.format(
                        link.created_at.strftime("%Y/%m/%d"), ' | Updated @ {} by {}'.format(
                            link.updated_at.strftime("%Y/%m/%d"),
                            link.last_update_user.username or link.last_update_user.first_name or ''
                        ) if link.last_update_user else ''
                    ),
                    link.url,
                    str(link),
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


class MyMusicCommand(Command):
    """
    Command /mymusic
    It can only be called from a private conversation
    Returns a list of the links sent by the caller user in all the chats from the beginning of time
    """
    COMMAND = 'mymusic'

    def get_response(self):
        all_time_links = self._get_all_time_links_from_user()
        return self._build_message(all_time_links), None

    @staticmethod
    def _build_message(all_time_links):
        msg = '<strong>Music sent in all your chats from the beginning of time:</strong> \n'
        for link in all_time_links:
            msg += '    {}  {} <a href="{}">{}</a> {}\n'.format(
                link.get_emoji(),
                '[{}{}@{}]'.format(
                    link.created_at.strftime("%Y/%m/%d"), ' | Updated @ {} by {}'.format(
                        link.updated_at.strftime("%Y/%m/%d"),
                        link.last_update_user.username or link.last_update_user.first_name or ''
                    ) if link.last_update_user else '',
                    link.chat.name
                ),
                link.url,
                str(link),
                '({})'.format(link.genres[0]) if link.genres else '')
        msg += '\n'
        return msg

    def _get_all_time_links_from_user(self):
        links = Link.select() \
            .join(User, on=(User.id == Link.user)) \
            .join(Chat, on=(Chat.id == Link.chat)) \
            .where(User.id == self.update.message.from_user.id) \
            .order_by(Link.updated_at.asc(), Link.created_at.asc())
        return links


class RecommendationsCommand(Command):
    """
    Command /recommendations
    Returns a recommendations list based on the links sent during the last week
    """
    COMMAND = 'recommendations'
    DAYS = 7
    LAST_WEEK = datetime.datetime.now() - datetime.timedelta(days=DAYS)

    def __init__(self, update, context):
        super().__init__(update, context)
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
        return self._build_message(track_recommendations, artist_seeds), None

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
                Track.get_emoji(),
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
    WEB_PAGE_PREVIEW = True

    def __init__(self, update, context):
        super().__init__(update, context)
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
            url_candidate = self._search_for_spotify_url_candidate(now_playing)
            if url_candidate:
                self._save_link(url_candidate)
        return msg, None

    @staticmethod
    def _build_message(now_playing, username):
        if not username:
            return f'There is no Last.fm username for your user. Please set your username with:\n' \
                   f'<i>/lastfmset username</i>'
        if not now_playing:
            return f'<b>{username}</b> is not currently playing music'

        artist = now_playing.get('artist')
        album = now_playing.get('album')
        track = now_playing.get('track')
        cover = now_playing.get('cover')

        msg = f"<b>{username}</b>'s now playing:\n"
        msg += f"{Track.get_emoji()} {track.title}\n"
        if album:
            msg += f"{Album.get_emoji()} {album.title}\n"
        if artist:
            msg += f"{Artist.get_emoji()} {artist}\n"
        if cover:
            msg += f"<a href='{cover}'>&#8205;</a>"
        return msg

    def _search_for_spotify_url_candidate(self, now_playing):
        album = now_playing.get('album')
        track = now_playing.get('track')
        if album:
            results = self.spotify_client.search_link(album, EntityType.ALBUM.value)
        else:
            results = self.spotify_client.search_link(track, EntityType.TRACK.value)
        candidate = results[0] if results else None
        if candidate:
            return candidate['external_urls']['spotify']
        return

    def _save_link(self, url):
        url_processor = UrlProcessor(self.update, self.context, url, self)
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
        return self._build_message(lastfm_username), None

    @staticmethod
    def _build_message(lastfm_username):
        if not lastfm_username:
            return 'Command usage /lastfmset username'
        return f"<strong>{lastfm_username}</strong>'s Last.fm username set correctly"

    def _set_lastfm_username(self, user):
        if not self.args:
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


class SavedLinksCommand(Command):
    """
    Command /savedlinks
    Shows the links that the user saved
    """
    COMMAND = 'savedlinks'

    def get_response(self):
        saved_links = self._get_saved_links_by_user()
        return self._build_message(saved_links), None

    @staticmethod
    def _build_message(saved_links):
        if not saved_links:
            return 'You have not saved links'

        msg = '<strong>Saved links:</strong> \n'
        for saved_link in saved_links:
            msg += f'- {saved_link.link.get_emoji()} <a href="{saved_link.link.url}">{str(saved_link.link)}</a>. ' \
                   f'Saved at: {saved_link.saved_at.strftime("%Y/%m/%d")}\n'
        return msg

    def _get_saved_links_by_user(self):
        saved_links_by_user = (SavedLink
                               .select()
                               .join(Link)
                               .join(User)
                               .where((User.id == self.update.message.from_user.id) & (SavedLink.deleted_at is None)))
        return saved_links_by_user


class DeleteSavedLinksCommand(Command):
    """
    Command /deletesavedlinks
    Shows a list of buttons with the saved links and deletes the when clicking
    """
    COMMAND = 'deletesavedlinks'

    def get_response(self):
        keyboard = self._build_keyboard()
        if not keyboard:
            return 'You have not saved links', None
        return 'Choose a saved link to delete:', keyboard

    def _build_keyboard(self):
        saved_links = self._get_saved_links_by_user()
        if not saved_links:
            return None
        return DeleteSavedLinkButton.get_keyboard_markup(saved_links)

    def _get_saved_links_by_user(self):
        saved_links_by_user = (SavedLink
                               .select()
                               .join(Link)
                               .join(User)
                               .where((User.id == self.update.message.from_user.id) & (SavedLink.deleted_at is None)))
        return saved_links_by_user


class StatsCommand(Command):
    """
    Command /stats
    Shows the links sent count for every user in the current chat
    """
    COMMAND = 'stats'

    def get_response(self):
        stats_by_user = self._get_stats_by_user()
        return self._build_message(stats_by_user), None

    @staticmethod
    def _build_message(stats_by_user):
        msg = '<strong>Links sent by the users from the beginning in this chat:</strong> \n'
        for user in stats_by_user:
            msg += '- {} <strong>{}:</strong> {}\n'.format(
                User.get_emoji(),
                user.username or user.first_name,
                user.links
            )
        return msg

    def _get_stats_by_user(self):
        stats_by_user = User.select(User, fn.Count(Link.url).alias('links')) \
            .join(Link, on=Link.user) \
            .join(Chat, on=Link.chat) \
            .where(Link.chat.id == self.update.message.chat_id) \
            .group_by(User) \
            .order_by(SQL('links').desc())
        return stats_by_user
