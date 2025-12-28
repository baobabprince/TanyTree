import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.scraper import Scraper
import threading
from queue import Queue, Empty

class ScraperEngine:
    def __init__(self, db_helper, max_workers=5):
        self.db = db_helper
        self.scraper = Scraper()
        self.visited_ids = set()
        self.pending_ids = set()
        self.lock = threading.Lock()
        self.queue = Queue()
        self.max_workers = max_workers
        self.session = requests.Session()

    def scrape_person(self, url):
        result = self._scrape_one(url)
        return result[0] if result else None

    def _scrape_one(self, url):
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            html_content = response.text
            
            # Extract biographical data
            data = self.scraper.extract_biographical_data(html_content, url)
            if data and data.get("id"):
                person_id = data["id"]
                
                with self.lock:
                    if person_id in self.visited_ids:
                        return None
                    self.visited_ids.add(person_id)

                self.db.add_individual(data)
                
                # Extract relationships
                rels = self.scraper.extract_relationships(html_content, person_id, base_url=url)
                for rel in rels:
                    self.db.add_relationship(rel["person_id"], rel["related_id"], rel["type"])
                    
                return data, rels
        except Exception as e:
            print(f"Error scraping {url}: {e}")
        return None

    def crawl(self, start_url, limit=100):
        # Initial scrape to start the process
        first_res = self._scrape_one(start_url)
        if not first_res:
            return
            
        data, rels = first_res
        count = 1
        print(f"Crawled {data['id']}: {start_url} ({count}/{limit})")
        
        # Add discovered URLs to queue
        for rel in rels:
            with self.lock:
                if rel["related_id"] not in self.visited_ids and rel["related_id"] not in self.pending_ids:
                    self.pending_ids.add(rel["related_id"])
                    self.queue.put((rel["related_id"], rel["url"]))
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            
            while (self.queue.qsize() > 0 or futures) and count < limit:
                # Fill up the futures
                while len(futures) < self.max_workers and count + len(futures) < limit:
                    try:
                        person_id, url = self.queue.get_nowait()
                        # Double check visited_ids in case it was finished by another thread
                        with self.lock:
                            if person_id in self.visited_ids:
                                continue
                        
                        future = executor.submit(self._scrape_one, url)
                        futures[future] = url
                    except Empty:
                        break
                
                if not futures:
                    if self.queue.qsize() == 0:
                        break
                    time.sleep(0.1)
                    continue
                    
                # Wait for at least one future to complete
                from concurrent.futures import wait, FIRST_COMPLETED
                done, not_done = wait(futures.keys(), return_when=FIRST_COMPLETED)
                
                for future in done:
                    url = futures.pop(future)
                    try:
                        result = future.result()
                        if result:
                            count += 1
                            data, rels = result
                            print(f"Crawled {data['id']}: {url} ({count}/{limit})")
                            for rel in rels:
                                with self.lock:
                                    if rel["related_id"] not in self.visited_ids and rel["related_id"] not in self.pending_ids:
                                        self.pending_ids.add(rel["related_id"])
                                        self.queue.put((rel["related_id"], rel["url"]))
                    except Exception as e:
                        print(f"Future for {url} raised exception: {e}")
                
                # Be a bit nice
                time.sleep(0.05)

        print(f"Crawl finished. Total individuals scraped: {count}")
