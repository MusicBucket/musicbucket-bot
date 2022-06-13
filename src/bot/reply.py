import logging
import time
from enum import Enum
from typing import List

from telegram import ParseMode

log = logging.getLogger(__name__)


class ReplyType(Enum):
    TEXT = 0
    IMAGE = 1
    AUDIO = 2


class ReplyMixin:
    MAX_RESPONSE_LENGTH = 4096

    def reply(self, update, context, message, reply_type=ReplyType.TEXT, reply_markup=None, audio=None, title=None,
              performer=None, image=None, disable_web_page_preview=False):
        if reply_type == ReplyType.TEXT:
            self._reply_text(update, message, reply_markup, disable_web_page_preview)
        if reply_type == ReplyType.AUDIO:
            self._reply_audio(update, context, audio, message, performer, title, reply_markup)
        if reply_type == ReplyType.IMAGE:
            self._reply_image(update, context, image, message, reply_markup)

    def _reply_text(self, update, message, reply_markup=None, disable_web_page_preview=True):
        """Replies the message to the original chat splitting the message if necessary"""

        # For some reason, can occur that message is None at this point
        if not message:
            return

        # If text can be sent in a single message
        if len(message) <= self.MAX_RESPONSE_LENGTH:
            update.message.reply_text(message, disable_web_page_preview=disable_web_page_preview,
                                      parse_mode=ParseMode.HTML, reply_markup=reply_markup)
            return

        # If the text is too large that has to be splitted into many messages
        parts = self._split_message_in_parts(message)

        for part in parts:
            update.message.reply_text(part, disable_web_page_preview=True,
                                      parse_mode=ParseMode.HTML)
            time.sleep(1)
        return

    def _split_message_in_parts(self, message) -> List[str]:
        """Splits the message into parts if necessary"""
        parts = []
        while len(message) > 0:
            if len(message) > self.MAX_RESPONSE_LENGTH:
                part = message[:self.MAX_RESPONSE_LENGTH]
                first_lnbr = part.rfind('\n')
                if first_lnbr != -1:
                    parts.append(part[:first_lnbr])
                    message = message[(first_lnbr + 1):]
                else:
                    parts.append(part)
                    message = message[self.MAX_RESPONSE_LENGTH:]
            else:
                parts.append(message)
                break
        return parts

    @staticmethod
    def _reply_image(update, context, image, caption, reply_markup=None):
        chat_id = update.message.chat_id
        context.bot.send_photo(chat_id, image, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup)

    @staticmethod
    def _reply_audio(update, context, audio, caption, performer, title, reply_markup=None):
        chat_id = update.message.chat_id
        reply_to_message_id = update.message.message_id
        context.bot.send_audio(chat_id, audio, title=title, performer=performer, caption=caption,
                               reply_to_message_id=reply_to_message_id,
                               parse_mode=ParseMode.HTML, reply_markup=reply_markup)
