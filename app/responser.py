from .music import spotify, deezer, music
from emoji import emojize


class Responser():
    def last_week_links_by_user(self, user_links):
        # spotify_parser = spotify.SpotifyParser()
        # deezer_parser = deezer.DeezerParser()

        msg = '<strong>Music from the last week:</strong> \n'
        for user, links in user_links.items():
            msg += '- {} <strong>{}:</strong>\n'.format(emojize(':baby:', use_aliases=True),
                                                        user.username or user.firstname)
            print('User links: {}'.format(user.links))
            for link in links:
                print('Link: {}'.format(link))
                link_info = music.LinkInfo(link_type=link.link_type,
                                     artist=link.artist_name,
                                     album=link.album_name,
                                     track=link.track_name)

                # if spotify_parser.is_spotify_url(link.link):
                #     link_info = spotify_parser.get_link_info(
                #         link.link, link.link_type)
                # elif deezer_parser.is_deezer_url(link.link):
                #     link_info = deezer_parser.get_link_info(
                #         link.link, link.link_type)

                if link_info is not None and link_info != '':
                    if link.link_type == spotify.LinkType.ARTIST.value:
                        msg += '    {} <a href="{}">{}</a>\n'.format(
                            emojize(':busts_in_silhouette:', use_aliases=True), link.link, link_info.artist)
                    elif link.link_type == spotify.LinkType.ALBUM.value:
                        msg += '    {} <a href="{}">{} - {}</a>\n'.format(
                            emojize(':cd:', use_aliases=True), link.link, link_info.artist, link_info.album)
                    elif link.link_type == spotify.LinkType.TRACK.value:
                        msg += '    {} <a href="{}">{} by {}</a>\n'.format(emojize(
                            ':musical_note:', use_aliases=True), link.link, link_info.track, link_info.artist)
            msg += '\n'
        return msg
