from collections import defaultdict

from peewee import fn, SQL
from app.music.spotify import SpotifyParser
from app.music.music import LinkType, EntityType
from app.db.db import db, User, Chat, Link
from app.responser import Responser, ResponseType
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler
from telegram import ParseMode, InlineQueryResultArticle, InputTextMessageContent
from dotenv import load_dotenv
from os import getenv as getenv
import app.util.utils as utils
import logging
import datetime

# Load environment variables from .env file
load_dotenv()

# Enable logging
logging.basicConfig(
    # filename='music-bucket-bot.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)

# Setup Database
db.connect()
db.create_tables([User, Chat, Link])


def error(bot, update, error):
    """Log Errors"""
    logger.warning('Update "%s" caused error "%s"', update, error)


def search(bot, update):
    spotify_parser = SpotifyParser()
    results = []

    user_input = update.inline_query.query

    entity_type = user_input.split(' ', 1)[0]
    query = user_input.replace(entity_type, '').strip()
    valid_entity_type = False

    if entity_type == EntityType.ARTIST.value:
        valid_entity_type = True
    elif entity_type == EntityType.ALBUM.value:
        valid_entity_type = True
    elif entity_type == EntityType.TRACK.value:
        valid_entity_type = True

    if valid_entity_type and len(query) >= 3:
        logger.info(f"Searching for entity:'{entity_type}' with query:'{query}'")
        search_result = spotify_parser.search_link(query, entity_type)
        for result in search_result:
            thumb_url = ''
            description = ''

            # If the result are tracks, look for the album cover
            if entity_type == EntityType.TRACK.value:
                album = result['album']
                artists = result['artists']
                thumb_url = album['images'][0]['url']
                # [o.my_attr for o in my_list]
                description = '{} - {}'.format(', '.join(artist['name'] for artist in artists), album['name'])
            elif entity_type == EntityType.ALBUM.value:
                thumb_url = result['images'][0]['url'] if len(result['images']) > 0 else ''
                artists = result['artists']
                description = ', '.join(artist['name'] for artist in artists)
            elif entity_type == EntityType.ARTIST.value:
                thumb_url = result['images'][0]['url'] if len(result['images']) > 0 else ''
                description = ', '.join(result['genres'])

            results.append(InlineQueryResultArticle(
                id=result['id'],
                thumb_url=thumb_url,
                title=result['name'],
                description=description,
                input_message_content=InputTextMessageContent(result['external_urls']['spotify'])))

    update.inline_query.answer(results)


def music(bot, update):
    """
    Command /music
    Gets the links sent by all the users of the chat in the last week
    and group them by user>links
    """
    days = 7
    now = datetime.datetime.now()
    last_week_timedelta = datetime.timedelta(days=days)

    last_week_links = defaultdict(list)

    links = Link.select() \
        .join(Chat) \
        .where(Chat.id == update.message.chat_id) \
        .where(
        (Link.created_at >= now - last_week_timedelta) | (Link.updated_at >= now - last_week_timedelta)) \
        .order_by(Link.updated_at.asc(), Link.created_at.asc())

    for link in links:
        last_week_links[link.user].append(link)
    last_week_links = dict(last_week_links)

    response = Responser.links_by_user(
        last_week_links, ResponseType.LAST_WEEK)

    update.message.reply_text(response, disable_web_page_preview=True,
                              parse_mode=ParseMode.HTML)
    logger.info(f"'/music' command was called by user {update.message.from_user.id} in chat {update.message.chat_id}")


def music_from_beginning(bot, update, args):
    """
    Command /music_from_beginning @username
    Gets the links sent by an specific username of the chat from the beginning
    """
    all_time_links = defaultdict(list)

    try:
        username = args[0]
        username = username.replace('@', '')
    except IndexError:
        response = Responser.music_from_beginning_no_username()
        update.message.reply_text(response, disable_web_page_preview=True,
                                  parse_mode=ParseMode.HTML)
        return

    links = Link.select() \
        .join(Chat, on=(Chat.id == Link.chat)) \
        .join(User, on=(User.id == Link.user)) \
        .where((Chat.id == update.message.chat_id) & (User.username == username)) \
        .order_by(Link.updated_at.asc(), Link.created_at.asc())

    if len(links) == 0:
        response = Responser.no_links_found(username)
        update.message.reply_text(response, disable_web_page_preview=True, parse_mode=ParseMode.HTML)
        return

    for link in links:
        all_time_links[link.user].append(link)
    all_time_links = dict(all_time_links)

    response = Responser.links_by_user(
        all_time_links, ResponseType.FROM_THE_BEGINNING)
    Responser.reply_message(update, response)
    logger.info(
        f"'/music_from_beginning' command was called by user {update.message.from_user.id} \
         in chat {update.message.chat_id} for the user {username}")


def stats(bot, update):
    """
    Command /stats
    Returns the number of links sent in a chat by every user
    """
    users = User.select(User, fn.Count(Link.url).alias('links')) \
        .join(Link, on=Link.user) \
        .join(Chat, on=Link.chat) \
        .where(Link.chat.id == update.message.chat_id) \
        .group_by(User) \
        .order_by(SQL('links').desc())

    response = Responser.stats_by_user(users)
    update.message.reply_text(response, disable_web_page_preview=True,
                              parse_mode=ParseMode.HTML)

    logger.info(
        f"'/stats' command was called by user {update.message.from_user.id} in the chat {update.message.chat_id}")


def find_streaming_link_in_text(bot, update):
    """
    Finds the streaming url, identifies the streaming service in the text and
    saves it to the database. 
    It also saves the user and the chat if they don't exist @ database
    """
    spotify_parser = SpotifyParser()

    link_type = None
    url = utils.extract_url_from_message(update.message.text)
    cleaned_url = ''

    # Check if is a Spotify url
    if spotify_parser.is_valid_url(url):
        link_type = spotify_parser.get_link_type(url)
        cleaned_url = spotify_parser.clean_url(url)

    # If link was resolved correctly, save or update it
    if link_type is not None and link_type != 0:
        _save_or_update_user_chat_link(update, cleaned_url, link_type, spotify_parser)


def _save_or_update_user_chat_link(update, cleaned_url, link_type, spotify_parser):
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
        logger.info(f"Chat '{chat.name}' with id '{chat.id}' was created")

    # Update the link if it exists for a chat, create if it doesn't exist
    link = Link.get_or_none((Link.url == cleaned_url) & (Link.chat == chat))
    if link is not None:
        # If link already exists, set updated_at and last_update_user to current
        link.apply_update(user)
        link.save()
        link_updated = True
    else:
        # If the link doesn't exists, get link info based on the link type and save it
        link_info = spotify_parser.get_link_info(cleaned_url, link_type)
        if link_info is None:
            logger.error("Error ocurred getting link info")

        link = Link.create(
            url=cleaned_url,
            link_type=link_type.value,
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

    return link


def main():
    """Bot start"""
    updater = Updater(getenv('TOKEN'))

    # Register handlers
    dispatcher = updater.dispatcher

    # Register commands
    dispatcher.add_handler(CommandHandler('music', music))
    dispatcher.add_handler(CommandHandler(
        'music_from_beginning', music_from_beginning, pass_args=True))
    dispatcher.add_handler(CommandHandler('stats', stats))
    dispatcher.add_handler(InlineQueryHandler(search))

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
