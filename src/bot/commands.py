import datetime
import logging
from collections import defaultdict, OrderedDict

from telegram import Update
from telegram.ext import CallbackContext

from bot.api_client.api_client import APIClientException
from bot.api_client.lastfm_api_client import LastfmAPIClient
from bot.api_client.spotify_api_client import SpotifyAPIClient
from bot.api_client.telegram_api_client import TelegramAPIClient
from bot.buttons import DeleteSavedLinkButton, UnfollowArtistButton
from bot import emojis
from bot.logger import LoggerMixin
from bot.messages import UrlProcessor
from bot.models import Link, CreateOrUpdateMixin, Artist
from bot.music.music import LinkType
from bot.music.spotify import SpotifyUtils
from bot.reply import ReplyMixin
from bot.utils import OUTPUT_DATE_FORMAT

log = logging.getLogger(__name__)


class CommandFactory:
    """Handles the execution of the commands"""

    @staticmethod
    def run_start_command(update: Update, context: CallbackContext):
        command = StartCommand(update, context)
        command.run()

    @staticmethod
    def run_help_command(update: Update, context: CallbackContext):
        command = HelpCommand(update, context)
        command.run()

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
        if update.message.chat.type != 'group' and update.message.chat.type != 'supergroup':
            command = MyMusicCommand(update, context)
            command.run()

    @staticmethod
    def run_now_playing_command(update: Update, context: CallbackContext):
        command = NowPlayingCommand(update, context)
        command.run()

    @staticmethod
    def run_top_albums_command(update: Update, context: CallbackContext):
        command = TopAlbumsCommand(update, context)
        command.run()

    @staticmethod
    def run_lastfmset_command(update: Update, context: CallbackContext):
        command = LastFMSetCommand(update, context)
        command.run()

    @staticmethod
    def run_saved_links_command(update: Update, context: CallbackContext):
        command = SavedLinksCommand(update, context)
        command.run()

    @staticmethod
    def run_delete_saved_links_command(update: Update, context: CallbackContext):
        if update.message.chat.type != 'group' and update.message.chat.type != 'supergroup':
            command = DeleteSavedLinksCommand(update, context)
            command.run()

    @staticmethod
    def run_followed_artists_command(update: Update, context: CallbackContext):
        command = FollowedArtistsCommand(update, context)
        command.run()

    @staticmethod
    def run_follow_artist_command(update: Update, context: CallbackContext):
        command = FollowArtistCommand(update, context)
        command.run()

    @staticmethod
    def run_unfollow_artists_command(update: Update, context: CallbackContext):
        if update.message.chat.type != 'group' and update.message.chat.type != 'supergroup':
            command = UnfollowArtistsCommand(update, context)
            command.run()

    @staticmethod
    def run_check_artist_new_music_releases_command(update: Update, context: CallbackContext):
        command = CheckArtistsNewMusicReleasesCommand(update, context)
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


class StartCommand(Command):
    """
    Command /start
    Shows a help text of how to use the bot
    """
    COMMAND = 'start'

    def get_response(self):
        return self._build_message(), None

    @staticmethod
    def _build_message():
        msg = "Hey! I'm <strong>MusicBucket Bot</strong>. \n\n" \
              "My main purpose is to help you and your mates to share music between yourselves, with some useful " \
              "features I have like to <strong>collect Spotify links and displaying information</strong> about what " \
              "you've sent in a chat. \n" \
              "Also, you can use me to have a <strong>personal list of saved music</strong> to listen later! \n\n" \
              "To get more information about how to use me, use the /help command."
        return msg


class HelpCommand(Command):
    """
    Command /help
    Shows a list of the available commands and another useful features of the bot
    """
    COMMAND = 'help'

    def get_response(self):
        return self._build_message(), None

    @staticmethod
    def _build_message():
        msg = "I give information about sent Spotify links in a chat. " \
              "I also give you a button to save this link and check it later! \n\n" \
              "Here's a list of the available commands: \n" \
              "-  /music [@username] Retrieves the music shared in the chat from the last week. " \
              "Grouped by user. Filter by @username optionally. \n" \
              "-  /music_from_beginning @username Retrieves the music shared in the chat from the beginning. " \
              "of time by an user. \n" \
              "-  /savedlinks Retrieves a list with your saved links. \n" \
              "-  /deletesavedlinks Shows a list of buttons for deleting saved link. \n" \
              "-  /followedartists Return a list of followed artists. \n" \
              "-  /followartist spotify_artist_url Starts following an artist to be notified about album releases. \n" \
              "-  /unfollowartists Shows a list of buttons for unfollowing artists. \n" \
              "-  /checkartistsnewmusicreleases Shows a list of buttons for checking new album releases. \n" \
              "-  /mymusic Retrieves the music that you shared in all the chats. " \
              "It has to be called from a private conversation. \n" \
              "-  /recommendations Returns a list of 10 recommended tracks. " \
              "based on the sent albums from the last week. \n" \
              "-  /np Now Playing. Returns track information about what you are currently playing in Last.fm. \n" \
              "-  /lastfmset username Sets a Last.fm username to your Telegram user. \n" \
              "-  /stats Retrieves an user list with a links counter for the current chat. \n" \
              "-  @music_bucket_bot artist|album|track name Search for an artist, an album or a track. " \
              "and send it to the chat. \n\n"
        return msg


