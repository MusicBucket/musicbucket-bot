import logging
import datetime
from collections import OrderedDict

from emoji import emojize

from bot.api_client.spotify_api_client import SpotifyAPIClient
from bot.api_client.telegram_api_client import TelegramAPIClient
from bot.music.music import LinkType

log = logging.getLogger(__name__)


class EmojiModelMixin:
    EMOJI = None

    @classmethod
    def get_emoji(cls):
        raise NotImplementedError()


class User(EmojiModelMixin):
    EMOJI = ':baby:'

    @classmethod
    def get_emoji(cls):
        return emojize(cls.EMOJI, use_aliases=True)


class Artist(EmojiModelMixin):
    EMOJI = ':busts_in_silhouette:'

    @classmethod
    def get_emoji(cls):
        return emojize(cls.EMOJI, use_aliases=True)


class Album(EmojiModelMixin):
    EMOJI = ':cd:'

    ALBUM_TYPES = (
        'album',
        'single',
        'compilation',
    )

    @staticmethod
    def parse_release_date(release_date: str, release_date_precision) -> datetime.date:
        if release_date_precision == 'day':
            return datetime.datetime.strptime(release_date, '%Y-%m-%d').date()
        elif release_date_precision == 'month':
            return datetime.datetime.strptime(release_date, '%Y-%m').date()
        elif release_date_precision == 'year':
            return datetime.datetime.strptime(release_date, '%Y').date()

    @classmethod
    def get_emoji(cls):
        return emojize(cls.EMOJI, use_aliases=True)


class Track(EmojiModelMixin):
    EMOJI = ':musical_note:'

    @classmethod
    def get_emoji(cls):
        return emojize(cls.EMOJI, use_aliases=True)


class Link(EmojiModelMixin):

    @staticmethod
    def get_name(link: OrderedDict):
        link_type = link.get('link_type')
        artist = link.get('artist')
        album = link.get('album')
        track = link.get('track')
        if link_type == LinkType.ARTIST.value:
            return artist.get('name')
        elif link_type == LinkType.ALBUM.value:
            return "{} - {}".format(
                album.get('artists')[0].get('name') if album.get('artists') else '',
                album.get('name')
            )
        elif link_type == LinkType.TRACK.value:
            return "{} by {}".format(
                track.get('name'),
                track.get('artists')[0].get('name') if track.get('artists') else '',
            )


class CreateOrUpdateMixin:

    @staticmethod
    def save_link(url: str, user_id: str, chat_id: str) -> OrderedDict:
        telegram_api_client = TelegramAPIClient()
        save_link_response = telegram_api_client.create_sent_link(url, user_id, chat_id)
        return save_link_response

    @staticmethod
    def save_chat(chat):
        telegram_api_client = TelegramAPIClient()
        create_chat_response = telegram_api_client.create_chat(chat)
        return create_chat_response

    @staticmethod
    def save_user(user):
        telegram_api_client = TelegramAPIClient()
        create_user_response = telegram_api_client.create_user(user)
        return create_user_response

    @staticmethod
    def save_artist(artist_id: str):
        spotify_api_client = SpotifyAPIClient()
        create_artist_response = spotify_api_client.create_artist(artist_id)
        return create_artist_response

    @staticmethod
    def save_album(album_id: str):
        spotify_api_client = SpotifyAPIClient()
        create_album_response = spotify_api_client.create_album(album_id)
        return create_album_response

    @staticmethod
    def save_track(track_id: str):
        spotify_api_client = SpotifyAPIClient()
        create_track_response = spotify_api_client.create_track(track_id)
        return create_track_response
