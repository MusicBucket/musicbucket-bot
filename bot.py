from app.music import spotify, deezer
from app.db.db import DB, User, UserChatLink
from app.responser import Responser
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
    Gets the Spotify links sent by all the users of the chat in the last week
    """
    responser = Responser()

    last_week_links = db.get_last_week_links(update.message.chat_id)
    response = responser.last_week_links_by_user(last_week_links)
    update.message.reply_text(response, disable_web_page_preview=True,
                              parse_mode=ParseMode.HTML)


def find_streaming_link_in_text(bot, update):
    """Fins the streaming link, identifies the streaming service in the text and saves it to the database. It also saves the user if it doesn't exist @ database"""
    spotify_parser = spotify.SpotifyParser()
    deezer_parser = deezer.DeezerParser()

    link = ''
    link_type = 0
    url = utils.extract_url_from_message(update.message.text)

    # Check if is a Spotify/Deezer link
    if spotify_parser.is_spotify_url(url):
        link_type = spotify_parser.get_link_type(url)
        link = spotify_parser.clean_url(url)
    elif deezer_parser.is_deezer_url(url):
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
        if db.check_if_same_link_same_chat_last_week(link, update.message.chat_id) is False:
            user_chat_link = UserChatLink(chat_id=update.message.chat_id, chat_name=update.message.chat.title or update.message.chat.username or update.message.chat.first_name, created_at=datetime.datetime.now(
            ), user_id=user_id, link_type=link_type.value, link=link)
            db.save_object(user_chat_link)
            logger.info('Saving new link')
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