class MusicCommand(Command):
    """
    Command /music
    Gets the links sent by all the users of the chat in the last week
    and group them by user>links
    """
    COMMAND = 'music'
    DAYS = 7
    LAST_WEEK = datetime.datetime.now() - datetime.timedelta(days=DAYS)

    def __init__(self, update: Update, context: CallbackContext):
        super().__init__(update, context)
        self.telegram_api_client = TelegramAPIClient()

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
        for user, sent_links in last_week_links.items():
            msg += '- {} <strong>{}:</strong>\n'.format(emojis.EMOJI_USER, user)
            for sent_link in sent_links:
                link = sent_link.get('link')
                genres = Link.get_genres(link)
                msg += '    {} <a href="{}">{}</a> {}\n'.format(
                    emojis.get_music_emoji(link.get('link_type')),
                    link.get('url'),
                    Link.get_name(link),
                    '({})'.format(', '.join(genres)) if genres else ''
                )
            msg += '\n'
        return msg

    def _get_links(self):
        links = self.telegram_api_client.get_sent_links(
            chat_id=self.update.message.chat_id,
            since_date=self.LAST_WEEK
        )
        return links

    def _get_links_from_user(self):
        username = self.args[0]
        username = username.replace('@', '')
        links = self.telegram_api_client.get_sent_links(
            chat_id=self.update.message.chat_id,
            user_username=username,
            since_date=self.LAST_WEEK
        )
        return links

    @staticmethod
    def _group_links_by_user(links):
        last_week_links = defaultdict(list)
        for link in links:
            last_week_links[
                link.get('sent_by').get('username') if link.get('sent_by').get('username') else link.get('sent_by').get(
                    'first_name')].append(link)
        return dict(last_week_links)


class MusicFromBeginningCommand(Command):
    """
    Command /music_from_beginning @username
    Gets the links sent by an specific username of the chat from the beginning
    """
    COMMAND = 'music_from_beginning'

    def __init__(self, update: Update, context: CallbackContext):
        super().__init__(update, context)
        self.telegram_api_client = TelegramAPIClient()

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
        for user, sent_links in all_time_links.items():
            msg += '- {} <strong>{}:</strong>\n'.format(emojis.EMOJI_USER, user)
            for sent_link in sent_links:
                link = sent_link.get('link')
                genres = Link.get_genres(link)
                msg += '    {}  <a href="{}">{}</a> {}\n'.format(
                    emojis.get_music_emoji(link.get('link_type')),
                    f'[{datetime.datetime.fromisoformat(sent_link.get("sent_at")).strftime(OUTPUT_DATE_FORMAT)}]',
                    link.get('url'),
                    Link.get_name(link),
                    '({})'.format(', '.join(genres)) if genres else ''
                )
            msg += '\n'
        return msg

    def _get_links_from_user(self):
        username = self.args[0]
        username = username.replace('@', '')
        links = self.telegram_api_client.get_sent_links(
            chat_id=self.update.message.chat_id,
            user_username=username
        )
        return links

    @staticmethod
    def _group_links_by_user(links):
        all_time_links = defaultdict(list)
        for link in links:
            all_time_links[
                link.get('sent_by').get('username') if link.get('sent_by').get('username') else link.get('sent_by').get(
                    'first_name')].append(link)
        return dict(all_time_links)


