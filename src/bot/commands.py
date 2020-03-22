import datetime
import logging
import random
from collections import defaultdict

from emoji import emojize
from peewee import fn, SQL
from telegram import Update
from telegram.ext import CallbackContext

from bot.buttons import DeleteSavedLinkButton, UnfollowArtistButton
from bot.logger import LoggerMixin
from bot.messages import UrlProcessor
from bot.models import Chat, Link, Album, LastFMUsername, User, CreateOrUpdateMixin, SavedLink, Track, Artist, ChatLink, \
    FollowedArtist
from bot.music.lastfm import LastFMClient
from bot.music.music import LinkType, EntityType
from bot.music.spotify import SpotifyClient
from bot.reply import ReplyMixin

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
    def run_recommendations_command(update: Update, context: CallbackContext):
        command = RecommendationsCommand(update, context)
        command.run()

    @staticmethod
    def run_now_playing_command(update: Update, context: CallbackContext):
        command = NowPlayingCommand(update, context)
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
              "-  /checkartistsnewalbumreleases Shows a list of buttons for checking new album releases. \n" \
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
        # TODO: Move to model
        links = Link.select() \
            .join(ChatLink, on=(ChatLink.link == Link.id)) \
            .join(Chat, on=(Chat.id == ChatLink.chat)) \
            .where(Chat.id == self.update.message.chat_id) \
            .where((ChatLink.sent_at >= self.LAST_WEEK)) \
            .order_by(ChatLink.sent_at.asc())
        return links

    def _get_links_from_user(self):
        # TODO: Move to model
        username = self.args[0]
        username = username.replace('@', '')
        links = Link.select() \
            .join(ChatLink, on=(ChatLink.link == Link.id)) \
            .join(User, on=(User.id == ChatLink.sent_by)) \
            .join(Chat, on=(Chat.id == ChatLink.chat)) \
            .where((Chat.id == self.update.message.chat_id) & (User.username == username)) \
            .where((ChatLink.sent_at >= self.LAST_WEEK)) \
            .order_by(ChatLink.sent_at.asc())
        return links

    @staticmethod
    def _group_links_by_user(links):
        # TODO: Move to model
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
        # TODO: Move to model
        username = self.args[0]
        username = username.replace('@', '')
        links = Link.select() \
            .join(ChatLink, on=(ChatLink.link == Link.id)) \
            .join(User, on=(User.id == ChatLink.sent_by)) \
            .join(Chat, on=(Chat.id == ChatLink.chat)) \
            .where((Chat.id == self.update.message.chat_id) & (User.username == username)) \
            .order_by(ChatLink.sent_at.asc())
        return links

    @staticmethod
    def _group_links_by_user(links):
        # TODO: Move to model
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
            .join(ChatLink, on=(ChatLink.link == Link.id)) \
            .join(User, on=(User.id == ChatLink.sent_by)) \
            .join(Chat, on=(Chat.id == ChatLink.chat)) \
            .where(User.id == self.update.message.from_user.id) \
            .order_by(ChatLink.sent_at.asc())
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
            .join(ChatLink) \
            .join(Chat) \
            .where(Chat.id == self.update.message.chat_id) \
            .where((ChatLink.sent_at >= self.LAST_WEEK)) \
            .where(Link.link_type == LinkType.ALBUM.value) \
            .order_by(ChatLink.sent_at.asc())
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


class LastFMSetCommand(Command, CreateOrUpdateMixin):
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

    def _build_message(self, lastfm_username):
        if not lastfm_username:
            return self._help_message()
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

    @staticmethod
    def _help_message():
        return 'Command usage: /lastfmset username'


class SavedLinksCommand(Command):
    """
    Command /savedlinks
    Shows a list of the links that the user saved
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
            msg += f'- {saved_link.link.get_emoji()} <a href="{saved_link.link.url}">{str(saved_link.link)}</a> ' \
                   f'({saved_link.link.genres[0] if saved_link.link.genres else ""}). ' \
                   f'Saved at: {saved_link.saved_at.strftime("%Y/%m/%d")}\n'
        return msg

    def _get_saved_links_by_user(self):
        saved_links_by_user = (SavedLink.select().join(Link).join(User).where(
            (SavedLink.user_id == self.update.message.from_user.id) & (SavedLink.deleted_at.is_null())))
        return saved_links_by_user


class DeleteSavedLinksCommand(Command):
    """
    Command /deletesavedlinks
    Shows a list of buttons with the saved links and deletes them when clicking
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
            .where(
            (SavedLink.user_id == self.update.message.from_user.id) & (SavedLink.deleted_at.is_null())))
        return saved_links_by_user


class FollowArtistMixin:
    @staticmethod
    def _get_followed_artists_by_user(update: Update):
        followed_artists_by_user = (
            FollowedArtist.select().join(Artist, on=FollowedArtist.artist_id == Artist.id).join(User,
                                                                                                on=FollowedArtist.user_id == User.id).where(
                FollowedArtist.user_id == update.message.from_user.id))
        return followed_artists_by_user

    @staticmethod
    def _not_following_any_artist_message():
        return 'You are not following any artist'


