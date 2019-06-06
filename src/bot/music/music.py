import logging
from enum import Enum

log = logging.getLogger(__name__)

class EntityType(Enum):
    """Streaming service entity types"""
    ARTIST = 'artist'
    ALBUM = 'album'
    TRACK = 'track'


class LinkType(Enum):
    """Different link types"""
    ARTIST = 'ARTIST'
    ALBUM = 'ALBUM'
    TRACK = 'TRACK'


class StreamingServiceType(Enum):
    """Available streaming services"""
    SPOTIFY = 'SPOTIFY'
    DEEZER = 'DEEZER'


class LinkInfo:
    """Represents a link with the related music information from the
    streaming service"""

    def __init__(self, link_type, cleaned_url=None, artist=None, album=None, track=None, genres=None):
        self.link_type = link_type
        self.url = cleaned_url
        self.artist = artist
        self.album = album
        self.track = track
        self.genres = genres
