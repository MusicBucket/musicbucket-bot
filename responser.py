import spotify
from emoji import emojize


class Responser():
    def last_week_links_by_user(self, user_links):
        parser = spotify.Parser()
        msg = '<strong>Music from the last week:</strong> \n'
        print('USER_LINKS')
        print(user_links)
        for user, links in user_links.items():
            msg += '{} <strong>{}:</strong>\n'.format(emojize(':baby:', use_aliases=True),
                                                      user.username or user.firstname)
            print('User links: {}'.format(user.links))
            for link in links:
                print('Link: {}'.format(link))

                link_info = parser.get_link_info(link.link, link.link_type)

                if link.link_type == spotify.LinkType.ARTIST.value:
                    msg += '    <strong>{}</strong> (Artist): {} @ {} \n'.format(
                        link_info.artist, link.link, link.created_at)
                elif link.link_type == spotify.LinkType.ALBUM.value:
                    msg += '    <strong>{} - {}</strong> (Album): {} @ {} \n'.format(link_info.artist, link_info.album, link.link,
                                                                                     link.created_at)
                elif link.link_type == spotify.LinkType.TRACK.value:
                    msg += '    <strong>{} by {}</strong> (Track): {} @ {} \n'.format(link_info.track, link_info.artist, link.link,
                                                                                      link.created_at)
        return msg
