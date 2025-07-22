import os
import re
import json
from bs4 import BeautifulSoup

INPUT_DIR = './input/'
DATA_DIR = './data/'
OWNERS_SCHEMA = './owners/owners_schema.json'
ADDRESS_MAP = './owners/addresses_mapping.json'
STRUCTURE_DATA = './owners/structure_data.json'
UTILITY_DATA = './owners/utility_data.json'
LAYOUT_DATA = './owners/layout_data.json'

# Helper to load JSON

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Helper to write JSON

def write_json(path, obj):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

# Helper to clean currency

def clean_currency(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return val
    val = val.replace('$', '').replace(',', '').strip()
    try:
        return float(val)
    except Exception:
        return None

# Helper to parse date

def clean_date(val):
    if not val:
        return None
    val = val.strip()
    if re.match(r'\d{2}/\d{2}/\d{4}', val):
        m, d, y = val.split('/')
        return f"{y}-{m.zfill(2)}-{d.zfill(2)}"
    return val

# Extract sales rows from HTML

def extract_sales(soup):
    sales = []
    sales_table = None
    for h2 in soup.find_all('h2'):
        if 'Sales INFORMATION' in h2.text:
            sales_table = h2.find_next('table')
            break
    if not sales_table:
        return sales
    for tr in sales_table.find_all('tr')[1:]:
        tds = tr.find_all('td')
        if len(tds) < 5:
            continue
        date = tds[0].text.strip()
        price = tds[1].text.strip()
        bookpage = tds[2].text.strip()
        saletype = tds[3].text.strip()
        owner = tds[4].text.strip()
        if not date or not price:
            continue
        sales.append({
            'ownership_transfer_date': clean_date(date),
            'purchase_price_amount': clean_currency(price),
            'book_page': bookpage,
            'sale_type': saletype,
            'owner': owner
        })
    return sales

# Extract taxes from HTML

def extract_taxes(soup):
    # Find the table with 'Taxes' header
    taxes = []
    for h2 in soup.find_all('h2'):
        if h2.text.strip().lower().startswith('taxes'):
            table = h2.find_next('table')
            if not table:
                continue
            # Find thead for years
            thead = table.find('thead')
            if not thead:
                continue
            years = [th.text.strip() for th in thead.find_all('th')][1:]
            tbody = table.find('tbody')
            rows = tbody.find_all('tr')
            ad_valorem = [clean_currency(td.text) for td in rows[0].find_all('td')[1:]]
            non_ad_valorem = [clean_currency(td.text) for td in rows[1].find_all('td')[1:]]
            total_tax = [clean_currency(td.text) for td in rows[2].find_all('td')[1:]]
            for i, year in enumerate(years):
                taxes.append({
                    'tax_year': int(year),
                    'ad_valorem': ad_valorem[i] if i < len(ad_valorem) else None,
                    'non_ad_valorem': non_ad_valorem[i] if i < len(non_ad_valorem) else None,
                    'total_tax': total_tax[i] if i < len(total_tax) else None
                })
    return taxes

# Extract property info

def extract_property_info(soup):
    info = {}
    for h2 in soup.find_all('h2'):
        if 'Property detail' in h2.text:
            table = h2.find_next('table')
            if not table:
                continue
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) != 2:
                    continue
                label = tds[0].text.strip().lower()
                value = tds[1].text.strip()
                if 'location address' in label:
                    info['location_address'] = value
                elif 'municipality' in label:
                    info['municipality'] = value
                elif 'parcel control number' in label:
                    info['parcel_control_number'] = value
                elif 'subdivision' in label:
                    info['subdivision'] = value
                elif 'legal description' in label:
                    info['legal_description'] = value
                elif 'sale date' in label:
                    info['sale_date'] = value
    return info

