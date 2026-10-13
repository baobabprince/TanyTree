import requests
import time
import random
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, FIRST_COMPLETED
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
        self.session.headers.update({'User-Agent': 'Lynx'})

    def scrape_person(self, url, force=False):
        result = self._scrape_one(url, force=force)
        return result[0] if result else None

    def _request_with_retry(self, url, max_retries=3, backoff_factor=5):
        for attempt in range(max_retries + 1):
            try:
                if self.delay > 0:
                    time.sleep(self.delay)

                response = self.session.get(url, timeout=30)

                if response.status_code == 429:
                    reason = "Rate limited (429)"
                elif response.status_code in [500, 502, 503, 504]:
                    reason = f"Server error ({response.status_code})"
                else:
                    response.raise_for_status()
                    return response

                if attempt < max_retries:
                    sleep_time = backoff_factor * (2 ** attempt) + random.uniform(0, 1)
                    print(f"{reason} for {url} (Attempt {attempt+1}/{max_retries+1}). Retrying in {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                    continue
                else:
                    print(f"{reason} for {url}. Max retries reached.")
                    return None

            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                if attempt < max_retries:
                    sleep_time = backoff_factor * (2 ** attempt) + random.uniform(0, 1)
                    print(f"Connection error/Timeout ({type(e).__name__}) for {url} (Attempt {attempt+1}/{max_retries+1}). Retrying in {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                    continue
                else:
                    print(f"Failed to connect to {url} after {max_retries+1} attempts: {type(e).__name__}")
                    return None
            except requests.exceptions.RequestException as e:
                print(f"HTTP error for {url}: {e}")
                return None
            except Exception as e:
                print(f"Unexpected error requesting {url}: {e}")
                return None
        return None

    def _seed_pending_from_db(self, limit):
        """Load pending discovered URLs into the queue (highest priority work)."""
        pending = self.db.get_pending_urls()
        if not pending:
            return 0

        added_count = 0
        for item in pending:
            if added_count >= limit:
                break
            with self.lock:
                if item["id"] not in self.visited_ids and item["id"] not in self.pending_ids:
                    self.pending_ids.add(item["id"])
                    self.queue.put((item["id"], item["url"]))
                    added_count += 1

        if added_count > 0:
            print(f"Seeded {added_count} pending URLs from database into queue.")
        return added_count

    def retry_failed(self, limit=100):
        pending = self.db.get_pending_urls()
        if not pending:
            print("No pending/failed URLs to retry.")
            return

        print(f"Retrying {len(pending)} pending/failed URLs...")
        self._seed_pending_from_db(limit=limit)
        self._process_queue(limit=limit)

    def _process_queue(self, limit=100):
        count = 0
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}

            while (self.queue.qsize() > 0 or futures) and count < limit:
                while len(futures) < self.max_workers and count + len(futures) < limit:
                    try:
                        person_id, url = self.queue.get_nowait()
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
                                self.db.add_discovered_url(rel["related_id"], rel["url"])
                                with self.lock:
                                    if rel["related_id"] not in self.visited_ids and rel["related_id"] not in self.pending_ids:
                                        self.pending_ids.add(rel["related_id"])
                                        self.queue.put((rel["related_id"], rel["url"]))
                    except Exception as e:
                        print(f"Future for {url} raised exception: {e}")

                time.sleep(0.05)
        return count

    def _scrape_one(self, url, force=False):
        url = url.replace('//?', '/?')
        parsed_url = urlparse(url)
        person_id = parse_qs(parsed_url.query).get('i', [None])[0]

        if person_id and not force:
            with self.lock:
                if person_id in self.visited_ids:
                    return None

        response = self._request_with_retry(url)
        if not response:
            if person_id:
                self.db.increment_failure_count(person_id)
            return None

        try:
            html_content = response.text
            if not html_content:
                print(f"Received empty response from {url}")
                if person_id:
                    self.db.increment_failure_count(person_id)
                return None

            data = self.scraper.extract_biographical_data(html_content, url)
            if data and data.get("id"):
                person_id = data["id"]

                with self.lock:
                    if not force and person_id in self.visited_ids:
                        return None
                    self.visited_ids.add(person_id)

                self.db.add_individual(data)
                self.db.reset_failure_count(person_id)

                rels = self.scraper.extract_relationships(html_content, person_id, base_url=url)
                for rel in rels:
                    self.db.add_relationship(rel["person_id"], rel["related_id"], rel["type"])
                    self.db.add_discovered_url(rel["related_id"], rel["url"])

                return data, rels
            else:
                if person_id:
                    self.db.increment_failure_count(person_id)
                return None
        except Exception as e:
            print(f"Unexpected error scraping {url}: {type(e).__name__}: {e}")
            if person_id:
                self.db.increment_failure_count(person_id)
            return None

    def _discover_from_db(self, limit=1000):
        """Find related_ids missing from individuals/discovered_urls and register URLs."""
        with self.lock:
            cursor = self.db.conn.cursor()
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
        for related_id, parent_url in rows:
            if not parent_url:
                continue
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

    def _probe_new_ids(self, base_url, limit=100, lookahead=500):
        """Probe for new IDs starting from the max ID in database (last resort)."""
        max_id = self.db.get_max_id()
        try:
            max_id_int = int(max_id)
        except (ValueError, TypeError):
            max_id_int = 0

        added = 0
        parsed = urlparse(base_url)

        for i in range(1, lookahead + 1):
            if added >= limit:
                break

            probe_id = str(max_id_int + i)
            with self.lock:
                if probe_id in self.visited_ids or probe_id in self.pending_ids:
                    continue

            query = parse_qs(parsed.query)
            query['i'] = [probe_id]
            new_query = urlencode(query, doseq=True)
            new_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

            with self.lock:
                if probe_id not in self.pending_ids:
                    self.pending_ids.add(probe_id)
                    self.queue.put((probe_id, new_url))
                    added += 1

        if added > 0:
            print(f"Probing {added} new IDs starting from {max_id_int + 1}...")
        return added

    def crawl(self, start_url, limit=100):
        """Crawl with pending-DB priority; probe only as last resort."""
        parsed_url = urlparse(start_url)
        start_id = parse_qs(parsed_url.query).get('i', [None])[0]
        count = 0

        # 1) Highest priority: work already known in discovered_urls
        self._seed_pending_from_db(limit=limit)

        # 2) Discover orphan related_ids from relationships
        if self.queue.qsize() < limit:
            self._discover_from_db(limit=limit)
            self._seed_pending_from_db(limit=limit - self.queue.qsize())

        # 3) Start URL: scrape if new, else pull neighbors
        if start_id and start_id not in self.visited_ids:
            first_res = self._scrape_one(start_url)
            if first_res:
                data, rels = first_res
                count = 1
                print(f"Crawled {data['id']}: {start_url} ({count}/{limit})")
                for rel in rels:
                    self.db.add_discovered_url(rel["related_id"], rel["url"])
                    with self.lock:
                        if rel["related_id"] not in self.visited_ids and rel["related_id"] not in self.pending_ids:
                            self.pending_ids.add(rel["related_id"])
                            self.queue.put((rel["related_id"], rel["url"]))
        elif start_id in self.visited_ids:
            print(f"Start node {start_id} already visited. Seeding from pending DB / neighbors.")
            try:
                response = self.session.get(start_url, timeout=30)
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
            except Exception as e:
                print(f"Error re-scraping {start_url} for neighbors: {e}")

        # 4) Process known work
        if count < limit:
            count += self._process_queue(limit=limit - count)

        # 5) Last resort only: probe new IDs if still under limit and queue empty
        if count < limit and self.queue.qsize() == 0:
            remaining = limit - count
            self._probe_new_ids(start_url, limit=min(remaining, 200), lookahead=min(remaining, 200))
            if self.queue.qsize() > 0:
                count += self._process_queue(limit=limit - count)

        print(f"Crawl finished. Total individuals scraped in this session: {count}")
