from enum import Enum


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
    PLAYLIST = 'PLAYLIST'


class StreamingServiceType(Enum):
    """Available streaming services"""
    SPOTIFY = 'SPOTIFY'
    DEEZER = 'DEEZER'


class LinkInfo:
    """Represents a link with the related music information from the
    streaming service"""

    def __init__(self, link_type, artist=None, album=None, track=None, genre=None, playlist_id=None, playlist_name=None,
                 playlist_description=None, playlist_owner_username=None, playlist_owner_id=None):
        self.link_type = link_type
        self.artist = artist
        self.album = album
        self.track = track
        self.genre = genre
        self.playlist_id = playlist_id
        self.playlist_name = playlist_name
        self.playlist_description = playlist_description
        self.playlist_owner_username = playlist_owner_username
        self.playlist_owner_id = playlist_owner_id
