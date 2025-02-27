# -*- coding: utf-8 -*-
import json
import csv
from typing import List, Dict, Any
from owlready2 import *
import os


class ScenarioOntologyGenerator:
    def __init__(self):
        self.level_map = {
            1: 'Entity', 2: 'Entity', 3: 'Entity', 4: 'Entity', 5: 'Entity',
            6: 'Item', 7: 'Item', 8: 'Item', 11: 'Item', 12: 'Item', 13: 'Entity'
        }

        self.range_map = {
            1: '车辆', 2: '路段', 3: '自然环境', 4: '应急资源', 5: '应急行为',
            6: '车辆部件', 7: '承载物', 8: '基础设施', 11: '车道', 12: '人类',
            13: '应急预案'
        }

        self.classes = {}
        self.relations = []

    def create_entity_map(self, data: List[Dict[Any, Any]]) -> Dict[int, str]:
        """Create a mapping from entity_id to entity_name"""

        return {entity['entity_id']: entity['entity_name'] for entity in data}

    def format_referenced_entities(self, entity_ids: List[int], entity_map: Dict[int, str]) -> str:
        """Convert list of entity IDs to comma-separated string of entity names"""
        if not entity_ids:
            return "None"
        entity_names = [entity_map.get(entity_id, f"Unknown_{entity_id}") for entity_id in entity_ids]
        return ", ".join(entity_names)

    def extract_relations(self, data: List[Dict[Any, Any]]) -> List[Dict[str, str]]:
        """Extract relations from JSON data"""
        # Create entity ID to name mapping
        entity_map = self.create_entity_map(data)

        for entity in data:
            source_name = entity['entity_name']

            # 1. Extract data properties
            for attr in entity.get('attributes', []):
                if attr.get('attribute_type_code') not in ['Item', 'Entity']:
                    self.relations.append({
                        'name': source_name,
                        'class': self.range_map[entity['entity_type_id']],
                        'level': self.level_map[entity['entity_type_id']],
                        'category': [item['category_name'] for item in entity['categories']] if entity['categories'] else [],
                        'relation_type': 'DataProperty',
                        'property_name': attr['attribute_name'],
                        'domain': source_name,
                        'range': attr['attribute_type_code'],
                        'value': str(attr.get('attribute_value', 'None'))
                    })

            # 2. Check associateWith relations
            for attr in entity.get('attributes', []):
                if attr.get('attribute_type_code') == 'Entity':
                    referenced_entities = attr.get('referenced_entities', [])
                    value = self.format_referenced_entities(referenced_entities, entity_map)
                    self.relations.append({
                        'name': source_name,
                        'class': self.range_map[entity['entity_type_id']],
                        'level': self.level_map[entity['entity_type_id']],
                        'category': [item['category_name'] for item in entity['categories']] if entity['categories'] else [],
                        'relation_type': 'associateWith',
                        'property_name': attr['attribute_name'],
                        'domain': source_name,
                        'range': self.range_map[attr['reference_target_type_id']] if attr.get(
                            'reference_target_type_id') else 'UnDefined',
                        'value': value
                    })

            # 3. Check consistComposition relations
            for attr in entity.get('attributes', []):
                if attr.get('attribute_type_code') == 'Item':
                    referenced_entities = []
                    for item in data:
                        if item['entity_parent_id'] == entity['entity_id'] and item['entity_type_id'] == attr['reference_target_type_id']:
                            referenced_entities.append(item['entity_id'])
                    value = self.format_referenced_entities(referenced_entities, entity_map)
                    self.relations.append({
                        'name': source_name,
                        'class': self.range_map[entity['entity_type_id']],
                        'level': self.level_map[entity['entity_type_id']],
                        'category': [item['category_name'] for item in entity['categories']] if entity['categories'] else [],
                        'relation_type': 'consistComposition',
                        'property_name': attr['attribute_name'],
                        'domain': source_name,
                        'range': self.range_map[attr['reference_target_type_id']],
                        'value': value
                    })

            # 4. Check hasEffectOn relations
            for behavior in entity.get('behaviors', []):
                object_entities = behavior.get('object_entities', [])
                value = self.format_referenced_entities(object_entities, entity_map)
                self.relations.append({
                    'name': source_name,
                    'class': self.range_map[entity['entity_type_id']],
                    'level': self.level_map[entity['entity_type_id']],
                    'category': [item['category_name'] for item in entity['categories']] if entity['categories'] else [],
                    'relation_type': 'hasEffectOn',
                    'property_name': behavior['behavior_name'],
                    'domain': source_name,
                    'range': self.range_map[behavior['object_entity_type_id']] if behavior.get('object_entity_type_id') else 'UnDefined',
                    'value': value
                })

        return self.relations

    @staticmethod
    def normalize_class_name(name: str) -> str:
        """Normalize class name to be valid in OWL"""
        name = "".join(c for c in name if c.isalnum() or c in ['-', '_'])
        if name[0].isdigit():
            name = 'Class_' + name
        return name

    def create_ontology(self, onto: Ontology):
        """Create ontology classes and properties with annotations"""
        with onto:
            # Create annotation properties
            class hasValue(AnnotationProperty):
                pass

            class hasDefaultValue(AnnotationProperty):
                pass

            class hasDescription(AnnotationProperty):
                pass

            # Create base classes
            class ScenarioElement(Thing):
                pass

            class AffectedElement(ScenarioElement):
                pass

            class HazardElement(ScenarioElement):
                pass

            class EnvironmentElement(ScenarioElement):
                pass

            class ResponsePlanElement(ScenarioElement):
                pass

            class Item(Thing):
                pass

            # First pass: Create all classes
            unique_names = set()
            for row in self.relations:
                name = row['name']
                if name not in unique_names:
                    unique_names.add(name)
                    normalized_name = self.normalize_class_name(name)
                    categorys = row['category']
                    # print(name)
                    # print(row)
                    # print(categorys)

                    parent_classes = []
                    for category in categorys:
                        if category == 'AffectedElement':
                            parent_classes.append(AffectedElement)
                        if category == 'HazardElement':
                            parent_classes.append(HazardElement)
                        if category == 'EnvironmentElement':
                            parent_classes.append(EnvironmentElement)
                        if category == 'ResponsePlanElement':
                            parent_classes.append(ResponsePlanElement)
                        if category == 'Item':
                            parent_classes.append(Item)
                    if not parent_classes:
                        parent_classes.append(ScenarioElement)

                    # Create class
                    new_class = types.new_class(normalized_name, tuple(parent_classes))
                    new_class.hasDescription = f"Class type: {row['class']}, Level: {row['level']}"
                    self.classes[name] = new_class
            # Create base object properties
            associateWith = types.new_class('associateWith', (ObjectProperty,))
            consistComposition = types.new_class('consistComposition', (ObjectProperty,))
            hasEffectOn = types.new_class('hasEffectOn', (ObjectProperty,))

            # Use a dictionary to track processed properties by their name AND domain
            processed_props = {}

            # Second pass: Create properties
            for row in self.relations:
                prop_name = row['property_name']
                domain_name = row['name']
                prop_key = f"{prop_name}_{domain_name}"  # Unique key combining property name and domain

                if row['relation_type'] == 'DataProperty':
                    if prop_key not in processed_props:
                        processed_props[prop_key] = True
                        prop = types.new_class(f"{prop_name}_{domain_name}", (DataProperty,))
                        if domain_name in self.classes:
                            prop.domain = [self.classes[domain_name]]
                        # Set range type
                        range_type = str
                        if row['range'] == 'Real':
                            range_type = float
                        elif row['range'] == 'Bool':
                            range_type = bool
                        prop.range = [range_type]
                        prop.hasValue = row['value']
                        prop.hasDescription = f"Range type: {row['range']}"

                else:
                    if prop_key not in processed_props:
                        processed_props[prop_key] = True
                        if row['relation_type'] == 'associateWith':
                            base_prop = associateWith
                        elif row['relation_type'] == 'consistComposition':
                            base_prop = consistComposition
                        elif row['relation_type'] == 'hasEffectOn':
                            base_prop = hasEffectOn
                        else:
                            continue

                        # Create property with unique name
                        prop = types.new_class(f"{prop_name}_{domain_name}", (base_prop,))

                        if domain_name in self.classes:
                            prop.domain = [self.classes[domain_name]]
                            if row['value']:
                                value_class = row['value']
                                if value_class in self.classes:
                                    prop.range = [self.classes[value_class]]
                                    prop.hasDescription = f"Links {domain_name} to {value_class}"
                        prop.hasValue = row['value']

    def generate(self, input_json, output_owl: str):
        """Main method to generate ontology from JSON input"""
        # Clear any existing ontology
        default_world.ontologies.clear()

        # Load JSON and extract relations
        data = input_json
        print(data)
        # 检查人类类型，如果存在且CasualtyCondition为true，则添加affectedelement的category
        for entity in data:
            if entity['entity_type_id'] == 12:
                for attr in entity.get('attributes', []):
                    if attr.get('attribute_code_name') == 'CasualtyCondition' and (
                            str(attr.get('attribute_value')).lower() == 'true' or str(
                            attr.get('attribute_value')) == '1'):
                        entity['categories'].append({"category_id": 1, "category_name": "AffectedElement", "description": "承灾要素"})

        print(data)
        self.extract_relations(data)

        # Create ontology
        onto = get_ontology("http://example.org/scenario_element.owl")
        self.create_ontology(onto)

        # Save ontology
        output_dir = os.path.dirname(output_owl)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        onto.save(file=output_owl, format="rdfxml")
        print(f"Ontology saved to: {output_owl}")


if __name__ == '__main__':
    generator = ScenarioOntologyGenerator()
    json_data = json.load(open(r'D:\PythonProjects\AcademicTool_PySide\result.json', 'r', encoding='utf-8'))
    generator.generate(json_data, 'scenario.owl')