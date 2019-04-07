from os import getenv as getenv

import spotipy
from dotenv import load_dotenv
from spotipy import util
from spotipy.oauth2 import SpotifyClientCredentials

from app.music.music import LinkType, LinkInfo, EntityType
from app.music.streaming_service import StreamingServiceParser

load_dotenv()

# Spotify client init
scope = 'playlist-read-private,playlist-modify-public,playlist-modify-private,playlist-read-collaborative'
spotify_user = getenv('SPOTIFY_USER')
client_id = getenv('SPOTIFY_CLIENT_ID')
client_secret = getenv('SPOTIFY_CLIENT_SECRET')
redirect_uri = getenv('SPOTIFY_REDIRECT_URI')

# client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
token = util.prompt_for_user_token(
    username=spotify_user,
    scope=scope,
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri)
if token:
    spotipy_client = spotipy.Spotify(auth=token)


class SpotifyParser(StreamingServiceParser):
    """Parser class that helps to identify which type of Spotify link is"""

    def get_link_type(self, url):
        """Resolves the Spotify link type"""
        if 'artist' in url:
            return LinkType.ARTIST
        elif 'album' in url:
            return LinkType.ALBUM
        elif 'track' in url:
            return LinkType.TRACK
        elif 'playlist' in url:
            return LinkType.PLAYLIST
        return None

    def search_link(self, query, entity_type):
        """
        Searches for a list of coincidences in Spotify
        :param query: query string term
        :param entity_type: EntityType
        :return: list of results
        """
        search_result = spotipy_client.search(query, type=entity_type)

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
        # Gets the entity id (and the user_id from the Spotify link:
        # https://open.spotify.com/album/*1yXlpa0dqoQCfucRNUpb8N*?si=GKPFOXTgRq2SLEE-ruNfZQ
        if link_type == LinkType.PLAYLIST:
            entity_id = self.get_entity_id_from_url(url, link_type)
            user_id = self.get_user_id_from_url(url, link_type)
        else:
            entity_id = self.get_entity_id_from_url(url, link_type)

        link_info = LinkInfo(link_type=link_type)
        if link_type == LinkType.ARTIST:
            uri = f'spotify:artist:{entity_id}'
            artist = spotipy_client.artist(uri)
            link_info.artist = artist['name']
            link_info.genre = artist['genres'][0] if len(
                artist['genres']) > 0 else None
        elif link_type == LinkType.ALBUM:
            uri = f'spotify:album:{entity_id}'
            album = spotipy_client.album(uri)
            link_info.album = album['name']
            link_info.artist = album['artists'][0]['name']
            if len(album['genres']) > 0:
                link_info.genre = album['genres'][0]
            else:
                album_artist = spotipy_client.artist(album['artists'][0]['id'])
                link_info.genre = album_artist['genres'][0] if len(
                    album_artist['genres']) > 0 else None
        elif link_type == LinkType.TRACK:
            uri = f'spotify:track:{entity_id}'
            track = spotipy_client.track(uri)
            link_info.track = track['name']
            link_info.album = track['album']['name']
            link_info.artist = track['artists'][0]['name']
            track_artist = spotipy_client.artist(track['artists'][0]['id'])
            link_info.genre = track_artist['genres'][0] if len(
                track_artist['genres']) > 0 else None
        elif link_type == LinkType.PLAYLIST:
            playlist = spotipy_client.user_playlist(user=user_id, playlist_id=entity_id)
            link_info.playlist_id = playlist['id']
            link_info.playlist_name = playlist['name']
            link_info.playlist_description = playlist['description']
            link_info.playlist_owner_username = playlist['owner']['display_name']
            link_info.playlist_owner_id = playlist['owner']['id']

        return link_info

    def create_playlist(self, name):
        return spotipy_client.user_playlist_create(user=spotify_user, name=name, public=True)

    def get_playlist(self, user_id, playlist_id):
        return spotipy_client.user_playlist(user_id, playlist_id)

    def add_track_to_playlist(self, url, playlist, link_type):
        """
        Adds a track to a playlist from a url
        """
        entity_id = self.get_entity_id_from_url(url, link_type)

        # If the url is an artist or an album, we'll get it's most popular track
        if link_type == LinkType.ARTIST:
            track_id = spotipy_client.artist_top_tracks(entity_id)['tracks'][0]['id']
        elif link_type == LinkType.ALBUM:
            track_id = spotipy_client.album_tracks(entity_id)['items'][0]['id']
        else:
            track_id = entity_id
        spotipy_client.user_playlist_add_tracks(spotify_user, playlist.spotify_id, [track_id])

    def get_entity_id_from_url(self, url, link_type):
        return url[url.rfind('/') + 1:]

    def get_user_id_from_url(self, url, link_type):
        return url[url.rfind('/') + 3:]

    def clean_url(self, url):
        """Receives a Spotify url and returns it cleaned"""
        if url.rfind('?') > -1:
            return url[:url.rfind('?')]
        return url

    def is_valid_url(self, url):
        """Check if a message contains a Spotify Link"""
        return 'open.spotify.com' in url
