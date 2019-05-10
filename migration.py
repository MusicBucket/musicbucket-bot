import logging
from os import getenv

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from app.models import Link, Artist, Genre, User, Chat, Album, Track, AlbumArtist, AlbumGenre, ArtistGenre, TrackArtist
from app.db import db
from app.music.music import LinkType, StreamingServiceType
from app.music.spotify import SpotifyClient

# Spotify client init
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

db.connect()
db.create_tables([User, Chat, Link, Artist, Album, Track, Genre, AlbumArtist, AlbumGenre, ArtistGenre, TrackArtist])

client_credentials_manager = SpotifyClientCredentials(client_id=getenv(
    'SPOTIFY_CLIENT_ID'), client_secret=getenv('SPOTIFY_CLIENT_SECRET'))
spotify_client = SpotifyClient()


def save_artist(artist):
    saved_artist, created = Artist.get_or_create(
        id=artist['id'],
        name=artist['name'],
        image=artist['images'][0]['url'],
        popularity=artist['popularity'],
        href=artist['href'],
        spotify_url=artist['external_urls']['spotify'],
        uri=artist['uri'])
    return saved_artist, created


def save_album(album):
    saved_album, created = Album.get_or_create(
        id=album['id'],
        name=album['name'],
        label=album['label'],
        image=album['images'][0]['url'],
        popularity=album['popularity'],
        href=album['href'],
        spotify_url=album['external_urls']['spotify'],
        album_type=album['type'],
        uri=album['uri'])
    return saved_album, created


def save_track(track, album):
    saved_track, created = Track.get_or_create(
        id=track['id'],
        name=track['name'],
        track_number=track['track_number'],
        duration_ms=track['duration_ms'],
        explicit=track['explicit'],
        popularity=track['popularity'],
        href=track['href'],
        spotify_url=track['external_urls']['spotify'],
        preview_url=track['preview_url'],
        uri=track['uri'],
        album=album)
    return saved_track, created


def save_genre(genre):
    saved_genre, created = Genre.get_or_create(name=genre)
    return saved_genre, created


def migrate_artist(link):
    logger.info(f"Migrating artist {link.artist_name}")
    artist_id = spotify_client.get_entity_id_from_url(link.url)
    artist = spotify_client.client.artist(artist_id)
    # Save the artist
    saved_artist, created = save_artist(artist)

    # Save the genres
    saved_genres = []
    logger.info(f"Saving genres for artist {saved_artist.name} with id {saved_artist.id}")
    for genre in artist['genres']:
        saved_genre, created = save_genre(genre)
        saved_genres.append(saved_genre)
        logger.info(f"Saved genre {saved_genre.name}")
    # Set the genres to the artist
    saved_artist.genres = saved_genres
    saved_artist.save()

    # Update the link
    link.artist = saved_artist
    link.save()

    logger.info(f'Saved artist {saved_artist.name}')


def migrate_album(link):
    logger.info(f"Migrating album {link.album_name}")
    album_id = spotify_client.get_entity_id_from_url(link.url)
    album = spotify_client.client.album(album_id)
    # Save the album
    saved_album, created = save_album(album)

    # Save the artists
    saved_artists = []
    logger.info(f"Saving artists for album {saved_album.name} with id {saved_album.id}")
    for album_artist in album['artists']:
        artist_id = album_artist['id']
        artist = spotify_client.client.artist(artist_id)
        saved_artist, created = save_artist(artist)
        saved_artists.append(saved_artist)
        logger.info(f"Saved artist {saved_artist.name}")
    # Set the artists to the album
    saved_album.artists = saved_artists
    saved_album.save()
    # Save the genres
    saved_genres = []
    logger.info(f"Saving genres for album {saved_album.name} with id {saved_album.id}")
    for genre in album['genres']:
        saved_genre, created = save_genre(genre)
        saved_genres.append(saved_genre)
        logger.info(f"Saved genre {saved_genre.name}")
    # Set the genres to the album
    saved_album.genres = saved_genres
    saved_album.save()

    link.album = saved_album
    link.save()

    logger.info(f'Saved album {saved_album.name}')


def migrate_track(link):
    logger.info(f"Migrating track {link.track_name}")
    track_id = spotify_client.get_entity_id_from_url(link.url)
    track = spotify_client.client.track(track_id)

    # Save the album
    logger.info(f"Saving the album for track {track['name']} with id {track['id']}")
    album_id = track['album']['id']
    album = spotify_client.client.album(album_id)
    saved_album, created = save_album(album)

    # Save the track
    saved_track, created = save_track(track, saved_album)

    # Save the artists
    saved_artists = []
    logger.info(f"Saving artists for album {saved_track.name} with id {saved_track.id}")
    for track_artist in track['artists']:
        artist_id = track_artist['id']
        artist = spotify_client.client.artist(artist_id)
        saved_artist, created = save_artist(artist)
        saved_artists.append(saved_artist)
        logger.info(f"Saved artist {saved_artist.name}")
    # Set the artists to the album
    saved_track.artists = saved_artists
    saved_track.save()

    link.track = saved_track
    link.save()

    logger.info(f"Saved track {saved_track.name}")


def migrate_links():
    logger.info("Processing links")
    links = Link.select()
    number_of_links = len(links)
    logger.info(f"There are {number_of_links} links to migrate")

    for i, link in enumerate(links):
        try:
            logger.info(f"Processing link {i} of {number_of_links}")
            if link.link_type == LinkType.ARTIST.value:
                migrate_artist(link)
            elif link.link_type == LinkType.ALBUM.value:
                migrate_album(link)
            elif link.link_type == LinkType.TRACK.value:
                migrate_track(link)
        except Exception as e:
            logger.error('FAILED at: ' + i)


def main():
    logger.info("Starting migration")
    migrate_links()
    logger.info("Migration finished")


if __name__ == '__main__':
    main()
