import logging
import re

from emoji import emojize
from telegram import Update, InlineKeyboardButton
from telegram.ext import CallbackContext

from bot.buttons import SaveLinkButton
from bot.logger import LoggerMixin
from bot.models import Link, CreateOrUpdateMixin
from bot.music.music import LinkType
from bot.music.spotify import SpotifyUrlMixin, SpotifyClient
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


class UrlProcessor(ReplyMixin, LoggerMixin, SpotifyUrlMixin, CreateOrUpdateMixin):

    def __init__(self, update, context, url, command=None):
        self.update = update
        self.context = context
        self.url = url
        self.command = command
        self.spotify_client = SpotifyClient()

    def process(self):
        is_valid = self.is_valid_url(self.url)
        link_type = self.get_link_type(self.url)
        self.log_url_processing(self.url, is_valid, self.update)
        if is_valid and link_type:
            cleaned_url = self.clean_url(self.url)
            entity_id = self.get_entity_id_from_url(self.url)
            user = self.save_user(self.update)
            chat = self.save_chat(self.update)
            link = Link(
                url=cleaned_url,
                link_type=link_type.value,
                user=user,
                chat=chat
            )

            spotify_track = None
            if link_type == LinkType.ARTIST:
                spotify_artist = self.spotify_client.client.artist(entity_id)
                artist = self.save_artist(spotify_artist)
                spotify_track = self.spotify_client.get_artist_top_track(artist)
                link.artist = artist
            elif link_type == LinkType.ALBUM:
                spotify_album = self.spotify_client.client.album(entity_id)
                album = self.save_album(spotify_album)
                spotify_track = self.spotify_client.get_album_first_track(album)
                link.album = album
            elif link_type == LinkType.TRACK:
                spotify_track = self.spotify_client.client.track(entity_id)
                track = self.save_track(spotify_track)
                link.track = track
            link, updated = self.save_link(link)

            return self._build_message(link, spotify_track, updated)

    def _build_message(self, link, spotify_track, updated):
        from bot.commands import NowPlayingCommand
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
        # Only show the link if the processed url comes from a /np command
        if isinstance(self.command, NowPlayingCommand):
            msg += f'{link.url} \n'

        msg += '<strong>Genres:</strong> {}'.format(genres if genres else 'N/A')
        save_link_button_keyboard_markup = SaveLinkButton.get_keyboard_markup(link.id)
        track_preview_url = spotify_track.get('preview_url', None)
        if track_preview_url:
            performer = spotify_track['artists'][0].get('name', 'unknown')
            title = spotify_track.get('name', 'unknown')
            self.reply(update=self.update, context=self.context, message=msg, reply_type=ReplyType.AUDIO,
                       audio=track_preview_url, title=title, performer=performer,
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
