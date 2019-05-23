import logging

from peewee import SqliteDatabase

logger = logging.getLogger(__name__)

db = SqliteDatabase('db.sqlite', pragmas={'foreign_keys': 1})
