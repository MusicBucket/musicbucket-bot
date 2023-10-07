import datetime
import logging
from collections import defaultdict, OrderedDict
from typing import Dict, Optional, Tuple, Any, List

from telegram import Update
from telegram import User as TgUser
from telegram.ext import CallbackContext, ContextTypes
from telegram.ext import CallbackContext, ContextTypes

from bot.api_client.api_client import APIClientException
from bot.api_client.lastfm_api_client import LastfmAPIClient
from bot.api_client.spotify_api_client import SpotifyAPIClient
from bot.api_client.telegram_api_client import TelegramAPIClient
from bot.buttons import DeleteSavedLinkButton, UnfollowArtistButton
from bot import emojis
from bot.logger import LoggerMixin
from bot.messages import UrlProcessor
from bot.models import Link, SaveTelegramEntityMixin, Artist, Album, Track, \
    User
from bot.music.music import LinkType
from bot.music.spotify import SpotifyUtils
from bot.reply import ReplyMixin, ReplyType
from bot.utils import OUTPUT_DATE_FORMAT

log = logging.getLogger(__name__)


class CommandFactory:
    """Handles the execution of the commands"""

    @staticmethod
    async def run_start_command(update: Update,
                                context: ContextTypes.DEFAULT_TYPE):
        command = StartCommand(update, context)
        await command.run()

    @staticmethod
    async def run_help_command(update: Update,
                               context: ContextTypes.DEFAULT_TYPE):
        command = HelpCommand(update, context)
        await command.run()

    @staticmethod
    async def run_music_command(update: Update,
                                context: ContextTypes.DEFAULT_TYPE):
        command = MusicCommand(update, context)
        await command.run()

    @staticmethod
    async def run_music_from_beginning_command(update: Update,
                                               context: ContextTypes.DEFAULT_TYPE):
        command = MusicFromBeginningCommand(update, context)
        await command.run()

    @staticmethod
    async def run_my_music_command(update: Update,
                                   context: ContextTypes.DEFAULT_TYPE):
        if update.message.chat.type != 'group' and update.message.chat.type != 'supergroup':
            command = MyMusicCommand(update, context)
            await command.run()

    @staticmethod
    async def run_now_playing_command(update: Update,
                                      context: ContextTypes.DEFAULT_TYPE):
        command = NowPlayingCommand(update, context)
        await command.run()

    @staticmethod
    async def run_collage_command(update: Update,
                                  context: ContextTypes.DEFAULT_TYPE):
        command = CollageCommand(update, context)
        command.run()

    @staticmethod
    async def run_top_albums_command(update: Update,
                                     context: ContextTypes.DEFAULT_TYPE):
        command = TopAlbumsCommand(update, context)
        await command.run()

    @staticmethod
    async def run_top_artists_command(update: Update,
                                      context: ContextTypes.DEFAULT_TYPE):
        command = TopArtistsCommand(update, context)
        await command.run()

    @staticmethod
    async def run_top_tracks_command(update: Update,
                                     context: ContextTypes.DEFAULT_TYPE):
        command = TopTracksCommand(update, context)
        await command.run()

    @staticmethod
    async def run_lastfmset_command(update: Update,
                                    context: ContextTypes.DEFAULT_TYPE):
        command = LastFMSetCommand(update, context)
        await command.run()

    @staticmethod
    async def run_saved_links_command(update: Update,
                                      context: ContextTypes.DEFAULT_TYPE):
        command = SavedLinksCommand(update, context)
        await command.run()

    @staticmethod
    async def run_delete_saved_links_command(update: Update,
                                             context: ContextTypes.DEFAULT_TYPE):
        if update.message.chat.type != 'group' and update.message.chat.type != 'supergroup':
            command = DeleteSavedLinksCommand(update, context)
            await command.run()

    @staticmethod
    async def run_followed_artists_command(update: Update,
                                           context: ContextTypes.DEFAULT_TYPE):
        command = FollowedArtistsCommand(update, context)
        await command.run()

    @staticmethod
    async def run_follow_artist_command(update: Update,
                                        context: ContextTypes.DEFAULT_TYPE):
        command = FollowArtistCommand(update, context)
        await command.run()

    @staticmethod
    async def run_unfollow_artists_command(update: Update,
                                           context: ContextTypes.DEFAULT_TYPE):
        if update.message.chat.type != 'group' and update.message.chat.type != 'supergroup':
            command = UnfollowArtistsCommand(update, context)
            await command.run()

    @staticmethod
    async def run_check_artist_new_music_releases_command(update: Update,
                                                          context: ContextTypes.DEFAULT_TYPE):
        command = CheckArtistsNewMusicReleasesCommand(update, context)
        await command.run()

    @staticmethod
    async def run_stats_command(update: Update,
                                context: ContextTypes.DEFAULT_TYPE):
        command = StatsCommand(update, context)
        await command.run()


