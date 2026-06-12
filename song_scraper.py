import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List
from song import Song
from song_type import SongType

class SongScraper:
    def __init__(self):
        self.songs: List[Song] = []
        self.line_identifier = "— <a href=\"https://tabs.ultimate-guitar.com/tab"
    
    @property
    def count(self) -> int:
        return len(self.songs)
    
    def add_song(self, song: Song) -> None:
        # Check for duplicates before adding
        for existing_song in self.songs:
            if (existing_song.url == song.url and 
                existing_song.title == song.title and 
                existing_song.artist == song.artist):
                return  # Don't add duplicate
        self.songs.append(song)
    
    def import_web(self) -> None:
        """Load songs from a user's contributions on UltimateGuitar from web"""
        page = 1
        consecutive_empty_pages = 0
        max_pages = 20  # Safety limit - increased to handle more songs
        
        # Add browser headers to avoid 403 errors
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        while page <= max_pages:
            if page == 1:
                url = "https://www.ultimate-guitar.com/contribution/6193383-gusp3r/tabs"
            else:
                url = f"https://www.ultimate-guitar.com/contribution/6193383-gusp3r/tabs?page={page}&per-page=50"
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            songs_before = len(self.songs)
            self._process_songs_in_html(soup)
            songs_after = len(self.songs)
            
            # If no new songs were added, increment counter
            if songs_after == songs_before:
                consecutive_empty_pages += 1
                
                # Stop if we get 2 consecutive pages with no new songs
                if consecutive_empty_pages >= 2:
                    break
            else:
                consecutive_empty_pages = 0  # Reset counter
                
            page += 1
    
    def import_file(self, file_path: str) -> None:
        """Pull out the songs in an HTML file and add them to the song list"""
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        self._process_songs_in_html(soup)
    
    def _process_songs_in_html(self, soup: BeautifulSoup) -> None:
        """Extract songs from HTML and add them to the song list"""
        song_nodes = soup.select("tbody tr")
        
        for song_node in song_nodes:
            try:
                # Get the first span element
                span_element = song_node.select_one("span")
                if not span_element:
                    continue
                
                # Find the anchor tag within the span
                anchor_tag = span_element.select_one("a")
                if not anchor_tag:
                    continue
                
                # Extract URL from href attribute
                url = anchor_tag.get('href', '')
                if not url:
                    continue
                
                # Extract title from anchor text
                title = anchor_tag.get_text().strip()
                
                # Extract artist (everything before the anchor tag)
                span_html = str(span_element)
                anchor_html = str(anchor_tag)
                
                # Find artist text before the anchor
                anchor_start = span_html.find(anchor_html)
                if anchor_start == -1:
                    continue
                
                artist_part = span_html[:anchor_start]
                artist_soup = BeautifulSoup(artist_part, 'html.parser')
                artist = artist_soup.get_text().strip()
                
                # Remove trailing characters like "—" or other separators
                artist = artist.rstrip('— ').strip()
                
                # Extract file type from second td
                file_type_element = song_node.select_one("td:nth-child(2)")
                if not file_type_element:
                    continue
                
                file_type = self._parse_song_type(file_type_element.get_text().strip())
                
                self.add_song(Song(
                    artist=artist,
                    title=title,
                    url=url,
                    file_type=file_type
                ))
            
            except Exception as e:
                # Skip problematic entries
                continue
    
    def generate_markdown(self) -> str:
        """Generate markdown output with Hugo shortcode formatting"""
        lines = []
        lines.append(f"{len(self.songs)} songs I've transcribed and shared as of {datetime.now().strftime('%B %d, %Y')}:\n")
        
        # Sort songs alphabetically by artist, then by title
        sorted_songs = sorted(self.songs, key=lambda s: (s.artist.lower(), s.title.lower()))
        
        for song in sorted_songs:
            line = f"* {song.artist} - {{{{<rawhtml>}}}}<a href=\"{song.url}\" target=\"blank\">{song.title}</a>{{{{</rawhtml>}}}} ({song.file_type})"
            lines.append(line)
        
        return '\n'.join(lines)
    
    def _parse_song_type(self, song_type: str) -> SongType:
        """Parse song type string to SongType enum"""
        song_type_lower = song_type.strip().lower()
        
        if song_type_lower == "tab":
            return SongType.TABS
        elif song_type_lower == "chord":
            return SongType.CHORDS
        elif song_type_lower == "guitar pro":
            return SongType.GUITAR_PRO
        else:
            return SongType.CHORDS