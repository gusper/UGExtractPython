#!/usr/bin/env python3

import sys
import glob
from typing import List
from song_scraper import SongScraper

class Program:
    def __init__(self):
        self.files: List[str] = []
    
    def run(self, args: List[str]) -> str:
        """Main program logic"""
        self._process_args(args)
        scraper = SongScraper()
        
        if not args:
            # No arguments - scrape from web
            scraper.import_web()
        else:
            # Process HTML files
            for file_path in self.files:
                scraper.import_file(file_path)
        
        output = scraper.generate_markdown()
        print(output)
        return output
    
    def _process_args(self, args: List[str]) -> None:
        """Process command line arguments and expand file wildcards"""
        for arg in args:
            # Use glob to expand wildcards
            matching_files = glob.glob(arg)
            if matching_files:
                self.files.extend(matching_files)
            else:
                # If no matches, add the argument as-is (might be a direct file path)
                self.files.append(arg)

def main():
    program = Program()
    program.run(sys.argv[1:])

if __name__ == "__main__":
    main()