from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, parse_qs
from src.utils import hebrew_to_civil
from src.name_parser import NameParser

class Scraper:
    def __init__(self):
        self.name_parser = NameParser()

    def _get_soup(self, html_content):
        try:
            return BeautifulSoup(html_content, 'lxml')
        except Exception:
            return BeautifulSoup(html_content, 'html.parser')

    def extract_biographical_data(self, html_content, url):
        soup = self._get_soup(html_content)
        
        # Extract ID from URL query parameter 'i'
        parsed_url = urlparse(url)
        person_id = parse_qs(parsed_url.query).get('i', [None])[0]
        
        person_container = soup.find(class_='person')
        if not person_container:
            return None
            
        info_container = person_container.find(class_='info')
        if not info_container:
            return None

        name_elem = info_container.find('h2')
        name = name_elem.get_text(strip=True) if name_elem else ""
        
        # Detect gender using NameParser
        gender = self.name_parser.detect_gender(name) or "M" # Default to M if unknown

        parsed_name = self.name_parser.parse_name(name)

        data = {
            "id": person_id,
            "name": name,
            "first_name": parsed_name["first_name"],
            "last_name": parsed_name["last_name"],
            "prefix": parsed_name["prefix"],
            "suffix": parsed_name["suffix"],
            "birth_date": None,
            "birth_date_civil": None,
            "birth_place": None,
            "death_date": None,
            "death_date_civil": None,
            "death_place": None,
            "gender": gender,
            "url": url
        }
        
        # Extract dates and places from list items
        for li in info_container.find_all('li'):
            text = li.get_text(strip=True)
            if 'תאריך לידה' in text:
                data["birth_date"] = text.replace('תאריך לידה:', '').strip()
                data["birth_date_civil"] = hebrew_to_civil(data["birth_date"])
            elif 'מקום לידה' in text:
                data["birth_place"] = text.replace('מקום לידה:', '').strip()
            elif 'תאריך פטירה' in text:
                data["death_date"] = text.replace('תאריך פטירה:', '').strip()
                data["death_date_civil"] = hebrew_to_civil(data["death_date"])
            elif 'מקום פטירה' in text:
                data["death_place"] = text.replace('מקום פטירה:', '').strip()
                
        # Explicit gender detection from class overrides name detection
        classes = person_container.get('class', [])
        if "female" in classes:
             data["gender"] = "F"
        elif "male" in classes:
             data["gender"] = "M"

        return data

    def extract_relationships(self, html_content, person_id, base_url=None):
        from urllib.parse import urljoin
        soup = self._get_soup(html_content)
        relationships = []
        
        # Parents
        parents_container = soup.find(class_='parents')
        if parents_container:
            for parent_link in parents_container.find_all('a'):
                href = parent_link.get('href', '')
                full_url = urljoin(base_url, href) if base_url else href
                parsed_href = urlparse(full_url)
                related_id = parse_qs(parsed_href.query).get('i', [None])[0]
                if related_id:
                    rel_type = "father" if "male" in parent_link.get('class', []) else "mother"
                    relationships.append({"person_id": person_id, "related_id": related_id, "type": rel_type, "url": full_url})
            
        # Spouse
        person_elem = soup.find(class_='person')
        if person_elem:
            info_container = person_elem.find(class_='info')
            if info_container:
                spouse_elem = info_container.find('h4')
                if spouse_elem and spouse_elem.find('a'):
                    href = spouse_elem.find('a').get('href', '')
                    full_url = urljoin(base_url, href) if base_url else href
                    parsed_href = urlparse(full_url)
                    related_id = parse_qs(parsed_href.query).get('i', [None])[0]
                    if related_id:
                        relationships.append({"person_id": person_id, "related_id": related_id, "type": "spouse", "url": full_url})

        # Children
        kids_container = soup.find(class_='kids')
        if kids_container:
            for child_link in kids_container.find_all('a'):
                href = child_link.get('href', '')
                full_url = urljoin(base_url, href) if base_url else href
                parsed_href = urlparse(full_url)
                related_id = parse_qs(parsed_href.query).get('i', [None])[0]
                if related_id:
                    relationships.append({"person_id": person_id, "related_id": related_id, "type": "child", "url": full_url})
                
        return relationships
