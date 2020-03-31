from emoji import emojize

from bot.music.music import LinkType

EMOJI_USER = emojize(':baby:', use_aliases=True)
EMOJI_ARTIST = emojize(':busts_in_silhouette:', use_aliases=True)
EMOJI_ALBUM = emojize(':cd:', use_aliases=True)
EMOJI_TRACK = emojize(':musical_note:', use_aliases=True)


def get_music_emoji(link_type: str):
    if link_type == LinkType.ARTIST.value:
        return EMOJI_ARTIST
    elif link_type == LinkType.ALBUM.value:
        return EMOJI_ALBUM
    elif link_type == LinkType.TRACK.value:
        return EMOJI_TRACK
