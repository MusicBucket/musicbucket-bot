from .music import spotify, deezer
from emoji import emojize


class Responser():
    def last_week_links_by_user(self, user_links):
        spotify_parser = spotify.SpotifyParser()
        deezer_parser = deezer.DeezerParser()

        msg = '<strong>Music from the last week:</strong> \n'
        for user, links in user_links.items():
            msg += '{} <strong>{}:</strong>\n'.format(emojize(':baby:', use_aliases=True),
                                                      user.username or user.firstname)
            print('User links: {}'.format(user.links))
            for link in links:
                print('Link: {}'.format(link))
                link_info = ''

                if spotify_parser.is_spotify_url(link.link):
                    link_info = spotify_parser.get_link_info(
                        link.link, link.link_type)
                elif deezer_parser.is_deezer_url(link.link):
                    link_info = deezer_parser.get_link_info(
                        link.link, link.link_type)

                if link_info is not None and link_info != '':
                    if link.link_type == spotify.LinkType.ARTIST.value:
                        msg += '{} <strong>{}</strong> (Artist): {} @ {} \n'.format(
                            emojize(':busts_in_silhouette:', use_aliases=True), link_info.artist, link.link, link.created_at.strftime('%d/%m/%Y'))
                    elif link.link_type == spotify.LinkType.ALBUM.value:
                        msg += '{} <strong>{}</strong> - <strong>{}</strong> (Album): {} @ {} \n'.format(emojize(':cd:', use_aliases=True), link_info.artist, link_info.album, link.link,
                                                                                        link.created_at.strftime('%d/%m/%Y'))
                    elif link.link_type == spotify.LinkType.TRACK.value:
                        msg += '{} <strong>{}</strong> by <strong>{}</strong> (Track): {} @ {} \n'.format(emojize(':musical_note:', use_aliases=True), link_info.track, link_info.artist, link.link,
                                                                                         link.created_at.strftime('%d/%m/%Y'))
        return msg
