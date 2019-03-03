from enum import Enum


class LinkType(Enum):
    """Different link types"""
    ARTIST = 0
    ALBUM = 1
    TRACK = 2


class StreamingServiceType(Enum):
    """Available streaming services"""
    SPOTIFY = 0
    DEEZER = 1


class LinkInfo():
    """Represents a link with the related music information from the
    streaming service"""

    def __init__(self, link_type, artist=None, album=None, track=None, genre=None):
        self.link_type = link_type
        self.artist = artist
        self.album = album
        self.track = track
        self.genre = genre
