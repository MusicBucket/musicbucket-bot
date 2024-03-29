from typing import Optional, List, Dict

from bot.api_client.api_client import BaseAPIClient


class LastfmAPIClient(BaseAPIClient):
    PERIOD_OVERALL = "overall"
    PERIOD_7DAYS = "7day"
    PERIOD_1MONTH = "1month"
    PERIOD_3MONTHS = "3month"
    PERIOD_6MONTHS = "6month"
    PERIOD_12MONTHS = "12month"

    PERIODS = (
        PERIOD_OVERALL,
        PERIOD_7DAYS,
        PERIOD_1MONTH,
        PERIOD_3MONTHS,
        PERIOD_6MONTHS,
        PERIOD_12MONTHS,
    )
    _url = 'lastfm/'

    def get_now_playing(self, user_id: str) -> {}:
        url = self._get_url(f'now-playing/{user_id}/')
        return self.process_request(url)

    def get_top_albums(self, user_id: str, period: str = PERIOD_7DAYS) -> Dict:
        url = self._get_url(f'users/{user_id}/top-albums/')
        params = {'period': period}
        return self.process_request(url, params=params)

    def get_top_artists(self, user_id: str, period: str = PERIOD_7DAYS) -> Dict:
        url = self._get_url(f'users/{user_id}/top-artists/')
        params = {'period': period}
        return self.process_request(url, params=params)

    def get_top_tracks(self, user_id: str, period: str = PERIOD_7DAYS) -> Dict:
        url = self._get_url(f'users/{user_id}/top-tracks/')
        params = {'period': period}
        return self.process_request(url, params=params)

    def get_collage(self, user_id: str, rows: Optional[int] = 5, cols: Optional[int] = 5,
                    period: Optional[str] = PERIOD_7DAYS) -> bytes:
        url = self._get_url(f'collage/{user_id}/')
        params = {'rows': rows, 'cols': cols, 'period': period}
        return self.process_request(url, params=params, is_json=False)

    def set_lastfm_user(self, user_id: str, lastfm_username: str) -> Dict:
        url = self._get_url(f'users/set-lastfm-user/')
        data = {
            'username': lastfm_username,
            'user_id': user_id,
        }
        return self.process_request(url, method='post', data=data)

    def _get_url(self, endpoint_url) -> str:
        return f'{super().url}{self._url}{endpoint_url}'
