import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.models import SavedLink


class ButtonMixin:

    @classmethod
    def get_callback_data(cls, query_data):
        callback_data = query_data.split(f"{cls.CALLBACK_NAME}:")[1]
        return callback_data


class SaveLinkButton(ButtonMixin):
    """
    Defines a Save Link Button used in messages to save a sent link into an user's savedlinks table
    """
    CALLBACK_NAME = 'save_link'

    @classmethod
    def handle(cls, update, context):
        """Handles the pulsation of the button"""
        query = update.callback_query
        user_id = query.from_user.id
        link_id = cls.get_callback_data(query.data)
        cls._save_to_user_saved_links(user_id, link_id)
        context.bot.edit_message_reply_markup(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )

    @staticmethod
    def _save_to_user_saved_links(user_id, link_id):
        """Saves a link to the SavedLink table"""
        return SavedLink.get_or_create(
            user_id=user_id,
            link_id=link_id,
            defaults={'saved_at': datetime.datetime.now()}
        )

    @classmethod
    def get_keyboard_markup(cls, link_id):
        keyboard = [[InlineKeyboardButton("Save", callback_data=f'{cls.CALLBACK_NAME}:{link_id}')]]
        return InlineKeyboardMarkup(keyboard)


class DeleteSavedLinkButton(ButtonMixin):
    """
    Defines the Delete Saved Link Button shown when calling /deletesavedlinks command
    """
    CALLBACK_NAME = 'delete_saved_link'

    @classmethod
    def handle(cls, update, context):
        """Handles the pulsation of the button"""
        query = update.callback_query
        saved_link_id = cls.get_callback_data(query.data)
        cls._delete_from_user_saved_links(saved_link_id)
        context.bot.edit_message_reply_markup(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id
        )

    @staticmethod
    def _delete_from_user_saved_links(saved_link_id):
        """(Soft)Deletes a link of an user from the SavedLink table"""
        query = SavedLink.update(deleted_at=datetime.datetime.now()).where(SavedLink.id == saved_link_id).returning(
            SavedLink)
        return query.execute()

    @classmethod
    def get_keyboard_markup(cls, saved_links):
        keyboard = []
        for saved_link in saved_links:
            keyboard.append([InlineKeyboardButton(
                str(saved_link.link), callback_data=f'{cls.CALLBACK_NAME}:{saved_link.id}'
            )])
        return InlineKeyboardMarkup(keyboard)
