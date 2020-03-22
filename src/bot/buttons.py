import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from bot.models import SavedLink, FollowedArtist


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
        user_id = query.from_user.id
        link_id = cls.get_callback_data(query.data)
        cls._save_to_user_saved_links(user_id, link_id)
        return

    @staticmethod
    def _save_to_user_saved_links(user_id, link_id):
        """Saves a link to the SavedLink table"""
        saved_link = SavedLink.get_or_none(user_id=user_id, link_id=link_id)
        if saved_link:
            saved_link.deleted_at = None
            saved_link.saved_at = datetime.datetime.now()
            saved_link.save()
        else:
            saved_link = SavedLink.create(
                user_id=user_id,
                link_id=link_id,
                saved_at=datetime.datetime.now()
            )
        return saved_link

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
            cls._unfollow_artist(followed_artist_id)
        context.bot.edit_message_reply_markup(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id
        )

    @staticmethod
    def _unfollow_artist(followed_artist_id):
        """Deletes a record of FollowedArtist table by it's id"""
        query = FollowedArtist.delete().where(FollowedArtist.id == followed_artist_id)
        return query.execute()

    @classmethod
    def get_keyboard_markup(cls, followed_artists):
        keyboard = []
        for followed_artist in followed_artists:
            keyboard.append([InlineKeyboardButton(
                str(followed_artist.artist), callback_data=f'{cls.CALLBACK_NAME}:{followed_artist.id}'
            )])
        keyboard.append([InlineKeyboardButton(
            str('Cancel'), callback_data=f'{cls.CALLBACK_NAME}:'
        )])
        return InlineKeyboardMarkup(keyboard)
