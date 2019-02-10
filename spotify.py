from enum import Enum
from os import getenv as getenv
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv()

# Spotify client init
client_credentials_manager = SpotifyClientCredentials(client_id=getenv(
    'SPOTIFY_CLIENT_ID'), client_secret=getenv('SPOTIFY_CLIENT_SECRET'))
spotipy_client = spotipy.Spotify(
    client_credentials_manager=client_credentials_manager)


class LinkType(Enum):
    """Different Spotify link types"""
    ARTIST = 1
    ALBUM = 2
    TRACK = 3


class LinkInfo():
    """Represents a Spotify link"""

    # whatever spotify returns from a id request
    def __init__(self, link_type, artist=None, album=None, track=None):
        self.link_type = link_type
        self.artist = artist
        self.album = album
        self.track = track


class Parser():
    """Parser class that helps to identify which type of Spotify link is"""

    def get_link_type(self, url):
        """Resolves the Spotify link type"""
        if self.__is_spotify_url(url):
            self.get_link_info(url, LinkType.ARTIST.value)
            if 'artist' in url:
                return LinkType.ARTIST
            elif 'album' in url:
                return LinkType.ALBUM
            elif 'track' in url:
                return LinkType.TRACK
        return None

    def get_link_info(self, url, link_type):
        """Resolves the name of the artist/album/track from a link
            Artist: 'spotify:artist:id'
            Album: 'spotify:album:id'
            Track: 'spotify:track:id'
        """
        # uri = ''

        # Gets the entity id from the Spotify link: https://open.spotify.com/album/*1yXlpa0dqoQCfucRNUpb8N*?si=GKPFOXTgRq2SLEE-ruNfZQ
        id = url[url.rfind('/')+1:].split('?', 1)[0]
        link_info = LinkInfo(link_type=link_type)
        if link_type == LinkType.ARTIST.value:
            uri = f'spotify:artist:{id}'
            artist = spotipy_client.artist(uri)
            link_info.artist = artist['name']
        elif link_type == LinkType.ALBUM.value:
            uri = f'spotify:album:{id}'
            album = spotipy_client.album(uri)
            link_info.album = album['name']
            link_info.artist = album['artists'][0]['name']
        elif link_type == LinkType.TRACK.value:
            uri = f'spotify:track:{id}'
            track = spotipy_client.track(uri)
            link_info.track = track['name']
            # TODO: fill artist and album info

        return link_info

    def __is_spotify_url(self, url):
        """Check if a message contains a Spotify Link"""
        if 'open.spotify.com' in url:
            return True
        return False
