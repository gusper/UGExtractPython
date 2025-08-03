from dataclasses import dataclass
from song_type import SongType

@dataclass
class Song:
    title: str = ""
    artist: str = ""
    url: str = ""
    file_type: SongType = SongType.NONE