import json
import sys
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from song import Song
from song_type import SongType

# Browser-like headers to avoid 403 errors.
# No 'br' in Accept-Encoding: requests can only decode Brotli if the optional brotli package is installed.
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# Pause between tab page requests so we don't hammer UG's servers
VIEW_FETCH_DELAY_SECONDS = 0.5

class SongScraper:
    def __init__(self):
        self.songs: List[Song] = []
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
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

        while page <= max_pages:
            if page == 1:
                url = "https://www.ultimate-guitar.com/contribution/6193383-gusp3r/tabs"
            else:
                url = f"https://www.ultimate-guitar.com/contribution/6193383-gusp3r/tabs?page={page}&per-page=50"
            
            response = self.session.get(url)
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
    
    def fetch_view_counts(self, cache_path: Path, refresh: bool = False) -> None:
        """Set each song's view count, reusing counts saved in the cache file.

        Only tabs missing from the cache are fetched from UG, unless refresh is
        True, in which case every tab is fetched again. Fetched counts are saved
        back to the cache.
        """
        cache = self._load_view_cache(cache_path)
        to_fetch = []
        for song in self.songs:
            if not refresh and song.url in cache:
                song.views = cache[song.url]["views"]
                song.views_as_of = cache[song.url].get("fetched")
            else:
                to_fetch.append(song)

        reused = len(self.songs) - len(to_fetch)
        print(f"Views: reusing {reused} saved, fetching {len(to_fetch)} from UG", file=sys.stderr)

        today = datetime.now().strftime("%Y-%m-%d")
        for i, song in enumerate(to_fetch, start=1):
            print(f"Fetching views {i}/{len(to_fetch)}: {song.artist} - {song.title}", file=sys.stderr)
            song.views = self._fetch_views(song.url)
            if song.views is not None:
                song.views_as_of = today
                cache[song.url] = {"views": song.views, "fetched": today}
            if i < len(to_fetch):
                time.sleep(VIEW_FETCH_DELAY_SECONDS)

        if to_fetch:
            self._save_view_cache(cache_path, cache)

    @staticmethod
    def _load_view_cache(cache_path: Path) -> Dict[str, dict]:
        """Read saved view counts ({url: {"views": int, "fetched": "YYYY-MM-DD"}})"""
        if not cache_path.exists():
            return {}
        try:
            with open(cache_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except (OSError, ValueError) as e:
            print(f"Couldn't read {cache_path}, ignoring it: {e}", file=sys.stderr)
            return {}

    @staticmethod
    def _save_view_cache(cache_path: Path, cache: Dict[str, dict]) -> None:
        with open(cache_path, 'w', encoding='utf-8') as file:
            json.dump(cache, file, indent=2, sort_keys=True)
            file.write('\n')

    def _fetch_views(self, url: str) -> Optional[int]:
        """Read view_total from the JSON UG embeds in a tab page's .js-store element"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            store = soup.select_one('.js-store')
            if not store or not store.get('data-content'):
                return None
            data = json.loads(store['data-content'])
            return int(data['store']['page']['data']['tab_view']['stats']['view_total'])
        except (requests.RequestException, ValueError, KeyError, TypeError) as e:
            print(f"  Couldn't get views for {url}: {e}", file=sys.stderr)
            return None

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
        def format_date(date: datetime) -> str:
            return f"{date:%B} {date.day}, {date.year}"  # e.g. "November 5, 2026" (no leading zero)

        today = datetime.now()
        header = f"{len(self.songs)} songs I've transcribed and shared as of {format_date(today)}"

        # Total views across every tab that has a count
        counted = [song for song in self.songs if song.views is not None]
        if counted:
            total_views = sum(song.views for song in counted)
            header += f" with a total of {total_views:,} views"

        # View counts can be older than the list, since they're reused from the cache.
        # When they are, add their date, using the oldest fetch date so the header
        # never overstates how fresh they are. If they're all from today, one date is enough.
        view_dates = [song.views_as_of for song in counted if song.views_as_of]
        if view_dates:
            oldest = datetime.strptime(min(view_dates), '%Y-%m-%d')
            if oldest.date() < today.date():
                header += f" (view counts as of {format_date(oldest)})"

        lines = [header + ":\n"]
        
        # Sort songs alphabetically by artist, then by title
        sorted_songs = sorted(self.songs, key=lambda s: (s.artist.lower(), s.title.lower()))
        
        for song in sorted_songs:
            details = str(song.file_type)
            if song.views is not None:
                details += f", {song.views:,} view{'' if song.views == 1 else 's'}"
            line = f"* {song.artist} - {{{{<rawhtml>}}}}<a href=\"{song.url}\" target=\"blank\">{song.title}</a>{{{{</rawhtml>}}}} ({details})"
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