class MyMusicCommand(Command):
    """
    Command /mymusic
    It can only be called from a private conversation
    Returns a list of the links sent by the caller user in all the chats from the beginning of time
    """
    COMMAND = 'mymusic'

    def __init__(self, update: Update, context: CallbackContext):
        super().__init__(update, context)
        self.telegram_api_client = TelegramAPIClient()

    def get_response(self):
        all_time_links = self._get_all_time_links_from_user()
        return self._build_message(all_time_links), None

    @staticmethod
    def _build_message(all_time_links):
        msg = '<strong>Music sent in all your chats from the beginning of time:</strong> \n'
        for sent_link in all_time_links:
            link = sent_link.get('link')
            genres = Link.get_genres(link)
            msg += '    {}  {} <a href="{}">{}</a> {}\n'.format(
                emojis.get_music_emoji(link.get('type')),
                '[{}@{}]'.format(
                    datetime.datetime.fromisoformat(sent_link.get('sent_at')).strftime(OUTPUT_DATE_FORMAT),
                    sent_link.get('chat').get('name')
                ),
                link.get('url'),
                Link.get_name(link),
                '({})'.format(', '.join(genres)) if genres else ''
            )
        msg += '\n'
        return msg

    def _get_all_time_links_from_user(self):
        links = self.telegram_api_client.get_sent_links(
            user_id=self.update.message.from_user.id
        )
        return links


class NowPlayingCommand(Command):
    """
    Command /np
    Shows which track is the user currently playing and saves it as a sent link
    """
    COMMAND = 'np'
    WEB_PAGE_PREVIEW = True

    def __init__(self, update, context):
        super().__init__(update, context)
        self.lastfm_api_client = LastfmAPIClient()
        self.spotify_api_client = SpotifyAPIClient()

    def get_response(self):
        now_playing_data = self.lastfm_api_client.get_now_playing(self.update.message.from_user.id)
        msg = self._build_message(now_playing_data)

        url_candidate = now_playing_data.get('url_candidate')
        if url_candidate:
            self._save_link(url_candidate)
        return msg, None

    @staticmethod
    def _build_message(now_playing_data):
        lastfm_user = now_playing_data.get('lastfm_user')
        if not lastfm_user or not lastfm_user.get('username'):
            return f'There is no Last.fm username for your user. Please set your username with:\n' \
                   f'<i>/lastfmset username</i>'
        if not now_playing_data.get('is_playing_now'):
            return f'<b>{lastfm_user.get("username")}</b> is not currently playing music'

        artist_name = now_playing_data.get('artist_name')
        album_name = now_playing_data.get('album_name')
        track_name = now_playing_data.get('track_name')
        cover = now_playing_data.get('cover')

        msg = f"<b>{lastfm_user.get('username')}</b>'s now playing:\n"
        msg += f"{emojis.EMOJI_TRACK} {track_name}\n"
        if album_name:
            msg += f"{emojis.EMOJI_ALBUM} {album_name}\n"
        if artist_name:
            msg += f"{emojis.EMOJI_ARTIST} {artist_name}\n"
        if cover:
            msg += f"<a href='{cover}'>&#8205;</a>"
        return msg

    def _save_link(self, url):
        url_processor = UrlProcessor(self.update, self.context, url, self)
        url_processor.process()


class TopAlbumsCommand(Command, CreateOrUpdateMixin):
    """
    Command /topalbums
    Gets the Last.fm top albums of the given user
    """
    COMMAND = 'topalbums'

    def __init__(self, update: Update, context: CallbackContext):
        super().__init__(update, context)
        self.lastfm_api_client = LastfmAPIClient()

    def get_response(self):
        self.save_user(self.update.message.from_user)
        top_albums_data = self.lastfm_api_client.get_top_albums(user_id=self.update.message.from_user.id)
        return self._build_message(top_albums_data), None

    @staticmethod
    def _build_message(top_albums_data: {}) -> str:
        top_albums = top_albums_data.get('top_albums', [])
        if not top_albums:
            return "You have not top albums"
        msg = f"<strong>{top_albums_data.get('lastfm_username')}</strong>'s top albums of last 7 days: \n"
        for album in top_albums:
            msg += f"- {emojis.EMOJI_ALBUM} <strong>{album['artist']}</strong> - <strong>{album['title']}</strong>. {album['scrobbles']} scrobbles\n"
        return msg


class LastFMSetCommand(Command, CreateOrUpdateMixin):
    """
    Command /lastfmset
    Sets the given Last.fm username to the current user
    """
    COMMAND = 'lastfmset'

    def __init__(self, update: Update, context: CallbackContext):
        super().__init__(update, context)
        self.telegram_api_client = TelegramAPIClient()
        self.lastfm_api_client = LastfmAPIClient()

    def get_response(self):
        # We call save_user() because we want to ensure
        # that the Telegram User already exists in the API Database
        self.save_user(self.update.message.from_user)

        lastfm_username = self._set_lastfm_username(self.update.message.from_user)
        return self._build_message(lastfm_username), None

    def _build_message(self, lastfm_username):
        if not lastfm_username:
            return self._help_message()
        return f"<strong>{lastfm_username}</strong>'s Last.fm username set correctly"

    def _set_lastfm_username(self, user):
        if not self.args:
            return None
        username = self.args[0]
        username = username.replace('@', '')
        user = self.telegram_api_client.create_user(user)
        lastfm_user = self.lastfm_api_client.set_lastfm_user(user.get('id'), username)
        return lastfm_user.get('username')

    @staticmethod
    def _help_message():
        return 'Command usage: /lastfmset username'


