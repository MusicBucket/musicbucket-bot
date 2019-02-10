from enum import Enum


class LinkType(Enum):
    """Different link types"""
    ARTIST = 1
    ALBUM = 2
    TRACK = 3


class LinkInfo():
    """Represents a link"""
    # whatever a music streaming service returns from a id request

    def __init__(self, link_type, artist=None, album=None, track=None):
        self.link_type = link_type
        self.artist = artist
        self.album = album
        self.track = track
