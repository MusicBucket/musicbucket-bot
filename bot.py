from collections import defaultdict

from app.music import spotify, deezer
from app.music.music import StreamingServiceType, LinkType
from app.db.db import db, User, Chat, Link
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
db.connect()
db.create_tables([User, Chat, Link])


def error(bot, update, error):
    """Log Errors"""
    logger.warning('Update "%s" caused error "%s"', update, error)


def music(bot, update):
    """
    Command /music
    Gets the links sent by all the users of the chat in the last week
    and group them by user>links
    """
    responser = Responser()
    days = 7
    now = datetime.datetime.now()
    last_week_timedelta = datetime.timedelta(days=days)

    last_week_links = defaultdict(list)

    qry_result = Link.select() \
        .join(Chat) \
        .where(Chat.id == update.message.chat_id) \
        .where(
        (Link.created_at >= now - last_week_timedelta) | (Link.updated_at >= now - last_week_timedelta)) \
        .order_by(Link.updated_at.asc(), Link.created_at.asc())

    for link in qry_result:
        last_week_links[link.user].append(link)
    last_week_links = dict(last_week_links)

    response = responser.links_by_user(
        last_week_links, ResponseType.LAST_WEEK)

    update.message.reply_text(response, disable_web_page_preview=True,
                              parse_mode=ParseMode.HTML)
    logger.info("'/music' command was called by user {} in chat {}".format(
        update.message.from_user.id, update.message.chat_id))


def music_from_beginning(bot, update):
    """
    Command /music_from_beginning
    Gets the links sent by all the users of the chat from the beginning
    """
    responser = Responser()

    all_time_links = defaultdict(list)

    qry_result = Link.select() \
        .join(Chat) \
        .where(Chat.id == update.message.chat_id) \
        .order_by(Link.updated_at.asc(), Link.created_at.asc())

    for link in qry_result:
        all_time_links[link.user].append(link)
    all_time_links = dict(all_time_links)

    response = responser.links_by_user(
        all_time_links, ResponseType.FROM_THE_BEGINNING)
    update.message.reply_text(response, disable_web_page_preview=True,
                              parse_mode=ParseMode.HTML)
    logger.info("'/music_from_beginning' command was called by user {} in chat {}".format(
        update.message.from_user.id, update.message.chat_id))


def find_streaming_link_in_text(bot, update):
    """
    Finds the streaming url, identifies the streaming service in the text and
    saves it to the database. 
    It also saves the user and the chat if they don't exist @ database
    """
    spotify_parser = spotify.SpotifyParser()
    deezer_parser = deezer.DeezerParser()

    link_type = None
    streaming_service_type = None
    url = utils.extract_url_from_message(update.message.text)
    cleaned_url = ''

    # Check if is a Spotify/Deezer url
    if spotify_parser.is_spotify_url(url):
        streaming_service_type = StreamingServiceType.SPOTIFY
        link_type = spotify_parser.get_link_type(url)
        cleaned_url = spotify_parser.clean_url(url)
    elif deezer_parser.is_deezer_url(url):
        streaming_service_type = StreamingServiceType.DEEZER
        link_type = deezer_parser.get_link_type(url)
        cleaned_url = deezer_parser.clean_url(url)

    # If link was resolved correctly, save or update it
    if link_type is not None and link_type != 0:
        _save_or_update_user_chat_link(update, cleaned_url, link_type, streaming_service_type, spotify_parser,
                                       deezer_parser)


def _save_or_update_user_chat_link(update, cleaned_url, link_type, streaming_service_type, spotify_parser,
                                   deezer_parser):
    link_updated = False

    # Create or get the user that sent the link
    user, user_created = User.get_or_create(
        id=update.message.from_user.id,
        username=update.message.from_user.username,
        first_name=update.message.from_user.first_name)
    if user_created:
        logger.info("User '{}' with id '{}' was created".format(
            user.username if user.username else user.first_name,
            user.id))

    # Create or get the chat where the link was sent
    chat, chat_created = Chat.get_or_create(
        id=update.message.chat_id,
        name=update.message.chat.title or update.message.chat.username or update.message.chat.first_name)
    if chat_created:
        logger.info("Chat '{}' with id '{}' was created".format(chat.name, chat.id))

    # Update the link if it exists for a chat, create if it doesn't exist

    link = Link.get_or_none((Link.url == cleaned_url) & (Link.chat == chat))
    if link is not None:
        # If link already exists, set updated_at and last_update_user to current
        link.updated_at = datetime.datetime.now()
        link.last_update_user = user
        link.save()
        link_updated = True
    else:
        # If the link doesn't exists, get link info based on the link type and save it
        link_info = None
        if streaming_service_type == StreamingServiceType.SPOTIFY:
            link_info = spotify_parser.get_link_info(cleaned_url, link_type)
        elif streaming_service_type == StreamingServiceType.DEEZER:
            link_info = deezer_parser.get_link_info(cleaned_url, link_type)
        if link_info is None:
            logger.error("Error ocurred getting link info")

        link = Link.create(
            url=cleaned_url,
            link_type=link_type.value,
            streaming_service_type=streaming_service_type.value,
            created_at=datetime.datetime.now(),
            artist_name=link_info.artist,
            album_name=link_info.album,
            track_name=link_info.track,
            genre=link_info.genre,
            user=user,
            chat=chat)

    # Log link operation
    link_operation = 'Saved' if not link_updated else 'Updated'

    if link_type == LinkType.ARTIST:
        logger.info("'{}' link '{}' of type '{}' in chat '{}'".format(
            link_operation, link.artist_name, link.link_type, link.chat.name))
    elif link_type == LinkType.ALBUM:
        logger.info("'{}' link '{}' of type '{}' in chat '{}'".format(
            link_operation, link.album_name, link.link_type, link.chat.name))
    elif link_type == LinkType.TRACK:
        logger.info("'{}' link '{}' of type '{}' in chat '{}'".format(
            link_operation, link.track_name, link.link_type, link.chat.name))


def main():
    """Bot start"""
    updater = Updater(getenv('TOKEN'))

    # Register handlers
    dispatcher = updater.dispatcher

    # Register commands
    # dispatcher.add_handler(CommandHandler('help', help))
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
