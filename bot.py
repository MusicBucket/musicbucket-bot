from app.music import spotify, deezer
from app.music.music import LinkType, StreamingServiceType
from app.db.db import DB, User, UserChatLink
from app.responser import Responser, ResponseType
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
from dotenv import load_dotenv
from os import getenv as getenv
import app.util.utils as utils
import logging
import datetime

load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)


# Setup Database
db = DB()


def start(bot, update):
    """Command /start"""
    msg = ''
    update.message.reply_text(msg)


def help(bot, update):
    """Command /help"""
    msg = ''
    update.message.reply_text(msg)


def error(bot, update, error):
    """Log Errors"""
    logger.warning('Update "%s" caused error "%s"', update, error)


def music(bot, update):
    """
    Command /music
    Gets the links sent by all the users of the chat in the last week
    """
    responser = Responser()

    last_week_links = db.get_links(update.message.chat_id, 7)
    response = responser.links_by_user(
        last_week_links, ResponseType.LAST_WEEK)
    update.message.reply_text(response, disable_web_page_preview=True,
                              parse_mode=ParseMode.HTML)


def music_from_beginning(bot, update):
    """
    Command /music_from_beginning
    Gets the links sent by all the users of the chat from the beginning
    """
    responser = Responser()

    all_time_links = db.get_links(update.message.chat_id)
    response = responser.links_by_user(
        all_time_links, ResponseType.FROM_THE_BEGINNING)
    update.message.reply_text(response, disable_web_page_preview=True,
                              parse_mode=ParseMode.HTML)


def find_streaming_link_in_text(bot, update):
    """Finds the streaming link, identifies the streaming service in the text and saves it to the database. It also saves the user if it doesn't exist @ database"""
    spotify_parser = spotify.SpotifyParser()
    deezer_parser = deezer.DeezerParser()

    link = ''
    link_type = None
    streaming_service_type = None
    url = utils.extract_url_from_message(update.message.text)

    # Check if is a Spotify/Deezer link
    if spotify_parser.is_spotify_url(url):
        streaming_service_type = StreamingServiceType.SPOTIFY.value
        link_type = spotify_parser.get_link_type(url)
        link = spotify_parser.clean_url(url)
    elif deezer_parser.is_deezer_url(url):
        streaming_service_type = StreamingServiceType.DEEZER.value
        link_type = deezer_parser.get_link_type(url)
        link = deezer_parser.clean_url(url)

    # If link was resolved correctly
    if link_type is not None and link_type != 0:
        user_id = update.message.from_user.id

        # If we didn't store the user yet, we do it now
        if db.check_if_user_exists(user_id) is False:
            user = User(id=user_id, username=update.message.from_user.username,
                        firstname=update.message.from_user.first_name)
            db.save_object(user)
        else:
            logger.info('User already exists')

        # We can't let the user save the same link at the same chat if he already save it within the last week
        if db.check_if_same_link_same_chat(link, update.message.chat_id, 7) is False:
            # Get link info based on the link type before saving it
            try:
                link_info = None
                if streaming_service_type == StreamingServiceType.SPOTIFY.value:
                    link_info = spotify_parser.get_link_info(link, link_type)
                elif streaming_service_type == StreamingServiceType.DEEZER.value:
                    link_info = deezer_parser.get_link_info(link, link_type)

                user_chat_link = UserChatLink(chat_id=update.message.chat_id,
                                              chat_name=update.message.chat.title or update.message.chat.username or update.message.chat.first_name,
                                              artist_name=link_info.artist,
                                              album_name=link_info.album,
                                              track_name=link_info.track,
                                              genre=link_info.genre,
                                              created_at=datetime.datetime.now(),
                                              user_id=user_id,
                                              link_type=link_type.value,
                                              link=link)
                db.save_object(user_chat_link)
                logger.info('Saving new link')
            except:
                logger.error('Error ocurred getting or saving the link')
        else:
            logger.warn(
                'This user already sent this link in this chat the last week')


def main():
    """Bot start"""
    updater = Updater(getenv('TOKEN'))

    # Register handlers
    dispatcher = updater.dispatcher

    # Register commands
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('help', help))
    dispatcher.add_handler(CommandHandler('music', music))
    dispatcher.add_handler(CommandHandler(
        'music_from_beginning', music_from_beginning))

    # Non command handlers
    dispatcher.add_handler(MessageHandler(
        Filters.text, find_streaming_link_in_text))

    # Log
    dispatcher.add_error_handler(error)

    # Start the bot
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