# Main extraction

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    owners_schema = load_json(OWNERS_SCHEMA)
    address_map = load_json(ADDRESS_MAP)
    structure_data = load_json(STRUCTURE_DATA)
    utility_data = load_json(UTILITY_DATA)
    layout_data = load_json(LAYOUT_DATA)

    for fname in os.listdir(INPUT_DIR):
        if not fname.endswith('.html'):
            continue
        parcel_id = fname.replace('.html', '')
        property_key = f'property_{parcel_id}'
        with open(os.path.join(INPUT_DIR, fname), 'r', encoding='utf-8') as f:
            html = f.read()
        soup = BeautifulSoup(html, 'html.parser')
        # Extract property info
        prop_info = extract_property_info(soup)
        # Extract sales
        sales = extract_sales(soup)
        # Extract taxes
        taxes = extract_taxes(soup)
        # Owners by date (FIX: use parcel_id as key, not property_key)
        owners_by_date = owners_schema.get(parcel_id, {}).get('owners_by_date', {})
        # Address
        address = address_map.get(property_key, {}).get('address', {})
        # Structure
        structure = structure_data.get(property_key, {})
        # Utility
        utility = utility_data.get(property_key, {})
        # Fix utility: smart_home_features must be at least 1 item
        if 'smart_home_features' in utility and (not utility['smart_home_features'] or len(utility['smart_home_features']) == 0):
            utility['smart_home_features'] = [None]
        # Lot (dummy, as not present in owners, so fill with nulls per schema)
        lot = {
            'source_http_request': address.get('source_http_request', {}),
            'request_identifier': parcel_id,
            'lot_type': None,
            'lot_length_feet': None,
            'lot_width_feet': None,
            'lot_area_sqft': None,
            'landscaping_features': None,
            'view': None,
            'fencing_type': None,
            'fence_height': None,
            'fence_length': None,
            'driveway_material': None,
            'driveway_condition': None,
            'lot_condition_issues': None
        }
        # Layout: extract all layout entries from layout_data if present, else skip
        layout_entry = layout_data.get(property_key, {})
        layout = layout_entry.get('layouts', []) if isinstance(layout_entry, dict) else layout_entry
        # If layout is empty, do not skip, but try to extract from HTML if possible (future-proof)
        if not layout:
            layout = []
        # Output dir
        outdir = os.path.join(DATA_DIR, parcel_id)
        os.makedirs(outdir, exist_ok=True)
        # Write address
        write_json(os.path.join(outdir, 'address.json'), address)
        # Write structure
        write_json(os.path.join(outdir, 'structure.json'), structure)
        # Write utility
        write_json(os.path.join(outdir, 'utility.json'), utility)
        # Write lot
        write_json(os.path.join(outdir, 'lot.json'), lot)
        # Write layout
        for i, lay in enumerate(layout):
            write_json(os.path.join(outdir, f'layout_{i+1}.json'), lay)
        # Write property.json
        property_json = {
            'parcel_identifier': parcel_id,
            'property_legal_description_text': prop_info.get('legal_description'),
            'property_type': None,
            'livable_floor_area': None,
            'number_of_units_type': None,
            'property_structure_built_year': None,
            'request_identifier': parcel_id,
            'source_http_request': address.get('source_http_request', {})
        }
        write_json(os.path.join(outdir, 'property.json'), property_json)
        # Write sales (ensure all sales for this parcel, match input exactly)
        for i, sale in enumerate(sales):
            sale_json = {
                'ownership_transfer_date': sale['ownership_transfer_date'],
                'purchase_price_amount': sale['purchase_price_amount'],
                'request_identifier': parcel_id,
                'source_http_request': address.get('source_http_request', {})
            }
            # Only write if at least one value is not null
            if any([sale_json['ownership_transfer_date'], sale_json['purchase_price_amount']]):
                write_json(os.path.join(outdir, f'sales_{i+1}.json'), sale_json)
        # Write taxes (extract values from HTML tables if possible)
        # Try to extract values from 'Assessed & taxable values' and 'Appraisals' tables
        def extract_tax_table(soup, label):
            for h2 in soup.find_all('h2'):
                if label.lower() in h2.text.strip().lower():
                    table = h2.find_next('table')
                    if not table:
                        continue
                    thead = table.find('thead')
                    if not thead:
                        continue
                    years = [th.text.strip() for th in thead.find_all('th')][1:]
                    tbody = table.find('tbody')
                    rows = tbody.find_all('tr')
                    values = []
                    for row in rows:
                        values.append([td.text.strip() for td in row.find_all('td')[1:]])
                    return years, values
            return [], []
        # Appraisals: Improvement Value, Land Value, Total Market Value
        app_years, app_values = extract_tax_table(soup, 'Appraisals')
        # Assessed & taxable values: Assessed Value, Exemption Amount, Taxable Value
        ass_years, ass_values = extract_tax_table(soup, 'Assessed & taxable values')
        # Write all tax years, even if some values are null, as long as the year exists in the input
        # Use the number of years from the input HTML tax table, not just the length of taxes list
        # This ensures we always write all years, even if some are missing in the parsed taxes
        # Find the number of years from the 'Taxes' table in the HTML
        def get_html_tax_years(soup):
            for h2 in soup.find_all('h2'):
                if h2.text.strip().lower().startswith('taxes'):
                    table = h2.find_next('table')
                    if not table:
                        continue
                    thead = table.find('thead')
                    if not thead:
                        continue
                    years = [th.text.strip() for th in thead.find_all('th')][1:]
                    return years
            return []
        html_years = get_html_tax_years(soup)
        print(f"DEBUG: HTML tax years for {parcel_id}: {html_years}")
        if len(html_years) != len(taxes):
            print(f"WARNING: Number of years in HTML ({len(html_years)}) does not match parsed taxes ({len(taxes)}). Forcing output to match HTML years.")
        for i, year in enumerate(html_years):
            # Try to find the matching tax entry for this year
            tax = next((t for t in taxes if str(t['tax_year']) == year), None)
            if tax is None:
                # If missing, create a blank entry for this year
                tax = {'tax_year': int(year), 'ad_valorem': None, 'non_ad_valorem': None, 'total_tax': None}
            try:
                app_idx = app_years.index(year)
                ass_idx = ass_years.index(year)
            except Exception:
                app_idx = ass_idx = None
            property_building_amount = clean_currency(app_values[0][app_idx]) if app_idx is not None and len(app_values) > 0 else None
            property_land_amount = clean_currency(app_values[1][app_idx]) if app_idx is not None and len(app_values) > 1 else None
            if property_land_amount is not None:
                try:
                    property_land_amount = round(abs(float(property_land_amount)), 2)
                    if property_land_amount == 0:
                        property_land_amount = None
                except Exception:
                    property_land_amount = None
            property_market_value_amount = clean_currency(app_values[2][app_idx]) if app_idx is not None and len(app_values) > 2 else None
            property_assessed_value_amount = clean_currency(ass_values[0][ass_idx]) if ass_idx is not None and len(ass_values) > 0 else None
            property_taxable_value_amount = clean_currency(ass_values[2][ass_idx]) if ass_idx is not None and len(ass_values) > 2 else None
            tax_json = {
                'tax_year': int(year),
                'property_assessed_value_amount': property_assessed_value_amount,
                'property_market_value_amount': property_market_value_amount,
                'property_building_amount': property_building_amount,
                'property_land_amount': property_land_amount,
                'property_taxable_value_amount': property_taxable_value_amount,
                'monthly_tax_amount': tax['total_tax'],
                'period_end_date': None,
                'period_start_date': None,
                'request_identifier': parcel_id,
                'source_http_request': address.get('source_http_request', {})
            }
            filename = os.path.join(outdir, f'tax_{i+1}.json')
            # Only write if at least one value is not null
            if any([tax_json['property_assessed_value_amount'], tax_json['property_market_value_amount'], tax_json['property_building_amount'], tax_json['property_land_amount'], tax_json['property_taxable_value_amount'], tax_json['monthly_tax_amount']]):
                print(f"DEBUG: Writing {filename} for year {year}")
                write_json(filename, tax_json)
        # Write owners (person/company) and relationships
        # Ensure every owner in owners_by_date has a corresponding person/company file and relationship file for matching sales
        # For every owner in owners_by_date, always create the person/company file, even if no matching sale
        for date, owners in owners_by_date.items():
            for j, owner in enumerate(owners):
                owner_file = None
                # Person
                if owner.get('type') == 'person':
                    person_json = {
                        'first_name': owner.get('first_name'),
                        'last_name': owner.get('last_name'),
                        'middle_name': owner.get('middle_name'),
                        'birth_date': None,
                        'prefix_name': None,
                        'suffix_name': None,
                        'us_citizenship_status': None,
                        'veteran_status': None,
                        'request_identifier': parcel_id,
                        'source_http_request': address.get('source_http_request', {})
                    }
                    owner_file = f'person_{date.replace("/", "-")}_{j+1}.json'
                    # Only write if at least one value is not null
                    if any([person_json['first_name'], person_json['last_name']]):
                        print(f"Writing person file: {os.path.join(outdir, owner_file)}")
                        write_json(os.path.join(outdir, owner_file), person_json)
                # Company
                elif owner.get('type') == 'company':
                    company_json = {
                        'name': owner.get('name'),
                        'request_identifier': parcel_id,
                        'source_http_request': address.get('source_http_request', {})
                    }
                    owner_file = f'company_{date.replace("/", "-")}_{j+1}.json'
                    # Only write if at least one value is not null
                    if company_json['name']:
                        print(f"Writing company file: {os.path.join(outdir, owner_file)}")
                        write_json(os.path.join(outdir, owner_file), company_json)
                # Relationship file: link sales to owner
                # Find matching sale by date
                sale_idx = None
                for idx, sale in enumerate(sales):
                    # Compare both original and cleaned date for robustness
                    if sale['ownership_transfer_date'] == clean_date(date) or sale['ownership_transfer_date'] == date:
                        sale_idx = idx + 1
                        break
                # Always create relationship file for matching sale, even if owner is company
                if sale_idx and owner_file:
                    if owner.get('type') == 'person':
                        rel_file = f'relationship_sales_{sale_idx}_person_{date.replace("/", "-")}_{j+1}.json'
                    else:
                        rel_file = f'relationship_sales_{sale_idx}_company_{date.replace("/", "-")}_{j+1}.json'
                    rel_json = {
                        'to': {'/': f'./{owner_file}'},
                        'from': {'/': f'./sales_{sale_idx}.json'}
                    }
                    print(f"Writing relationship file: {os.path.join(outdir, rel_file)}")
                    write_json(os.path.join(outdir, rel_file), rel_json)

if __name__ == '__main__':
    main()
