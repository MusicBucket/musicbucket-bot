import logging

from dotenv import load_dotenv

from bot.db import db
from bot.models import ChatLink, Link

log = logging.getLogger(__name__)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

load_dotenv()


def _setup_database():
    db.connect()
    db.create_tables([ChatLink])


def _migrate_link(link: Link):
    created_chat_link = ChatLink.create(
        sent_at=link.created_at,
        chat=link.chat,
        link=link,
        sent_by=link.user,
    )
    log.info(f'Created ChatLink: {str(created_chat_link)}')


def _migrate_links():
    links = Link.select().order_by(Link.created_at.asc())
    links_num = len(links)

    log.info(f'Migrating {len(links)} links')
    for i, link in enumerate(links):
        log.info(f'Migrating link {i + 1} of {links_num}. ID: {link.id}. {str(link)}')
        _migrate_link(link)


def _clean_links():
    links = Link.select().order_by(Link.created_at.asc())
    links_num = len(links)
    processed_links = {}

    log.info(f'Cleaning {len(links)} links')
    for i, link in enumerate(links):
        if link.url not in processed_links:
            log.info(f'Cleaning link {i + 1} of {links_num}. ID: {link.id}. {str(link)}')
            same_url_links = list(Link.select().where(Link.url == link.url, Link.id != link.id))
            processed_links[link.url] = same_url_links
            created_chat_link = ChatLink.create(
                sent_at=link.created_at,
                chat=link.chat,
                link=link,
                sent_by=link.user,
            )
            log.info(f'Created ChatLink: {str(created_chat_link)} from Link ID: {link.id}')
            log.info(f'---- Creating duplicated ChatLinks')
            for same_url_link in same_url_links:
                created_chat_link = ChatLink.create(
                    sent_at=same_url_link.created_at,
                    chat=same_url_link.chat,
                    link=link,
                    sent_by=same_url_link.user,
                )
                log.info(f'---- Created duplicated ChatLink: {str(created_chat_link)} from Link ID: {same_url_link.id}')
        else:
            log.info(f'Url link already marked as processed, omitting. ID: {link.id}. {str(link)}')

    for url, duplicated_links in processed_links.items():
        if duplicated_links:
            log.info(f'Deleting duplicated links of url: {url}')
            for duplicated_link in duplicated_links:
                log.info(f'Deleting duplicated link. ID: {duplicated_link.id}. {str(duplicated_link)}')
                duplicated_link.delete_instance()


def main():
    log.info('Starting migration')
    _setup_database()
    _clean_links()
    log.info('Migration finished')


if __name__ == '__main__':
    main()