class SavedLinksCommand(Command):
    """
    Command /savedlinks
    Shows a list of the links that the user saved
    """
    COMMAND = 'savedlinks'

    def __init__(self, update: Update, context: CallbackContext):
        super().__init__(update, context)
        self.spotify_api_client = SpotifyAPIClient()

    def get_response(self):
        saved_links_response = self.spotify_api_client.get_saved_links(self.update.message.from_user.id)
        return self._build_message(saved_links_response), None

    @staticmethod
    def _build_message(saved_links_response: {}):
        if not saved_links_response:
            return 'You have not saved links'

        msg = '<strong>Saved links:</strong> \n'
        for saved_link in saved_links_response:
            link = saved_link.get('link')
            genres = Link.get_genres(link)
            msg += f'- {emojis.get_music_emoji(link.get("link_type"))} <a href="{link.get("url")}">{Link.get_name(link)}</a> ' \
                   f'({", ".join(genres) if genres else ""}). ' \
                   f'Saved at: {datetime.datetime.fromisoformat(saved_link.get("saved_at")).strftime(OUTPUT_DATE_FORMAT)}\n'
        return msg


class DeleteSavedLinksCommand(Command):
    """
    Command /deletesavedlinks
    Shows a list of buttons with the saved links and deletes them when clicking
    """
    COMMAND = 'deletesavedlinks'

    def __init__(self, update: Update, context: CallbackContext):
        super().__init__(update, context)
        self.spotify_api_client = SpotifyAPIClient()

    def get_response(self):
        keyboard = self._build_keyboard()
        if not keyboard:
            return 'You have not saved links', None
        return 'Choose a saved link to delete:', keyboard

    def _build_keyboard(self):
        saved_links_response = self.spotify_api_client.get_saved_links(self.update.message.from_user.id)
        if not saved_links_response:
            return None
        return DeleteSavedLinkButton.get_keyboard_markup(saved_links_response)


class FollowArtistMixin:

    @property
    def not_following_any_artist_message(self):
        return 'You are not following any artist'


class FollowedArtistsCommand(FollowArtistMixin, Command):
    """
    Command /followedartists
    Shows a list of the followed artists the request's user
    """
    COMMAND = 'followedartists'

    def __init__(self, update: Update, context: CallbackContext):
        super().__init__(update, context)
        self.telegram_api_client = TelegramAPIClient()
        self.spotify_api_client = SpotifyAPIClient()

    def get_response(self):
        followed_artists_response = self.spotify_api_client.get_followed_artists(self.update.message.from_user.id)
        return self._build_message(followed_artists_response), None

    def _build_message(self, followed_artists_response):
        if not followed_artists_response:
            return self.not_following_any_artist_message

        msg = '<strong>Following artists:</strong> \n'
        for followed_artist in followed_artists_response:
            artist = followed_artist.get('artist')
            msg += f'- {emojis.EMOJI_ARTIST} ' \
                   f'<a href="{artist.get("url")}">{artist.get("name")}</a> ' \
                   f'Followed at: {datetime.datetime.fromisoformat(followed_artist.get("followed_at")).strftime(OUTPUT_DATE_FORMAT)}\n'
        return msg


