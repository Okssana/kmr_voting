import re
import pandas as pd


# Define a function for case-insensitive replacement
def replace_company_names(text):
    if pd.isna(text):
        return text
    
    # Dictionary of replacements (lowercase key to replacement)
    replacements = {
        'товариство з обмеженою відповідальністю': 'ТОВ',
        'товариству з обмеженою відповідальністю': 'ТОВ',
        'товариства з обмеженою відповідальністю': 'ТОВ',
        'товариство з додатковою відповідальністю': 'ТДВ',
        'товариству з додатковою відповідальністю': 'ТДВ',
        'приватне підприємство': 'ПП',
        'приватному підприємству': 'ПП',
        'приватне акціонерне товариство': 'ПАТ',
        'приватному акціонерному товариству': 'ПАТ',
        'комунальне підприємство': 'КП',
        'комунальному підприємству': 'КП',
        'ТОВАРИСТВУ З ОБМЕЖЕНОЮ ВІДПОВІДАЛЬНИСТЮ': 'ТОВ',
        'ТОВАРИСТВУ З ОБМЕЖЕНОЮ З ОБМЕЖЕНОЮ ВІДПОВІДАЛЬНІСТЮ': 'ТОВ',
        'ТОВАРИСТВУ З ОБМЕЖЕНОЮВІДПОВІДАЛЬНІСТЮ': 'ТОВ',
        'приватному акціонерному підприємству': 'ПАТ'
    }
    
    result = text
    for old_text, new_text in replacements.items():
        # Case insensitive replacement using regex
        pattern = re.compile(re.escape(old_text), re.IGNORECASE)
        result = pattern.sub(new_text, result)
    
    return result



