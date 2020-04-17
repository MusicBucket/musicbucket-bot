import logging
import datetime
from collections import OrderedDict

from emoji import emojize
from peewee import Model, CharField, DateTimeField, IntegerField, ForeignKeyField, ManyToManyField, \
    BooleanField, AutoField, DateField

from bot.api_client.spotify_api_client import SpotifyAPIClient
from bot.api_client.telegram_api_client import TelegramAPIClient
from bot.db import db
from bot.music.music import StreamingServiceType, LinkType

log = logging.getLogger(__name__)


class BaseModel(Model):
    class Meta:
        database = db


class EmojiModelMixin:
    EMOJI = None

    @classmethod
    def get_emoji(cls):
        raise NotImplementedError()


class User(BaseModel, EmojiModelMixin):
    EMOJI = ':baby:'

    id = CharField(primary_key=True)
    username = CharField(null=True)
    first_name = CharField(null=True)

    @classmethod
    def get_emoji(cls):
        return emojize(cls.EMOJI, use_aliases=True)

    def __str__(self):
        return 'User {}'.format(self.id)


class Chat(BaseModel):
    id = CharField(primary_key=True)
    name = CharField()

    def __str__(self):
        return 'Chat {}-{}'.format(self.id, self.name)


class Genre(BaseModel):
    name = CharField(primary_key=True)

    def __str__(self):
        return self.name


class Artist(BaseModel, EmojiModelMixin):
    EMOJI = ':busts_in_silhouette:'

    id = CharField(primary_key=True)
    name = CharField()
    image = CharField(null=True)
    popularity = IntegerField(null=True)
    href = CharField(null=True)
    spotify_url = CharField(null=True)
    uri = CharField()
    genres = ManyToManyField(Genre, backref='artists')

    def __str__(self):
        return self.name

    @classmethod
    def get_emoji(cls):
        return emojize(cls.EMOJI, use_aliases=True)


ArtistGenre = Artist.genres.get_through_model()


class Album(BaseModel, EmojiModelMixin):
    EMOJI = ':cd:'

    ALBUM_TYPES = (
        'album',
        'single',
        'compilation',)
    id = CharField(primary_key=True)
    name = CharField()
    label = CharField(null=True)
    image = CharField(null=True)
    popularity = IntegerField(null=True)
    href = CharField(null=True)
    spotify_url = CharField(null=True)
    album_type = CharField(null=True)
    uri = CharField()
    release_date = DateField()
    release_date_precision = CharField(null=True)

    genres = ManyToManyField(Genre, backref='albums')
    artists = ManyToManyField(Artist, backref='albums')

    def __str__(self):
        return self.name

    def get_first_artist(self):
        if self.artists:
            return self.artists.first()
        return None

    @staticmethod
    def parse_release_date(release_date: str, release_date_precision) -> datetime.date:
        if release_date_precision == 'day':
            return datetime.datetime.strptime(release_date, '%Y-%m-%d').date()
        elif release_date_precision == 'month':
            return datetime.datetime.strptime(release_date, '%Y-%m').date()
        elif release_date_precision == 'year':
            return datetime.datetime.strptime(release_date, '%Y').date()

    @classmethod
    def get_emoji(cls):
        return emojize(cls.EMOJI, use_aliases=True)


AlbumGenre = Album.genres.get_through_model()
AlbumArtist = Album.artists.get_through_model()


class Track(BaseModel, EmojiModelMixin):
    EMOJI = ':musical_note:'

    id = CharField(primary_key=True)
    name = CharField()
    track_number = IntegerField(null=True)
    duration_ms = IntegerField(null=True)
    explicit = BooleanField(null=True)
    popularity = IntegerField(null=True)
    href = CharField(null=True)
    spotify_url = CharField(null=True)
    preview_url = CharField(null=True)
    uri = CharField()
    album = ForeignKeyField(Album, backref='tracks')
    artists = ManyToManyField(Artist, backref='tracks')

    def __str__(self):
        return self.name

    def get_first_artist(self):
        if self.artists:
            return self.artists.first()
        return None

    @classmethod
    def get_emoji(cls):
        return emojize(cls.EMOJI, use_aliases=True)


TrackArtist = Track.artists.get_through_model()


