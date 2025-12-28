import re
from pyluach.dates import HebrewDate, GregorianDate

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

def parse_hebrew_date(date_str):
    if not date_str:
        return None
    
    # Check if it's already a Gregorian year (numeric and 4 digits)
    if re.match(r'^\d{4}$', date_str):
        return {"year": int(date_str), "month": None, "day": None, "type": "gregorian"}

    # Try to parse as Hebrew date
    # Formats: 
    # 1. 'ט' בכסלו תרנ"ד'
    # 2. 'כסלו תרנ"ד'
    # 3. 'תרנ"ד'
    
    parts = date_str.split()
    
    day = None
    month = None
    year = None
    
    # Year is usually the last part
    if parts:
        year_str = parts[-1]
        year = gematria_to_int(year_str)
        if year < 1000:
            year += 5000
            
    # Month
    for part in parts:
        clean_part = part.replace('ב', '', 1) if part.startswith('ב') else part
        if clean_part in HEBREW_MONTHS:
            month = HEBREW_MONTHS[clean_part]
            break
        # Handle "אדר א'" etc.
        if part in ["א", "ב", "א'", "ב'"] and parts.index(part) > 0:
            prev_part = parts[parts.index(part) - 1]
            if "אדר" in prev_part:
                full_month = f"אדר {part}"
                if full_month in HEBREW_MONTHS:
                    month = HEBREW_MONTHS[full_month]

    # Day
    if len(parts) >= 3:
        day_str = parts[0]
        day = gematria_to_int(day_str)
        
    if year:
        return {"year": year, "month": month, "day": day, "type": "hebrew"}
    
    return None

def hebrew_to_civil(date_str):
    parsed = parse_hebrew_date(date_str)
    if not parsed:
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
            # Just month and year, return first of month or just month year?
            # For GEDCOM, partial dates are OK.
            # But conversion needs a day. Let's use 1st of month but maybe just return year/month
            hd = HebrewDate(parsed["year"], parsed["month"], 1)
            gd = hd.to_pydate()
            # GEDCOM format for month year: "MON YYYY"
            months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
            return f"{months[gd.month-1]} {gd.year}"
        else:
            # Just year
            # Hebrew year spans two Gregorian years.
            # e.g. 5784 is 2023-2024.
            # GEDCOM doesn't have a great way for this other than "ABT 2024" or "2023/24"
            # Let's return the Gregorian year that mostly overlaps or just a range.
            # 1 Tishrei 5784 is Sept 2023.
            hd = HebrewDate(parsed["year"], 7, 1)
            gd = hd.to_pydate()
            return str(gd.year)
    except Exception:
        return None
