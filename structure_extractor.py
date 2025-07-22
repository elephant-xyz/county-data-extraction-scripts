import os
import re
import json
from bs4 import BeautifulSoup

INPUT_DIR = './input/'
OUTPUT_FILE = 'owners/structure_data.json'

def extract_structure_from_html(html, property_id):
    soup = BeautifulSoup(html, 'html.parser')
    structure = {
        'request_identifier': property_id,
        'source_http_request': {},
        'architectural_style_type': None,
        'attachment_type': None,
        'exterior_wall_material_primary': None,
        'exterior_wall_material_secondary': None,
        'exterior_wall_condition': None,
        'exterior_wall_insulation_type': None,
        'flooring_material_primary': None,
        'flooring_material_secondary': None,
        'subfloor_material': None,
        'flooring_condition': None,
        'interior_wall_structure_material': None,
        'interior_wall_surface_material_primary': None,
        'interior_wall_surface_material_secondary': None,
        'interior_wall_finish_primary': None,
        'interior_wall_finish_secondary': None,
        'interior_wall_condition': None,
        'roof_covering_material': None,
        'roof_underlayment_type': None,
        'roof_structure_material': None,
        'roof_design_type': None,
        'roof_condition': None,
        'roof_age_years': None,
        'gutters_material': None,
        'gutters_condition': None,
        'roof_material_type': None,
        'foundation_type': None,
        'foundation_material': None,
        'foundation_waterproofing': None,
        'foundation_condition': None,
        'ceiling_structure_material': None,
        'ceiling_surface_material': None,
        'ceiling_insulation_type': None,
        'ceiling_height_average': None,
        'ceiling_condition': None,
        'exterior_door_material': None,
        'interior_door_material': None,
        'window_frame_material': None,
        'window_glazing_type': None,
        'window_operation_type': None,
        'window_screen_material': None,
        'primary_framing_material': None,
        'secondary_framing_material': None,
        'structural_damage_indicators': None
    }

    # Example: extract exterior wall material
    for row in soup.find_all('tr'):
        label = row.find('td', class_='label')
        value = row.find('td', class_='value')
        if not label or not value:
            continue
        label_text = label.get_text(strip=True).lower()
        value_text = value.get_text(strip=True)
        if 'exterior wall 1' in label_text:
            if 'stucco' in value_text.lower():
                structure['exterior_wall_material_primary'] = 'Stucco'
            elif 'cb' in value_text.lower() or 'concrete block' in value_text.lower():
                structure['exterior_wall_material_primary'] = 'Concrete Block'
            elif 'brick' in value_text.lower():
                structure['exterior_wall_material_primary'] = 'Brick'
        if 'roof structure' in label_text:
            if 'wood' in value_text.lower():
                structure['roof_structure_material'] = 'Wood Truss'
            elif 'steel' in value_text.lower():
                structure['roof_structure_material'] = 'Steel Truss'
            elif 'concrete' in value_text.lower():
                structure['roof_structure_material'] = 'Concrete Beam'
        if 'roof cover' in label_text:
            if 'tile' in value_text.lower():
                structure['roof_covering_material'] = 'Concrete Tile'
            elif 'shingle' in value_text.lower():
                structure['roof_covering_material'] = 'Architectural Asphalt Shingle'
            elif 'metal' in value_text.lower():
                structure['roof_covering_material'] = 'Metal Standing Seam'
        if 'stories' in label_text:
            try:
                structure['ceiling_height_average'] = int(value_text)
            except:
                pass
    return structure

def main():
    os.makedirs('owners', exist_ok=True)
    data = {}
    for fname in os.listdir(INPUT_DIR):
        if not fname.endswith('.html'):
            continue
        property_id = fname.replace('.html', '')
        with open(os.path.join(INPUT_DIR, fname), 'r', encoding='utf-8') as f:
            html = f.read()
        structure = extract_structure_from_html(html, property_id)
        data[f'property_{property_id}'] = structure
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

if __name__ == '__main__':
    main()
