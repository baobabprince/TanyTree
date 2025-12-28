from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, parse_qs

class Scraper:
    def extract_biographical_data(self, html_content, url):
        soup = BeautifulSoup(html_content, 'html.parser')
        
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
        
        # Default gender detection based on name/titles
        gender = "M"
        female_indicators = ["הרבנית", "מרת", "ע\"ה", "בת"]
        # If the name contains any female indicator, and doesn't contain male indicators like "רבי" or "רב"
        # but "הרבנית" contains "רב", so we should be careful.
        if any(ind in name for ind in female_indicators):
            if not any(ind in name for ind in ["רבי", "הרה\"ק", "אדמו\"ר"]) or "הרבנית" in name:
                gender = "F"

        data = {
            "id": person_id,
            "name": name,
            "birth_date": None,
            "birth_place": None,
            "death_date": None,
            "death_place": None,
            "gender": gender,
            "url": url
        }
        
        # Extract dates and places from list items
        for li in info_container.find_all('li'):
            text = li.get_text(strip=True)
            if 'תאריך לידה' in text:
                data["birth_date"] = text.replace('תאריך לידה:', '').strip()
            elif 'מקום לידה' in text:
                data["birth_place"] = text.replace('מקום לידה:', '').strip()
            elif 'תאריך פטירה' in text:
                data["death_date"] = text.replace('תאריך פטירה:', '').strip()
            elif 'מקום פטירה' in text:
                data["death_place"] = text.replace('מקום פטירה:', '').strip()
                
        # Improved gender detection if class is present in related links
        # But for the main person, we might check the photo or other cues.
        # Let's check the container class again
        classes = person_container.get('class', [])
        if "female" in classes:
             data["gender"] = "F"
        elif "male" in classes:
             data["gender"] = "M"

        return data

    def extract_relationships(self, html_content, person_id, base_url=None):
        from urllib.parse import urljoin
        soup = BeautifulSoup(html_content, 'html.parser')
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
