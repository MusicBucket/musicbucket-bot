import sentry_sdk

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, CallbackQueryHandler
from dotenv import load_dotenv
from os import getenv
import logging

from bot.buttons import SaveLinkButton, DeleteSavedLinkButton, UnfollowArtistButton
from bot.db import db
from bot.messages import MessageProcessor
from bot.models import Link, Artist, Genre, User, Chat, Album, Track, AlbumArtist, AlbumGenre, ArtistGenre, \
    TrackArtist, LastFMUsername, SavedLink, ChatLink, FollowedArtist
from bot.commands import CommandFactory, MusicCommand, MusicFromBeginningCommand, MyMusicCommand, NowPlayingCommand, \
    LastFMSetCommand, SavedLinksCommand, DeleteSavedLinksCommand, StatsCommand, StartCommand, HelpCommand, \
    FollowArtistCommand, FollowedArtistsCommand, UnfollowArtistsCommand, CheckArtistsNewMusicReleasesCommand
from bot.search import SearchInline

load_dotenv()

if getenv('DEBUG', False):
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
else:
    logging.basicConfig(
        filename='musicbucket-bot.log',
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

log = logging.getLogger(__name__)


def _setup_database():
    db.connect()
    db.create_tables(
        [User, Chat, Link, ChatLink, Artist, Album, Track, Genre, AlbumArtist, AlbumGenre, ArtistGenre, TrackArtist,
         LastFMUsername, SavedLink, FollowedArtist])


def _setup_sentry():
    public_key = getenv('SENTRY_PUBLIC_KEY', None)
    project_id = getenv('SENTRY_PROJECT_ID', None)

    if public_key and project_id:
        sentry_sdk.init(f"https://{public_key}@sentry.io/{project_id}")


def main():
    # Init app
    _setup_database()
    _setup_sentry()

    # Bot start
    updater = Updater(getenv('TOKEN'), use_context=True)

    # Register handlers
    dispatcher = updater.dispatcher

    # Register commands
    dispatcher.add_handler(
        CommandHandler(StartCommand.COMMAND, CommandFactory.run_start_command)
    )
    dispatcher.add_handler(
        CommandHandler(HelpCommand.COMMAND, CommandFactory.run_help_command)
    )
    dispatcher.add_handler(
        CommandHandler(MusicCommand.COMMAND, CommandFactory.run_music_command, pass_args=True)
    )
    dispatcher.add_handler(
        CommandHandler(
            MusicFromBeginningCommand.COMMAND, CommandFactory.run_music_from_beginning_command, pass_args=True
        )
    )
    dispatcher.add_handler(
        CommandHandler(MyMusicCommand.COMMAND, CommandFactory.run_my_music_command)
    )
    dispatcher.add_handler(
        CommandHandler(NowPlayingCommand.COMMAND, CommandFactory.run_now_playing_command)
    )
    dispatcher.add_handler(
        CommandHandler(LastFMSetCommand.COMMAND, CommandFactory.run_lastfmset_command, pass_args=True)
    )
    dispatcher.add_handler(
        CommandHandler(SavedLinksCommand.COMMAND, CommandFactory.run_saved_links_command)
    )
    dispatcher.add_handler(
        CommandHandler(DeleteSavedLinksCommand.COMMAND, CommandFactory.run_delete_saved_links_command)
    )
    dispatcher.add_handler(
        CommandHandler(FollowedArtistsCommand.COMMAND, CommandFactory.run_followed_artists_command)
    )
    dispatcher.add_handler(
        CommandHandler(FollowArtistCommand.COMMAND, CommandFactory.run_follow_artist_command, pass_args=True)
    )
    dispatcher.add_handler(
        CommandHandler(UnfollowArtistsCommand.COMMAND, CommandFactory.run_unfollow_artists_command)
    )
    dispatcher.add_handler(
        CommandHandler(
            CheckArtistsNewMusicReleasesCommand.COMMAND, CommandFactory.run_check_artist_new_music_releases_command
        )
    )
    dispatcher.add_handler(
        CommandHandler(StatsCommand.COMMAND, CommandFactory.run_stats_command)
    )
    dispatcher.add_handler(
        InlineQueryHandler(SearchInline)
    )
    dispatcher.add_handler(
        CallbackQueryHandler(SaveLinkButton.handle, pattern=f'{SaveLinkButton.CALLBACK_NAME}')
    )
    dispatcher.add_handler(
        CallbackQueryHandler(DeleteSavedLinkButton.handle, pattern=f'{DeleteSavedLinkButton.CALLBACK_NAME}')
    )
    dispatcher.add_handler(
        CallbackQueryHandler(UnfollowArtistButton.handle, pattern=f'{UnfollowArtistButton.CALLBACK_NAME}')
    )

    # Non command handlers
    dispatcher.add_handler(MessageHandler(
        Filters.text, MessageProcessor.process_message))

    # Start the bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
