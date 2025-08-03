from enum import Enum

class SongType(Enum):
    NONE = "none"
    CHORDS = "chords"
    TABS = "tabs"
    GUITAR_PRO = "guitar pro"
    
    def __str__(self):
        return self.value