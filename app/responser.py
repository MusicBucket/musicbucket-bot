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
                        link.artist.name,
                        '({})'.format(link.genres[0]) if len(link.genres) > 0 is not None else '')
                elif link.link_type == LinkType.ALBUM.value:
                    msg += '    {} <a href="{}">{} - {}</a> {}\n'.format(
                        emojize(':cd:', use_aliases=True),
                        link.url,
                        link.album.artists.first().name,
                        link.album.name,
                        '({})'.format(link.genres[0]) if len(link.genres) > 0 is not None else '')
                elif link.link_type == LinkType.TRACK.value:
                    msg += '    {} <a href="{}">{} by {}</a> {}\n'.format(
                        emojize(':musical_note:', use_aliases=True),
                        link.url,
                        link.track.name,
                        link.track.artists.first().name,
                        '({})'.format(link.genres[0]) if len(
                            link.genres) > 0 is not None else '')
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
                        link.artist.name,
                        '({})'.format(link.genres[0]) if len(link.genres) > 0 is not None else '')
                elif link.link_type == LinkType.ALBUM.value:
                    msg += '    {}  {} <a href="{}">{} - {}</a> {}\n'.format(
                        emojize(':cd:', use_aliases=True),
                        '[{}{}]'.format(link.created_at.strftime(
                            "%Y/%m/%d"),
                            ' | Updated @ {} by {}'.format(link.updated_at.strftime(
                                "%Y/%m/%d"),
                                link.last_update_user.username or link.last_update_user.first_name or '') if link.last_update_user else ''),
                        link.url,
                        link.album.artists[0].name,
                        link.album.name,
                        '({})'.format(link.genres[0]) if len(link.genres) > 0 is not None else '')
                elif link.link_type == LinkType.TRACK.value:
                    msg += '    {}  {} <a href="{}">{} by {}</a> {}\n'.format(
                        emojize(':musical_note:', use_aliases=True),
                        '[{}{}]'.format(link.created_at.strftime(
                            "%Y/%m/%d"),
                            ' | Updated @ {} by {}'.format(link.updated_at.strftime(
                                "%Y/%m/%d"),
                                link.last_update_user.username or link.last_update_user.first_name or '') if link.last_update_user else ''),
                        link.url,
                        link.track.name,
                        link.track.artists[0].name,
                        '({})'.format(link.genres[0]) if len(
                            link.genres) > 0 is not None else '')
            msg += '\n'
        self._reply(msg)

    def reply_recommendations(self, track_recommendations, artist_seeds):
        if len(track_recommendations['tracks']) == 0 or len(artist_seeds) == 0:
            msg = 'There are not recommendations for this week yet. Send some music!'
            self._reply(msg)
            return

        artists_names = [artist.name for artist in artist_seeds]
        msg = 'Track recommendations of the week, based on the artists: <strong>{}</strong>\n'.format(
            '</strong>, <strong>'.join(artists_names))

        for track in track_recommendations['tracks']:
            msg += '{} <a href="{}">{}</a> by <strong>{}</strong>\n'.format(
                emojize(':musical_note:', use_aliases=True),
                track['external_urls']['spotify'],
                track['name'],
                track['artists'][0]['name'])
        self._reply(msg)

    def reply_now_playing(self, now_playing, username):
        if not now_playing:
            msg = f'<b>{username}</b> is not currently playing music'
            self._reply(msg)
            return

        artist_emoji = emojize(':busts_in_silhouette:', use_aliases=True)
        album_emoji = emojize(':cd:', use_aliases=True)
        track_emoji = emojize(':musical_note:', use_aliases=True)
        artist = now_playing['artist_name']
        album = now_playing['album_name']
        track = now_playing['track_name']
        cover = now_playing['cover']

        msg = f"<b>{username}</b>'s now playing:\n"
        msg += f"{track_emoji} {track or ''}\n"
        msg += f"{album_emoji} {album or ''}\n"
        msg += f"{artist_emoji} {artist or ''}\n"

        self._reply_image(cover, msg)

    def reply_lastfmset(self, username):
        msg = f"<b>{username}</b>'s Last.fm username set correctly"
        self._reply(msg)

    def reply_stats(self, users):
        msg = '<strong>Links sent by the users from the beginning in this chat:</strong> \n'

        for user in users:
            msg += '- {} <strong>{}:</strong> {}\n'.format(emojize(':baby:', use_aliases=True),
                                                           user.username or user.firstname,
                                                           user.links)
        self._reply(msg)

    def reply_save_link(self, link, updated):
        msg = '<strong>{}: </strong>'.format(
            'Saved' if not updated else 'Updated')
        genre_names = [g.name for g in link.genres]
        genres = ', '.join(genre_names)

        if link.link_type == LinkType.ARTIST.value:
            msg += '{} <strong>{}</strong>\n'.format(emojize(':busts_in_silhouette:', use_aliases=True),
                                                     link.artist.name)
        elif link.link_type == LinkType.ALBUM.value:
            msg += '{} <strong>{}</strong> - <strong>{}</strong>\n'.format(emojize(':cd:', use_aliases=True),
                                                                           link.album.artists.first().name,
                                                                           link.album.name)
        elif link.link_type == LinkType.TRACK.value:
            msg += '{} {} by <strong>{}</strong>\n'.format(emojize(':musical_note:', use_aliases=True),
                                                           link.track.name,
                                                           link.track.artists.first().name)
        msg += '<strong>Genres:</strong> {}'.format(genres if len(genres) > 0 else 'N/A')
        self._reply(msg)

    def show_search_results(self, results):
        self.update.inline_query.answer(results)

    def error_music_from_beginning_no_username(self):
        msg = 'Command usage /music_from_beginning @username'
        self._reply(msg)

    def error_lastfmset_username_no_username(self):
        msg = 'Command usage /lastfmset username'
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

    def _reply_image(self, image, caption):
        chat_id = self.update.message.chat_id
        self.bot.send_photo(chat_id, image, caption, disable_web_page_preview=True, parse_mode=ParseMode.HTML)
