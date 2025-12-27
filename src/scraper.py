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

    def extract_relationships(self, html_content, person_id):
        soup = BeautifulSoup(html_content, 'html.parser')
        relationships = []
        
        rel_container = soup.find(class_='relationships')
        if not rel_container:
            return relationships
            
        # Father
        father_elem = rel_container.find(class_='father')
        if father_elem and father_elem.find('a'):
            related_id = father_elem.find('a')['href'].split('/')[-1]
            relationships.append({"person_id": person_id, "related_id": related_id, "type": "father"})
            
        # Mother
        mother_elem = rel_container.find(class_='mother')
        if mother_elem and mother_elem.find('a'):
            related_id = mother_elem.find('a')['href'].split('/')[-1]
            relationships.append({"person_id": person_id, "related_id": related_id, "type": "mother"})
            
        # Spouse
        spouse_elem = rel_container.find(class_='spouse')
        if spouse_elem and spouse_elem.find('a'):
            related_id = spouse_elem.find('a')['href'].split('/')[-1]
            relationships.append({"person_id": person_id, "related_id": related_id, "type": "spouse"})
            
        # Children
        children_elem = rel_container.find(class_='children')
        if children_elem:
            for child_link in children_elem.find_all('a'):
                related_id = child_link['href'].split('/')[-1]
                relationships.append({"person_id": person_id, "related_id": related_id, "type": "child"})
                
        return relationships
