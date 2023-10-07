from bot.models import Artist, Track, Album
from bot.music.music import LinkType


def get_music_emoji(link_type: str):
    if link_type == LinkType.ARTIST.value:
        return Artist.EMOJI
    elif link_type == LinkType.ALBUM.value:
        return Album.EMOJI
    elif link_type == LinkType.TRACK.value:
        return Track.EMOJI
