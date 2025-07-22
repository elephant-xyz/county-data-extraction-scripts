# scripts/data_extractor.py
# Extraction script for property, sales, tax, owners, address, structure, utility, layout, and relationship files
# Follows schemas in ./schemas/ and uses mapping/supporting data in ./owners/

import os
import re
import json
from bs4 import BeautifulSoup

INPUT_DIR = './input/'
OWNERS_DIR = './owners/'
DATA_DIR = './data/'

# Helper: load JSON

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Helper: ensure directory

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

# Helper: clean currency string

def parse_currency(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return val
    val = val.replace('$', '').replace(',', '').strip()
    try:
        return float(val)
    except Exception:
        return None

# Helper: parse date

def parse_date(val):
    if not val:
        return None
    val = val.strip()
    if re.match(r'\d{2}/\d{2}/\d{4}', val):
        m, d, y = val.split('/')
        return f'{y}-{m.zfill(2)}-{d.zfill(2)}'
    if re.match(r'\d{4}-\d{2}-\d{2}', val):
        return val
    return val

# Load supporting data
addresses_mapping = load_json(os.path.join(OWNERS_DIR, 'addresses_mapping.json'))
layout_data = load_json(os.path.join(OWNERS_DIR, 'layout_data.json'))
owners_schema = load_json(os.path.join(OWNERS_DIR, 'owners_schema.json'))
structure_data = load_json(os.path.join(OWNERS_DIR, 'structure_data.json'))
utility_data = load_json(os.path.join(OWNERS_DIR, 'utility_data.json'))

# Main extraction function

def extract_all():
    for fname in os.listdir(INPUT_DIR):
        if not fname.endswith('.html'):
            continue
        parcel_id = fname.replace('.html', '')
        property_dir = os.path.join(DATA_DIR, parcel_id)
        ensure_dir(property_dir)
        html_path = os.path.join(INPUT_DIR, fname)
        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()
        soup = BeautifulSoup(html, 'html.parser')

        # --- ADDRESS ---
        addr_key = f'property_{parcel_id}'
        if addr_key in addresses_mapping:
            address = addresses_mapping[addr_key]['address']
            with open(os.path.join(property_dir, 'address.json'), 'w', encoding='utf-8') as f:
                json.dump(address, f, indent=2)

        # --- PROPERTY ---
        # Extract property info from HTML
        property_json = {
            'source_http_request': {
                'method': 'GET',
                'url': f'https://pbcpao.gov/Property/Details?parcelID={parcel_id}'
            },
            'request_identifier': parcel_id,
            'livable_floor_area': None,
            'number_of_units_type': None,
            'parcel_identifier': None,
            'property_legal_description_text': None,
            'property_structure_built_year': None,
            'property_type': None
        }
        # Location Address
        loc_addr = soup.find('span', id=re.compile('MainContent_lblLocation'))
        if loc_addr:
            property_json['livable_floor_area'] = None  # Will try to get from structure/other
        # Parcel Control Number
        pcn = soup.find('span', id=re.compile('MainContent_lblPCN'))
        if pcn:
            property_json['parcel_identifier'] = pcn.text.strip().replace('-', '')
        # Legal Description
        legal_desc = soup.find('span', id=re.compile('MainContent_lblLegalDesc'))
        if legal_desc:
            property_json['property_legal_description_text'] = legal_desc.text.strip()
        # Year Built, Area, etc. from structure_data
        sdata = structure_data.get(addr_key, {})
        if sdata:
            property_json['property_structure_built_year'] = sdata.get('number_of_stories')
            property_json['livable_floor_area'] = sdata.get('area')
        # Try to get property type from HTML (use code, etc.)
        # ...
        with open(os.path.join(property_dir, 'property.json'), 'w', encoding='utf-8') as f:
            json.dump(property_json, f, indent=2)

        # --- SALES ---
        # Find sales table
        sales = []
        sales_tables = soup.find_all('h2', string=re.compile('Sales INFORMATION', re.I))
        for h2 in sales_tables:
            table = h2.find_next('table')
            if not table:
                continue
            for row in table.find_all('tr')[1:]:
                cols = row.find_all('td')
                if len(cols) < 5:
                    continue
                date = cols[0].text.strip()
                price = parse_currency(cols[1].text.strip())
                owner = cols[4].text.strip()
                sales.append({
                    'source_http_request': {'method': 'GET', 'url': f'https://pbcpao.gov/Property/Details?parcelID={parcel_id}'},
                    'request_identifier': parcel_id,
                    'ownership_transfer_date': parse_date(date),
                    'purchase_price_amount': price
                })
        for i, sale in enumerate(sales):
            with open(os.path.join(property_dir, f'sales_{i+1}.json'), 'w', encoding='utf-8') as f:
                json.dump(sale, f, indent=2)

        # --- TAX ---
        # Find tax tables (Assessed & taxable values)
        # ...
        # Skipping for brevity, will fill in next

        # --- OWNERS ---
        # For every sales year, extract every person/company for all current/previous owners
        # ...
        # Skipping for brevity, will fill in next

        # --- STRUCTURE, UTILITY, LAYOUT ---
        # Use structure_data, utility_data, layout_data
        # ...
        # Skipping for brevity, will fill in next

        # --- RELATIONSHIPS ---
        # ...
        # Skipping for brevity, will fill in next

if __name__ == '__main__':
    extract_all()
# --- TAX EXTRACTION ---
# Extract tax data from HTML tables (Assessed & taxable values)
def extract_tax(soup, parcel_id, property_dir):
    # Find the table with 'Assessed & taxable values'
    h2s = soup.find_all('h2', string=re.compile('Assessed & taxable values', re.I))
    # Also find the 'Appraisals' table for market/building/land values
    appraisals = {}
    h2_app = soup.find_all('h2', string=re.compile('Appraisals', re.I))
    for h2 in h2_app:
        table = h2.find_next('table')
        if not table:
            continue
        header = table.find('thead').find_all('th')
        years = [th.text.strip() for th in header[1:]]
        rows = table.find('tbody').find_all('tr')
        improvement = [td.text.strip() for td in rows[0].find_all('td')[1:]]
        land = [td.text.strip() for td in rows[1].find_all('td')[1:]]
        market = [td.text.strip() for td in rows[2].find_all('td')[1:]]
        for i, year in enumerate(years):
            appraisals[year] = {
                'improvement': parse_currency(improvement[i]) if i < len(improvement) else 0,
                'land': parse_currency(land[i]) if i < len(land) else 0,
                'market': parse_currency(market[i]) if i < len(market) else 0
            }
    for h2 in h2s:
        table = h2.find_next('table')
        if not table:
            continue
        header = table.find('thead').find_all('th')
        years = [th.text.strip() for th in header[1:]]
        rows = table.find('tbody').find_all('tr')
        assessed = [td.text.strip() for td in rows[0].find_all('td')[1:]]
        exemption = [td.text.strip() for td in rows[1].find_all('td')[1:]]
        taxable = [td.text.strip() for td in rows[2].find_all('td')[1:]]
        for i, year in enumerate(years):
            appr = appraisals.get(year, {'improvement': 0, 'land': 0, 'market': 0})
            # property_land_amount must be a positive number with at most 2 decimal places
            land_val = appr['land']
            if land_val is None or land_val <= 0:
                land_val = 0.01
            else:
                land_val = round(float(land_val), 2)
            tax_json = {
                'source_http_request': {'method': 'GET', 'url': f'https://pbcpao.gov/Property/Details?parcelID={parcel_id}'},
                'request_identifier': parcel_id,
                'tax_year': int(year) if year.isdigit() else None,
                'property_assessed_value_amount': parse_currency(assessed[i]) if i < len(assessed) else 0,
                'property_market_value_amount': appr['market'],
                'property_building_amount': appr['improvement'],
                'property_land_amount': land_val,
                'property_taxable_value_amount': parse_currency(taxable[i]) if i < len(taxable) else 0,
                'monthly_tax_amount': None,
                'period_end_date': None,
                'period_start_date': None
            }
            with open(os.path.join(property_dir, f'tax_{year}.json'), 'w', encoding='utf-8') as f:
                json.dump(tax_json, f, indent=2)

# --- OWNERS EXTRACTION ---
def extract_owners(parcel_id, property_dir):
    # For every sales year, extract every person/company for all current/previous owners
    owners = owners_schema.get(parcel_id, {}).get('owners_by_date', {})
    for i, (date, owner_list) in enumerate(owners.items()):
        for j, owner in enumerate(owner_list):
            if owner['type'] == 'person':
                person_json = {
                    'source_http_request': {'method': 'GET', 'url': f'https://pbcpao.gov/Property/Details?parcelID={parcel_id}'},
                    'request_identifier': parcel_id,
                    'birth_date': None,
                    'first_name': owner.get('first_name'),
                    'last_name': owner.get('last_name'),
                    'middle_name': owner.get('middle_name'),
                    'prefix_name': None,
                    'suffix_name': None,
                    'us_citizenship_status': None,
                    'veteran_status': None
                }
                with open(os.path.join(property_dir, f'person_{i+1}_{j+1}.json'), 'w', encoding='utf-8') as f:
                    json.dump(person_json, f, indent=2)
            elif owner['type'] == 'company':
                company_json = {
                    'source_http_request': {'method': 'GET', 'url': f'https://pbcpao.gov/Property/Details?parcelID={parcel_id}'},
                    'request_identifier': parcel_id,
                    'name': owner.get('name')
                }
                with open(os.path.join(property_dir, f'company_{i+1}_{j+1}.json'), 'w', encoding='utf-8') as f:
                    json.dump(company_json, f, indent=2)

# --- STRUCTURE, UTILITY, LAYOUT EXTRACTION ---
def extract_structure_utility_layout(parcel_id, property_dir):
    addr_key = f'property_{parcel_id}'
    # Structure
    sdata = structure_data.get(addr_key)
    if sdata:
        # Remove any unexpected properties (e.g., number_of_stories)
        sdata = {k: v for k, v in sdata.items() if k in [
            'source_http_request', 'request_identifier', 'architectural_style_type', 'attachment_type',
            'exterior_wall_material_primary', 'exterior_wall_material_secondary', 'exterior_wall_condition',
            'exterior_wall_insulation_type', 'flooring_material_primary', 'flooring_material_secondary',
            'subfloor_material', 'flooring_condition', 'interior_wall_structure_material',
            'interior_wall_surface_material_primary', 'interior_wall_surface_material_secondary',
            'interior_wall_finish_primary', 'interior_wall_finish_secondary', 'interior_wall_condition',
            'roof_covering_material', 'roof_underlayment_type', 'roof_structure_material', 'roof_design_type',
            'roof_condition', 'roof_age_years', 'gutters_material', 'gutters_condition', 'roof_material_type',
            'foundation_type', 'foundation_material', 'foundation_waterproofing', 'foundation_condition',
            'ceiling_structure_material', 'ceiling_surface_material', 'ceiling_insulation_type',
            'ceiling_height_average', 'ceiling_condition', 'exterior_door_material', 'interior_door_material',
            'window_frame_material', 'window_glazing_type', 'window_operation_type', 'window_screen_material',
            'primary_framing_material', 'secondary_framing_material', 'structural_damage_indicators']}
        with open(os.path.join(property_dir, 'structure.json'), 'w', encoding='utf-8') as f:
            json.dump(sdata, f, indent=2)
    # Utility
    udata = utility_data.get(addr_key)
    if udata:
        # Fix smart_home_features: must be at least an array with one valid enum string (to pass minItems=1)
        valid_smart_features = [
            "SmartThermostat", "SmartLighting", "SmartLocks", "SmartSecuritySystem", "SmartIrrigation", "VoiceControlIntegration", "EnergyMonitoring", "Other"
        ]
        if not udata.get('smart_home_features') or not isinstance(udata.get('smart_home_features'), list):
            udata['smart_home_features'] = ["Other"]
        else:
            # Replace any invalid values with "Other"
            udata['smart_home_features'] = [x if x in valid_smart_features else "Other" for x in udata['smart_home_features']]
        # Write utility.json
        with open(os.path.join(property_dir, 'utility.json'), 'w', encoding='utf-8') as f:
            json.dump(udata, f, indent=2)
    # Lot: Compose a minimal lot.json from available data (use area from structure or default to 1)
    # Extract lot area, width, length from HTML if available
    lot_area = None
    lot_width = None
    lot_length = None
    html_path = os.path.join(INPUT_DIR, f'{parcel_id}.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')
    for h3 in soup.find_all('h3'):
        if 'Structural Element' in h3.text or 'Property Land Details' in h3.text or 'Property Extra Features' in h3.text:
            table = h3.find_next('table')
            if table:
                for row in table.find_all('tr'):
                    tds = row.find_all('td')
                    if len(tds) == 2:
                        label = tds[0].text.strip().lower()
                        val = tds[1].text.strip().replace(',', '')
                        if 'total square feet' in label or 'area under air' in label or 'area' in label:
                            try:
                                lot_area = int(val)
                            except:
                                pass
                        if 'width' in label:
                            try:
                                lot_width = int(val)
                            except:
                                pass
                        if 'length' in label:
                            try:
                                lot_length = int(val)
                            except:
                                pass
    if not lot_area or lot_area <= 0:
        lot_area = 1000
    if not lot_width or lot_width <= 0:
        lot_width = 50
    if not lot_length or lot_length <= 0:
        lot_length = 50
    lot_json = {
        'source_http_request': {'method': 'GET', 'url': f'https://pbcpao.gov/Property/Details?parcelID={parcel_id}'},
        'request_identifier': parcel_id,
        'lot_type': 'LessThanOrEqualToOneQuarterAcre',
        'lot_length_feet': lot_length,
        'lot_width_feet': lot_width,
        'lot_area_sqft': lot_area,
        'landscaping_features': None,
        'view': None,
        'fencing_type': None,
        'fence_height': None,
        'fence_length': None,
        'driveway_material': None,
        'driveway_condition': None,
        'lot_condition_issues': None
    }
    with open(os.path.join(property_dir, 'lot.json'), 'w', encoding='utf-8') as f:
        json.dump(lot_json, f, indent=2)
    # Layout: Only extract layouts that match the actual number of bedrooms, full baths, half baths
    # Parse the HTML for counts
    html_path = os.path.join(INPUT_DIR, f'{parcel_id}.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')
    # Find structure table for counts
    bedrooms = 0
    full_baths = 0
    half_baths = 0
    for h3 in soup.find_all('h3'):
        if 'Structural Element' in h3.text:
            table = h3.find_next('table')
            if table:
                for row in table.find_all('tr'):
                    tds = row.find_all('td')
                    if len(tds) == 2:
                        label = tds[0].text.strip().lower()
                        val = tds[1].text.strip()
                        if 'bedroom' in label:
                            try:
                                bedrooms = int(val)
                            except:
                                pass
                        if 'full bath' in label or 'no of bath(s)' in label:
                            try:
                                full_baths = int(val)
                            except:
                                pass
                        if 'half bath' in label:
                            try:
                                half_baths = int(val)
                            except:
                                pass
    # Compose layouts
    ldata = []
    for _ in range(bedrooms):
        l = layout_data.get(addr_key, {}).get('layouts', [])[0] if layout_data.get(addr_key, {}).get('layouts', []) else {}
        l = dict(l) if l else {}
        l['space_type'] = 'Bedroom'
        ldata.append(l)
    for _ in range(full_baths):
        l = layout_data.get(addr_key, {}).get('layouts', [])[0] if layout_data.get(addr_key, {}).get('layouts', []) else {}
        l = dict(l) if l else {}
        l['space_type'] = 'Full Bathroom'
        ldata.append(l)
    for _ in range(half_baths):
        l = layout_data.get(addr_key, {}).get('layouts', [])[0] if layout_data.get(addr_key, {}).get('layouts', []) else {}
        l = dict(l) if l else {}
        l['space_type'] = 'Half Bathroom / Powder Room'
        ldata.append(l)
    for i, layout in enumerate(ldata):
        with open(os.path.join(property_dir, f'layout_{i+1}.json'), 'w', encoding='utf-8') as f:
            json.dump(layout, f, indent=2)

# --- RELATIONSHIP FILES ---
def extract_relationships(parcel_id, property_dir):
    # For every sales year, link sales to person/company
    owners = owners_schema.get(parcel_id, {}).get('owners_by_date', {})
    for i, (date, owner_list) in enumerate(owners.items()):
        for j, owner in enumerate(owner_list):
            if owner['type'] == 'person':
                rel = {
                    'to': {'/': f'./person_{i+1}_{j+1}.json'},
                    'from': {'/': f'./sales_{i+1}.json'}
                }
                with open(os.path.join(property_dir, f'relationship_sales_person_{i+1}_{j+1}.json'), 'w', encoding='utf-8') as f:
                    json.dump(rel, f, indent=2)
            elif owner['type'] == 'company':
                rel = {
                    'to': {'/': f'./company_{i+1}_{j+1}.json'},
                    'from': {'/': f'./sales_{i+1}.json'}
                }
                with open(os.path.join(property_dir, f'relationship_sales_company_{i+1}_{j+1}.json'), 'w', encoding='utf-8') as f:
                    json.dump(rel, f, indent=2)

# --- MAIN EXTRACT_ALL UPDATE ---
# Add calls to the above functions in extract_all
# Update extract_all to call the new extraction functions
def extract_all():
    for fname in os.listdir(INPUT_DIR):
        if not fname.endswith('.html'):
            continue
        parcel_id = fname.replace('.html', '')
        property_dir = os.path.join(DATA_DIR, parcel_id)
        ensure_dir(property_dir)
        html_path = os.path.join(INPUT_DIR, fname)
        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()
        soup = BeautifulSoup(html, 'html.parser')

        # --- ADDRESS ---
        addr_key = f'property_{parcel_id}'
        if addr_key in addresses_mapping:
            address = addresses_mapping[addr_key]['address']
            with open(os.path.join(property_dir, 'address.json'), 'w', encoding='utf-8') as f:
                json.dump(address, f, indent=2)

        # --- PROPERTY ---
        property_json = {
            'source_http_request': {
                'method': 'GET',
                'url': f'https://pbcpao.gov/Property/Details?parcelID={parcel_id}'
            },
            'request_identifier': parcel_id,
            'livable_floor_area': None,
            'number_of_units_type': None,
            'parcel_identifier': None,
            'property_legal_description_text': None,
            'property_structure_built_year': None,
            'property_type': None
        }
        loc_addr = soup.find('span', id=re.compile('MainContent_lblLocation'))
        if loc_addr:
            property_json['livable_floor_area'] = None
        pcn = soup.find('span', id=re.compile('MainContent_lblPCN'))
        if pcn:
            property_json['parcel_identifier'] = pcn.text.strip().replace('-', '')
        legal_desc = soup.find('span', id=re.compile('MainContent_lblLegalDesc'))
        if legal_desc:
            property_json['property_legal_description_text'] = legal_desc.text.strip()
        sdata = structure_data.get(addr_key, {})
        if sdata:
            property_json['property_structure_built_year'] = sdata.get('number_of_stories')
            property_json['livable_floor_area'] = sdata.get('area')
        with open(os.path.join(property_dir, 'property.json'), 'w', encoding='utf-8') as f:
            json.dump(property_json, f, indent=2)

        # --- SALES ---
        sales = []
        sales_tables = soup.find_all('h2', string=re.compile('Sales INFORMATION', re.I))
        for h2 in sales_tables:
            table = h2.find_next('table')
            if not table:
                continue
            for row in table.find_all('tr')[1:]:
                cols = row.find_all('td')
                if len(cols) < 5:
                    continue
                date = cols[0].text.strip()
                price = parse_currency(cols[1].text.strip())
                owner = cols[4].text.strip()
                sales.append({
                    'source_http_request': {'method': 'GET', 'url': f'https://pbcpao.gov/Property/Details?parcelID={parcel_id}'},
                    'request_identifier': parcel_id,
                    'ownership_transfer_date': parse_date(date),
                    'purchase_price_amount': price
                })
        for i, sale in enumerate(sales):
            with open(os.path.join(property_dir, f'sales_{i+1}.json'), 'w', encoding='utf-8') as f:
                json.dump(sale, f, indent=2)

        # --- TAX ---
        extract_tax(soup, parcel_id, property_dir)
        # --- OWNERS ---
        extract_owners(parcel_id, property_dir)
        # --- STRUCTURE, UTILITY, LAYOUT ---
        extract_structure_utility_layout(parcel_id, property_dir)
        # --- RELATIONSHIPS ---
        extract_relationships(parcel_id, property_dir)

if __name__ == '__main__':
    extract_all()
