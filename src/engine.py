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
                        # Always save discovered URL to DB for future crawling/retries
                        self.db.add_discovered_url(rel["related_id"], rel["url"])
                        
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

    def _discover_from_db(self, limit=1000):
        """Try to find missing URLs by looking at relationships of already visited people."""
        # Find people in 'individuals' who have relationships with people NOT in 'individuals'
        # and we don't have a URL for those related people in 'discovered_urls'.
        with self.lock:
            cursor = self.db.conn.cursor()
            # This is a bit complex, let's find IDs first
            cursor.execute("""
                SELECT DISTINCT r.related_id, i.url
                FROM relationships r
                JOIN individuals i ON r.person_id = i.id
                LEFT JOIN individuals i2 ON r.related_id = i2.id
                LEFT JOIN discovered_urls d ON r.related_id = d.id
                WHERE i2.id IS NULL AND d.id IS NULL
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            
        added = 0
        from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
        
        for related_id, parent_url in rows:
            # Construct URL based on parent_url but with related_id
            parsed = urlparse(parent_url)
            query = parse_qs(parsed.query)
            query['i'] = [related_id]
            new_query = urlencode(query, doseq=True)
            new_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
            
            self.db.add_discovered_url(related_id, new_url)
            added += 1
            
        if added > 0:
            print(f"Heuristically discovered {added} URLs from existing relationships in database.")
        return added

    def crawl(self, start_url, limit=100):
        # Initial scrape to start the process
        first_res = self._scrape_one(start_url)
        
        count = 0
        if first_res:
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
        else:
            # If already visited, we might still want to start crawling from its relationships
            # to continue where we left off.
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(start_url)
            start_id = parse_qs(parsed_url.query).get('i', [None])[0]
            
            if start_id in self.visited_ids:
                print(f"Start node {start_id} already visited. Exploring its relationships to resume crawl...")
                # Re-scrape just to get fresh relationships and URLs
                try:
                    response = self.session.get(start_url, timeout=10)
                    response.raise_for_status()
                    html_content = response.text
                    rels = self.scraper.extract_relationships(html_content, start_id, base_url=start_url)
                    for rel in rels:
                        self.db.add_discovered_url(rel["related_id"], rel["url"])
                        with self.lock:
                            if rel["related_id"] not in self.visited_ids and rel["related_id"] not in self.pending_ids:
                                self.pending_ids.add(rel["related_id"])
                                self.queue.put((rel["related_id"], rel["url"]))
                    print(f"Added {len(rels)} neighbors of {start_id} to queue.")
                    
                    # If we still don't have enough work, try to discover URLs from DB
                    if self.queue.qsize() < limit:
                         self._discover_from_db(limit=limit)
                    
                    # If we don't have enough pending work in the queue to reach the limit,
                    # pull pending URLs from the DB.
                    if self.queue.qsize() < limit:
                        pending = self.db.get_pending_urls()
                        if pending:
                            added_count = 0
                            for item in pending:
                                with self.lock:
                                    if item["id"] not in self.visited_ids and item["id"] not in self.pending_ids:
                                        self.pending_ids.add(item["id"])
                                        self.queue.put((item["id"], item["url"]))
                                        added_count += 1
                                if added_count + self.queue.qsize() >= limit:
                                    break
                            if added_count > 0:
                                print(f"Added {added_count} pending URLs from database to resume crawl.")
                except Exception as e:
                    print(f"Error re-scraping {start_url} to resume: {e}")
            else:
                print(f"Failed to scrape start URL: {start_url}")
                return

        if count < limit:
            count += self._process_queue(limit=limit - count)
            
        print(f"Crawl finished. Total individuals scraped in this session: {count}")
