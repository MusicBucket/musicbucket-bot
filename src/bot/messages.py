import datetime
import re

from bot.logger import LoggerMixin
from bot.models import SaveChatMixin, SaveUserMixin, Link
from bot.music.music import LinkType
from bot.music.spotify import SpotifyUrlMixin, SpotifyClient


class MessageProcessor:
    @staticmethod
    def process_message(bot, update):
        message = update.message.text
        url = UrlProcessor.extract_url_from_message(message)
        if url:
            url_processor = UrlProcessor(bot, update, url)
            url_processor.process()


class UrlProcessor(LoggerMixin, SpotifyUrlMixin, SaveChatMixin, SaveUserMixin):
    def __init__(self, bot, update, url):
        self.bot = bot
        self.update = update
        self.url = url
        self.spotify_client = SpotifyClient()

    def process(self):
        is_valid = self.is_valid_url(self.url)
        link_type = self.get_link_type(self.url)
        self.log_url_processing(self.url, is_valid, self.update)
        if is_valid and link_type:
            cleaned_url = self.clean_url(self.url)
            entity_id = self.get_entity_id_from_url(self.url)
            user = self.save_user()
            chat = self.save_chat()
            link = Link(
                url=cleaned_url,
                link_type=link_type.value,
                user=user,
                chat=chat
            )

            if link_type == LinkType.ARTIST:
                spotify_artist = self.spotify_client.client.artist(entity_id)
                artist = self._save_artist(spotify_artist)
                spotify_track = self.spotify_client.get_artist_top_track(artist)
                link.artist = artist
            elif link_type == LinkType.ALBUM:
                spotify_album = self.spotify_client.client.album(entity_id)
                album = self._save_album(spotify_album)
                spotify_track = self.spotify_client.get_album_first_track(album)
                link.album = album
            elif link_type == LinkType.TRACK:
                spotify_track = self.spotify_client.client.track(entity_id)
                track = self._save_track(spotify_track)
                link.track = track
            link, updated = self._save_link(link)

            self.responser.reply_save_link(link, spotify_track, updated)

    def _save_link(self, link):
        """Update the link if it exists for a chat, create if it doesn't exist"""
        updated = False
        update_user = link.user
        existent_link = Link.get_or_none((Link.url == link.url) & (Link.chat == link.chat))
        if existent_link is not None:
            link = existent_link
            link.apply_update(update_user)
            link.save()
            updated = True
            self.log_db_operation(self.DBOperation.UPDATE, link)
        else:
            link.created_at = datetime.datetime.now()
            link.save()
            self.log_db_operation(self.DBOperation.CREATE, link)

        return link, updated

    def _save_artist(self):
        pass

    def _save_album(self):
        pass

    def _save_track(self):
        pass

    def _save_genres(self):
        pass

    @staticmethod
    def extract_url_from_message(text):
        """Gets the first url of a message"""
        link = re.search("(?P<url>https?://[^\s]+)", text)
        if link is not None:
            url = link.group('url')
            return url
        return ''
