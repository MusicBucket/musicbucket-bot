from app.db import db
from app.models import Link, Artist, Genre, User, Chat, Album, Track, AlbumArtist, AlbumGenre, ArtistGenre, TrackArtist
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler
from dotenv import load_dotenv
from os import getenv as getenv
import logging

# Load environment variables from .env file
from app.music_bucket_bot import MusicBucketBotFactory

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)


def _setup_database():
    db.connect()
    db.create_tables([User, Chat, Link, Artist, Album, Track, Genre, AlbumArtist, AlbumGenre, ArtistGenre, TrackArtist])


def main():
    # Init app
    _setup_database()

    # Bot start
    updater = Updater(getenv('TOKEN'))

    # Register handlers
    dispatcher = updater.dispatcher

    music_bucket_bot_factory = MusicBucketBotFactory()

    # Register commands
    dispatcher.add_handler(CommandHandler('music',
                                          music_bucket_bot_factory.handle_music_command))
    dispatcher.add_handler(CommandHandler('music_from_beginning',
                                          music_bucket_bot_factory.handle_music_from_beginning_command, pass_args=True))
    dispatcher.add_handler(CommandHandler('recommendations', music_bucket_bot_factory.handle_recommendations))
    dispatcher.add_handler(CommandHandler('stats',
                                          music_bucket_bot_factory.handle_stats_command))
    dispatcher.add_handler(InlineQueryHandler(music_bucket_bot_factory.handle_search_command))

    # Non command handlers
    dispatcher.add_handler(MessageHandler(
        Filters.text, music_bucket_bot_factory.handle_save_link))

    # Start the bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
