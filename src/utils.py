import re
from pyluach.dates import HebrewDate, GregorianDate

def normalize_whitespace(text):
    if not text:
        return text
    return " ".join(text.split())

HEBREW_MONTHS = {
    "ניסן": 1,
    "אייר": 2,
    "סיון": 3,
    "תמוז": 4,
    "אב": 5,
    "אלול": 6,
    "תשרי": 7,
    "חשון": 8,
    "חשוון": 8,
    "כסלו": 9,
    "טבת": 10,
    "שבט": 11,
    "אדר": 12,
    "אדר א": 12,
    "אדר א'": 12,
    "אדר ב": 13,
    "אדר ב'": 13,
}

GEMATRIA_VALUES = {
    'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9,
    'י': 10, 'כ': 20, 'ל': 30, 'מ': 40, 'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90,
    'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400,
    'ך': 20, 'ם': 40, 'ן': 50, 'ף': 80, 'ץ': 90
}

def gematria_to_int(text):
    if not text:
        return 0
    # Remove non-Hebrew characters
    clean_text = "".join([c for c in text if c in GEMATRIA_VALUES])
    total = 0
    for char in clean_text:
        total += GEMATRIA_VALUES.get(char, 0)
    return total

def parse_hebrew_year(year_str):
    """
    Carefully parse a Hebrew year string.
    Handles the thousands prefix 'ה' correctly.
    """
    if not year_str:
        return None

    # Remove common non-year punctuation but keep Hebrew letters
    clean_year = "".join([c for c in year_str if c in GEMATRIA_VALUES])

    if not clean_year:
        return None

    # Check if it's likely a year (usually starts with 'ת')
    # If it starts with 'ה' and is followed by 'ת', the 'ה' is 5000.
    # Example: ה'תשל"ו -> ה (5) + תשל"ו (736).
    # If we just sum them, we get 741.
    # We should treat leading 'ה' as 5000 if it's followed by letters summing to 400-999.

    total = 0
    if len(clean_year) > 1 and clean_year[0] == 'ה':
        # Potential thousands prefix
        remainder = clean_year[1:]
        remainder_val = gematria_to_int(remainder)
        if remainder_val >= 400: # Years in our range start with 'ת' (400)
            return 5000 + remainder_val
        else:
            # Just sum it up normally
            return gematria_to_int(clean_year)
    else:
        total = gematria_to_int(clean_year)
        if 0 < total < 1000:
            return 5000 + total
        return total

def parse_hebrew_date(date_str):
    if not date_str:
        return None

    clean_date = normalize_whitespace(date_str).strip()
    if clean_date.lower() == "array":
        return None
    
    # Check if it's already a Gregorian year (numeric and 4 digits)
    if re.match(r'^\d{4}$', date_str.strip()):
        return {"year": int(date_str.strip()), "month": None, "day": None, "type": "gregorian"}

    # Replace special Hebrew quotes with standard ones for easier splitting if needed
    # but split() handles whitespace which is most important.
    # Normalize Hebrew punctuation
    normalized = date_str.replace('׳', "'").replace('״', '"')
    parts = normalized.split()
    
    day = None
    month = None
    year = None
    year_type = "hebrew"
    
    # Try to find a Gregorian year anywhere in the string
    for part in parts:
        if re.match(r'^\d{4}$', part):
            year = int(part)
            year_type = "gregorian"
            # If we found a Gregorian year, we might still want to parse the rest
            break

    # If no Gregorian year, look for Hebrew year
    if not year:
        # Years usually come last, but we might have extra words like "בעומר"
        # We need to find the part that looks like a year (starts with ת or ה'ת)
        for i in reversed(range(len(parts))):
            part = parts[i]
            clean_part = "".join([c for c in part if c in GEMATRIA_VALUES])
            
            # A Hebrew year in our context starts with 'ת' or is 'ה' followed by 'ת'
            # Also check if it's a month name - if so, it's NOT a year
            is_month = False
            for m_name in HEBREW_MONTHS:
                if m_name in part:
                    is_month = True
                    break

            if is_month:
                continue

            if clean_part.startswith('ת') or (len(clean_part) > 1 and clean_part.startswith('הת')):
                year = parse_hebrew_year(part)
                break

    # Month
    for i, part in enumerate(parts):
        clean_part = part.replace('ב', '', 1) if part.startswith('ב') else part

        # Remove punctuation for matching
        clean_part = clean_part.replace("'", "").replace('"', '')

        # Check for multi-part months like "אדר א'"
        if i + 1 < len(parts):
            next_part = parts[i+1].replace("'", "").replace('"', '')
            combined = f"{clean_part} {next_part}"
            if combined in HEBREW_MONTHS:
                month = HEBREW_MONTHS[combined]
                break

        if clean_part in HEBREW_MONTHS:
            month = HEBREW_MONTHS[clean_part]
            break

    # Day
    # Day is usually the first part if it's a full date
    if parts:
        first_part = parts[0]
        # Check if first part is a month - if so, day is probably missing
        first_clean = first_part.replace("'", "").replace('"', '')
        if first_clean not in HEBREW_MONTHS and first_clean.replace('ב', '', 1) not in HEBREW_MONTHS:
            # Check if it's numeric
            if first_part.isdigit():
                day_val = int(first_part)
            else:
                day_val = gematria_to_int(first_part)
            if 0 < day_val <= 31:
                day = day_val
        
    # Validation: If we have a day or month but no year, we shouldn't return a partial date
    # that might lead to an incorrect year being inferred (like 5170 from a month name)
    if year:
        return {"year": year, "month": month, "day": day, "type": year_type}
    
    return None

def hebrew_to_civil(date_str):
    parsed = parse_hebrew_date(date_str)
    if not parsed:
        return None
    
    # If year is missing, we don't calculate civil date
    if parsed.get("year") is None:
        return None

    if parsed["type"] == "gregorian":
        return str(parsed["year"])
        
    try:
        if parsed["day"] and parsed["month"]:
            # Check if it's a leap year and we have Adar
            # pyluach handles this in HebrewDate constructor
            hd = HebrewDate(parsed["year"], parsed["month"], parsed["day"])
            gd = hd.to_pydate()
            return gd.strftime("%d %b %Y")
        elif parsed["month"]:
            # Just month and year
            hd = HebrewDate(parsed["year"], parsed["month"], 1)
            gd = hd.to_pydate()
            # GEDCOM format for month year: "MON YYYY"
            months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
            return f"{months[gd.month-1]} {gd.year}"
        else:
            # Just year
            hd = HebrewDate(parsed["year"], 7, 1)
            gd = hd.to_pydate()
            return str(gd.year)
    except Exception:
        return None
