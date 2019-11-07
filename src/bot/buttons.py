import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.models import SavedLink


class SaveLinkButton:
    """
    Defines a Save Link Button used in messages to save a sent link into an user's savedlinks table
    """

    @classmethod
    def handle(cls, update, context):
        """Handles the pulsation of the button"""
        query = update.callback_query
        user_id = query.from_user.id
        link_id = query.data
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

    @staticmethod
    def get_keyboard_markup(link_id):
        keyboard = [[InlineKeyboardButton("Save", callback_data=link_id)]]
        return InlineKeyboardMarkup(keyboard)
