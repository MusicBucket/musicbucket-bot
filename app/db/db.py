import logging

from peewee import SqliteDatabase, Model, CharField, DateTimeField, ForeignKeyField, CompositeKey

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
        return 'Chat {}'.format(self.id)


class Link(Model):
    url = CharField()
    link_type = CharField()
    streaming_service_type = CharField()
    created_at = DateTimeField()
    updated_at = DateTimeField(null=True)
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

    def __str__(self):
        return 'Link: {}'.format(self.url)
