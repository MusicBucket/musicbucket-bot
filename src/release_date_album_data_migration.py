import datetime
import logging
import time

import spotipy
from dotenv import load_dotenv

from bot.models import Album
from bot.music.spotify import SpotifyClient

log = logging.getLogger(__name__)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

load_dotenv()

spotify_client = SpotifyClient()


def fill_albums_release_date_and_type():
    for album in Album.select():
        log.info(f'Updating album {album.name} ({album.id}) by {album.get_first_artist().name}')
        spotify_album = spotify_client.client.album(album.id)
        spotify_album_type = spotify_album.get('album_type')
        spotify_album_release_date = spotify_album.get('release_date')
        spotify_album_release_date_precision = spotify_album.get('release_date_precision')
        if spotify_album_release_date:
            album.release_date = Album.parse_release_date(spotify_album_release_date,
                                                          spotify_album_release_date_precision)
        album.release_date_precision = spotify_album_release_date_precision
        album.album_type = spotify_album_type
        log.info(f'Album release date: {album.release_date} ({album.release_date_precision})')
        album.save()


def main():
    start_time = time.time()
    log.info('Starting migration')
    fill_albums_release_date_and_type()
    end_time = time.time()
    log.info(f'Migration finished. Elapsed {end_time - start_time} seconds')


if __name__ == '__main__':
    main()
