import logging

import musicbrainzngs
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class MusicBrainzClient:
    MB_APP = 'musicbucketbot'
    MB_VERSION = '1.0'
    MB_CONTACT = 'www.musicbucket.net'

    def __init__(self):
        self.client = musicbrainzngs
        self.client.set_useragent(self.MB_APP, self.MB_VERSION, self.MB_CONTACT)

    def get_artist(self, mbid):
        artist = self.client.get_artist_by_id(mbid, includes=['url-rels'])
        return artist
