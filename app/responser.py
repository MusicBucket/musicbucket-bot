import logging
import time
from enum import Enum

from telegram import ParseMode

from app.music.music import LinkType
from emoji import emojize

logger = logging.getLogger(__name__)


class Responser:
    MAX_MESSAGE_LENGTH = 4096

    def __init__(self, bot, update):
        self.bot = bot
        self.update = update

    def reply_music(self, user_links):
        msg = '<strong>Music from the last week:</strong> \n'
        for user, links in user_links.items():
            msg += '- {} <strong>{}:</strong>\n'.format(emojize(':baby:', use_aliases=True),
                                                        user.username or user.firstname)
            for link in links:
                if link.link_type == LinkType.ARTIST.value:
                    msg += '    {} <a href="{}">{}</a> {}\n'.format(
                        emojize(':busts_in_silhouette:', use_aliases=True),
                        link.url,
                        link.artist_name,
                        '({})'.format(link.genre) if link.genre is not None else '')
                elif link.link_type == LinkType.ALBUM.value:
                    msg += '    {} <a href="{}">{} - {}</a> {}\n'.format(
                        emojize(':cd:', use_aliases=True),
                        link.url,
                        link.artist_name,
                        link.album_name,
                        '({})'.format(link.genre) if link.genre is not None else '')
                elif link.link_type == LinkType.TRACK.value:
                    msg += '    {} <a href="{}">{} by {}</a> {}\n'.format(
                        emojize(':musical_note:', use_aliases=True),
                        link.url,
                        link.track_name,
                        link.artist_name,
                        '({})'.format(link.genre) if link.genre is not None else '')
            msg += '\n'
        self._reply(msg)

    def reply_music_from_beginning(self, user_links):
        msg = '<strong>Music from the beginning of time:</strong> \n'
        for user, links in user_links.items():
            msg += '- {} <strong>{}:</strong>\n'.format(emojize(':baby:', use_aliases=True),
                                                        user.username or user.firstname)
            for link in links:
                if link.link_type == LinkType.ARTIST.value:
                    msg += '    {}  {} <a href="{}">{}</a> {}\n'.format(
                        emojize(':busts_in_silhouette:', use_aliases=True),
                        '[{}]'.format(link.created_at.strftime(
                            "%Y/%m/%d"),
                            ' | Updated @ {} by {}'.format(link.updated_at.strftime(
                                "%Y/%m/%d"),
                                link.last_update_user.username or link.last_update_user.first_name or '') if link.last_update_user else ''),
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
                                link.last_update_user.username or link.last_update_user.first_name or '') if link.last_update_user else ''),
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
                                link.last_update_user.username or link.last_update_user.first_name or '') if link.last_update_user else ''),
                        link.url,
                        link.track_name,
                        link.artist_name,
                        '({})'.format(link.genre) if link.genre is not None else '')
            msg += '\n'
        self._reply(msg)

    def reply_stats(self, users):
        msg = '<strong>Links sent by the users from the beginning in this chat:</strong> \n'

        for user in users:
            msg += '- {} <strong>{}:</strong> {}\n'.format(emojize(':baby:', use_aliases=True),
                                                           user.username or user.firstname,
                                                           user.links)
        self._reply(msg)

    def reply_save_link(self, link_info, updated):
        msg = '<strong>{}: </strong>'.format(
            'Saved' if not updated else 'Updated')
        genres = ', '.join(link_info.genres)

        if link_info.link_type == LinkType.ARTIST:

            msg += '{} <strong>{}</strong>\n'.format(emojize(':busts_in_silhouette:', use_aliases=True),
                                    link_info.artist)
        elif link_info.link_type == LinkType.ALBUM:
            msg += '{} <strong>{}</strong> - <strong>{}</strong>\n'.format(emojize(':cd:', use_aliases=True),
                                         link_info.artist,
                                         link_info.album)
        elif link_info.link_type == LinkType.TRACK:
            msg += '{} {} by <strong>{}</strong>\n'.format(emojize(':musical_note:', use_aliases=True),
                                          link_info.track,
                                          link_info.artist)
        msg += '<strong>Genres:</strong> {}'.format(genres)
        self._reply(msg)

    def show_search_results(self, results):
        self.update.inline_query.answer(results)

    def error_music_from_beginning_no_username(self):
        msg = 'Command usage /music_from_beginning @username'
        self._reply(msg)

    def error_no_links_found(self, username):
        if username:
            msg = f'No links were found for this username {username}'
        else:
            msg = 'No links were found.'
        self._reply(msg)

    def _reply(self, message):
        """Replies the message to the original chat"""
        if len(message) <= self.MAX_MESSAGE_LENGTH:
            self.update.message.reply_text(message, disable_web_page_preview=True,
                                           parse_mode=ParseMode.HTML)
            return

        parts = []
        while len(message) > 0:
            if len(message) > self.MAX_MESSAGE_LENGTH:
                part = message[:self.MAX_MESSAGE_LENGTH]
                first_lnbr = part.rfind('\n')
                if first_lnbr != -1:
                    parts.append(part[:first_lnbr])
                    message = message[(first_lnbr + 1):]
                else:
                    parts.append(part)
                    message = message[self.MAX_MESSAGE_LENGTH:]
            else:
                parts.append(message)
                break

        for part in parts:
            self.update.message.reply_text(part, disable_web_page_preview=True,
                                           parse_mode=ParseMode.HTML)
            time.sleep(1)
        return
