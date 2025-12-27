from bs4 import BeautifulSoup
import re

class Scraper:
    def extract_biographical_data(self, html_content, url):
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract ID from URL
        # Example: http://example.com/person1 -> person1
        person_id = url.split('/')[-1] if url else None
        
        name_elem = soup.find(class_='person-name')
        birth_elem = soup.find(class_='birth-date')
        death_elem = soup.find(class_='death-date')
        gender_elem = soup.find(class_='gender')
        
        data = {
            "id": person_id,
            "name": name_elem.get_text(strip=True) if name_elem else None,
            "birth_date": birth_elem.get_text(strip=True) if birth_elem else None,
            "death_date": death_elem.get_text(strip=True) if death_elem else None,
            "gender": gender_elem.get_text(strip=True) if gender_elem else None,
            "url": url
        }
        
        return data
