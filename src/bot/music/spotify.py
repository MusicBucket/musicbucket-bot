import logging

from bot.music.music import LinkType

log = logging.getLogger(__name__)


class SpotifyUtils:
    SPOTIFY_LINK_URL = 'open.spotify.com'

    @staticmethod
    def clean_url(url):
        """Receives a Spotify url and returns it cleaned"""
        if url.rfind('?') > -1:
            return url[:url.rfind('?')]
        return url

    @classmethod
    def is_valid_url(cls, url):
        """Check if a message contains a Spotify Link"""
        return cls.SPOTIFY_LINK_URL in url

    @staticmethod
    def get_link_type_from_url(url):
        """Resolves the Spotify link type"""
        if 'artist' in url:
            return LinkType.ARTIST.value
        elif 'album' in url:
            return LinkType.ALBUM.value
        elif 'track' in url:
            return LinkType.TRACK.value
        return None

    @staticmethod
    def get_entity_id_from_url(url):
        return url[url.rfind('/') + 1:]
