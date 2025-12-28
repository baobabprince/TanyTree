import requests
import time
from src.scraper import Scraper

class ScraperEngine:
    def __init__(self, db_helper):
        self.db = db_helper
        self.scraper = Scraper()
        self.visited_ids = set()
        self.queue = []

    def scrape_person(self, url):
        # This is for backward compatibility or direct calls
        return self._scrape_one(url)

    def _scrape_one(self, url):
        response = requests.get(url)
        response.raise_for_status()
        
        html_content = response.text
        
        # Extract biographical data
        data = self.scraper.extract_biographical_data(html_content, url)
        if data and data.get("id"):
            self.db.add_individual(data)
            self.visited_ids.add(data["id"])
            
            # Extract relationships
            rels = self.scraper.extract_relationships(html_content, data["id"], base_url=url)
            for rel in rels:
                self.db.add_relationship(rel["person_id"], rel["related_id"], rel["type"])
                
                # Add to queue if not visited
                if rel["related_id"] not in self.visited_ids:
                    if rel["related_id"] not in [item[0] for item in self.queue]:
                        self.queue.append((rel["related_id"], rel["url"]))
                
        return data

    def crawl(self, start_url, limit=100):
        # Initialize queue with start_url
        data = self._scrape_one(start_url)
        
        count = 0
        if data:
            count += 1
            
        while self.queue and count < limit:
            person_id, url = self.queue.pop(0)
            if person_id in self.visited_ids:
                continue
                
            print(f"Crawling {person_id}: {url} ({count}/{limit})")
            try:
                res = self._scrape_one(url)
                if res:
                    count += 1
                time.sleep(1) # Be nice to the server
            except Exception as e:
                print(f"Error scraping {url}: {e}")
        
        print(f"Crawl finished. Total individuals scraped: {count}")
