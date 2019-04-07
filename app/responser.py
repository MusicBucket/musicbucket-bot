import logging
from enum import Enum

from app.music.music import LinkType
from emoji import emojize

logger = logging.getLogger(__name__)


class ResponseType(Enum):
    """Response types based on the available commands"""
    FROM_THE_BEGINNING = 0
    LAST_WEEK = 1


class Responser:

    @staticmethod
    def links_by_user(user_links, response_type):
        msg = ''
        if response_type == ResponseType.LAST_WEEK:
            msg += '<strong>Music from the last week:</strong> \n'
        elif response_type == ResponseType.FROM_THE_BEGINNING:
            msg += '<strong>Music from the beginning of time:</strong> \n'

        for user, links in user_links.items():
            msg += '- {} <strong>{}:</strong>\n'.format(emojize(':baby:', use_aliases=True),
                                                        user.username or user.firstname)
            logger.info('User: {}, Links: {}'.format(user.id, links))
            for link in links:
                logger.info('Link: {}'.format(link.url))

                if link.link_type == LinkType.ARTIST.value:
                    msg += '    {}  {} <a href="{}">{}</a> {}\n'.format(
                        emojize(':busts_in_silhouette:', use_aliases=True),
                        '[{}{}]'.format(link.created_at.strftime(
                            "%Y/%m/%d"),
                            ' | Updated @ {} by {}'.format(link.updated_at.strftime(
                                "%Y/%m/%d"),
                                link.last_update_user.username or link.last_update_user.first_name or '') if link.last_update_user else '') if response_type == ResponseType.FROM_THE_BEGINNING else '',
                        link.url,
                        link.artist_name,
                        '({})'.format(link.genre) if link.genre is not None else '')
                elif link.link_type == LinkType.ALBUM.value:
                    msg += '    {}  {} <a href="{}">{} - {}</a> {}\n'.format(
                        emojize(':cd:', use_aliases=True),
                        '[{}{}]'.format(link.created_at.strftime(
                            "%Y/%m/%d"),
                            ' | Updated @ {} by {}'.format(link.updated_at.strftime(
                                "%Y/%m/%d"),
                                link.last_update_user.username or link.last_update_user.first_name or '') if link.last_update_user else '') if response_type == ResponseType.FROM_THE_BEGINNING else '',
                        link.url,
                        link.artist_name,
                        link.album_name,
                        '({})'.format(link.genre) if link.genre is not None else '')
                elif link.link_type == LinkType.TRACK.value:
                    msg += '    {}  {} <a href="{}">{} by {}</a> {}\n'.format(
                        emojize(':musical_note:', use_aliases=True),
                        '[{}{}]'.format(link.created_at.strftime(
                            "%Y/%m/%d"),
                            ' | Updated @ {} by {}'.format(link.updated_at.strftime(
                                "%Y/%m/%d"),
                                link.last_update_user.username or link.last_update_user.first_name or '') if link.last_update_user else '') if response_type == ResponseType.FROM_THE_BEGINNING else '',
                        link.url,
                        link.track_name,
                        link.artist_name,
                        '({})'.format(link.genre) if link.genre is not None else '')
            msg += '\n'
        return msg

    @staticmethod
    def playlist(spotify_playlist, playlist):
        name = spotify_playlist['name']
        description = spotify_playlist['description']
        tracks = spotify_playlist['tracks']['items']
        added_at = playlist.added_at
        url = playlist.url
        msg = f'<strong>{name}</strong> \n \
        <i>{description}</i> \n \
        Added at: {added_at} \n \
        Url: {url} \n \
        Tracks: \n'

        for index, track_item in enumerate(tracks):
            track = track_item['track']
            msg += f'{index + 1} - <strong>{track["name"]}</strong> by <i>{track["artists"][0]["name"]}</i> \n'

        return msg

    @staticmethod
    def playlist_created_successfully(playlist):
        return f'The playlist <strong>{playlist["name"]}</strong> was created succesfully. \n \
        <strong>Url:</strong>{playlist["external_urls"]["spotify"]}'

    @staticmethod
    def chat_has_already_playlist():
        return f'The current chat has already a playlist'

    @staticmethod
    def set_playlist_invalid_url(url):
        return f'The url `{url}` is not a valid playlist url'

    @staticmethod
    def stats_by_user(users):
        msg = '<strong>Links sent by the users from the beginning in this chat:</strong> \n'

        for user in users:
            msg += '- {} <strong>{}:</strong> {}\n'.format(emojize(':baby:', use_aliases=True),
                                                           user.username or user.firstname,
                                                           user.links)
        return msg
