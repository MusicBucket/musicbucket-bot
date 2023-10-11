import logging
import datetime
from collections import OrderedDict

import emoji
from emoji import emojize

from bot.api_client.spotify_api_client import SpotifyAPIClient
from bot.api_client.telegram_api_client import TelegramAPIClient
from bot.music.music import LinkType

log = logging.getLogger(__name__)


class EmojiModelMixin:
    EMOJI = None


class User(EmojiModelMixin):
    EMOJI = emoji.emojize(':baby:')


class Artist(EmojiModelMixin):
    EMOJI = emoji.emojize(':busts_in_silhouette:')


class Album(EmojiModelMixin):
    EMOJI = emoji.emojize(':cd:', language="alias")

    ALBUM_TYPES = (
        'album',
        'single',
        'compilation',
    )

    @staticmethod
    def parse_release_date(release_date: str,
                           release_date_precision) -> datetime.date:
        if release_date_precision == 'day':
            return datetime.datetime.strptime(release_date, '%Y-%m-%d').date()
        elif release_date_precision == 'month':
            return datetime.datetime.strptime(release_date, '%Y-%m').date()
        elif release_date_precision == 'year':
            return datetime.datetime.strptime(release_date, '%Y').date()


class Track(EmojiModelMixin):
    EMOJI = emoji.emojize(':musical_note:')


class Link:

    @staticmethod
    def get_genres(link: OrderedDict):
        link_type = link.get('link_type')
        artist = link.get('artist')
        album = link.get('album')
        track = link.get('track')
        genres = None
        if link_type == LinkType.ARTIST.value:
            genres = artist.get('genres')
        elif link_type == LinkType.ALBUM.value:
            genres = album.get('artists')[0].get('genres') if \
                album.get('artists')[0] else None
        elif link_type == LinkType.TRACK.value:
            genres = track.get('artists')[0].get('genres') if \
                track.get('artists')[0] else None
        if not genres:
            return []
        return [genre.get('name') for genre in genres]

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
                album.get('artists')[0].get('name') if album.get(
                    'artists') else '',
                album.get('name')
            )
        elif link_type == LinkType.TRACK.value:
            return "{} by {}".format(
                track.get('name'),
                track.get('artists')[0].get('name') if track.get(
                    'artists') else '',
            )


class SaveTelegramEntityMixin:

    @staticmethod
    async def save_link(url: str, user_id: str, chat_id: str) -> OrderedDict:
        telegram_api_client = TelegramAPIClient()
        save_link_response = telegram_api_client.create_sent_link(url, user_id,
                                                                  chat_id)
        return save_link_response

    @staticmethod
    async def save_chat(chat):
        telegram_api_client = TelegramAPIClient()
        create_chat_response = telegram_api_client.create_chat(chat)
        return create_chat_response

    @staticmethod
    async def save_user(user):
        telegram_api_client = TelegramAPIClient()
        create_user_response = telegram_api_client.create_user(user)
        return create_user_response

    @staticmethod
    async def save_artist(artist_id: str):
        spotify_api_client = SpotifyAPIClient()
        create_artist_response = spotify_api_client.create_artist(artist_id)
        return create_artist_response

    @staticmethod
    async def save_album(album_id: str):
        spotify_api_client = SpotifyAPIClient()
        create_album_response = spotify_api_client.create_album(album_id)
        return create_album_response

    @staticmethod
    async def save_track(track_id: str):
        spotify_api_client = SpotifyAPIClient()
        create_track_response = spotify_api_client.create_track(track_id)
        return create_track_response
