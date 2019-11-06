import logging
from os import getenv

from dotenv import load_dotenv

from peewee import PostgresqlDatabase

log = logging.getLogger(__name__)

load_dotenv()

db = PostgresqlDatabase(getenv('DB_NAME'),
                        user=getenv('DB_USER'),
                        password=getenv('DB_PASSWORD'),
                        host=getenv('DB_HOST'),
                        port=getenv('DB_PORT'))
