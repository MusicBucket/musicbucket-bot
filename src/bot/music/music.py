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
    ARTIST = 'artist'
    ALBUM = 'album'
    TRACK = 'track'


class StreamingServiceType(Enum):
    """Available streaming services"""
    SPOTIFY = 'SPOTIFY'
    DEEZER = 'DEEZER'
