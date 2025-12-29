import re

class NameParser:
    def __init__(self):
        # Comprehensive list of Hebrew titles and honorifics
        self.titles = [
            'הרבנית הצדקנית', 'הרבנית', 'הצדקנית', 'מרת', 'ע"ה',
            'הרה"ק', 'רבי', 'רבנו', 'הגדול', 'בעל התניא והשולחן ערוך', 'זצוקללה"ה',
            'זי"ע', 'הרה"צ', 'הרה"ג', 'כ"ק', 'אדמו"ר', 'האדמו"ר', 'הזקן'
        ]
        # Regex to remove titles, designed to be greedy and handle multiple titles
        self.title_regex = re.compile(r'\b(' + '|'.join(re.escape(t) for t in self.titles) + r')\b', re.IGNORECASE)

    def parse_name(self, full_name):
        # Clean the name from titles
        name = self.title_regex.sub('', full_name).strip()
        name = re.sub(r'\s{2,}', ' ', name)  # Replace multiple spaces with a single one

        # Handle last names in brackets, e.g., "רבקה ע"ה [סגל]"
        last_name_match = re.search(r'\[(.*?)\]', name)
        if last_name_match:
            last_name = last_name_match.group(1).strip()
            # Remove the bracketed part from the name
            name = name.replace(last_name_match.group(0), '').strip()
            first_name = name
            return {"first_name": first_name, "last_name": last_name}

        # Handle locational names like "שניאור זלמן מליאדי"
        locational_match = re.search(r'\s+מ(.*?)$', name)
        if locational_match:
            last_name = "מ" + locational_match.group(1).strip()
            first_name = name.replace(locational_match.group(0), '').strip()
            return {"first_name": first_name, "last_name": last_name}

        # General case: split by space
        parts = name.split()
        if len(parts) > 1:
            first_name = ' '.join(parts[:-1])
            last_name = parts[-1]
        else:
            first_name = name
            last_name = None

        return {"first_name": first_name, "last_name": last_name}
