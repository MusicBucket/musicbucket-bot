import logging
import time
from enum import Enum

from telegram import ParseMode

log = logging.getLogger(__name__)

class ReplyType(Enum):
    TEXT = 0
    IMAGE = 1
    AUDIO = 2


class ReplyMixin:
    MAX_RESPONSE_LENGTH = 4096

    def reply(self, bot, update, message, reply_type=ReplyType.TEXT, audio=None, title=None, performer=None,
              image=None, disable_web_page_preview=False):
        if reply_type == ReplyType.TEXT:
            self._reply_text(update, message, disable_web_page_preview)
        if reply_type == ReplyType.AUDIO:
            self._reply_audio(bot, update, audio, message, performer, title)
        if reply_type == ReplyType.IMAGE:
            self._reply_image(bot, update, image, message)

    def _reply_text(self, update, message, disable_web_page_preview=True):
        """Replies the message to the original chat splitting the message if necessary"""
        if len(message) <= self.MAX_RESPONSE_LENGTH:
            update.message.reply_text(message, disable_web_page_preview=disable_web_page_preview,
                                      parse_mode=ParseMode.HTML)
            return

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

        for part in parts:
            update.message.reply_text(part, disable_web_page_preview=True,
                                      parse_mode=ParseMode.HTML)
            time.sleep(1)
        return

    @staticmethod
    def _reply_image(bot, update, image, caption):
        chat_id = update.message.chat_id
        bot.send_photo(chat_id, image, caption=caption, disable_web_page_preview=True, parse_mode=ParseMode.HTML)

    @staticmethod
    def _reply_audio(bot, update, audio, caption, performer, title):
        chat_id = update.message.chat_id
        reply_to_message_id = update.message.message_id
        bot.send_audio(chat_id, audio, title=title, performer=performer, caption=caption,
                       reply_to_message_id=reply_to_message_id, disable_web_page_preview=True,
                       parse_mode=ParseMode.HTML)
