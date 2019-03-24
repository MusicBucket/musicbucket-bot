import re
import logging


logger = logging.getLogger(__name__)


def extract_url_from_message(text):
    """Gets the first url of a message"""
    link = re.search("(?P<url>https?://[^\s]+)", text)
    if link is not None:
        logger.info(f'Extracting url from message: {text}')
        return link.group('url')
    return ''
