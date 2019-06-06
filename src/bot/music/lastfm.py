import logging
from os import getenv

import pylast
from dotenv import load_dotenv

log = logging.getLogger(__name__)

load_dotenv()

API_KEY = getenv('LAST_FM_API_KEY')
API_SECRET = getenv('LAST_FM_SHARED_SECRET')


class LastFMClient:

    def __init__(self):
        self.network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET)

    def now_playing(self, username):
        try:
            track = self.network.get_user(username).get_now_playing()
            if not track:
                return
        except pylast.WSError:
            return

        album = track.get_album()

        try:
            cover = track.get_cover_image()
        except IndexError:
            cover = None

        data = {
            'artist': track.artist,
            'album': album,
            'track': track,
            'cover': cover
        }
        return data

    def set_lastfm_username_to_user(self, user, lastfm_username):
        pass
