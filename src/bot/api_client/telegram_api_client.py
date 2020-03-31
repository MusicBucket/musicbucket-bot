import datetime
from collections import OrderedDict

from bot.api_client.api_client import BaseAPIClient


class TelegramAPIClient(BaseAPIClient):
    _url = 'telegram/'

    def create_user(self, user):
        url = self._get_url('users/')
        data = {
            'telegram_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'link': user.link,
        }
        return self.process_request(url, method='post', data=data)

    def create_chat(self, chat):
        url = self._get_url('chats/')
        data = {
            'telegram_id': chat.id,
            'name': chat.title or chat.username or chat.first_name,
            'chat_type': chat.type,
        }
        return self.process_request(url, method='post', data=data)

    def create_sent_link(self, spotify_url: str, user_id: str, chat_id: str) -> OrderedDict:
        """
        We do not create links directly, so we create a sent-spotify-link sending the
        link url because if it doesn't exist in the DB, it creates automatically
        :param spotify_url:
        :param user_id:
        :param chat_id:
        :return:
        """
        url = self._get_url('sent-spotify-links/')
        data = {
            'url': spotify_url,
            'sent_by_id': user_id,
            'chat_id': chat_id,
        }
        return self.process_request(url, method='post', data=data)

    def get_sent_links(self, chat_id: str = None, user_id: str = None, user_username: str = None,
                       since_date: datetime.date = None) -> []:
        url = self._get_url('sent-spotify-links/')
        params = {}
        if chat_id:
            params.update({'chat__telegram_id': chat_id})
        if user_id:
            params.update({'sent_by__telegram_id': user_id})
        if user_username:
            params.update({'sent_by__username': user_username})
        if since_date:
            params.update({'sent_at__gte': since_date.strftime(self.DATE_FORMAT)})
        return self.process_request(url, params=params)

    def get_stats(self, chat_id: str) -> []:
        url = self._get_url(f'stats/{chat_id}/')
        return self.process_request(url)

    def _get_url(self, endpoint_url: str) -> str:
        return f'{super().url}{self._url}{endpoint_url}'
