from enum import Enum

from .music import spotify, deezer, music
from emoji import emojize


class ResponseType(Enum):
    """Response types based on the available commands"""
    FROM_THE_BEGINNING = 0
    LAST_WEEK = 1


class Responser():
    def links_by_user(self, user_links, response_type):
        msg = ''
        if response_type == ResponseType.LAST_WEEK:
            msg += '<strong>Music from the last week:</strong> \n'
        elif response_type == ResponseType.FROM_THE_BEGINNING:
            msg += '<strong>Music from the beginning of time:</strong> \n'

        for user, links in user_links.items():
            msg += '- {} <strong>{}:</strong>\n'.format(emojize(':baby:', use_aliases=True),
                                                        user.username or user.firstname)
            print('User links: {}'.format(user.links))
            for link in links:
                print('Link: {}'.format(link))
                link_info = music.LinkInfo(link_type=link.link_type,
                                           artist=link.artist_name,
                                           album=link.album_name,
                                           track=link.track_name,
                                           genre=link.genre)

                if link_info is not None and link_info != '':
                    if link.link_type == spotify.LinkType.ARTIST.value:
                        msg += '    {} <a href="{}">{}</a> {}\n'.format(
                            emojize(':busts_in_silhouette:', use_aliases=True), link.link, link_info.artist, '(' + link_info.genre + ')' if link_info.genre is not None else '')
                    elif link.link_type == spotify.LinkType.ALBUM.value:
                        msg += '    {} <a href="{}">{} - {}</a> {}\n'.format(
                            emojize(':cd:', use_aliases=True), link.link, link_info.artist, link_info.album, '(' + link_info.genre + ')' if link_info.genre is not None else '')
                    elif link.link_type == spotify.LinkType.TRACK.value:
                        msg += '    {} <a href="{}">{} by {}</a> {}\n'.format(emojize(
                            ':musical_note:', use_aliases=True), link.link, link_info.track, link_info.artist, '(' + link_info.genre + ')' if link_info.genre is not None else '')
            msg += '\n'
        return msg
