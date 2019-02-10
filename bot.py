from responser import Responser
from db import DB, User, UserChatLink
import spotify
import datetime
import logging
from os import getenv as getenv
from dotenv import load_dotenv
from telegram import ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)
load_dotenv()

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


def find_spotify_link_in_text(bot, update):
    """Fins the Spotify link in the text and saves it to the database. It also saves the user if it doesn't exist @ database"""
    print(update.message)
    parser = spotify.Parser()
    spotify_link = update.message.text
    spotify_link_type = parser.get_link_type(spotify_link)

    # If the spotify link is correct
    if spotify_link_type is not None:
        user_id = update.message.from_user.id

        # If we didn't store the user yet, we do it now
        if db.check_if_user_exists(user_id) is False:
            user = User(id=user_id, username=update.message.from_user.username,
                        firstname=update.message.from_user.first_name)
            db.save_object(user)
        else:
            print('User already exists')

        # We can't let the user save the same link at the same chat if he already save it within the last week
        if db.check_if_same_link_same_chat_last_week(spotify_link, update.message.chat_id) is False:
            user_chat_link = UserChatLink(chat_id=update.message.chat_id, created_at=datetime.datetime.now(
            ), user_id=user_id, link_type=spotify_link_type.value, link=spotify_link)
            db.save_object(user_chat_link)
        else:
            print('This user already sent this link in this chat the last week')


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
        Filters.text, find_spotify_link_in_text))

    # Log
    dispatcher.add_error_handler(error)

    # Start the bot
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
