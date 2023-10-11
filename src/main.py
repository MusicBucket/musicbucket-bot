import sentry_sdk

from telegram.ext import CommandHandler, MessageHandler, \
    InlineQueryHandler, CallbackQueryHandler, ApplicationBuilder, filters
from dotenv import load_dotenv
from os import getenv
import logging

from bot.buttons import SaveLinkButton, DeleteSavedLinkButton, \
    UnfollowArtistButton
from bot.messages import MessageProcessor
from bot.commands import CommandFactory, MusicCommand, \
    MusicFromBeginningCommand, MyMusicCommand, NowPlayingCommand, \
    LastFMSetCommand, SavedLinksCommand, DeleteSavedLinksCommand, StatsCommand, \
    StartCommand, HelpCommand, \
    FollowArtistCommand, FollowedArtistsCommand, UnfollowArtistsCommand, \
    CheckArtistsNewMusicReleasesCommand, \
    TopAlbumsCommand, TopArtistsCommand, TopTracksCommand, CollageCommand
from bot.search import SearchInline

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

log = logging.getLogger(__name__)


def _setup_sentry():
    public_key = getenv('SENTRY_PUBLIC_KEY', None)
    project_id = getenv('SENTRY_PROJECT_ID', None)

    if public_key and project_id:
        sentry_sdk.init(f"https://{public_key}@sentry.io/{project_id}")


def main():
    # Init app
    _setup_sentry()

    # Bot start
    application = ApplicationBuilder().token(
        getenv("TOKEN")
    ).concurrent_updates(True).build()

    # Register commands
    application.add_handler(
        CommandHandler(
            StartCommand.COMMAND,
            CommandFactory.run_start_command,
            block=False
        )
    )
    application.add_handler(
        CommandHandler(
            HelpCommand.COMMAND,
            CommandFactory.run_help_command,
            block=False
        )
    )
    application.add_handler(
        CommandHandler(
            MusicCommand.COMMAND,
            CommandFactory.run_music_command,
            block=False
        )
    )
    application.add_handler(
        CommandHandler(
            MusicFromBeginningCommand.COMMAND,
            CommandFactory.run_music_from_beginning_command,
            block=False
        )
    )
    application.add_handler(
        CommandHandler(
            MyMusicCommand.COMMAND,
            CommandFactory.run_my_music_command,
            block=False
        )
    )
    application.add_handler(
        CommandHandler(
            NowPlayingCommand.COMMAND,
            CommandFactory.run_now_playing_command,
            block=False
        )
    )
    application.add_handler(
        CommandHandler(
            CollageCommand.COMMAND,
            CommandFactory.run_collage_command,
            block=False
        )
    )
    application.add_handler(
        CommandHandler(
            TopAlbumsCommand.COMMAND,
            CommandFactory.run_top_albums_command,
            block=False
        )
    )
    application.add_handler(
        CommandHandler(
            TopArtistsCommand.COMMAND,
            CommandFactory.run_top_artists_command,
            block=False
        )
    )
    application.add_handler(
        CommandHandler(
            TopTracksCommand.COMMAND,
            CommandFactory.run_top_tracks_command,
            block=False
        )
    )
    application.add_handler(
        CommandHandler(
            LastFMSetCommand.COMMAND,
            CommandFactory.run_lastfmset_command,
            block=False
        )
    )
    application.add_handler(
        CommandHandler(
            SavedLinksCommand.COMMAND,
            CommandFactory.run_saved_links_command,
            block=False
        )
    )
    application.add_handler(
        CommandHandler(
            DeleteSavedLinksCommand.COMMAND,
            CommandFactory.run_delete_saved_links_command,
            block=False
        )
    )
    application.add_handler(
        CommandHandler(
            FollowedArtistsCommand.COMMAND,
            CommandFactory.run_followed_artists_command,
            block=False
        )
    )
    application.add_handler(
        CommandHandler(
            FollowArtistCommand.COMMAND,
            CommandFactory.run_follow_artist_command,
            block=False
        )
    )
    application.add_handler(
        CommandHandler(
            UnfollowArtistsCommand.COMMAND,
            CommandFactory.run_unfollow_artists_command,
            block=False
        )
    )
    application.add_handler(
        CommandHandler(
            CheckArtistsNewMusicReleasesCommand.COMMAND,
            CommandFactory.run_check_artist_new_music_releases_command,
            block=False
        )
    )
    application.add_handler(
        CommandHandler(
            StatsCommand.COMMAND,
            CommandFactory.run_stats_command,
            block=False
        )
    )
    application.add_handler(
        InlineQueryHandler(
            SearchInline,
            block=False
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            SaveLinkButton.handle,
            pattern=f'{SaveLinkButton.CALLBACK_NAME}',
            block=False
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            DeleteSavedLinkButton.handle,
            pattern=f'{DeleteSavedLinkButton.CALLBACK_NAME}',
            block=False
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            UnfollowArtistButton.handle,
            pattern=f'{UnfollowArtistButton.CALLBACK_NAME}',
            block=False
        )
    )

    # Non command handlers
    application.add_handler(
        MessageHandler(
            filters.TEXT,
            MessageProcessor.process_message,
            block=False
        )
    )

    # Start the bot
    application.run_polling()


if __name__ == '__main__':
    main()