class Command(ReplyMixin, SaveTelegramEntityMixin, LoggerMixin):
    COMMAND = None
    WEB_PAGE_PREVIEW = False
    SAVE_USER_AND_CHAT = True

    def __init__(self, update, context):
        self.update = update
        self.context = context
        self.args = context.args or []

    async def run(self):
        self.log_command(self.COMMAND, self.args, self.update)
        response, reply_markup = await self.get_response()
        await self.reply(
            self.update,
            self.context,
            response,
            disable_web_page_preview=not self.WEB_PAGE_PREVIEW,
            reply_markup=reply_markup
        )

    async def get_response(self):
        if self.SAVE_USER_AND_CHAT:
            await self.save_user(self.update.message.from_user)
            await self.save_chat(self.update.message.chat)
        return await self._get_response()

    async def _get_response(self):
        raise NotImplementedError()


class StartCommand(Command):
    """
    Command /start
    Shows a help text of how to use the bot
    """
    COMMAND = 'start'

    async def _get_response(self) -> Tuple[Any, Optional[Any]]:
        return self._build_message(), None

    @staticmethod
    def _build_message() -> str:
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

    async def _get_response(self) -> Tuple[Any, Optional[Any]]:
        return self._build_message(), None

    @staticmethod
    def _build_message() -> str:
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
              "-  /collage [rows] [cols] [period](7day 'default'/1month/3month/6month/12month/overall) " \
              "Returns a collage of your most listened albums in a period. \n" \
              "-  /topalbums [period](7day 'default'/1month/3month/6month/12month/overall) " \
              "Top Albums. Returns the Last.fm top albums of your user. \n" \
              "-  /topartists [period](7day 'default'/1month/3month/6month/12month/overall) " \
              "Top Artists. Returns the Last.fm top artists of your user. \n" \
              "-  /toptracks [period](7day 'default'/1month/3month/6month/12month/overall) " \
              "Top Tracks. Returns the Last.fm top tracks of your user. \n" \
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

    async def _get_response(self) -> Tuple[Any, Optional[Any]]:
        if self.args:
            links = self._get_links_from_user()
        else:
            links = self._get_links()
        last_week_links = self._group_links_by_user(links)
        return self._build_message(last_week_links), None

    @staticmethod
    def _build_message(last_week_links) -> str:
        msg = '<strong>Music from the last week:</strong> \n'
        for user, sent_links in last_week_links.items():
            msg += '- {} <strong>{}:</strong>\n'.format(
                User.EMOJI,
                user
            )
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

    def _get_links(self) -> List[Dict]:
        links = self.telegram_api_client.get_sent_links(
            chat_id=self.update.message.chat_id,
            since_date=self.LAST_WEEK
        )
        return links

    def _get_links_from_user(self) -> List[Dict]:
        username = self.args[0]
        username = username.replace('@', '')
        links = self.telegram_api_client.get_sent_links(
            chat_id=self.update.message.chat_id,
            user_username=username,
            since_date=self.LAST_WEEK
        )
        return links

    @staticmethod
    def _group_links_by_user(links) -> Dict:
        last_week_links = defaultdict(list)
        for link in links:
            last_week_links[
                link.get('sent_by').get('username') if link.get('sent_by').get(
                    'username') else link.get('sent_by').get(
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

    async def _get_response(self) -> Tuple[Any, Optional[Any]]:
        if self.args:
            links = self._get_links_from_user()
            all_time_links = self._group_links_by_user(links)
            return self._build_message(all_time_links), None
        else:
            msg = 'Command usage /music_from_beginning @username'
            return msg, None

    @staticmethod
    def _build_message(all_time_links) -> str:
        msg = '<strong>Music from the beginning of time:</strong> \n'
        for user, sent_links in all_time_links.items():
            msg += '- {} <strong>{}:</strong>\n'.format(User.EMOJI, user)
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

    def _get_links_from_user(self) -> List[Dict]:
        username = self.args[0]
        username = username.replace('@', '')
        links = self.telegram_api_client.get_sent_links(
            chat_id=self.update.message.chat_id,
            user_username=username
        )
        return links

    @staticmethod
    def _group_links_by_user(links) -> Dict:
        all_time_links = defaultdict(list)
        for link in links:
            all_time_links[
                link.get('sent_by').get('username') if link.get('sent_by').get(
                    'username') else link.get('sent_by').get(
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

    async def _get_response(self) -> Tuple[Any, Optional[Any]]:
        all_time_links = self._get_all_time_links_from_user()
        return self._build_message(all_time_links), None

    @staticmethod
    def _build_message(all_time_links) -> str:
        msg = '<strong>Music sent in all your chats from the beginning of time:</strong> \n'
        for sent_link in all_time_links:
            link = sent_link.get('link')
            genres = Link.get_genres(link)
            msg += '    {}  {} <a href="{}">{}</a> {}\n'.format(
                emojis.get_music_emoji(link.get('type')),
                '[{}@{}]'.format(
                    datetime.datetime.fromisoformat(
                        sent_link.get('sent_at')).strftime(OUTPUT_DATE_FORMAT),
                    sent_link.get('chat').get('name')
                ),
                link.get('url'),
                Link.get_name(link),
                '({})'.format(', '.join(genres)) if genres else ''
            )
        msg += '\n'
        return msg

    def _get_all_time_links_from_user(self) -> List[Dict]:
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

    async def _get_response(self) -> Tuple[Any, Optional[Any]]:
        now_playing_data = self.lastfm_api_client.get_now_playing(
            self.update.message.from_user.id)
        msg = self._build_message(now_playing_data)

        url_candidate = now_playing_data.get('url_candidate')
        if url_candidate:
            await self._save_link(url_candidate)
            return None, None
        else:
            return msg, None

    @staticmethod
    def _build_message(now_playing_data) -> str:
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
        msg += f"{Track.EMOJI} {track_name}\n"
        if album_name:
            msg += f"{Album.EMOJI} {album_name}\n"
        if artist_name:
            msg += f"{Artist.EMOJI} {artist_name}\n"
        if cover:
            msg += f"<a href='{cover}'>&#8205;</a>"
        return msg

    async def _save_link(self, url):
        url_processor = UrlProcessor(self.update, self.context, url, self)
        await url_processor.process()


class CollageCommand(Command):
    """
    Command /collage
    Returns an image of a top albums or artists from a given period and custom size
    """
    COMMAND = 'collage'

    def __init__(self, update, context):
        super().__init__(update, context)
        self.lastfm_api_client = LastfmAPIClient()

    def run(self):
        """Need to override the method because the response type must be an Image"""
        self.log_command(self.COMMAND, self.args, self.update)
        response, reply_markup = self.get_response()
        if type(response) == bytes:
            # we have an image
            self.reply(self.update, self.context, message="", image=response,
                       reply_type=ReplyType.IMAGE,
                       disable_web_page_preview=not self.WEB_PAGE_PREVIEW,
                       reply_markup=reply_markup)
        else:
            # we have an error message
            self.reply(self.update, self.context, response,
                       disable_web_page_preview=not self.WEB_PAGE_PREVIEW,
                       reply_markup=reply_markup)

    async def _get_response(self) -> Tuple[Any, Optional[Any]]:
        try:
            collage_image_data = self.lastfm_api_client.get_collage(
                self.update.message.from_user.id, *self.args[0:3])
        except APIClientException:
            # TODO: Check if the APIClientException is a 404
            return self._build_message(), None
        except Exception:
            return self.help_message, None
        return collage_image_data, None

    @staticmethod
    def _build_message() -> str:
        return f'There is no Last.fm username for your user. Please set your username with:\n' \
               f'<i>/lastfmset username</i>'

    @property
    def help_message(self) -> str:
        return 'Command usage: ' \
               '/collage <rows (max:5. Default: 5)> ' \
               '<cols (max:5. Default: 5)> ' \
               '<period (7day/1month/3month/6month/12month/overall. Default: 7day>'


class TopAlbumsCommand(Command):
    """
    Command /topalbums
    Gets the Last.fm top albums of the given user
    """
    COMMAND = 'topalbums'

    def __init__(self, update: Update, context: CallbackContext):
        super().__init__(update, context)
        self.lastfm_api_client = LastfmAPIClient()

    async def _get_response(self) -> Tuple[Any, Optional[Any]]:
        if self.args:
            period = self.args[0]
            if not period in self.lastfm_api_client.PERIODS:
                return self.help_message, None
            top_albums_data = self.lastfm_api_client.get_top_albums(
                user_id=self.update.message.from_user.id,
                period=period
            )
        else:
            top_albums_data = self.lastfm_api_client.get_top_albums(
                user_id=self.update.message.from_user.id)
        return self._build_message(top_albums_data), None

    @staticmethod
    def _build_message(top_albums_data: Dict) -> str:
        lastfm_user = top_albums_data.get('lastfm_user')
        if not lastfm_user or not lastfm_user.get('username'):
            return f'There is no Last.fm username for your user. Please set your username with:\n' \
                   f'<i>/lastfmset username</i>'
        top_albums = top_albums_data.get('top_albums', [])
        if not top_albums:
            return "You have not top albums"
        msg = f"<strong>{lastfm_user.get('username')}</strong>'s top albums of the period: \n"
        for album in top_albums[:10]:
            msg += f"- {Album.EMOJI} <strong>{album['artist']}</strong> - <strong>{album['title']}</strong>. {album['scrobbles']} scrobbles\n"
        return msg

    @property
    def help_message(self) -> str:
        return "Command usage: /topalbums [period] (7day 'default'/1month/3month/6month/12month/overall)"


class TopArtistsCommand(Command):
    """
    Command /topartists
    Gets the Last.fm top artists of the given user
    """
    COMMAND = 'topartists'

    def __init__(self, update: Update, context: CallbackContext):
        super().__init__(update, context)
        self.lastfm_api_client = LastfmAPIClient()

    async def _get_response(self) -> Tuple[Any, Optional[Any]]:
        if self.args:
            period = self.args[0]
            if period not in self.lastfm_api_client.PERIODS:
                return self.help_message, None
            top_artists_data = self.lastfm_api_client.get_top_artists(
                user_id=self.update.message.from_user.id,
                period=period
            )
        else:
            top_artists_data = self.lastfm_api_client.get_top_artists(
                user_id=self.update.message.from_user.id)
        return self._build_message(top_artists_data), None

    @staticmethod
    def _build_message(top_artists_data: Dict) -> str:
        lastfm_user = top_artists_data.get('lastfm_user')
        if not lastfm_user or not lastfm_user.get('username'):
            return f'There is no Last.fm username for your user. Please set your username with:\n' \
                   f'<i>/lastfmset username</i>'
        top_artists = top_artists_data.get('top_artists', [])
        if not top_artists:
            return "You have not top artists"
        msg = f"<strong>{lastfm_user.get('username')}</strong>'s top artists of the period: \n"
        for artist in top_artists[:10]:
            msg += f"- {Artist.EMOJI} <strong>{artist['name']}</strong>. {artist['scrobbles']} scrobbles\n"
        return msg

    @property
    def help_message(self) -> str:
        return "Command usage: /topartists [period] (7day 'default'/1month/3month/6month/12month/overall)"


class TopTracksCommand(Command):
    """
    Command /toptracks
    Gets the Last.fm top albums of the given user
    """
    COMMAND = 'toptracks'

    def __init__(self, update: Update, context: CallbackContext):
        super().__init__(update, context)
        self.lastfm_api_client = LastfmAPIClient()

    async def _get_response(self) -> Tuple[Any, Optional[Any]]:
        if self.args:
            period = self.args[0]
            if period not in self.lastfm_api_client.PERIODS:
                return self.help_message, None
            top_tracks_data = self.lastfm_api_client.get_top_tracks(
                user_id=self.update.message.from_user.id,
                period=period
            )
        else:
            top_tracks_data = self.lastfm_api_client.get_top_tracks(
                user_id=self.update.message.from_user.id)
        return self._build_message(top_tracks_data), None

    @staticmethod
    def _build_message(top_tracks_data: Dict) -> str:
        lastfm_user = top_tracks_data.get('lastfm_user')
        if not lastfm_user or not lastfm_user.get('username'):
            return f'There is no Last.fm username for your user. Please set your username with:\n' \
                   f'<i>/lastfmset username</i>'
        top_tracks = top_tracks_data.get('top_tracks', [])
        if not top_tracks:
            return "You have not top tracks"
        msg = f"<strong>{lastfm_user.get('username')}</strong>'s top tracks of the period: \n"
        for track in top_tracks[:10]:
            msg += f"- {Album.EMOJI} <strong>{track['artist']}</strong> - <strong>{track['title']}</strong>. {track['scrobbles']} scrobbles\n"
        return msg

    @property
    def help_message(self) -> str:
        return "Command usage: /toptracks [period] (7day 'default'/1month/3month/6month/12month/overall)"


class LastFMSetCommand(Command):
    """
    Command /lastfmset
    Sets the given Last.fm username to the current user
    """
    COMMAND = 'lastfmset'

    def __init__(self, update: Update, context: CallbackContext):
        super().__init__(update, context)
        self.telegram_api_client = TelegramAPIClient()
        self.lastfm_api_client = LastfmAPIClient()

    @property
    def help_message(self) -> str:
        return 'Command usage: /lastfmset username'

    async def _get_response(self) -> Tuple[Any, Optional[Any]]:
        lastfm_username = self._set_lastfm_username(
            self.update.message.from_user)
        return self._build_message(lastfm_username), None

    def _set_lastfm_username(self, user: TgUser) -> Optional[str]:
        if not self.args:
            return None
        username = self.args[0]
        username = username.replace('@', '')
        user = self.telegram_api_client.create_user(user)
        lastfm_user = self.lastfm_api_client.set_lastfm_user(user.get('id'),
                                                             username)
        return lastfm_user.get('username')

    def _build_message(self, lastfm_username: str) -> str:
        if not lastfm_username:
            return self.help_message
        return f"<strong>{lastfm_username}</strong>'s Last.fm username set correctly"


class SavedLinksCommand(Command):
    """
    Command /savedlinks
    Shows a list of the links that the user saved
    """
    COMMAND = 'savedlinks'

    def __init__(self, update: Update, context: CallbackContext):
        super().__init__(update, context)
        self.spotify_api_client = SpotifyAPIClient()

    async def _get_response(self) -> Tuple[Any, Optional[Any]]:
        saved_links_response = self.spotify_api_client.get_saved_links(
            self.update.message.from_user.id)
        return self._build_message(saved_links_response), None

    @staticmethod
    def _build_message(saved_links_response: {}) -> str:
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

    async def _get_response(self) -> Tuple[Any, Optional[Any]]:
        keyboard = self._build_keyboard()
        if not keyboard:
            return 'You have not saved links', None
        return 'Choose a saved link to delete:', keyboard

    def _build_keyboard(self):
        saved_links_response = self.spotify_api_client.get_saved_links(
            self.update.message.from_user.id)
        if not saved_links_response:
            return None
        return DeleteSavedLinkButton.get_keyboard_markup(saved_links_response)


class FollowArtistMixin:

    @property
    def not_following_any_artist_message(self) -> str:
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

    async def _get_response(self) -> Tuple[Any, Optional[Any]]:
        followed_artists_response = self.spotify_api_client.get_followed_artists(
            self.update.message.from_user.id)
        return self._build_message(followed_artists_response), None

    def _build_message(self, followed_artists_response) -> str:
        if not followed_artists_response:
            return self.not_following_any_artist_message

        msg = '<strong>Following artists:</strong> \n'
        for followed_artist in followed_artists_response:
            artist = followed_artist.get('artist')
            msg += f'- {Artist.EMOJI} ' \
                   f'<a href="{artist.get("url")}">{artist.get("name")}</a> ' \
                   f'Followed at: {datetime.datetime.fromisoformat(followed_artist.get("followed_at")).strftime(OUTPUT_DATE_FORMAT)}\n'
        return msg


class FollowArtistCommand(Command):
    """
    Command /followartist
    Allows user to follow an artist and be notified when they release an album
    """
    COMMAND = 'followartist'

    def __init__(self, update: Update, context: CallbackContext):
        super().__init__(update, context)
        self.spotify_api_client = SpotifyAPIClient()
        self.telegram_api_client = TelegramAPIClient()

    async def _get_response(self) -> Tuple[Any, Optional[Any]]:
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
            followed_artist_response = self.spotify_api_client.create_followed_artist(
                artist.get('id'), user.get('id'))
        except APIClientException as e:
            response = e.args[0].response
            if response.status_code == 400 and "unique" in response.text:
                return self.already_following_this_artist_message, None
            raise e
        return self._build_message(followed_artist_response), None

    def _extract_artist_id_from_url(self, url: str) -> str:
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
    def already_following_this_artist_message(self) -> str:
        return 'You are already following this artist'

    @property
    def error_invalid_link_message(self) -> str:
        return 'Invalid artist link'

    @property
    def help_message(self) -> str:
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

    async def _get_response(self) -> Tuple[Any, Optional[Any]]:
        keyboard = self._build_keyboard()
        if not keyboard:
            return self.not_following_any_artist_message, None
        return 'Choose an artist to unfollow:', keyboard

    def _build_keyboard(self):
        followed_artists = self.spotify_api_client.get_followed_artists(
            self.update.message.from_user.id)
        if not followed_artists:
            return None
        return UnfollowArtistButton.get_keyboard_markup(followed_artists)


class CheckArtistsNewMusicReleasesCommand(FollowArtistMixin, Command):
    """
    Command /checkartistsnewmusicreleases
    Shows a list of buttons with followed artists for checking their new album releases when clicking
    """
    COMMAND = 'checkartistsnewmusicreleases'

    def __init__(self, update: Update, context: CallbackContext):
        super().__init__(update, context)
        self.spotify_api_client = SpotifyAPIClient()

    async def _get_response(self) -> Tuple[Any, Optional[Any]]:
        new_music_releases_response = self.spotify_api_client.check_new_music_releases(
            self.update.message.from_user.id)
        if not new_music_releases_response:
            return self.no_new_music_message, None
        message = self._build_message(new_music_releases_response), None
        return message

    @staticmethod
    def _build_message(new_music_releases_response: List) -> str:
        msg = 'Found new music: \n'
        for new_album in new_music_releases_response:
            new_album_first_artist = new_album.get('artists')[0]
            msg += f'    - <a href="{new_album.get("url")}">{new_album_first_artist.get("name")} - {new_album.get("name")} ({new_album.get("album_type")})</a> ' \
                   f'Released at: {datetime.datetime.fromisoformat(new_album.get("release_date")).strftime(OUTPUT_DATE_FORMAT)} \n'
        return msg

    @property
    def no_new_music_message(self) -> str:
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

    async def _get_response(self) -> Tuple[Any, Optional[Any]]:
        stats = self.telegram_api_client.get_stats(self.update.message.chat_id)
        return self._build_message(stats), None

    @staticmethod
    def _build_message(stats: Dict) -> str:
        msg = '<strong>Links sent by the users from the beginning in this chat:</strong> \n'
        users = stats.get('users_with_chat_link_count', [])
        most_sent_genres = stats.get('most_sent_genres', [])
        for user in users:
            msg += '- {} <strong>{}:</strong> {}\n'.format(
                User.EMOJI,
                user.get('username') or user.get('first_name'),
                user.get('sent_links_chat__count')
            )
        msg += f'\n <strong>Most sent genres:</strong> {", ".join(most_sent_genres)}'
        return msg
