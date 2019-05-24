import datetime
import logging

from peewee import Model, CharField, DateTimeField, IntegerField, ForeignKeyField, CompositeKey, ManyToManyField, \
    BooleanField

from app.db import db
from app.music.music import StreamingServiceType, LinkType

logger = logging.getLogger(__name__)


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    id = CharField(primary_key=True)
    username = CharField(null=True)
    first_name = CharField(null=True)

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


class Artist(BaseModel):
    id = CharField(primary_key=True)
    name = CharField()
    image = CharField(null=True)
    popularity = IntegerField(null=True)
    href = CharField(null=True)
    spotify_url = CharField(null=True)
    uri = CharField()
    genres = ManyToManyField(Genre, backref='artists')


ArtistGenre = Artist.genres.get_through_model()


class Album(BaseModel):
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
    spotify_url = CharField(null=True)  # external_urls['spotify']
    album_type = CharField(null=True)
    uri = CharField()
    genres = ManyToManyField(Genre, backref='albums')
    artists = ManyToManyField(Artist, backref='albums')

    def get_first_artist(self):
        if self.artists:
            return self.artists.first()
        return None


AlbumGenre = Album.genres.get_through_model()
AlbumArtist = Album.artists.get_through_model()


class Track(BaseModel):
    id = CharField(primary_key=True)
    name = CharField()
    track_number = IntegerField(null=True)
    duration_ms = IntegerField(null=True)
    explicit = BooleanField(null=True)
    popularity = IntegerField(null=True)
    href = CharField(null=True)
    spotify_url = CharField(null=True)  # external_urls['spotify']
    preview_url = CharField(null=True)
    uri = CharField()
    album = ForeignKeyField(Album, backref='tracks')
    artists = ManyToManyField(Artist, backref='tracks')

    def get_first_artist(self):
        if self.artists:
            return self.artists.first()
        return None


TrackArtist = Track.artists.get_through_model()


class Link(BaseModel):
    url = CharField()
    link_type = CharField()
    streaming_service_type = CharField(default=StreamingServiceType.SPOTIFY.value)
    created_at = DateTimeField()
    updated_at = DateTimeField(null=True)
    times_sent = IntegerField(default=1)
    artist = ForeignKeyField(Artist, backref='links', null=True)
    album = ForeignKeyField(Album, backref='links', null=True)
    track = ForeignKeyField(Track, backref='links', null=True)
    user = ForeignKeyField(User, backref='links')
    chat = ForeignKeyField(Chat, backref='links')
    last_update_user = ForeignKeyField(User, backref='updated_links', null=True)

    class Meta:
        primary_key = CompositeKey('url', 'chat')

    @property
    def genres(self):
        genres = None
        if self.link_type == LinkType.ARTIST.value:
            genres = self.artist.genres
        elif self.link_type == LinkType.ALBUM.value:
            genres = self.album.get_first_artist().genres if self.album.get_first_artist() else None
        elif self.link_type == LinkType.TRACK.value:
            genres = self.track.get_first_artist().genres if self.track.get_first_artist() else None
        if not genres:
            return []
        return genres

    def apply_update(self, user):
        """
        Set the update fields to the current values
        """
        self.updated_at = datetime.datetime.now()
        self.last_update_user = user
        self.times_sent += 1

    def __str__(self):
        return 'Link: {}'.format(self.url)


class LastFMUsername(BaseModel):
    user = ForeignKeyField(User, backref='lastfm_username', primary_key=True)
    username = CharField(unique=True)
