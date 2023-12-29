import logging

from bot import models

log = logging.getLogger(__name__)


class LoggerMixin:
    class DBOperation:
        CREATE = 'Create'
        UPDATE = 'Update'
        DELETE = 'Delete'

    @staticmethod
    def log_command(command, command_args, update):
        if update.message:
            user = update.message.from_user
            chat = update.message.chat
        elif update.edited_message:
            user = update.edited_message.from_user
            chat = update.edited_message.chat
        else:
            raise Exception(f"No message or edited_message: {update}")

        log.info(
            f'Command: "{command}". Args: "{", ".join(command_args)}". '
            f'User: "{user.id} ({user.username or ""})". Chat: "{chat.id} ({chat.title or ""})"'
        )

    @staticmethod
    def log_inline(inline, update):
        user = update.inline_query.from_user
        query = update.inline_query.query

        log.info(
            f'Inline: "{inline}". Query: "{query}". '
            f'User: "{user.id} ({user.username or ""})"'
        )

    @staticmethod
    def log_url_processing(url, is_valid, update):
        user = update.message.from_user
        chat = update.message.chat

        log.info(
            f'URL: "{url}". Valid: "{is_valid}". '
            f'User: "{user.id} ({user.username or ""})". Chat: "{chat.id} ({chat.title or ""})"'
        )

    @staticmethod
    def log_db_operation(db_operation, entity):
        msg = ''
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

        log.info(msg)
