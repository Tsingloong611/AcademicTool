import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import logging
import os
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PropertyInfo:
    name: str
    type: str  # DataProperty or ObjectProperty
    domain: List[str]
    range: Optional[str]
    value: Optional[Any]  # Can be string, bool, float, or None
    description: Optional[str]

class XMLOWLParser:
    def __init__(self, owl_file_path: str):
        self.owl_file_path = owl_file_path
        self.ns = {
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'owl': 'http://www.w3.org/2002/07/owl#',
            'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
            'xsd': 'http://www.w3.org/2001/XMLSchema#',
            '': 'http://test.org/onto.owl#'  # Add default namespace
        }
        self.RDF_ABOUT = f"{{{self.ns['rdf']}}}about"
        self.RDF_RESOURCE = f"{{{self.ns['rdf']}}}resource"
        self.RDF_DATATYPE = f"{{{self.ns['rdf']}}}datatype"

        self.tree = ET.parse(owl_file_path)
        self.root = self.tree.getroot()

    def clean_uri(self, uri: str) -> str:
        """Remove namespace and '#' from URIs"""
        if '#' in uri:
            return uri.split('#')[1]
        return uri

    def parse_property(self, prop_elem: ET.Element, prop_type: str) -> Optional[Dict]:
        """Parse a single property element with corrected value handling"""
        if self.RDF_ABOUT not in prop_elem.attrib:
            return None

        prop_name = self.clean_uri(prop_elem.attrib[self.RDF_ABOUT])

        # Get domain
        domain = []
        domain_elem = prop_elem.find("rdfs:domain", self.ns)
        if domain_elem is not None and self.RDF_RESOURCE in domain_elem.attrib:
            domain.append(self.clean_uri(domain_elem.attrib[self.RDF_RESOURCE]))

        # Get range
        range_type = None
        range_elem = prop_elem.find("rdfs:range", self.ns)
        if range_elem is not None and self.RDF_RESOURCE in range_elem.attrib:
            range_type = self.clean_uri(range_elem.attrib[self.RDF_RESOURCE])

        data_type = range_type.split('#')[-1] if range_type else None

        # Get value and description - Updated logic for both ObjectProperty and DatatypeProperty
        value = None
        description = None

        # Handle value
        value_elem = prop_elem.find('.//{*}hasValue')  # Match hasValue in any namespace

        if value_elem is not None:
            value_text = value_elem.text
            raw_value = value_text

            # Skip empty or None values
            print(f"{prop_name}")
            print(f"34155135{value_elem}")
            print(f"34155135{value_text}")
            print(f"34155135{data_type}")
            if value_text and value_text.lower() != 'none':
                if data_type == 'boolean':
                    if value_text.lower() == 'true' or value_text == '1':
                        value = "True"
                    else:
                        value = "False"
                elif data_type == 'decimal':
                    try:
                        value = str(float(value_text))
                        print(f"34155135431{value}")
                    except (ValueError, TypeError):
                        pass
                elif data_type == 'string':
                    value = value_text
                else:
                    value = value_text

        # Handle description
        desc_elem = prop_elem.find("hasDescription", None)
        if desc_elem is not None:
            description = desc_elem.text if desc_elem.text != "None" else None

        return {
            "property_name": prop_name,
            "property_type": prop_type,
            "property_domain": domain,
            "property_range": range_type,
            "property_value": value if value else "None",
            "property_description": description if description else None
        }

    def parse(self) -> Dict[str, Dict]:
        """Parse the OWL file"""
        result = {}

        # First collect all classes
        for class_elem in self.root.findall(".//owl:Class", self.ns):
            if self.RDF_ABOUT not in class_elem.attrib:
                continue

            class_name = self.clean_uri(class_elem.attrib[self.RDF_ABOUT])

            # Get class description
            desc = None
            desc_elem = class_elem.find("hasDescription", None)
            if desc_elem is not None:
                desc = desc_elem.text

            # Get parent classes
            parent_classes = []
            for subclass_elem in class_elem.findall("rdfs:subClassOf", self.ns):
                if self.RDF_RESOURCE in subclass_elem.attrib:
                    parent_classes.append(
                        self.clean_uri(subclass_elem.attrib[self.RDF_RESOURCE])
                    )

            result[class_name] = {
                "parent_classes": parent_classes,
                "sub_classes": [],
                "properties": [],
                "description": desc
            }

        # Parse object properties
        for prop_elem in self.root.findall(".//owl:ObjectProperty", self.ns):
            prop_info = self.parse_property(prop_elem, "ObjectProperty")
            if prop_info and prop_info["property_domain"]:
                for domain_class in prop_info["property_domain"]:
                    if domain_class in result:
                        result[domain_class]["properties"].append(prop_info)

        # Parse data properties
        for prop_elem in self.root.findall(".//owl:DatatypeProperty", self.ns):
            prop_info = self.parse_property(prop_elem, "DatatypeProperty")
            if prop_info and prop_info["property_domain"]:
                for domain_class in prop_info["property_domain"]:
                    if domain_class in result:
                        result[domain_class]["properties"].append(prop_info)

        # Populate sub_classes
        for class_name, class_info in result.items():
            for parent_class in class_info["parent_classes"]:
                if parent_class in result:
                    result[parent_class]["sub_classes"].append(class_name)

        return result

    def print_structure(self):
        """Print the ontology structure"""
        data = self.parse()
        for class_name, info in data.items():
            print(f"\nClass: {class_name}")
            if info.get('description'):
                print(f"Description: {info['description']}")
            print(f"Parent classes: {info['parent_classes']}")
            print(f"Sub classes: {info['sub_classes']}")
            print("Properties:")
            for prop in info['properties']:
                print(f"  - {prop['property_name']} ({prop['property_type']})")
                print(f"    Domain: {prop['property_domain']}")
                print(f"    Range: {prop['property_range']}")
                print(f"    Value: {prop['property_value']}")
                if prop['property_description']:
                    print(f"    Description: {prop['property_description']}")

    def export_json(self, output_path: str):
        """Export the parsed data to JSON"""
        try:
            data = self.parse()
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Successfully exported to {output_path}")
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")

    def combine_json(self, output_file):
        output_dir = os.path.dirname(output_file)
        output_file = os.path.basename(output_file)
        json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
        json_files = [file for file in json_files if file != output_file]
        print(json_files)
        # 把这些json文件合并到一个json文件中
        combined_data = {}
        for file in json_files:
            with open(os.path.join(output_dir, file), 'r', encoding='utf-8') as f:
                data = json.load(f)
                combined_data.update(data)
        with open(os.path.join(output_dir, output_file), 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Successfully exported to {output_file}")


def parse_owl(owl_file_path: str, json_data=None):
    parser = XMLOWLParser(owl_file_path)
    parser.print_structure()

    # Export to JSON with timestamp
    owl_name = os.path.splitext(os.path.basename(owl_file_path))[0]
    output_path = os.path.dirname(owl_file_path)
    output_file = os.path.join(output_path, f"{owl_name}_ontology_structure.json")
    if owl_name == 'Merge':
        parser.combine_json(output_file)
    else:
        parser.export_json(output_file)

if __name__ == "__main__":
    owl_file = r"D:\PythonProjects\AcademicTool_PySide\data\sysml2\3\owl\Merge.owl"
    parse_owl(owl_file)
