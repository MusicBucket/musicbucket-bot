import re
import logging


logger = logging.getLogger(__name__)


def extract_url_from_message(text):
    """Gets the first url of a message"""
    logger.info(f'Extracting url from message: {text}')
    link = re.search("(?P<url>https?://[^\s]+)", text).group("url")
    return link