class Link(BaseModel, EmojiModelMixin):
    id = AutoField()
    url = CharField()
    link_type = CharField()
    streaming_service_type = CharField(default=StreamingServiceType.SPOTIFY.value)
    created_at = DateTimeField()
    artist = ForeignKeyField(Artist, backref='links', null=True)
    album = ForeignKeyField(Album, backref='links', null=True)
    track = ForeignKeyField(Track, backref='links', null=True)
    updated_at = DateTimeField(null=True)  # deprecated field
    times_sent = IntegerField(default=1)  # deprecated field
    user = ForeignKeyField(User, backref='links')  # deprecated field
    chat = ForeignKeyField(Chat, backref='links')  # deprecated field
    last_update_user = ForeignKeyField(User, backref='updated_links', null=True)  # deprecated field

    def get_emoji(self):
        if self.link_type == LinkType.ARTIST.value:
            return Artist.get_emoji()
        elif self.link_type == LinkType.ALBUM.value:
            return Album.get_emoji()
        elif self.link_type == LinkType.TRACK.value:
            return Track.get_emoji()

    def apply_update(self, user):
        """
        DEPRECATED
        Set the update fields to the current values
        """
        self.updated_at = datetime.datetime.now()
        self.last_update_user = user
        self.times_sent += 1

    @staticmethod
    def get_genres(link: OrderedDict):
        link_type = link.get('link_type')
        artist = link.get('artist')
        album = link.get('album')
        track = link.get('track')
        genres = None
        if link_type == LinkType.ARTIST.value:
            genres = artist.get('genres')
        elif link_type == LinkType.ALBUM.value:
            genres = album.get('artists')[0].get('genres') if album.get('artists')[0] else None
        elif link_type == LinkType.TRACK.value:
            genres = track.get('artists')[0].get('genres') if track.get('artists')[0] else None
        if not genres:
            return []
        return [genre.get('name') for genre in genres]

    @staticmethod
    def get_name(link: OrderedDict):
        link_type = link.get('link_type')
        artist = link.get('artist')
        album = link.get('album')
        track = link.get('track')
        if link_type == LinkType.ARTIST.value:
            return artist.get('name')
        elif link_type == LinkType.ALBUM.value:
            return "{} - {}".format(
                album.get('artists')[0].get('name') if album.get('artists') else '',
                album.get('name')
            )
        elif link_type == LinkType.TRACK.value:
            return "{} by {}".format(
                track.get('name'),
                track.get('artists')[0].get('name') if track.get('artists') else '',
            )

    def __str__(self):
        if self.link_type == LinkType.ARTIST.value:
            return self.artist.name
        elif self.link_type == LinkType.ALBUM.value:
            return "{} - {}".format(
                self.album.get_first_artist().name if self.album.get_first_artist() else '',
                self.album.name
            )
        elif self.link_type == LinkType.TRACK.value:
            return "{} by {}".format(
                self.track.name,
                self.track.artists.first().name if self.track.get_first_artist() else '',
            )


class LastFMUsername(BaseModel):
    user = ForeignKeyField(User, backref='lastfm_username', primary_key=True)
    username = CharField(unique=True)


class ChatLink(BaseModel):
    """
    TODO: Work in Progress
    Represents a link sent in a chat
    """
    id = AutoField()
    sent_at = DateTimeField()
    chat = ForeignKeyField(Chat, backref='links', on_delete='CASCADE')
    link = ForeignKeyField(Link, backref='chats', on_delete='CASCADE')
    sent_by = ForeignKeyField(User, backref='links', on_delete='CASCADE')

    def __str__(self):
        if self.link.link_type == LinkType.ARTIST.value:
            return self.link.artist.name
        elif self.link.link_type == LinkType.ALBUM.value:
            return "{} - {}".format(
                self.link.album.get_first_artist().name if self.link.album.get_first_artist() else '',
                self.link.album.name
            )
        elif self.link.link_type == LinkType.TRACK.value:
            return "{} by {}".format(
                self.link.track.name,
                self.link.track.artists.first().name if self.link.track.get_first_artist() else '',
            )


class SavedLink(BaseModel):
    id = AutoField()
    user = ForeignKeyField(User, backref='saved_links', on_delete='CASCADE')
    link = ForeignKeyField(Link, backref='saved_links', on_delete='CASCADE')
    saved_at = DateTimeField()
    deleted_at = DateTimeField(null=True)

    class Meta:
        indexes = (
            (('user', 'link'), True),
        )


class FollowedArtist(BaseModel):
    id = AutoField()
    user = ForeignKeyField(User, backref='followed_artists', on_delete='CASCADE')
    artist = ForeignKeyField(Artist, backref='followed_by', on_delete='CASCADE')
    followed_at = DateTimeField()
    last_lookup = DateTimeField(null=True)

    def __str__(self):
        return f'{self.user.username or self.user.first_name} ({self.user.id}) - {self.artist.name} ({self.artist.id})'


class CreateOrUpdateMixin:

    @staticmethod
    def save_link(url: str, user_id: str, chat_id: str) -> OrderedDict:
        telegram_api_client = TelegramAPIClient()
        save_link_response = telegram_api_client.create_sent_link(url, user_id, chat_id)
        return save_link_response

    @staticmethod
    def save_chat(chat):
        telegram_api_client = TelegramAPIClient()
        create_chat_response = telegram_api_client.create_chat(chat)
        return create_chat_response

    @staticmethod
    def save_user(user):
        telegram_api_client = TelegramAPIClient()
        create_user_response = telegram_api_client.create_user(user)
        return create_user_response

    @staticmethod
    def save_artist(artist_id: str):
        spotify_api_client = SpotifyAPIClient()
        create_artist_response = spotify_api_client.create_artist(artist_id)
        return create_artist_response

    @staticmethod
    def save_album(album_id: str):
        spotify_api_client = SpotifyAPIClient()
        create_album_response = spotify_api_client.create_album(album_id)
        return create_album_response

    @staticmethod
    def save_track(track_id: str):
        spotify_api_client = SpotifyAPIClient()
        create_track_response = spotify_api_client.create_track(track_id)
        return create_track_response
