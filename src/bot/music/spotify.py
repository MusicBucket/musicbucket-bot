import logging
from typing import Optional

import requests

from bot.music.music import LinkType

log = logging.getLogger(__name__)


class SpotifyUtils:
    SPOTIFY_LINK_URL = 'open.spotify.com'
    SPOTIFY_SHORTCUT_LINK_URL = 'spotify.link'

    @classmethod
    def clean_url(cls, url: str) -> str:
        """Receives a Spotify url and returns it cleaned"""
        if cls.SPOTIFY_SHORTCUT_LINK_URL in url:
            url = cls.get_url_from_shortcut_url(url)
        if url.rfind('?') > -1:
            return url[:url.rfind('?')]
        return url

    @classmethod
    def is_valid_url(cls, url: str) -> bool:
        """Check if a message contains a Spotify Link"""
        return (
                cls.SPOTIFY_LINK_URL in url
                or cls.SPOTIFY_SHORTCUT_LINK_URL in url
        )

    @staticmethod
    def get_link_type_from_url(url: str) -> Optional[str]:
        """Resolves the Spotify link type"""
        if 'artist' in url:
            return LinkType.ARTIST.value
        elif 'album' in url:
            return LinkType.ALBUM.value
        elif 'track' in url:
            return LinkType.TRACK.value
        return None

    @staticmethod
    def get_entity_id_from_url(url: str) -> str:
        return url[url.rfind('/') + 1:]

    @staticmethod
    def get_url_from_shortcut_url(shortcut_url: str) -> str:
        response = requests.get(shortcut_url)
        return response.url