def extract_company(text):
    # Pattern for various types of enterprises
    patterns = [
        # Private enterprises
        r'(ПРИВАТНОМУ ПІДПРИЄМСТВУ|ПП)\s+[«"]([А-ЯІЇЄҐ\w\s\-]+)[»"]',
        # Private joint-stock enterprises
        r'приватному акціонерному підприємству\s+[«"]([А-ЯІЇЄҐ\w\s\-]+)[»"]',
        # Municipal enterprises with name
        r'комунальному підприємству\s+[А-ЯІЇЄҐ\w\s]+?\s*[«"]([А-ЯІЇЄҐ\w\s\-]+)[»"](\s*\([А-ЯІЇЄҐ\w\s]+\))?',
        # Kyiv municipal associations
        r'Київському комунальному об\'єднанню\s+[«"]([А-ЯІЇЄҐ\w\s\-]+)[»"]',
        # Companies with limited liability
        r'товариству з обмеженою відповідальністю\s+[«"]([А-ЯІЇЄҐ\w\s\-]+)[»"]',
        # Generic pattern for any company with a name in quotes
        r'(ТОВАРИСТВУ З|ТОВАРИСТВА З|товариству з)\s+[А-ЯІЇЄҐа-яіїєґ\s]+\s+[«"]([А-ЯІЇЄҐ\w\s\-]+)[»"]',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Return the entire matched text
            return match.group(0)
    
    return None



def extract_address(text):
    # Normalize apostrophes
    text = text.replace("'", "'")
    
    # Special case for abbreviated first names with initial followed by period
    abbreviated_name_pattern = r'на вул\. ([А-ЯІЇЄҐа-яіїєґ]\.\s+[А-ЯІЇЄҐа-яіїєґ\'\-]+(?:-[А-ЯІЇЄҐа-яіїєґ\'\-]+)?),\s*(\d+(?:[-/][а-я\d]+)?)'
    match = re.search(abbreviated_name_pattern, text)
    if match:
        return f"на вул. {match.group(1)}, {match.group(2)}"
    
    # Handle specific apostrophe cases with both types of apostrophes
    apostrophe_streets = [
        ("Лук'янівській", r'на вул\. Лук[\'\']янівській,\s*(\d+(?:[-/][а-я\d]+)?)'),
        ("В'ячеслава", r'на вул\. В[\'\']ячеслава\s+([А-ЯІЇЄҐа-яіїєґ]+),\s*(\d+(?:[-/][а-я\d]+)?)'),
        # вулиці Сім’ї Хохлових
        ("Сім'ї Хохлових", r'на вул\. Сім[\'\']ї Хохлових,\s*(\d+(?:[-/][а-я\d]+)?)'),
    ]
    
    for name, pattern in apostrophe_streets:
        if name.replace("'", "") in text.replace("'", ""):  # Normalize both for comparison
            match = re.search(pattern, text)
            if match:
                if "В'ячеслава" in name:
                    return f"на вул. {name} {match.group(1)}, {match.group(2)}"
                else:
                    return f"на вул. {name}, {match.group(1)}"
    
    # Extremely flexible approach for streets with apostrophes
    flexible_apostrophe_pattern = r'на вул\.\s+([А-ЯІЇЄҐа-яіїєґ]+[\'\'](?:[а-яіїєґ]+))'
    match = re.search(flexible_apostrophe_pattern, text)
    if match:
        # Look ahead for the full name and number
        start_idx = match.start()
        lookahead = text[start_idx:start_idx+100]
        full_pattern = r'на вул\.\s+([А-ЯІЇЄҐа-яіїєґ]+[\'\'][а-яіїєґ]+(?:\s+[А-ЯІЇЄҐа-яіїєґ]+)?),\s*(\d+(?:[-/][а-я\d]+)?)'
        better_match = re.search(full_pattern, lookahead)
        if better_match:
            return f"на вул. {better_match.group(1)}, {better_match.group(2)}"
    
    # Special case for streets with initial+surname format
    if re.search(r'на вул\. [А-ЯІЇЄҐ]\. ', text):
        match = re.search(r'на вул\. ([А-ЯІЇЄҐ]\. [А-ЯІЇЄҐа-яіїєґ\'\-]+(?:-[А-ЯІЇЄҐа-яіїєґ\'\-]+)?),\s*(\d+(?:[-/][а-я\d]+)?)', text)
        if match:
            return f"на вул. {match.group(1)}, {match.group(2)}"
    
    # Handle specific case with erroneous character in Воскресе?нському
    if "Воскресе" in text and "нському" in text:
        match = re.search(r'на просп\. Воскресе.?нському,\s*(\d+(?:[-/][а-я\d]+)?)', text)
        if match:
            return f"на просп. Воскресенському, {match.group(1)}"
    
    # Look for any street with abbreviated names (first initial + period)
    if re.search(r'вул\. [А-ЯІЇЄҐ]\.', text):
        # Try to capture the full street name
        match = re.search(r'(вул\. [А-ЯІЇЄҐ]\.[^,]+),\s*(\d+(?:[-/][а-я\d]+)?)', text)
        if match:
            # Clean up any trailing district info
            street_name = match.group(1)
            if ' у ' in street_name:
                street_name = street_name.split(' у ')[0].strip()
            return f"{street_name}, {match.group(2)}"
    
    # General pattern for any street address with number, handling apostrophes
    street_with_number = r'на вул\.\s+([^,]+),\s*(\d+(?:[-/][а-я\d]+)?)'
    match = re.search(street_with_number, text)
    if match:
        # Clean up the street name and handle any special characters
        street_name = match.group(1).strip()
        if ' у ' in street_name:
            street_name = street_name.split(' у ')[0].strip()
        return f"на вул. {street_name}, {match.group(2)}"
    
    # General avenue pattern for 2-word and 3-word avenue names with building number
    # Also allows for any non-letter characters between letters to handle typos/special characters
    avenue_pattern = r'на просп\. ([А-ЯІЇЄҐа-яіїєґ]+(?:[^,\.\(\)\d]*[А-ЯІЇЄҐа-яіїєґ]+){1,2}),\s*(\d+(?:[-/][а-я\d]+)?)'
    match = re.search(avenue_pattern, text)
    if match:
        # Clean up any special characters
        clean_name = re.sub(r'[^\w\s\'\-]', '', match.group(1))
        return f"на просп. {clean_name}, {match.group(2)}"
    
    # Handle cases where avenue name and number are inverted (Бандери Степана)
    inverted_avenue_pattern = r'на просп\. ([А-ЯІЇЄҐа-яіїєґ]+\s+[А-ЯІЇЄҐа-яіїєґ]+),\s*(\d+(?:[-/][а-я\d]+)?)'
    match = re.search(inverted_avenue_pattern, text)
    if match:
        # Clean up any special characters
        clean_name = re.sub(r'[^\w\s\'\-]', '', match.group(1))
        return f"на просп. {clean_name}, {match.group(2)}"
    
    # First try specific name patterns for avenues that often get truncated
    avenue_names = [
        # Standard patterns with name first
        ('Академіка Глушкова', r'на просп\. Академіка Глушкова,\s*(\d+(?:[-/][а-я\d]+)?)'),
        ('Бандери Степана', r'на просп\. Бандери Степана,\s*(\d+(?:[-/][а-я\d]+)?)'),
        ('Степана Бандери', r'на просп\. Степана Бандери,\s*(\d+(?:[-/][а-я\d]+)?)'),
        ('Перемоги', r'на просп\. Перемоги,\s*(\d+(?:[-/][а-я\d]+)?)'),
        ('Павла Тичини', r'на просп\. Павла Тичини,\s*(\d+(?:[-/][а-я\d]+)?)'),
        ('Миколи Бажана', r'на просп\. Миколи Бажана,\s*(\d+(?:[-/][а-я\d]+)?)'),
        ('Броварському', r'на просп\. Броварському,\s*(\d+(?:[-/][а-я\d]+)?)'),
        ('Петра Григоренка', r'на просп\. Петра Григоренка,\s*(\d+(?:[-/][а-я\d]+)?)'),
        ('Оболонському', r'на просп\. Оболонському,\s*(\d+(?:[-/][а-я\d]+)?)'),
        ('Шухевича Романа', r'на просп\. Шухевича Романа,\s*(\d+(?:[-/][а-я\d]+)?)'),
        ('Червоної Калини', r'на просп\. Червоної Калини,\s*(\d+(?:[-/][а-я\d]+)?)'),
        ('Голосіївському', r'на просп\. Голосіївському,\s*(\d+(?:[-/][а-я\d]+)?)'),
        ('Леся Курбаса', r'на просп\. Леся Курбаса,\s*(\d+(?:[-/][а-я\d]+)?)'),
        ('Академіка Палладіна', r'на просп\. Академіка Палладіна,\s*(\d+(?:[-/][а-я\d]+)?)'),
        ('Берестейському', r'на просп\. Берестейському,\s*(\d+(?:[-/][а-я\d]+)?)'),
        ('Володимира Маяковського', r'на просп\. Володимира Маяковського,\s*(\d+(?:[-/][а-я\d]+)?)'),
        ('Георгія Гонгадзе', r'на просп\. Георгія Гонгадзе,\s*(\d+(?:[-/][а-я\d]+)?)'),
        ('Лісовому', r'на просп\. Лісовому,\s*(\d+(?:[-/][а-я\d]+)?)')
    ]
    
    # Check for specific avenue names - with allowance for unexpected characters
    for name, pattern in avenue_names:
        # Create a more flexible pattern that allows special chars between words
        flexible_name = name.replace(' ', '[^,\\d\\(\\)]*')
        if re.search(f"{flexible_name}", text, re.IGNORECASE):
            # Try the original pattern first
            match = re.search(pattern, text)
            if match:
                return f"на просп. {name}, {match.group(1)}"
            
            # If not found, try a more flexible pattern that allows special chars
            flexible_pattern = pattern.replace(name, flexible_name)
            match = re.search(flexible_pattern, text)
            if match:
                return f"на просп. {name}, {match.group(1)}"
    
    # Specific multi-street patterns
    specific_patterns = [
        # Between street and avenue
        (r'між\s+вулицею\s+([А-ЯІЇЄҐа-яіїєґ\'\-]+(?:-[А-ЯІЇЄҐа-яіїєґ\'\-]+)?)\s+та\s+проспектом\s+([А-ЯІЇЄҐа-яіїєґ\'\-]+)', 
         lambda m: f"між вулицею {m.group(1)} та проспектом {m.group(2)}"),
        
        # Within streets boundaries
        (r'в\s+межах\s+вулиць\s+([А-ЯІЇЄҐа-яіїєґ\'\s\-]+),\s+([А-ЯІЇЄҐа-яіїєґ\'\s\-]+)(?:\s+\([А-ЯІЇЄҐа-яіїєґ\'\s\-]+\))(?:\s+та\s+(?:західної|північної|східної|південної)\s+межі\s+\w+)?',
         lambda m: f"в межах вулиць {m.group(1)}, {m.group(2)}"),
        
        # Three streets in area
        (r'в\s+межах\s+вулиць\s+([А-ЯІЇЄҐа-яіїєґ\'\s\-]+),\s+([А-ЯІЇЄҐа-яіїєґ\'\s\-]+)\s+та\s+([А-ЯІЇЄҐа-яіїєґ\'\s\-]+)',
         lambda m: f"в межах вулиць {m.group(1)}, {m.group(2)} та {m.group(3)}"),
        
        # Corner of streets
        (r'на\s+розі\s+вулиць\s+([А-ЯІЇЄҐа-яіїєґ\'\s\-]+)\s+та\s+([А-ЯІЇЄҐа-яіїєґ\'\s\-]+)',
         lambda m: f"на розі вулиць {m.group(1)} та {m.group(2)}"),
        
        # Multiple prospekts
        (r'на просп\. ([А-ЯІЇЄҐа-яіїєґ\'\s\-]+),\s*([\d,\s]+)\s+та просп\. ([А-ЯІЇЄҐа-яіїєґ\'\s\-]+),\s*([\d,\s]+)',
         lambda m: f"на просп. {m.group(1)}, {m.group(2)} та просп. {m.group(3)}, {m.group(4)}")
    ]
    
    # Try specific multi-street patterns
    for pattern, formatter in specific_patterns:
        match = re.search(pattern, text)
        if match:
            return formatter(match)
    
    # Special case for Космодем'янської with curly apostrophe
    if "Космодем" in text:
        # Find the street name without relying on regex apostrophe matching
        start_idx = text.find("вулиці Зої Космодем")
        if start_idx >= 0:
            # Look for "янської" within a reasonable distance
            end_idx = text.find("янської", start_idx)
            if end_idx >= 0 and end_idx - start_idx < 30:  # Within 30 chars to avoid false matches
                return text[start_idx:end_idx+8]  # Include "янської"
    
    # Handle renamed streets
    rename_patterns = [
        r'перейменування\s+(вулиц[іея]\s+[А-ЯІЇЄҐа-яіїєґ\'\s\-]+)(?:\s+[уУвВ])',
        r'назви\s+(вулиц[іея]\s+[А-ЯІЇЄҐа-яіїєґ\'\s\-]+)(?:\s+[уУвВ])'
    ]
    
    for pattern in rename_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    
    # Try a general approach for any avenue by looking for text between "на просп." and a comma
    prosp_flexible = r'на просп\.\s+([^,]+),\s*(\d+(?:[-/][а-я\d]+)?)'
    match = re.search(prosp_flexible, text)
    if match:
        # Clean up any special characters in the avenue name
        clean_name = re.sub(r'[^\w\s\'\-]', '', match.group(1))
        return f"на просп. {clean_name}, {match.group(2)}"
    
    # Generic patterns as fallback
    fallback_patterns = [
        # Generic avenue pattern
        r'на просп\. ([А-ЯІЇЄҐа-яіїєґ\'\s\-]+)',
        
        # Generic street pattern
        r'на вул\. ([А-ЯІЇЄҐа-яіїєґ\'\s\-]+)',
        
        # Generic вулиці pattern
        r'(вулиц[іея]\s+[А-ЯІЇЄҐа-яіїєґ\'\s\-]+)'
    ]
    
    for pattern in fallback_patterns:
        match = re.search(pattern, text)
        if match:
            full_match = match.group(0)
            # Clean up if needed
            if ' у ' in full_match:
                full_match = full_match.split(' у ')[0].strip()
            if ' в ' in full_match:
                full_match = full_match.split(' в ')[0].strip()
            return full_match
    
    return None


# Expanded district mapping with all variations
district_mapping = {
    # Голосіївський variations
    'Голосіївському': 'Голосіївський',
    'Голосiївському': 'Голосіївський',  # with i instead of і
    'Голосіївських': 'Голосіївський',
    'Голосіївської': 'Голосіївський',
    
    # Дарницький variations
    'Дарницькому': 'Дарницький',
    'Дарницьких': 'Дарницький',
    'Дарницької': 'Дарницький',
    
    # Деснянський variations
    'Деснянському': 'Деснянський',
    'Деснянських': 'Деснянський',
    'Деснянської': 'Деснянський',
    
    # Дніпровський variations
    'Дніпровському': 'Дніпровський',
    'Дніпровських': 'Дніпровський',
    'Дніпровської': 'Дніпровський',
    
    # Оболонський variations
    'Оболонському': 'Оболонський',
    'Оболонських': 'Оболонський',
    'Оболонської': 'Оболонський',
    
    # Печерський variations
    'Печерському': 'Печерський',
    'Печерських': 'Печерський',
    'Печерської': 'Печерський',
    
    # Подільський variations
    'Подільському': 'Подільський',
    'Подільських': 'Подільський',
    'Подільської': 'Подільський',
    
    # Святошинський variations
    'Святошинському': 'Святошинський',
    'Святошинських': 'Святошинський',
    'Святошинської': 'Святошинський',
    
    # Солом'янський variations (with different apostrophe styles)
    # 'Солом\'янському': 'Солом\'янський',
    # 'Солом\'янському': 'Солом\'янський',
    # 'Соломянському': 'Солом\'янський',
    # 'Соломенському': 'Солом\'янський',
    # 'Солом\'янських': 'Солом\'янський',
    # 'Солом\'янських': 'Солом\'янський',
    # 'Соломянських': 'Солом\'янський',
    # 'Соломенських': 'Солом\'янський',
    # 'Солом\'янської': 'Солом\'янський',
    # 'Солом\'янської': 'Солом\'янський',
    # 'Соломянської': 'Солом\'янський',
    # 'Соломенської': 'Солом\'янський',

      # Солом'янський variations (with different apostrophe styles)
    'Солом\'янському': 'Солом\'янський',
    'Солом’янський': 'Солом\'янський',  # straight apostrophe variant
    'Солом`янському': 'Солом\'янський',  # with backtick apostrophe
    'Солом’янського ': 'Солом\'янський',  # straight apostrophe variant
    'Солом?янському ': 'Солом\'янський',  # with question mark apostrophe
    'Солом’янського': 'Солом\'янський',  # straight apostrophe variant
    'Солом’янського': 'Солом\'янський',  # straight apostrophe variant
    'Солом’янського': 'Солом\'янський',  # straight apostrophe variant
    'Солом’янському': 'Солом\'янський',  # straight apostrophe variant
    'Солом’янському': 'Солом\'янський',  # straight apostrophe variant
    'Солом\'янському': 'Солом\'янський',  # straight apostrophe variant
    'Соломянському': 'Солом\'янський',
    'Соломенському': 'Солом\'янський',
    'Солом\'янських': 'Солом\'янський',
    'Солом\'янських': 'Солом\'янський',
    'Соломянських': 'Солом\'янський',
    'Соломенських': 'Солом\'янський',
    'Солом\'янської': 'Солом\'янський',
    'Солом\'янської': 'Солом\'янський',
    'Соломянської': 'Солом\'янський',
    'Соломенської': 'Солом\'янський',
    
    # Шевченківський variations
    'Шевченківському': 'Шевченківський',
    'Шевченківських': 'Шевченківський',
    'Шевченківської': 'Шевченківський',
}


def extract_all_districts(text):
    """Extract all unique districts mentioned in the text"""
    if not isinstance(text, str):
        return []
        
    # Normalize apostrophes first
    normalized_text = text.replace("'", "'")
    
    districts_found = set()
    
    # Look for district patterns using the mapping
    for district_variant, district_name in district_mapping.items():
        pattern = rf'[уУвВ]\s+{re.escape(district_variant)}\s+район[іуах]?'
        matches = re.finditer(pattern, normalized_text, re.IGNORECASE)
        for match in matches:
            districts_found.add(district_name)
    
    return list(districts_found)

def extract_district(text):
    if not isinstance(text, str):
        return None
        
    # Normalize apostrophes first
    normalized_text = text.replace("'", "'")
    
    # Look for district patterns
    for district_suffix, district_name in district_mapping.items():
        pattern = rf'[уУвВ]\s+{district_suffix}\s+район[іуах]?'
        match = re.search(pattern, normalized_text, re.IGNORECASE)
        if match:
            return district_name
    
    # Handle variations of district names without "районі" suffix
    for district_suffix, district_name in district_mapping.items():
        # Remove "ському" ending to match base forms like "Дарницькому"
        base_form = district_suffix.replace('ському', '')
        pattern = rf'[уУвВ]\s+{base_form}[а-яіїєґ]*'
        match = re.search(pattern, normalized_text, re.IGNORECASE)
        if match:
            return district_name
    
    # Special case for Солом'янський with different spellings
    special_cases = [
        r'[уУвВ]\s+Солом\'?янськ[а-яіїєґ]*',
        r'[уУвВ]\s+Соломенськ[а-яіїєґ]*', 
        r'[уУвВ]\s+Соломянськ[а-яіїєґ]*'
    ]
    
    for pattern in special_cases:
        if re.search(pattern, normalized_text, re.IGNORECASE):
            return 'Солом\'янський'
    
    # Handle uppercase variants
    for district_suffix, district_name in district_mapping.items():
        pattern = rf'[УВ]\s+{district_suffix.upper()}'
        match = re.search(pattern, normalized_text)
        if match:
            return district_name
            
    return None

# Function to extract person
def extract_person(text):
    match = re.search(r'(громадянці|громадянину) ([А-ЯІЇЄҐ][а-яіїєґ]+\s[А-ЯІЇЄҐ][а-яіїєґ]+\s[А-ЯІЇЄҐ][а-яіїєґ]+)', text)
    return match.group(2) if match else None

# Function to extract date description
def extract_date_description(text):
    match = re.search(r'від\s([\d{2}\.\d{2}\.\d{4}].+?№\s\d{2}/\d{3}-\d{4}/ПР)', text)
    return match.group(0) if match else None


def extract_all_persons(text):
    """Extract all person mentions from the text"""
    if not isinstance(text, str):
        return None
    
    # Normalize apostrophes
    normalized_text = text.replace("'", "'")
    
    person_groups = []
    
    # Pattern 1: Single person after громадянці/громадянину/громадянином

    single_pattern = r'громадян(?:кою|ці|ину|ином|ина)\s+([А-ЯІЇЄҐ][а-яіїєґ\']+(?:\s+[А-ЯІЇЄҐ][а-яіїєґ\']+){2,})'
    single_matches = re.finditer(single_pattern, normalized_text, re.IGNORECASE)
    
    for match in single_matches:
        person_groups.append(match.group(1).strip())
    
    # Pattern 2: Multiple persons after громадянами/громадянками
    # This captures everything between the keyword and "земельної ділянки" and "земельних ділянок"

    multiple_pattern = r'громадян(?:ами|ам|ками)\s+([^.]+?)(?=\s+земельної\s+ділянки|\s+земельних\s+ділянок)'
    multiple_matches = re.finditer(multiple_pattern, normalized_text, re.IGNORECASE)
    
    for match in multiple_matches:
        person_group = match.group(1).strip()
        # Clean up any trailing punctuation
        person_group = re.sub(r'[,\s]+,', '', person_group)
        if person_group:
            person_groups.append(person_group)
    
    # Join all person groups with semicolon
    return '; '.join(person_groups) if person_groups else None


def extract_all_persons(text):
    """Extract all person mentions from the text"""
    if not isinstance(text, str):
        return None
    
    # Normalize apostrophes
    normalized_text = text.replace("'", "'")
    
    person_groups = []
    
    # Special Pattern: Handle "передачу громадянину/громадянам" cases
    transfer_single_pattern = r'передачу\s+громадянину\s+([А-ЯІЇЄҐ][а-яіїєґ\']+(?:\s+[А-ЯІЇЄҐ][а-яіїєґ\']+){2,})\s+у\s+приватну\s+власність'
    transfer_single_matches = re.finditer(transfer_single_pattern, normalized_text, re.IGNORECASE)
    
    for match in transfer_single_matches:
        person_groups.append(match.group(1).strip())
    
    transfer_multiple_pattern = r'передачу\s+громадянам\s+([^у]+?)\s+у\s+власність'
    transfer_multiple_matches = re.finditer(transfer_multiple_pattern, normalized_text, re.IGNORECASE)
    
    for match in transfer_multiple_matches:
        person_group = match.group(1).strip()
        # Clean up any trailing punctuation
        person_group = re.sub(r'[,\s]+$', '', person_group)
        if person_group:
            person_groups.append(person_group)
    
    # Pattern 1: Single person with full names - covers most cases
    single_pattern = r'громадян(?:кою|ці|ину|ином|ина|ки)\s+([А-ЯІЇЄҐ][а-яіїєґ\']+(?:\s+[А-ЯІЇЄҐ][а-яіїєґ\']+){2,})'
    single_matches = re.finditer(single_pattern, normalized_text, re.IGNORECASE)
    
    for match in single_matches:
        person_groups.append(match.group(1).strip())
    
    # Pattern 2: Single person with abbreviated names (e.g., "Каплуновській Т. І.")
    abbreviated_pattern = r'громадян(?:кою|ці|ину|ином|ина|ки)\s+([А-ЯІЇЄҐ][а-яіїєґ\']+\s+[А-ЯІЇЄҐ]\.\s*[А-ЯІЇЄҐ]\.)'
    abbreviated_matches = re.finditer(abbreviated_pattern, normalized_text, re.IGNORECASE)
    
    for match in abbreviated_matches:
        person_groups.append(match.group(1).strip())
    
    # Pattern 3: Multiple persons after громадянами/громадянах/громадянам
    multiple_pattern = r'громадян(?:ами|ам|ками|ах)\s+([^.]+?)(?=\s+земельної\s+ділянки|\s+земельних\s+ділянок|\s+у\s+власність|\s+у\s+приватну\s+власність|\s+для\s+ведення)'
    multiple_matches = re.finditer(multiple_pattern, normalized_text, re.IGNORECASE)
    
    for match in multiple_matches:
        person_group = match.group(1).strip()
        # Clean up any trailing punctuation
        person_group = re.sub(r'[,\s]+$', '', person_group)
        if person_group:
            person_groups.append(person_group)
    
    # Pattern 4: Genitive plural "громадян" (ownership cases)
    genitive_pattern = r'громадян\s+([^.]+?)(?=\s+для\s+будівництва|\s+земельної\s+ділянки|\s+земельних\s+ділянок)'
    genitive_matches = re.finditer(genitive_pattern, normalized_text, re.IGNORECASE)
    
    for match in genitive_matches:
        person_group = match.group(1).strip()
        # Clean up any trailing punctuation
        person_group = re.sub(r'[,\s]+$', '', person_group)
        if person_group:
            person_groups.append(person_group)
    
    # Join all person groups with semicolon
    return '; '.join(person_groups) if person_groups else None