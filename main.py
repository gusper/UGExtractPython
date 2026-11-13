#!/usr/bin/env python3

import argparse
import glob
from pathlib import Path
from typing import List, Optional
from song_scraper import SongScraper

# Saved view counts, so a normal run only fetches views for tabs it hasn't seen yet
VIEW_CACHE_PATH = Path(__file__).resolve().parent / "view_counts.json"

class Program:
    def __init__(self):
        self.files: List[str] = []

    def run(self, argv: Optional[List[str]] = None) -> str:
        """Main program logic"""
        args = self._parse_args(argv)
        self._expand_files(args.files)
        scraper = SongScraper()

        if not self.files:
            # No file arguments - scrape from web
            scraper.import_web()
        else:
            # Process HTML files
            for file_path in self.files:
                scraper.import_file(file_path)

        if not args.no_views:
            scraper.fetch_view_counts(VIEW_CACHE_PATH, refresh=args.refresh_views)

        output = scraper.generate_markdown()
        print(output)
        return output

    @staticmethod
    def _parse_args(argv: Optional[List[str]]) -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            description="Generate a markdown list of songs contributed to Ultimate Guitar.")
        parser.add_argument(
            "files", nargs="*",
            help="saved HTML pages to read instead of scraping the web (wildcards allowed)")
        views = parser.add_mutually_exclusive_group()
        views.add_argument(
            "--refresh-views", action="store_true",
            help="fetch every tab's view count from UG again, instead of reusing saved counts")
        views.add_argument(
            "--no-views", action="store_true",
            help="leave view counts out of the list entirely")
        return parser.parse_args(argv)

    def _expand_files(self, patterns: List[str]) -> None:
        """Expand file wildcards"""
        for pattern in patterns:
            matching_files = glob.glob(pattern)
            if matching_files:
                self.files.extend(matching_files)
            else:
                # If no matches, add the argument as-is (might be a direct file path)
                self.files.append(pattern)

def main():
    Program().run()

if __name__ == "__main__":
    main()
