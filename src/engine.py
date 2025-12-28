import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.scraper import Scraper
import threading
from queue import Queue, Empty

class ScraperEngine:
    def __init__(self, db_helper, max_workers=2, delay=1.0):
        self.db = db_helper
        self.scraper = Scraper()
        self.visited_ids = set(self.db.get_all_ids())
        self.pending_ids = set()
        self.lock = threading.Lock()
        self.queue = Queue()
        self.max_workers = max_workers
        self.delay = delay
        self.session = requests.Session()

    def scrape_person(self, url):
        result = self._scrape_one(url)
        return result[0] if result else None

    def retry_failed(self, limit=100):
        pending = self.db.get_pending_urls()
        if not pending:
            print("No pending/failed URLs to retry.")
            return
            
        print(f"Retrying {len(pending)} pending/failed URLs...")
        for item in pending:
            with self.lock:
                if item["id"] not in self.visited_ids and item["id"] not in self.pending_ids:
                    self.pending_ids.add(item["id"])
                    self.queue.put((item["id"], item["url"]))
        
        self._process_queue(limit=limit)

    def _process_queue(self, limit=100):
        count = 0
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
                            print(f"Crawled {data['id']}: {url} ({count}/{limit if limit < 1000000 else 'all'})")
                            for rel in rels:
                                # Save discovered URL to DB
                                self.db.add_discovered_url(rel["related_id"], rel["url"])
                                with self.lock:
                                    if rel["related_id"] not in self.visited_ids and rel["related_id"] not in self.pending_ids:
                                        self.pending_ids.add(rel["related_id"])
                                        self.queue.put((rel["related_id"], rel["url"]))
                    except Exception as e:
                        print(f"Future for {url} raised exception: {e}")
                
                # Be a bit nice
                time.sleep(0.05)
        return count

    def _scrape_one(self, url):
        retries = 1
        backoff = 2
        for attempt in range(retries + 1):
            try:
                # Add delay before request to be respectful
                if self.delay > 0:
                    time.sleep(self.delay)
                
                try:
                    response = self.session.get(url, timeout=10)
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    if attempt < retries:
                        print(f"Connection error/Timeout for {url} (Attempt {attempt+1}/{retries+1}). Retrying...")
                        time.sleep(backoff)
                        continue
                    else:
                        print(f"Failed to connect to {url} after {retries+1} attempts.")
                        return None

                if response.status_code == 429:
                    if attempt < retries:
                        sleep_time = backoff ** (attempt + 1)
                        print(f"Rate limited (429). Retrying {url} in {sleep_time}s...")
                        time.sleep(sleep_time)
                        continue
                    else:
                        print(f"Rate limited (429). Max retries reached for {url}")
                        return None
                        
                response.raise_for_status()
                
                html_content = response.text
                if not html_content:
                    print(f"Received empty response from {url}")
                    return None
                
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
                else:
                    if attempt < retries:
                         continue
                    return None

            except requests.exceptions.RequestException as e:
                print(f"HTTP error scraping {url} (Attempt {attempt+1}/{retries+1}): {e}")
                if attempt < retries:
                    time.sleep(backoff)
                else:
                    return None
            except Exception as e:
                print(f"Unexpected error scraping {url}: {e}")
                return None
        return None

    def crawl(self, start_url, limit=100):
        # Initial scrape to start the process
        first_res = self._scrape_one(start_url)
        if not first_res:
            return
            
        data, rels = first_res
        count = 1
        print(f"Crawled {data['id']}: {start_url} ({count}/{limit})")
        
        # Add discovered URLs to queue and DB
        for rel in rels:
            self.db.add_discovered_url(rel["related_id"], rel["url"])
            with self.lock:
                if rel["related_id"] not in self.visited_ids and rel["related_id"] not in self.pending_ids:
                    self.pending_ids.add(rel["related_id"])
                    self.queue.put((rel["related_id"], rel["url"]))
        
        count += self._process_queue(limit=limit - 1)
        print(f"Crawl finished. Total individuals scraped in this session: {count}")
