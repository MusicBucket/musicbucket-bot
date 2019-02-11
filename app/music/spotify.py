from os import getenv as getenv
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from .music import LinkType, LinkInfo

load_dotenv()

# Spotify client init
client_credentials_manager = SpotifyClientCredentials(client_id=getenv(
    'SPOTIFY_CLIENT_ID'), client_secret=getenv('SPOTIFY_CLIENT_SECRET'))
spotipy_client = spotipy.Spotify(
    client_credentials_manager=client_credentials_manager)


class SpotifyParser():
    """Parser class that helps to identify which type of Spotify link is"""

    def get_link_type(self, url):
        """Resolves the Spotify link type"""
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
        # Gets the entity id from the Spotify link: https://open.spotify.com/album/*1yXlpa0dqoQCfucRNUpb8N*?si=GKPFOXTgRq2SLEE-ruNfZQ
        id = url[url.rfind('/')+1:]
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
            link_info.album = track['album']['name']
            link_info.artist = track['artists'][0]['name']
        return link_info

    def clean_url(self, url):
        """Receives a Spotify url and returns it cleaned"""
        if url.rfind('?') > -1:
            return url[:url.rfind('?')]
        return url

    def is_spotify_url(self, url):
        """Check if a message contains a Spotify Link"""
        return 'open.spotify.com' in url
