# -*- coding: utf-8 -*-
# @Time    : 2025/2/21 19:27
# @FileName: test3.py
# @Software: PyCharm
import json
import csv
from typing import List, Dict, Any

level_map = {
1:	'Entity',
2:	'Entity',
3:	'Entity',
4:	'Entity',
5:	'Entity',
6:	'Item',
7:	'Item',
8:	'Item',
11:	'Item',
12:	'Item',
13:	'Entity'}

range_map = {
1:'车辆',
2:'路段',
3:'自然环境',
4:'应急资源',
5:'应急行为',
6:'车辆部件',
7:'承载物',
8:'基础设施',
11:'车道',
    12:'人类',
    13:'应急预案'
}



def create_entity_map(data: List[Dict[Any, Any]]) -> Dict[int, str]:
    """
    Create a mapping from entity_id to entity_name
    """
    return {entity['entity_id']: entity['entity_name'] for entity in data}


def format_referenced_entities(entity_ids: List[int], entity_map: Dict[int, str]) -> str:
    """
    Convert list of entity IDs to comma-separated string of entity names
    """
    if not entity_ids:
        return ""
    entity_names = [entity_map.get(entity_id, f"Unknown_{entity_id}") for entity_id in entity_ids]
    return ", ".join(entity_names)


def extract_relations(data: List[Dict[Any, Any]]) -> List[Dict[str, str]]:
    """
    Extract relations from JSON data.
    Returns list of dictionaries containing class, relation_type, name, domain, range and value.
    """
    relations = []
    # Create entity ID to name mapping
    entity_map = create_entity_map(data)

    for entity in data:
        source_name = entity['entity_name']

        # 1. Extract data properties
        for attr in entity.get('attributes', []):
            if attr.get('attribute_type_code') not in ['Item', 'Entity']:
                relations.append({
                    'name': source_name,
                    'class': range_map[entity['entity_type_id']],
                    'level': level_map[entity['entity_type_id']],
                    'category': [item['category_name'] for item in entity['categories']],
                    'relation_type': 'DataProperty',
                    'property_name': attr['attribute_name'],
                    'domain': source_name,
                    'range': attr['attribute_type_code'],
                    'value': str(attr.get('attribute_value', ''))
                })

        # 2. Check associateWith relations in attributes (Entity type)
        for attr in entity.get('attributes', []):
            if attr.get('attribute_type_code') == 'Entity':
                referenced_entities = attr.get('referenced_entities', [])
                value = format_referenced_entities(referenced_entities, entity_map)

                relations.append({
                    'name': source_name,
                    'class': range_map[entity['entity_type_id']],
                    'level': level_map[entity['entity_type_id']],
                    'category': [item['category_name'] for item in entity['categories']],
                    'relation_type': 'associateWith',
                    'property_name': attr['attribute_name'],
                    'domain': source_name,
                    'range': range_map[attr['reference_target_type_id']] if attr.get('reference_target_type_id') else 'UnDefined',
                    'value': value
                })

        # 3. Check consistComposition relations in attributes (Item type)
        for attr in entity.get('attributes', []):
            if attr.get('attribute_type_code') == 'Item':
                referenced_entities = attr.get('referenced_entities', [])
                value = format_referenced_entities(referenced_entities, entity_map)

                relations.append({
                    'name': source_name,
                    'class': range_map[entity['entity_type_id']],
                    'level': level_map[entity['entity_type_id']],
                    'category': [item['category_name'] for item in entity['categories']],
                    'relation_type': 'consistComposition',
                    'property_name': attr['attribute_name'],
                    'domain': source_name,
                    'range': range_map[attr['reference_target_type_id']],
                    'value': value
                })

        # 4. Check hasEffectOn relations in behaviors
        for behavior in entity.get('behaviors', []):
            object_entities = behavior.get('object_entities', [])
            value = format_referenced_entities(object_entities, entity_map)

            relations.append({
                'name': source_name,
                'class': range_map[entity['entity_type_id']],
                'level': level_map[entity['entity_type_id']],
                'category': [item['category_name'] for item in entity['categories']],
                'relation_type': 'hasEffectOn',
                'property_name': behavior['behavior_name'],
                'domain': source_name,
                'range': range_map[behavior['object_entity_type_id']],
                'value': value
            })

    return relations


def write_to_csv(relations: List[Dict[str, str]], output_file: str):
    """
    Write relations to CSV file
    """
    fieldnames = ['name', 'class','level','category', 'relation_type', 'property_name', 'domain', 'range', 'value']

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(relations)


def main(input_json: str, output_csv: str):
    """
    Main function to process JSON and generate CSV
    """
    # Load JSON data
    with open(input_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Extract relations
    relations = extract_relations(data)

    # Write to CSV
    write_to_csv(relations, output_csv)


if __name__ == '__main__':
    # Example usage
    main(r'D:\PythonProjects\AcademicTool_PySide\result.json', 'relations.csv')