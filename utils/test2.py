import xml.etree.ElementTree as ET
from typing import Dict, Optional
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_parse_datatype_property(owl_file_path: str) -> Dict:
    """
    Minimal test function to parse DatatypeProperty from file
    """
    namespaces = {
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'owl': 'http://www.w3.org/2002/07/owl#',
        'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
        'xsd': 'http://www.w3.org/2001/XMLSchema#'
    }

    RDF_ABOUT = f'{{{namespaces["rdf"]}}}about'
    RDF_RESOURCE = f'{{{namespaces["rdf"]}}}resource'
    RDF_DATATYPE = f'{{{namespaces["rdf"]}}}datatype'

    # Parse XML file
    tree = ET.parse(owl_file_path)
    root = tree.getroot()

    # Find all DatatypeProperty elements
    results = []
    for prop in root.findall('.//owl:DatatypeProperty', namespaces):
        # Get property name
        prop_name = prop.get(RDF_ABOUT, '').replace('#', '')

        # Get domain
        domain_elem = prop.find('rdfs:domain', namespaces)
        domain = domain_elem.get(RDF_RESOURCE, '').replace('#', '') if domain_elem is not None else None

        # Get range
        range_elem = prop.find('rdfs:range', namespaces)
        range_type = range_elem.get(RDF_RESOURCE, '') if range_elem is not None else None
        data_type = range_type.split('#')[-1] if range_type else None

        # Get value with improved parsing
        value_elem = prop.find('.//{*}hasValue')  # Match hasValue in any namespace
        value = None
        raw_value = None

        if value_elem is not None:
            value_text = value_elem.text
            raw_value = value_text

            # Skip empty or None values
            if value_text and value_text.lower() != 'none':
                if data_type == 'boolean':
                    value = value_text.lower() == 'true' or value_text == '1'
                elif data_type == 'decimal':
                    try:
                        value = float(value_text)
                    except (ValueError, TypeError):
                        pass
                elif data_type == 'string':
                    value = value_text

        # Get description
        desc_elem = prop.find('.//{*}hasDescription')
        description = desc_elem.text if desc_elem is not None else None

        # Log detailed information about the property
        logger.debug(f"\nProperty: {prop_name}")
        logger.debug(f"  Domain: {domain}")
        logger.debug(f"  Range Type: {data_type}")
        logger.debug(f"  Raw Value: {raw_value}")
        logger.debug(f"  Parsed Value: {value} (type: {type(value).__name__ if value is not None else 'None'})")
        logger.debug(f"  Description: {description}")

        property_info = {
            'name': prop_name,
            'domain': domain,
            'range_type': data_type,
            'raw_value': raw_value,
            'value': value,
            'description': description
        }
        results.append(property_info)

    return results


def main():
    owl_file = r"D:\PythonProjects\AcademicTool_PySide\data\sysml2\3\owl\ScenarioElement.owl"  # Replace with actual path
    results = test_parse_datatype_property(owl_file)

    # Print results in a readable format
    print("\nParsed DatatypeProperties:")
    print("=" * 60)
    for prop in results:
        print(f"\nProperty: {prop['name']}")
        print(f"Domain: {prop['domain']}")
        print(f"Range Type: {prop['range_type']}")
        print(f"Raw Value: {prop['raw_value']}")
        print(
            f"Parsed Value: {prop['value']} (type: {type(prop['value']).__name__ if prop['value'] is not None else 'None'})")
        print(f"Description: {prop['description']}")
        print("-" * 60)


if __name__ == "__main__":
    main()