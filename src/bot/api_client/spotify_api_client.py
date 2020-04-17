from collections import OrderedDict

from bot.api_client.api_client import BaseAPIClient


class SpotifyAPIClient(BaseAPIClient):
    _url = 'spotify/'

    def search(self, query: str, entity_type: str) -> []:
        """
        Searches for a list of coincidences in Spotify
        :param query: query string term
        :param entity_type: EntityType value
        :return: list of results
        """
        url = self._get_url('search/')
        params = {
            'entity_type': entity_type,
            'query': query
        }
        return self.process_request(url, params=params)

    def get_artist(self, artist_id: str) -> OrderedDict:
        url = self._get_url(f'artists/{artist_id}/')
        return self.process_request(url)

    def create_artist(self, artist_id: str) -> OrderedDict:
        url = self._get_url('artists/')
        data = {'spotify_id': artist_id}
        return self.process_request(url, method='post', data=data)

    def create_album(self, album_id: str) -> OrderedDict:
        url = self._get_url('albums/')
        data = {'spotify_id': album_id}
        return self.process_request(url, method='post', data=data)

    def create_track(self, track_id: str) -> OrderedDict:
        url = self._get_url('tracks/')
        data = {'spotify_id': track_id}
        return self.process_request(url, method='post', data=data)

    def get_saved_links(self, user_id: str) -> []:
        url = self._get_url('saved-links/')
        params = {'user__telegram_id': user_id}
        return self.process_request(url, params=params)

    def create_saved_link(self, link_id: int, user_id: int):
        url = self._get_url(f'saved-links/')
        data = {
            'link_id': link_id,
            'user_id': user_id,
        }
        return self.process_request(url, method='post', data=data)

    def delete_saved_link(self, saved_link_id: int) -> OrderedDict:
        url = self._get_url(f'saved-links/{saved_link_id}/')
        return self.process_request(url, method='delete')

    def get_followed_artists(self, user_id: str) -> []:
        url = self._get_url('followed-artists/')
        params = {'user__telegram_id': user_id}
        return self.process_request(url, params=params)

    def create_followed_artist(self, artist_id: int, user_id: int) -> OrderedDict:
        url = self._get_url('followed-artists/')
        data = {
            'artist_id': artist_id,
            'user_id': user_id,
        }
        return self.process_request(url, method='post', json=data)

    def delete_followed_artist(self, followed_artist_id: int) -> OrderedDict:
        url = self._get_url(f'followed-artists/{followed_artist_id}/')
        return self.process_request(url, method='delete')

    def check_new_music_releases(self, user_id: int) -> OrderedDict:
        url = self._get_url(f'followed-artists/check-new-music-releases/')
        params = {'user__telegram_id': user_id}
        return self.process_request(url, params=params)

    def _get_url(self, endpoint_url: str) -> str:
        return f'{super().url}{self._url}{endpoint_url}'
