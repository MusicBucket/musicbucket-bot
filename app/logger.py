import logging
from enum import Enum

from app import models

logger = logging.getLogger(__name__)


class Logger:
    class DBOperation:
        CREATE = 'Create'
        UPDATE = 'Update'
        DELETE = 'Delete'

    @staticmethod
    def log_command(command, command_args, update):
        user = update.message.from_user
        chat = update.message.chat

        logger.info(f'Command: "{command.value}". Args: "{", ".join(command_args)}". '
                    f'User: "{user.id} ({user.username or ""})". Chat: "{chat.id} ({chat.title or ""})"')

    @staticmethod
    def log_inline(command, update):
        user = update.inline_query.from_user
        query = update.inline_query.query

        logger.info(f'Inline: "{command.value}". Query: "{query}". '
                    f'User: "{user.id} ({user.username or ""})"')

    @staticmethod
    def log_url_processing(url, is_valid, update):
        user = update.message.from_user
        chat = update.message.chat

        logger.info(
            f'URL: "{url}". Valid: "{is_valid}". '
            f'User: "{user.id} ({user.username or ""})". Chat: "{chat.id} ({chat.title or ""})"')

    @staticmethod
    def log_db_operation(db_operation, entity):

        if isinstance(entity, models.Link):
            msg = f'{db_operation}. Link: "{entity.url}". Type: "{entity.link_type}". ' \
                f'User: "{entity.user.id} ({entity.user.username or ""}"). ' \
                f'Chat: {entity.chat.id} ({entity.chat.name or ""})'
        elif isinstance(entity, models.User):
            msg = f'{db_operation}. User: "{entity.id} ({entity.username or entity.first_name or ""}")'
        elif isinstance(entity, models.Chat):
            msg = f'{db_operation}. Chat: "{entity.id} ({entity.name})"'
        elif isinstance(entity, models.Artist):
            msg = f'{db_operation}. Artist: "{entity.name}"'
        elif isinstance(entity, models.Album):
            msg = f'{db_operation}. Album: "{entity.name}". Artist: "{entity.artists.first().name or ""}"'
        elif isinstance(entity, models.Track):
            msg = f'{db_operation}. Track: "{entity.name}". Artist: "{entity.artists.first().name or ""}"'
        elif isinstance(entity, models.Genre):
            msg = f'{db_operation}. Genre: "{entity}"'

        logger.info(msg)
