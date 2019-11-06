import logging
import datetime

from peewee import Model, CharField, DateTimeField, IntegerField, ForeignKeyField, CompositeKey, ManyToManyField, \
    BooleanField, AutoField

from bot.db import db
from bot.music.music import StreamingServiceType, LinkType

log = logging.getLogger(__name__)


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
    spotify_url = CharField(null=True)
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
    spotify_url = CharField(null=True)
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
    id = AutoField()
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


class CreateOrUpdateMixin:
    """
    TODO: Replace get_or_create for insert_or_replace or equivalent to create_or_update
    """

    def save_link(self, link):
        """Update the link if it exists for a chat, create if it doesn't exist"""
        updated = False
        existent_link = Link.get_or_none((Link.url == link.url) & (Link.chat == link.chat))
        if existent_link:
            update_user = link.user
            link = existent_link
            link.apply_update(update_user)
            link.save()
            updated = True
            self.log_db_operation(self.DBOperation.UPDATE, link)
        else:
            link.created_at = datetime.datetime.now()
            link.save(force_insert=True)
            self.log_db_operation(self.DBOperation.CREATE, link)

        return link, updated

    def save_chat(self, update):
        chat, was_created = Chat.get_or_create(
            id=update.message.chat_id,
            defaults={
                'name': update.message.chat.title or update.message.chat.username or update.message.chat.first_name
            })
        if was_created:
            self.log_db_operation(self.DBOperation.CREATE, chat)
        return chat

    def save_user(self, update):
        user, was_created = User.get_or_create(
            id=update.message.from_user.id,
            defaults={
                'username': update.message.from_user.username,
                'first_name': update.message.from_user.first_name})
        if was_created:
            self.log_db_operation(self.DBOperation.CREATE, user)
        return user

    def save_genres(self, genres):
        saved_genres = []
        for genre in genres:
            saved_genre, was_created = Genre.get_or_create(name=genre)
            saved_genres.append(saved_genre)
            if was_created:
                self.log_db_operation(self.DBOperation.CREATE, saved_genre)
        return saved_genres

    def save_artist(self, spotify_artist):
        image = spotify_artist['images'][0]['url'] if spotify_artist['images'] else ''

        saved_artist, was_created = Artist.get_or_create(
            id=spotify_artist['id'],
            defaults={
                'name': spotify_artist['name'],
                'image': image,
                'popularity': spotify_artist['popularity'],
                'href': spotify_artist['href'],
                'spotify_url': spotify_artist['external_urls']['spotify'],
                'uri': spotify_artist['uri']})

        # Save or retrieve the genres
        if was_created:
            saved_genres = self.save_genres(spotify_artist['genres'])
            saved_artist.genres = saved_genres
            saved_artist.save()
            self.log_db_operation(self.DBOperation.CREATE, saved_artist)
        return saved_artist

    def save_album(self, spotify_album):
        image = spotify_album['images'][0]['url'] if spotify_album['images'] else ''

        saved_album, was_created = Album.get_or_create(
            id=spotify_album['id'],
            defaults={
                'name': spotify_album['name'],
                'label': spotify_album['label'],
                'image': image,
                'popularity': spotify_album['popularity'],
                'href': spotify_album['href'],
                'spotify_url': spotify_album['external_urls']['spotify'],
                'uri': spotify_album['uri']})

        if was_created:
            saved_artists = []
            for album_artist in spotify_album['artists']:
                artist_id = album_artist['id']
                artist = self.spotify_client.client.artist(artist_id)
                saved_artist = self.save_artist(artist)
                saved_artists.append(saved_artist)
            # Set the artists to the album
            saved_album.artists = saved_artist
            saved_album.save()

            saved_genres = self.save_genres(spotify_album['genres'])
            saved_album.genres = saved_genres
            saved_album.save()
            self.log_db_operation(self.DBOperation.CREATE, saved_album)
        return saved_album

    def save_track(self, spotify_track):
        album_id = spotify_track['album']['id']
        album = self.spotify_client.client.album(album_id)
        saved_album = self.save_album(album)

        # Save the track (with the album)
        saved_track, was_created = Track.get_or_create(
            id=spotify_track['id'],
            defaults={
                'name': spotify_track['name'],
                'track_number ': spotify_track['track_number'],
                'duration_ms ': spotify_track['duration_ms'],
                'explicit': spotify_track['explicit'],
                'popularity ': spotify_track['popularity'],
                'href': spotify_track['href'],
                'spotify_url': spotify_track['external_urls']['spotify'],
                'preview_url ': spotify_track['preview_url'],
                'uri': spotify_track['uri'],
                'album': saved_album})

        if was_created:
            saved_artists = []
            for track_artist in spotify_track['artists']:
                artist_id = track_artist['id']
                artist = self.spotify_client.client.artist(artist_id)
                saved_artist = self.save_artist(artist)
                saved_artists.append(saved_artist)
            # Set the artists to the album
            saved_track.artists = saved_artists
            saved_track.save()
            self.log_db_operation(self.DBOperation.CREATE, saved_track)
        return saved_track