class FollowArtistCommand(CreateOrUpdateMixin, Command):
    """
    Command /followartist
    Allows user to follow an artist and be notified when they release an album
    """
    COMMAND = 'followartist'

    def __init__(self, update: Update, context: CallbackContext):
        super().__init__(update, context)
        self.spotify_api_client = SpotifyAPIClient()
        self.telegram_api_client = TelegramAPIClient()

    def get_response(self):
        if not self.args:
            return self.help_message, None
        url = self.args[0]
        try:
            spotify_artist_id = self._extract_artist_id_from_url(url)
        except ValueError:
            log.warning('Error trying to process artist url')
            return self.error_invalid_link_message, None
        user = self.save_user(self.update.message.from_user)
        artist = self.spotify_api_client.get_artist(spotify_artist_id)
        try:
            followed_artist_response = self.spotify_api_client.create_followed_artist(artist.get('id'), user.get('id'))
        except APIClientException as e:
            response = e.args[0].response
            if response.status_code == 400 and "unique" in response.text:
                return self.already_following_this_artist_message, None
            raise e
        return self._build_message(followed_artist_response), None

    def _extract_artist_id_from_url(self, url: str) -> Artist:
        url = self._url_cleaning_and_validations(url)
        return SpotifyUtils.get_entity_id_from_url(url)

    @staticmethod
    def _url_cleaning_and_validations(url: str) -> str:
        if not SpotifyUtils.is_valid_url(url):
            raise ValueError
        if SpotifyUtils.get_link_type_from_url(url) != LinkType.ARTIST.value:
            raise ValueError
        cleaned_url = SpotifyUtils.clean_url(url)
        return cleaned_url

    @property
    def already_following_this_artist_message(self):
        return 'You are already following this artist'

    @property
    def error_invalid_link_message(self):
        return 'Invalid artist link'

    @property
    def help_message(self):
        return 'Command usage:  /followartist spotify_artist_url'

    @staticmethod
    def _build_message(followed_artist_response: OrderedDict) -> str:
        artist = followed_artist_response.get('artist')
        msg = f'<strong>Followed artist:</strong> {artist.get("name")}. \n'
        msg += 'You will be aware of it\'s albums releases'
        return msg


class UnfollowArtistsCommand(FollowArtistMixin, Command):
    """
    Command /unfollowartist
    Shows a list of buttons with followed artists and deletes them when clicking
    """
    COMMAND = 'unfollowartists'

    def __init__(self, update: Update, context: CallbackContext):
        super().__init__(update, context)
        self.spotify_api_client = SpotifyAPIClient()

    def get_response(self):
        keyboard = self._build_keyboard()
        if not keyboard:
            return self.not_following_any_artist_message, None
        return 'Choose an artist to unfollow:', keyboard

    def _build_keyboard(self):
        followed_artists = self.spotify_api_client.get_followed_artists(self.update.message.from_user.id)
        if not followed_artists:
            return None
        return UnfollowArtistButton.get_keyboard_markup(followed_artists)


class CheckArtistsNewMusicReleasesCommand(FollowArtistMixin, CreateOrUpdateMixin, Command):
    """
    Command /checkartistsnewmusicreleases
    Shows a list of buttons with followed artists for checking their new album releases when clicking
    """
    COMMAND = 'checkartistsnewmusicreleases'

    def __init__(self, update: Update, context: CallbackContext):
        super().__init__(update, context)
        self.spotify_api_client = SpotifyAPIClient()

    def get_response(self):
        new_music_releases_response = self.spotify_api_client.check_new_music_releases(self.update.message.from_user.id)
        if not new_music_releases_response:
            return self.no_new_music_message, None
        message = self._build_message(new_music_releases_response), None
        return message

    @staticmethod
    def _build_message(new_music_releases_response: []) -> str:
        msg = 'Found new music: \n'
        for new_album in new_music_releases_response:
            new_album_first_artist = new_album.get('artists')[0]
            msg += f'    - <a href="{new_album.get("url")}">{new_album_first_artist.get("name")} - {new_album.get("name")} ({new_album.get("album_type")})</a> ' \
                   f'Released at: {datetime.datetime.fromisoformat(new_album.get("release_date")).strftime(OUTPUT_DATE_FORMAT)} \n'
        return msg

    @property
    def no_new_music_message(self):
        return 'There is no new music of your followed artists'


class StatsCommand(Command):
    """
    Command /stats
    Shows the links sent count for every user in the current chat
    """
    COMMAND = 'stats'

    def __init__(self, update: Update, context: CallbackContext):
        super().__init__(update, context)
        self.telegram_api_client = TelegramAPIClient()

    def get_response(self):
        stats = self.telegram_api_client.get_stats(self.update.message.chat_id)
        return self._build_message(stats), None

    @staticmethod
    def _build_message(stats: {}):
        msg = '<strong>Links sent by the users from the beginning in this chat:</strong> \n'
        users = stats.get('users_with_chat_link_count', [])
        most_sent_genres = stats.get('most_sent_genres', [])
        for user in users:
            msg += '- {} <strong>{}:</strong> {}\n'.format(
                emojis.EMOJI_USER,
                user.get('username') or user.get('first_name'),
                user.get('sent_links_chat__count')
            )
        msg += f'\n <strong>Most sent genres:</strong> {", ".join(most_sent_genres)}'
        return msg
