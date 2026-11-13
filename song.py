from dataclasses import dataclass
from typing import Optional
from song_type import SongType

@dataclass
class Song:
    title: str = ""
    artist: str = ""
    url: str = ""
    file_type: SongType = SongType.NONE
    views: Optional[int] = None  # Total views on UG; None if not fetched
