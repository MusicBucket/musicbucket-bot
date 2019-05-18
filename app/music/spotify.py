import logging
from os import getenv as getenv

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials

from app.music.music import LinkType, LinkInfo, EntityType

# Spotify client init
load_dotenv()

logger = logging.getLogger(__name__)

CLIENT_ID = getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = getenv('SPOTIFY_CLIENT_SECRET')


class SpotifyClient:
    """Spotify client that helps to manage and get info from a Spotify link"""
    RECOMMENDATIONS_NUMBER = 10
    MAX_RECOMMENDATIONS_SEEDS = 5

    def __init__(self):
        client_credentials_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
        self.client = spotipy.Spotify(
            client_credentials_manager=client_credentials_manager)

    @staticmethod
    def get_link_type(url):
        """Resolves the Spotify link type"""
        if 'artist' in url:
            return LinkType.ARTIST
        elif 'album' in url:
            return LinkType.ALBUM
        elif 'track' in url:
            return LinkType.TRACK
        return None

    @staticmethod
    def get_entity_id_from_url(url):
        return url[url.rfind('/') + 1:]

    @staticmethod
    def clean_url(url):
        """Receives a Spotify url and returns it cleaned"""
        if url.rfind('?') > -1:
            return url[:url.rfind('?')]
        return url

    @staticmethod
    def is_valid_url(url):
        """Check if a message contains a Spotify Link"""
        return 'open.spotify.com' in url

    def search_link(self, query, entity_type):
        """
        Searches for a list of coincidences in Spotify
        :param query: query string term
        :param entity_type: EntityType
        :return: list of results
        """
        search_result = self.client.search(query, type=entity_type)

        if entity_type == EntityType.ARTIST.value:
            search_result = search_result['artists']['items']
        elif entity_type == EntityType.ALBUM.value:
            search_result = search_result['albums']['items']
        elif entity_type == EntityType.TRACK.value:
            search_result = search_result['tracks']['items']

        return search_result

    def get_link_info(self, url, link_type):
        """
        Resolves the name and the genre of the artist/album/track from a link
        Artist: 'spotify:artist:id'
        Album: 'spotify:album:id'
        Track: 'spotify:track:id'
        """
        # Gets the entity id from the Spotify link:
        # https://open.spotify.com/album/*1yXlpa0dqoQCfucRNUpb8N*?si=GKPFOXTgRq2SLEE-ruNfZQ
        entity_id = self.get_entity_id_from_url(url)
        link_info = LinkInfo(link_type=link_type, cleaned_url=url)
        if link_type == LinkType.ARTIST:
            uri = f'spotify:artist:{entity_id}'
            artist = self.client.artist(uri)
            link_info.artist = artist['name']
            link_info.genres = artist['genres']

        elif link_type == LinkType.ALBUM:
            uri = f'spotify:album:{entity_id}'
            album = self.client.album(uri)
            link_info.album = album['name']
            link_info.artist = album['artists'][0]['name']
            if len(album['genres']) > 0:
                link_info.genres = album['genres']
            else:
                album_artist = self.client.artist(album['artists'][0]['id'])
                link_info.genres = album_artist['genres']

        elif link_type == LinkType.TRACK:
            uri = f'spotify:track:{entity_id}'
            track = self.client.track(uri)
            link_info.track = track['name']
            link_info.album = track['album']['name']
            link_info.artist = track['artists'][0]['name']
            track_artist = self.client.artist(track['artists'][0]['id'])
            link_info.genres = track_artist['genres']

        return link_info

    def get_recommendations(self, seed_artists):
        """Get track recommendations based on a list of max. 5 artist seeds"""
        artists_ids = [artist.id for artist in seed_artists]
        tracks = self.client.recommendations(seed_artists=artists_ids, limit=self.RECOMMENDATIONS_NUMBER)
        return tracks
