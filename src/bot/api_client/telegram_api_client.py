import datetime

from bot.api_client.api_client import BaseAPIClient


class TelegramAPIClient(BaseAPIClient):
    _url = 'telegram/'

    def get_url(self) -> str:
        return f'{super().url}{self._url}'

    def get_sent_links(self, chat_id: str, user_id: str = None, since_date: datetime.date = None) -> []:
        params = {
            'chat__telegram_id': chat_id,
        }
        if user_id:
            params.update({'sent_by__telegram_id': user_id})
        if since_date:
            params.update({'sent_at__gte': since_date.strftime(self.DATE_FORMAT)})
        return self.process_request(params=params)
