from bot.api_client.api_client import BaseAPIClient


class LastfmAPIClient(BaseAPIClient):
    PERIOD_OVERALL = "overall"
    PERIOD_7DAYS = "7day"
    PERIOD_1MONTH = "1month"
    PERIOD_3MONTHS = "3month"
    PERIOD_6MONTHS = "6month"
    PERIOD_12MONTHS = "12month"
    _url = 'lastfm/'

    def get_now_playing(self, user_id: str) -> {}:
        url = self._get_url(f'now-playing/{user_id}/')
        return self.process_request(url)

    def get_top_albums(self, user_id: str, period=PERIOD_7DAYS) -> []:
        url = self._get_url(f'users/{user_id}/top-albums/')
        return self.process_request(url)

    def set_lastfm_user(self, user_id: str, lastfm_username: str) -> {}:
        url = self._get_url(f'users/set-lastfm-user/')
        data = {
            'username': lastfm_username,
            'user_id': user_id,
        }
        return self.process_request(url, method='post', data=data)

    def _get_url(self, endpoint_url) -> str:
        return f'{super().url}{self._url}{endpoint_url}'
