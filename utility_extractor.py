import os
import re
import json
from bs4 import BeautifulSoup

INPUT_DIR = './input/'
OUTPUT_FILE = 'owners/utility_data.json'

def extract_utility_from_html(html, property_id):
    soup = BeautifulSoup(html, 'html.parser')
    utility = {
        'request_identifier': property_id,
        'source_http_request': {},
        'cooling_system_type': None,
        'heating_system_type': None,
        'public_utility_type': None,
        'sewer_type': None,
        'water_source_type': None,
        'plumbing_system_type': None,
        'plumbing_system_type_other_description': None,
        'electrical_panel_capacity': None,
        'electrical_wiring_type': None,
        'hvac_condensing_unit_present': None,
        'electrical_wiring_type_other_description': None,
        'solar_panel_present': False,
        'solar_panel_type': None,
        'solar_panel_type_other_description': None,
        'smart_home_features': [],
        'smart_home_features_other_description': None,
        'hvac_unit_condition': None,
        'solar_inverter_visible': False,
        'hvac_unit_issues': None
    }
    for row in soup.find_all('tr'):
        label = row.find('td', class_='label')
        value = row.find('td', class_='value')
        if not label or not value:
            continue
        label_text = label.get_text(strip=True).lower()
        value_text = value.get_text(strip=True)
        if 'air condition' in label_text or 'ac' in label_text:
            if 'central' in value_text.lower():
                utility['cooling_system_type'] = 'CentralAir'
            elif 'htg' in value_text.lower() or 'forced air' in value_text.lower():
                utility['cooling_system_type'] = 'CentralAir'
        if 'heat type' in label_text:
            if 'forced air' in value_text.lower():
                utility['heating_system_type'] = 'ElectricFurnace'
            elif 'electric' in value_text.lower():
                utility['heating_system_type'] = 'Electric'
        if 'heat fuel' in label_text:
            if 'electric' in value_text.lower():
                utility['heating_system_type'] = 'Electric'
        if 'sewer' in label_text:
            if 'public' in value_text.lower():
                utility['sewer_type'] = 'Public'
            elif 'septic' in value_text.lower():
                utility['sewer_type'] = 'Septic'
        if 'water' in label_text:
            if 'public' in value_text.lower():
                utility['water_source_type'] = 'Public'
            elif 'well' in value_text.lower():
                utility['water_source_type'] = 'Well'
        if 'plumbing' in label_text:
            if 'copper' in value_text.lower():
                utility['plumbing_system_type'] = 'Copper'
            elif 'pex' in value_text.lower():
                utility['plumbing_system_type'] = 'PEX'
            elif 'pvc' in value_text.lower():
                utility['plumbing_system_type'] = 'PVC'
    return utility

def main():
    os.makedirs('owners', exist_ok=True)
    data = {}
    for fname in os.listdir(INPUT_DIR):
        if not fname.endswith('.html'):
            continue
        property_id = fname.replace('.html', '')
        with open(os.path.join(INPUT_DIR, fname), 'r', encoding='utf-8') as f:
            html = f.read()
        utility = extract_utility_from_html(html, property_id)
        data[f'property_{property_id}'] = utility
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

if __name__ == '__main__':
    main()
