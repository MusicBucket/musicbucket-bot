import logging

from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import CallbackContext

from bot.api_client.spotify_api_client import SpotifyAPIClient
from bot.logger import LoggerMixin
from bot.music.music import EntityType

log = logging.getLogger(__name__)


class SearchInline(LoggerMixin):
    INLINE = 'search'

    def __init__(self, update: Update, context: CallbackContext):
        self.update = update
        self.context = context
        self.spotify_api_client = SpotifyAPIClient()
        self._perform_search()

    def _perform_search(self):
        self.log_inline(self.INLINE, self.update)
        user_input = self.update.inline_query.query
        entity_type = self._get_entity_type(user_input)
        if not entity_type:
            return

        query = user_input.replace(entity_type, '').strip()
        results = []
        if len(query) >= 3:
            pass
            search_results = self.spotify_api_client.search(query, entity_type)
            results = self._build_results(search_results.get('results'), entity_type)
        self._show_search_results(results)

    def _show_search_results(self, results):
        self.update.inline_query.answer(results)

    @staticmethod
    def _build_results(search_results: [], entity_type: str) -> []:
        results = []
        for result in search_results:
            thumb_url = ''
            description = ''

            if entity_type == EntityType.TRACK.value:
                album = result['album']
                artists = result['artists']
                thumb_url = album['images'][0]['url']
                description = '{} - {}'.format(', '.join(artist['name'] for artist in artists), album['name'])
            elif entity_type == EntityType.ALBUM.value:
                thumb_url = result['images'][0]['url'] if result['images'] else ''
                artists = result['artists']
                description = ', '.join(artist['name'] for artist in artists)
            elif entity_type == EntityType.ARTIST.value:
                thumb_url = result['images'][0]['url'] if result['images'] else ''
                description = ', '.join(result['genres'])

            results.append(
                InlineQueryResultArticle(
                    id=result['id'],
                    thumb_url=thumb_url,
                    title=result['name'],
                    description=description,
                    input_message_content=InputTextMessageContent(result['external_urls']['spotify'])
                )
            )
        return results

    @staticmethod
    def _get_entity_type(user_input: str) -> str:
        entity_type = user_input.split(' ', 1)[0]
        valid_entity_type = False

        if entity_type == EntityType.ARTIST.value:
            valid_entity_type = True
        elif entity_type == EntityType.ALBUM.value:
            valid_entity_type = True
        elif entity_type == EntityType.TRACK.value:
            valid_entity_type = True

        if valid_entity_type:
            return entity_type
