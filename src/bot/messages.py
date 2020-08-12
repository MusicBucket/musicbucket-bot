import logging
import re
from collections import OrderedDict

from emoji import emojize
from telegram import Update
from telegram.ext import CallbackContext

from bot import emojis
from bot.buttons import SaveLinkButton
from bot.logger import LoggerMixin
from bot.models import Link, CreateOrUpdateMixin
from bot.music.music import LinkType
from bot.music.spotify import SpotifyUtils
from bot.reply import ReplyMixin, ReplyType

log = logging.getLogger(__name__)


class MessageProcessor:
    @staticmethod
    def process_message(update: Update, context: CallbackContext):
        if not update.message:
            return
        message = update.message.text
        url = UrlProcessor.extract_url_from_message(message)
        if url:
            url_processor = UrlProcessor(update, context, url)
            url_processor.process()


class UrlProcessor(ReplyMixin, LoggerMixin, SpotifyUtils, CreateOrUpdateMixin):

    def __init__(self, update, context, url, command=None):
        self.update = update
        self.context = context
        self.url = url
        self.command = command

    def process(self):
        is_valid = self.is_valid_url(self.url)
        self.log_url_processing(self.url, is_valid, self.update)
        if is_valid:
            cleaned_url = self.clean_url(self.url)
            user = self.save_user(self.update.message.from_user)
            chat = self.save_chat(self.update.message.chat)
            sent_link = self.save_link(cleaned_url, user.get('id'), chat.get('id'))
            return self._build_message(sent_link)

    def _build_message(self, sent_link: OrderedDict):
        from bot.commands import NowPlayingCommand
        msg = '<strong>Saved: </strong>'
        link = sent_link.get('link')
        genres = ', '.join(Link.get_genres(link))

        if link.get('link_type') == LinkType.ARTIST.value:
            msg += '{} <strong>{}</strong>\n'.format(emojis.EMOJI_ARTIST, link.get('artist').get('name'))
        elif link.get('link_type') == LinkType.ALBUM.value:
            msg += '{} <strong>{}</strong> - <strong>{}</strong>\n'.format(
                emojis.EMOJI_ALBUM,
                link.get('album').get('artists')[0].get('name'),
                link.get('album').get('name')
            )
        elif link.get('link_type') == LinkType.TRACK.value:
            msg += '{} {} by <strong>{}</strong>\n'.format(
                emojis.EMOJI_TRACK,
                link.get('track').get('name'),
                link.get('track').get('artists')[0].get('name'),
            )
        # Only show the link if the processed url comes from a /np command
        if isinstance(self.command, NowPlayingCommand):
            msg += f'{link.get("url")} \n'

        msg += '<strong>Genres:</strong> {}'.format(genres if genres else 'N/A')
        save_link_button_keyboard_markup = SaveLinkButton.get_keyboard_markup(link.get('id'))
        preview_track = sent_link.get('spotify_preview_track', None)
        if preview_track:
            performer = preview_track.get('artists')[0].get('name', 'unknown')
            title = preview_track.get('name', 'unknown')
            self.reply(update=self.update, context=self.context, message=msg, reply_type=ReplyType.AUDIO,
                       audio=preview_track.get('preview_url'), title=title, performer=performer,
                       reply_markup=save_link_button_keyboard_markup)
        else:
            self.reply(self.update, self.context, msg, reply_markup=save_link_button_keyboard_markup)

    @staticmethod
    def extract_url_from_message(text):
        """Gets the first url of a message"""
        link = re.search("(?P<url>https?://[^\s]+)", text)
        if link is not None:
            url = link.group('url')
            return url
        return ''
