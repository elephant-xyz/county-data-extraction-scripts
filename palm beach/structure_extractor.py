import os
import json
import re
from bs4 import BeautifulSoup

INPUT_DIR = './input/'
OUTPUT_FILE = './owners/structure_data.json'

def extract_structure_from_html(html, file_id):
    soup = BeautifulSoup(html, 'html.parser')
    # Required fields from schema
    def safe_enum(val, allowed):
        if val is None or val == '' or val == 'N/A':
            return None
        if val in allowed:
            return val
        return None

    structure = {
        'request_identifier': str(file_id),
        'source_http_request': {
            'method': 'GET',
            'url': f'https://www.pbcgov.org/papa/Property/Details?parcelID={file_id}'
        },
        'architectural_style_type': None,
        'attachment_type': None,
        'number_of_stories': None,
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
    # Building type/attachment and architectural_style_type
    use_code = soup.find(string=re.compile(r'Property Use Code'))
    if use_code:
        val = use_code.find_parent('tr').find_all('td')[-1].get_text(strip=True)
        val_upper = val.upper()
        # Attachment type
        if 'TOWNHOUSE' in val_upper or 'CONDO' in val_upper or 'CONDOMINIUM' in val_upper:
            structure['attachment_type'] = 'Attached'
        else:
            structure['attachment_type'] = None
        # Architectural style type
        if 'TOWNHOUSE' in val_upper:
            structure['architectural_style_type'] = 'Contemporary'  # Closest enum for modern townhouses
        elif 'CONDO' in val_upper or 'CONDOMINIUM' in val_upper:
            structure['architectural_style_type'] = 'Minimalist'  # Closest enum for condos
        else:
            structure['architectural_style_type'] = None
    else:
        use_code_desc = soup.find(string=re.compile(r'UseCodeDesc|Use Code Desc|Use Code'))
        if use_code_desc:
            val = use_code_desc.find_parent('tr').find_all('td')[-1].get_text(strip=True)
            val_upper = val.upper()
            if 'TOWNHOUSE' in val_upper or 'CONDO' in val_upper or 'CONDOMINIUM' in val_upper:
                structure['attachment_type'] = 'Attached'
            else:
                structure['attachment_type'] = None
            if 'TOWNHOUSE' in val_upper:
                structure['architectural_style_type'] = 'Contemporary'
            elif 'CONDO' in val_upper or 'CONDOMINIUM' in val_upper:
                structure['architectural_style_type'] = 'Minimalist'
            else:
                structure['architectural_style_type'] = None
    # Ensure all string fields are either string or None
    # For enum fields, set to None if missing; for required string fields, set to '' if missing and schema does not allow null
    enum_fields = [
        'architectural_style_type', 'attachment_type', 'ceiling_condition', 'ceiling_insulation_type', 'ceiling_structure_material',
        'ceiling_surface_material', 'exterior_door_material', 'exterior_wall_condition', 'exterior_wall_insulation_type',
        'exterior_wall_material_primary', 'exterior_wall_material_secondary', 'flooring_condition', 'flooring_material_primary',
        'flooring_material_secondary', 'foundation_condition', 'foundation_material', 'foundation_type', 'foundation_waterproofing',
        'gutters_condition', 'gutters_material', 'interior_door_material', 'interior_wall_condition', 'interior_wall_finish_primary',
        'interior_wall_finish_secondary', 'interior_wall_structure_material', 'interior_wall_surface_material_primary',
        'interior_wall_surface_material_secondary', 'primary_framing_material', 'roof_condition', 'roof_covering_material',
        'roof_design_type', 'roof_material_type', 'roof_structure_material', 'roof_underlayment_type', 'secondary_framing_material',
        'structural_damage_indicators', 'subfloor_material', 'window_frame_material', 'window_glazing_type', 'window_operation_type',
        'window_screen_material'
    ]
    for k in structure:
        if k in ['roof_age_years', 'ceiling_height_average', 'request_identifier', 'source_http_request']:
            continue
        if structure[k] is None:
            if k in enum_fields:
                structure[k] = None
            else:
                structure[k] = ''
    # Exterior wall
    ext_wall = soup.find(string=re.compile(r'Exterior Wall 1'))
    if ext_wall:
        val = ext_wall.find_parent('tr').find_all('td')[-1].get_text(strip=True)
        val_upper = val.upper()
        if 'CB' in val_upper or 'CONCRETE BLOCK' in val_upper:
            structure['exterior_wall_material_primary'] = 'Concrete Block'
        elif 'STUCCO' in val_upper:
            structure['exterior_wall_material_primary'] = 'Stucco'
        else:
            structure['exterior_wall_material_primary'] = None
    # Secondary wall
    ext_wall2 = soup.find(string=re.compile(r'Exterior Wall 2'))
    if ext_wall2:
        val = ext_wall2.find_parent('tr').find_all('td')[-1].get_text(strip=True)
        val_upper = val.upper()
        if 'STUCCO' in val_upper:
            structure['exterior_wall_material_secondary'] = 'Stucco Accent'
        elif 'NONE' in val_upper:
            structure['exterior_wall_material_secondary'] = None
        elif 'WSF' in val_upper:
            structure['exterior_wall_material_secondary'] = 'Stucco Accent'
        else:
            structure['exterior_wall_material_secondary'] = None
    # Roof
    roof_struct = soup.find(string=re.compile(r'Roof Structure'))
    if roof_struct:
        val = roof_struct.find_parent('tr').find_all('td')[-1].get_text(strip=True)
        if 'WOOD' in val.upper():
            structure['roof_structure_material'] = 'Wood Truss'
        elif 'CONCRETE' in val.upper():
            structure['roof_structure_material'] = 'Concrete Beam'
        else:
            structure['roof_structure_material'] = None
    roof_cover = soup.find(string=re.compile(r'Roof Cover'))
    if roof_cover:
        val = roof_cover.find_parent('tr').find_all('td')[-1].get_text(strip=True)
        val_upper = val.upper()
        if 'CONCRETE TILE' in val_upper:
            structure['roof_covering_material'] = 'Concrete Tile'
        elif 'MIN. ROOFING' in val_upper or 'CORR/SH.M' in val_upper or 'METAL' in val_upper:
            structure['roof_covering_material'] = 'Metal Corrugated'
        else:
            structure['roof_covering_material'] = None
    # Stories
    stories = soup.find(string=re.compile(r'Stories'))
    if stories:
        val = stories.find_parent('tr').find_all('td')[-1].get_text(strip=True)
        try:
            structure['number_of_stories'] = int(val)
        except:
            structure['number_of_stories'] = None
    # Flooring
    floor1 = soup.find(string=re.compile(r'Floor Type 1'))
    if floor1:
        val = floor1.find_parent('tr').find_all('td')[-1].get_text(strip=True)
        if 'CARPET' in val.upper():
            structure['flooring_material_primary'] = 'Carpet'
        elif 'TILE' in val.upper():
            structure['flooring_material_primary'] = 'Ceramic Tile'
        else:
            structure['flooring_material_primary'] = None
    floor2 = soup.find(string=re.compile(r'Floor Type 2'))
    if floor2:
        val = floor2.find_parent('tr').find_all('td')[-1].get_text(strip=True)
        if 'TILE' in val.upper():
            structure['flooring_material_secondary'] = 'Ceramic Tile'
        elif 'CARPET' in val.upper():
            structure['flooring_material_secondary'] = 'Carpet'
        else:
            structure['flooring_material_secondary'] = None
    # Framing
    structure['primary_framing_material'] = None  # Only set if explicitly present in input
    # Add more extraction as needed
    return structure

def main():
    result = {}
    for fname in os.listdir(INPUT_DIR):
        if not fname.endswith('.html'):
            continue
        file_id = fname.replace('.html', '')
        with open(os.path.join(INPUT_DIR, fname), 'r', encoding='utf-8') as f:
            html = f.read()
        structure = extract_structure_from_html(html, file_id)
        result[f'property_{file_id}'] = structure
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

if __name__ == '__main__':
    main()
