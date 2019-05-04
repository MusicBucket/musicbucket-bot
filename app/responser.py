import logging
import time
from enum import Enum

from telegram import ParseMode

from app.music.music import LinkType
from emoji import emojize

logger = logging.getLogger(__name__)


class ResponseType(Enum):
    """Response types based on the available commands"""
    FROM_THE_BEGINNING = 0
    LAST_WEEK = 1


class Responser:
    MAX_MESSAGE_LENGTH = 4096

    @classmethod
    def reply_message(cls, update, message):
        if len(message) <= cls.MAX_MESSAGE_LENGTH:
            update.message.reply_text(message, disable_web_page_preview=True,
                                      parse_mode=ParseMode.HTML)
            return

        parts = []
        while len(message) > 0:
            if len(message) > cls.MAX_MESSAGE_LENGTH:
                part = message[:cls.MAX_MESSAGE_LENGTH]
                first_lnbr = part.rfind('\n')
                if first_lnbr != -1:
                    parts.append(part[:first_lnbr])
                    message = message[(first_lnbr + 1):]
                else:
                    parts.append(part)
                    message = message[cls.MAX_MESSAGE_LENGTH:]
            else:
                parts.append(message)
                break

        for part in parts:
            update.message.reply_text(part, disable_web_page_preview=True,
                                      parse_mode=ParseMode.HTML)
            time.sleep(1)
        return

    @staticmethod
    def links_by_user(user_links, response_type):
        msg = ''
        if response_type == ResponseType.LAST_WEEK:
            msg += '<strong>Music from the last week:</strong> \n'
        elif response_type == ResponseType.FROM_THE_BEGINNING:
            msg += '<strong>Music from the beginning of time:</strong> \n'

        for user, links in user_links.items():
            msg += '- {} <strong>{}:</strong>\n'.format(emojize(':baby:', use_aliases=True),
                                                        user.username or user.firstname)
            logger.info('User: {}, Links: {}'.format(user.id, links))
            for link in links:
                logger.info('Link: {}'.format(link.url))

                if link.link_type == LinkType.ARTIST.value:
                    msg += '    {}  {} <a href="{}">{}</a> {}\n'.format(
                        emojize(':busts_in_silhouette:', use_aliases=True),
                        '[{}{}]'.format(link.created_at.strftime(
                            "%Y/%m/%d"),
                            ' | Updated @ {} by {}'.format(link.updated_at.strftime(
                                "%Y/%m/%d"),
                                link.last_update_user.username or link.last_update_user.first_name or '') if link.last_update_user else '') if response_type == ResponseType.FROM_THE_BEGINNING else '',
                        link.url,
                        link.artist_name,
                        '({})'.format(link.genre) if link.genre is not None else '')
                elif link.link_type == LinkType.ALBUM.value:
                    msg += '    {}  {} <a href="{}">{} - {}</a> {}\n'.format(
                        emojize(':cd:', use_aliases=True),
                        '[{}{}]'.format(link.created_at.strftime(
                            "%Y/%m/%d"),
                            ' | Updated @ {} by {}'.format(link.updated_at.strftime(
                                "%Y/%m/%d"),
                                link.last_update_user.username or link.last_update_user.first_name or '') if link.last_update_user else '') if response_type == ResponseType.FROM_THE_BEGINNING else '',
                        link.url,
                        link.artist_name,
                        link.album_name,
                        '({})'.format(link.genre) if link.genre is not None else '')
                elif link.link_type == LinkType.TRACK.value:
                    msg += '    {}  {} <a href="{}">{} by {}</a> {}\n'.format(
                        emojize(':musical_note:', use_aliases=True),
                        '[{}{}]'.format(link.created_at.strftime(
                            "%Y/%m/%d"),
                            ' | Updated @ {} by {}'.format(link.updated_at.strftime(
                                "%Y/%m/%d"),
                                link.last_update_user.username or link.last_update_user.first_name or '') if link.last_update_user else '') if response_type == ResponseType.FROM_THE_BEGINNING else '',
                        link.url,
                        link.track_name,
                        link.artist_name,
                        '({})'.format(link.genre) if link.genre is not None else '')
            msg += '\n'
        return msg

    @staticmethod
    def link_info(link):
        return ''

    @staticmethod
    def stats_by_user(users):
        msg = '<strong>Links sent by the users from the beginning in this chat:</strong> \n'

        for user in users:
            msg += '- {} <strong>{}:</strong> {}\n'.format(emojize(':baby:', use_aliases=True),
                                                           user.username or user.firstname,
                                                           user.links)
        return msg

    @staticmethod
    def music_from_beginning_no_username():
        msg = 'Command usage /music_from_beginning @username'
        return msg

    @staticmethod
    def no_links_found(username):
        if username:
            msg = f'No links were found for this username {username}'
        else:
            msg = 'No links were found.'
        return msg


