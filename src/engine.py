import requests
from src.scraper import Scraper

class ScraperEngine:
    def __init__(self, db_helper):
        self.db = db_helper
        self.scraper = Scraper()

    def scrape_person(self, url):
        response = requests.get(url)
        response.raise_for_status()
        
        html_content = response.text
        
        # Extract biographical data
        data = self.scraper.extract_biographical_data(html_content, url)
        if data and data.get("id"):
            self.db.add_individual(data)
            
            # Extract relationships
            rels = self.scraper.extract_relationships(html_content, data["id"])
            for rel in rels:
                self.db.add_relationship(rel["person_id"], rel["related_id"], rel["type"])
                
        return data
