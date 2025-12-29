import re

class NameParser:
    def __init__(self):
        # Hebrew titles and honorifics categorized by gender
        self.male_titles = [
            'הרה"ק', 'רבי', 'רבנו', 'הגדול', 'בעל התניא והשולחן ערוך', 'זצוקללה"ה',
            'זי"ע', 'הרה"צ', 'הרה"ג', 'כ"ק', 'אדמו"ר', 'האדמו"ר', 'הזקן', 'רבינו',
            'הרה"ח', 'החסיד', 'הרב', 'מרן', 'האמצעי'
        ]
        self.female_titles = [
            'הרבנית הצדקנית', 'הרבנית', 'הצדקנית', 'מרת', 'ע"ה'
        ]
        
        self.all_titles = list(set(self.male_titles + self.female_titles))
        
        # Regex to remove titles, designed to be greedy and handle multiple titles
        # Sorted by length descending to match longest titles first
        sorted_titles = sorted(self.all_titles, key=len, reverse=True)
        self.title_regex = re.compile(r'\b(' + '|'.join(re.escape(t) for t in sorted_titles) + r')\b', re.IGNORECASE)

    def detect_gender(self, full_name):
        """Detect gender based on titles and keywords in the name."""
        if not full_name:
            return None

        # Check for female indicators first
        female_indicators = [
            'הרבנית', 'מרת', 'ע"ה', 'הצדקנית', 'אמנו', 'בת ', 'אשת '
        ]
        
        if any(ind in full_name for ind in female_indicators):
            return "F"

        male_indicators = [
            'רבי', 'הרה"ק', 'אדמו"ר', 'הרה"צ', 'הרה"ג', 'הרה"ח', 'החסיד', 'הרב', 'מרן', 'אבינו', 'בן '
        ]
        if any(ind in full_name for ind in male_indicators):
            return "M"

        return None

    def parse_name(self, full_name):
        if not full_name:
            return {"first_name": "", "last_name": None, "prefix": None, "suffix": None}

        # Original name for reference
        name = full_name

        # Extract suffix description like "- האדמו\"ר מהורש\"א"
        suffix = None
        if " - " in name:
            name_part, suffix_part = name.split(" - ", 1)
            name = name_part.strip()
            suffix = suffix_part.strip()

        # Capture ALL honorifics
        found_titles = []
        matches = list(self.title_regex.finditer(name))
        for m in matches:
            found_titles.append(m.group(0))
        
        prefix = ' '.join(found_titles) if found_titles else None
        
        # Clean the name from ALL titles
        name = self.title_regex.sub('', name).strip()
        name = re.sub(r'\s{2,}', ' ', name)

        last_name = None
        last_name_match = re.search(r'\[(.*?)\]', name)
        if last_name_match:
            last_name = last_name_match.group(1).strip()
            name = name.replace(last_name_match.group(0), '').strip()
            first_name = name
            return {"first_name": first_name, "last_name": last_name, "prefix": prefix, "suffix": suffix}

        # Handle locational names like "שניאור זלמן מליאדי"
        locational_match = re.search(r'\s+מ(.*?)$', name)
        if locational_match:
            last_name = "מ" + locational_match.group(1).strip()
            first_name = name.replace(locational_match.group(0), '').strip()
            return {"first_name": first_name, "last_name": last_name, "prefix": prefix, "suffix": suffix}

        # Handle patronymics "בן/בת ..." as last name if it appears at the end
        patronymic_match = re.search(r'\s+(ב[ןת]\s+.*?)$', name)
        if patronymic_match:
            last_name = patronymic_match.group(1).strip()
            first_name = name.replace(patronymic_match.group(0), '').strip()
            return {"first_name": first_name, "last_name": last_name, "prefix": prefix, "suffix": suffix}

        # Special handling for known surnames or patterns
        parts = name.split()
        if len(parts) > 1:
            last_part = parts[-1]
            if last_part.endswith('סון') or last_part.endswith('סאן') or last_part in ['כהן', 'לוי', 'סגל']:
                first_name = ' '.join(parts[:-1])
                last_name = last_part
                return {"first_name": first_name, "last_name": last_name, "prefix": prefix, "suffix": suffix}
            
            double_names = ['שניאור זלמן', 'דובער', 'מנחם מענדל', 'יוסף יצחק', 'שלום דובער', 'דבורה לאה']
            full_stripped = ' '.join(parts)
            if any(dn in full_stripped for dn in double_names):
                 if full_stripped in double_names:
                      return {"first_name": full_stripped, "last_name": None, "prefix": prefix, "suffix": suffix}
            
            first_name = ' '.join(parts[:-1])
            last_name = parts[-1]
        else:
            first_name = name
            last_name = None

        return {"first_name": first_name, "last_name": last_name, "prefix": prefix, "suffix": suffix}