class FollowedArtistsCommand(FollowArtistMixin, Command):
    """
    Command /followedartists
    Shows a list of the followed artists the request's user
    """
    COMMAND = 'followedartists'

    def get_response(self):
        followed_artists = self._get_followed_artists_by_user(self.update)
        return self._build_message(followed_artists), None

    def _build_message(self, followed_artists):
        if not followed_artists:
            return self._not_following_any_artist_message()

        msg = '<strong>Following artists:</strong> \n'
        for followed_artist in followed_artists:
            msg += f'- {followed_artist.artist.get_emoji()} ' \
                   f'<a href="{followed_artist.artist.spotify_url}">{str(followed_artist.artist)}</a> ' \
                   f'Followed at: {followed_artist.followed_at.strftime("%Y/%m/%d")}\n'
        return msg


class FollowArtistCommand(CreateOrUpdateMixin, Command):
    """
    Command /followartist
    Allows user to follow an artist and be notified when they release an album
    """
    COMMAND = 'followartist'

    def __init__(self, update, context):
        super().__init__(update, context)
        self.spotify_client = SpotifyClient()

    def get_response(self):
        if not self.args:
            return self._help_message(), None
        url = self.args[0]
        try:
            artist = self._process_artist_url(url)
        except ValueError:
            log.exception('Error trying to process artist url')
            return self._error_invalid_link_message()
        user = self.save_user(self.update)
        followed_artist, was_created = self._follow_artist(artist, user)
        return self._build_message(followed_artist, was_created), None

    def _follow_artist(self, artist: Artist, user: User) -> FollowedArtist:
        return self.save_followed_artist(artist, user)

    def _process_artist_url(self, url: str) -> Artist:
        url = self._url_cleaning_and_validations(url)
        artist_id = self.spotify_client.get_entity_id_from_url(url)
        spotify_artist = self.spotify_client.client.artist(artist_id)
        return self.save_artist(spotify_artist)

    def _url_cleaning_and_validations(self, url: str) -> str:
        if not self.spotify_client.is_valid_url(url):
            raise ValueError(self._error_invalid_link_message())
        if self.spotify_client.get_link_type(url) != LinkType.ARTIST:
            raise ValueError(self._error_invalid_link_message())
        cleaned_url = self.spotify_client.clean_url(url)
        return cleaned_url

    @staticmethod
    def _error_invalid_link_message():
        return 'Invalid artist link'

    @staticmethod
    def _help_message():
        return 'Command usage:  /followartist spotify_artist_url'

    @staticmethod
    def _build_message(followed_artist: FollowedArtist, was_created: bool) -> str:
        if not was_created:
            return 'You are already following this artist'
        msg = f'<strong>Followed artist:</strong> {followed_artist.artist.name}. \n'
        msg += 'You will be aware of it\'s albums releases'
        return msg


class UnfollowArtistsCommand(FollowArtistMixin, Command):
    """
    Command /unfollowartist
    Shows a list of buttons with followed artists and deletes them when clicking
    """
    COMMAND = 'unfollowartists'

    def get_response(self):
        keyboard = self._build_keyboard()
        if not keyboard:
            return self._not_following_any_artist_message(), None
        return 'Choose an artist to unfollow:', keyboard

    def _build_keyboard(self):
        followed_artists = self._get_followed_artists_by_user(self.update)
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
        self.spotify_client = SpotifyClient()

    def get_response(self):
        followed_artists = self._get_followed_artists_by_user(self.update)
        if not followed_artists:
            return self._not_following_any_artist_message()
        self._update_followed_artists_albums(followed_artists)
        message = self._build_message(followed_artists), None
        self._update_followed_artists_last_lookup(followed_artists)
        return message

    @staticmethod
    def _update_followed_artists_last_lookup(followed_artists: []):
        for followed_artist in followed_artists:
            followed_artist.last_lookup = datetime.datetime.now()
            followed_artist.save()

    def _update_followed_artists_albums(self, followed_artists: []):
        for followed_artist in followed_artists:
            spotify_artist_albums = self.spotify_client.get_all_artist_albums(followed_artist.artist)
            for spotify_album in spotify_artist_albums:
                self.save_album(spotify_album)

    def _build_message(self, followed_artists: []) -> str:
        if not followed_artists:
            return self._not_following_any_artist_message()
        new_albums_found = False
        for followed_artist in followed_artists:
            new_artist_albums = self._extract_new_artist_albums(followed_artist)
            if not new_artist_albums:
                continue
            new_albums_found = True
            msg = f'Found new {followed_artist.artist.name} music: \n'
            for new_album in new_artist_albums:
                msg += f'    - <a href="">{new_album.name} ({new_album.album_type})</a> ' \
                       f'Released at: {new_album.release_date.strftime("%Y/%m/%d")} \n'
            return msg
        if not new_albums_found:
            return self._no_new_music_message()

    @staticmethod
    def _extract_new_artist_albums(followed_artist: FollowedArtist) -> []:
        last_artist_lookup = followed_artist.last_lookup
        new_albums = []
        for album in followed_artist.artist.albums:
            if last_artist_lookup and album.release_date >= last_artist_lookup.date():
                new_albums.append(album)
        return new_albums

    @staticmethod
    def _no_new_music_message():
        return 'There is no new music of your followed artists'


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
        stats_by_user = User.select(User, fn.Count(ChatLink.id).alias('links')) \
            .join(ChatLink, on=ChatLink.sent_by) \
            .join(Chat, on=ChatLink.chat) \
            .where(Chat.id == self.update.message.chat_id) \
            .group_by(User) \
            .order_by(SQL('links').desc())
        return stats_by_user
