from collections import OrderedDict

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from bot.api_client.spotify_api_client import SpotifyAPIClient
from bot.api_client.telegram_api_client import TelegramAPIClient
from bot.models import FollowedArtist, Link


class BaseButton:
    CALLBACK_NAME = None

    @classmethod
    def get_callback_data(cls, query_data):
        callback_data = query_data.split(f"{cls.CALLBACK_NAME}:")[1]
        return callback_data


class SaveLinkButton(BaseButton):
    """
    Defines a Save Link Button used in messages to save a sent link into an user's savedlinks table
    """
    CALLBACK_NAME = 'save_link'

    @classmethod
    def handle(cls, update: Update, context: CallbackContext):
        """Handles the pulsation of the button"""
        query = update.callback_query
        link_id = cls.get_callback_data(query.data)
        user = cls._save_user(query.from_user)
        cls._save_link(link_id, user.get('id'))
        return

    @staticmethod
    def _save_user(user):
        telegram_api_client = TelegramAPIClient()
        create_user_response = telegram_api_client.create_user(user)
        return create_user_response

    @staticmethod
    def _save_link(link_id: int, user_id: int) -> OrderedDict:
        spotify_api_client = SpotifyAPIClient()
        create_saved_link_response = spotify_api_client.create_saved_link(link_id, user_id)
        return create_saved_link_response

    @classmethod
    def get_keyboard_markup(cls, link_id):
        keyboard = [[InlineKeyboardButton("Save", callback_data=f'{cls.CALLBACK_NAME}:{link_id}')]]
        return InlineKeyboardMarkup(keyboard)


class DeleteSavedLinkButton(BaseButton):
    """
    Defines the Delete Saved Link Button shown when calling /deletesavedlinks command
    """
    CALLBACK_NAME = 'delete_saved_link'

    @classmethod
    def handle(cls, update: Update, context: CallbackContext):
        """Handles the pulsation of the button"""
        query = update.callback_query
        saved_link_id = cls.get_callback_data(query.data)
        if saved_link_id:
            SpotifyAPIClient().delete_saved_link(saved_link_id)
        context.bot.edit_message_reply_markup(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id
        )

    @classmethod
    def get_keyboard_markup(cls, saved_links):
        keyboard = []
        for saved_link in saved_links:
            link = saved_link.get('link')
            keyboard.append([InlineKeyboardButton(
                Link.get_name(link), callback_data=f'{cls.CALLBACK_NAME}:{saved_link.get("id")}'
            )])
        keyboard.append([InlineKeyboardButton(
            'Cancel', callback_data=f'{cls.CALLBACK_NAME}:'
        )])
        return InlineKeyboardMarkup(keyboard)


class UnfollowArtistButton(BaseButton):
    """
    Defines the UnfollowArtist Button show when calling /unfollowartists command
    """
    CALLBACK_NAME = 'unfollow_artist'

    @classmethod
    def handle(cls, update: Update, context: CallbackContext):
        """Handles the pulsation of the button"""
        query = update.callback_query
        followed_artist_id = cls.get_callback_data(query.data)
        if followed_artist_id:
            SpotifyAPIClient().delete_followed_artist(followed_artist_id)
        context.bot.edit_message_reply_markup(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id
        )

    @classmethod
    def get_keyboard_markup(cls, followed_artists):
        keyboard = []
        for followed_artist in followed_artists:
            keyboard.append([InlineKeyboardButton(
                followed_artist.get('artist').get('name'),
                callback_data=f'{cls.CALLBACK_NAME}:{followed_artist.get("id")}'
            )])
        keyboard.append([InlineKeyboardButton(
            str('Cancel'), callback_data=f'{cls.CALLBACK_NAME}:'
        )])
        return InlineKeyboardMarkup(keyboard)
