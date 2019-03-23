from enum import Enum


class LinkType(Enum):
    """Different link types"""
    ARTIST = 'ARTIST'
    ALBUM = 'ALBUM'
    TRACK = 'TRACK'


class StreamingServiceType(Enum):
    """Available streaming services"""
    SPOTIFY = 'SPOTIFY'
    DEEZER = 'DEEZER'


class LinkInfo():
    """Represents a link with the related music information from the
    streaming service"""

    def __init__(self, link_type, artist=None, album=None, track=None, genre=None):
        self.link_type = link_type
        self.artist = artist
        self.album = album
        self.track = track
        self.genre = genre
