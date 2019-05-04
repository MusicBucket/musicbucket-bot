import datetime
import logging

from peewee import SqliteDatabase, Model, CharField, IntegerField, DateTimeField, ForeignKeyField, CompositeKey

from app.music.music import StreamingServiceType

logger = logging.getLogger(__name__)

db = SqliteDatabase('db.sqlite', pragmas={'foreign_keys': 1})


class User(Model):
    id = CharField(primary_key=True)
    username = CharField(null=True)
    first_name = CharField(null=True)

    class Meta:
        database = db

    def __str__(self):
        return 'User {}'.format(self.id)


class Chat(Model):
    id = CharField(primary_key=True)
    name = CharField()

    class Meta:
        database = db

    def __str__(self):
        return 'Chat {}-{}'.format(self.id, self.name)


class Link(Model):
    url = CharField()
    link_type = CharField()
    streaming_service_type = CharField(default=StreamingServiceType.SPOTIFY)
    created_at = DateTimeField()
    updated_at = DateTimeField(null=True)
    times_sent = IntegerField(default=1)
    artist_name = CharField(null=True)
    album_name = CharField(null=True)
    track_name = CharField(null=True)
    genre = CharField(null=True)
    user = ForeignKeyField(User, backref='links')
    chat = ForeignKeyField(Chat, backref='links')
    last_update_user = ForeignKeyField(User, backref='updated_links', null=True)

    class Meta:
        database = db
        primary_key = CompositeKey('url', 'chat')

    def apply_update(self, user):
        """
        Set the update fields to the current values
        """
        self.updated_at = datetime.datetime.now()
        self.last_update_user = user
        self.times_sent += 1

    def __str__(self):
        return 'Link: {}'.format(self.url)
