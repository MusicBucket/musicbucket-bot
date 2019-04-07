import deezer

from app.music.music import LinkType, LinkInfo
from app.music.streaming_service import StreamingServiceParser

# Deezer client init
deezer_client = deezer.Client()


class DeezerParser(StreamingServiceParser):
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

    def search_link(self, query, entity_type):
        """Not implemented"""
        pass

    def get_link_info(self, url, link_type):
        """
        Resolves the name of the artist/album/track from a link
        Artist: 'https://www.deezer.com/artist/10443'
        Album: 'https://www.deezer.com/album/74271122'
        Track: 'http://www.deezer.com/track/71999722'
        """
        # Gets the entity id from the Deezer link:
        entity_id = self.get_entity_id_from_url(url)
        link_info = LinkInfo(link_type=link_type)
        if link_type == LinkType.ARTIST:
            artist = deezer_client.get_artist(entity_id)
            link_info.artist = artist.name
            # An artist doesn't return genres, so we'll get his last album, get genre id
            # and ask for genre data to API
            artist_albums = [
                album for album in artist.get_albums() if album.record_type == 'album']
            artist_albums.sort(key=lambda x: x.release_date, reverse=True)
            last_artist_album = artist_albums[0] if len(
                artist_albums) > 0 else None
            if last_artist_album is not None:
                genre = deezer_client.get_genre(last_artist_album.genre_id)
                link_info.genre = genre.name

        elif link_type == LinkType.ALBUM:
            album = deezer_client.get_album(entity_id)
            link_info.album = album.title
            link_info.artist = album.artist.name
            if len(album.genres) > 0:
                link_info.genre = album.genres[0].name

        elif link_type == LinkType.TRACK:
            track = deezer_client.get_track(entity_id)
            link_info.track = track.title
            link_info.album = track.album.title
            link_info.artist = track.artist.name
            # A track doesn't return genres, so we'll get his album, get genre id
            # and ask for genre data to API
            album = deezer_client.get_album(track.album.id)
            try:
                album.error
            except AttributeError:
                if len(album.genres) > 0:
                    link_info.genre = album.genres[0].name

        return link_info

    def get_entity_id_from_url(self, url):
        return url[url.rfind('/') + 1:]

    def get_user_id_from_url(self, url):
        # Not implemented
        pass

    def clean_url(self, url, link_type):
        """Receives a Deezer url and returns it cleaned"""
        if url.rfind('?') > -1:
            return url[:url.rfind('?')]
        return url

    def is_valid_url(self, url):
        """Check if a message contains a Deezer link"""
        return 'www.deezer.com' in url
