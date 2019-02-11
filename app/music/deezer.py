import deezer
from .music import LinkType, LinkInfo

deezer_client = deezer.Client()


class DeezerParser():
    """Parser class tat helps to identify withc type of Deezer link is"""

    def get_link_type(self, url):
        """Resolves the Deezer link type"""
        if 'artist' in url:
            return LinkType.ARTIST
        elif 'album' in url:
            return LinkType.ALBUM
        elif 'track' in url:
            return LinkType.TRACK
        return None

    def get_link_info(self, url, link_type):
        """Resolves the name of the artist/album/track from a link
        Artist: 'https://www.deezer.com/artist/10443'
        Album: 'https://www.deezer.com/album/74271122'
        Track: 'http://www.deezer.com/track/71999722'
        """
        # Gets the entity id from the Deezer link:
        id = url[url.rfind('/')+1:]
        link_info = LinkInfo(link_type=link_type)
        if link_type == LinkType.ARTIST.value:
            artist = deezer_client.get_artist(id)
            link_info.artist = artist.name
        elif link_type == LinkType.ALBUM.value:
            album = deezer_client.get_album(id)
            link_info.album = album.title
            link_info.artist = album.get_artist().name
        elif link_type == LinkType.TRACK.value:
            track = deezer_client.get_track(id)
            link_info.track = track.title
            # link_info.album = track.get_album().title
            link_info.artist = track.get_artist().name

        return link_info

    def clean_url(self, url):
        """Receives a Deezer url and returns it cleaned"""
        if url.rfind('?') > -1:
            return url[:url.rfind('?')]
        return url

    def is_deezer_url(self, url):
        """Check if a message contains a Deezer link"""
        return 'www.deezer.com' in url
