import os
import re
import json
from bs4 import BeautifulSoup

INPUT_DIR = './input/'
OUTPUT_FILE = 'owners/layout_data.json'

# Map for space_type schema enums
BEDROOM_ENUM = 'Bedroom'
FULL_BATH_ENUM = 'Full Bathroom'
HALF_BATH_ENUM = 'Half Bathroom / Powder Room'

# Helper to extract room counts from HTML

def extract_layout_from_html(html, property_id):
    soup = BeautifulSoup(html, 'html.parser')
    layouts = []
    # Find the table with bedroom/bathroom counts
    for row in soup.find_all('tr'):
        label = row.find('td', class_='label')
        value = row.find('td', class_='value')
        if not label or not value:
            continue
        label_text = label.get_text(strip=True).lower()
        value_text = value.get_text(strip=True)
        if 'bedroom' in label_text:
            try:
                n_bed = int(re.search(r'\d+', value_text).group())
                for i in range(n_bed):
                    layouts.append({
                        'request_identifier': property_id,
                        'source_http_request': {},
                        'space_type': BEDROOM_ENUM,
                        'flooring_material_type': None,
                        'size_square_feet': None,
                        'floor_level': None,
                        'has_windows': None,
                        'window_design_type': None,
                        'window_material_type': None,
                        'window_treatment_type': None,
                        'is_finished': True,
                        'furnished': None,
                        'paint_condition': None,
                        'flooring_wear': None,
                        'clutter_level': None,
                        'visible_damage': None,
                        'countertop_material': None,
                        'cabinet_style': None,
                        'fixture_finish_quality': None,
                        'design_style': None,
                        'natural_light_quality': None,
                        'decor_elements': None,
                        'pool_type': None,
                        'pool_equipment': None,
                        'spa_type': None,
                        'safety_features': None,
                        'view_type': None,
                        'lighting_features': None,
                        'condition_issues': None,
                        'is_exterior': False,
                        'pool_condition': None,
                        'pool_surface_type': None,
                        'pool_water_quality': None
                    })
            except:
                pass
        if 'bath' in label_text and 'half' not in label_text:
            try:
                n_full = int(re.search(r'\d+', value_text).group())
                for i in range(n_full):
                    layouts.append({
                        'request_identifier': property_id,
                        'source_http_request': {},
                        'space_type': FULL_BATH_ENUM,
                        'flooring_material_type': None,
                        'size_square_feet': None,
                        'floor_level': None,
                        'has_windows': None,
                        'window_design_type': None,
                        'window_material_type': None,
                        'window_treatment_type': None,
                        'is_finished': True,
                        'furnished': None,
                        'paint_condition': None,
                        'flooring_wear': None,
                        'clutter_level': None,
                        'visible_damage': None,
                        'countertop_material': None,
                        'cabinet_style': None,
                        'fixture_finish_quality': None,
                        'design_style': None,
                        'natural_light_quality': None,
                        'decor_elements': None,
                        'pool_type': None,
                        'pool_equipment': None,
                        'spa_type': None,
                        'safety_features': None,
                        'view_type': None,
                        'lighting_features': None,
                        'condition_issues': None,
                        'is_exterior': False,
                        'pool_condition': None,
                        'pool_surface_type': None,
                        'pool_water_quality': None
                    })
            except:
                pass
        if 'half bath' in label_text or 'half bath' in value_text.lower():
            try:
                n_half = int(re.search(r'\d+', value_text).group())
                for i in range(n_half):
                    layouts.append({
                        'request_identifier': property_id,
                        'source_http_request': {},
                        'space_type': HALF_BATH_ENUM,
                        'flooring_material_type': None,
                        'size_square_feet': None,
                        'floor_level': None,
                        'has_windows': None,
                        'window_design_type': None,
                        'window_material_type': None,
                        'window_treatment_type': None,
                        'is_finished': True,
                        'furnished': None,
                        'paint_condition': None,
                        'flooring_wear': None,
                        'clutter_level': None,
                        'visible_damage': None,
                        'countertop_material': None,
                        'cabinet_style': None,
                        'fixture_finish_quality': None,
                        'design_style': None,
                        'natural_light_quality': None,
                        'decor_elements': None,
                        'pool_type': None,
                        'pool_equipment': None,
                        'spa_type': None,
                        'safety_features': None,
                        'view_type': None,
                        'lighting_features': None,
                        'condition_issues': None,
                        'is_exterior': False,
                        'pool_condition': None,
                        'pool_surface_type': None,
                        'pool_water_quality': None
                    })
            except:
                pass
    return layouts

def main():
    os.makedirs('owners', exist_ok=True)
    data = {}
    for fname in os.listdir(INPUT_DIR):
        if not fname.endswith('.html'):
            continue
        property_id = fname.replace('.html', '')
        with open(os.path.join(INPUT_DIR, fname), 'r', encoding='utf-8') as f:
            html = f.read()
        layouts = extract_layout_from_html(html, property_id)
        data[f'property_{property_id}'] = {'layouts': layouts}
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

if __name__ == '__main__':
    main()
