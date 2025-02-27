import csv
from owlready2 import *
import os


def normalize_class_name(name: str) -> str:
    """
    Normalize class name to be valid in OWL
    """
    # Remove special characters, replace spaces with underscores
    name = "".join(c for c in name if c.isalnum() or c in ['-', '_'])
    # Ensure first character is a letter
    if name[0].isdigit():
        name = 'Class_' + name
    return name


def create_ontology_from_csv(csv_file: str, output_owl: str):
    """
    Create OWL ontology from CSV data
    """
    # Clear any existing ontology
    default_world.ontologies.clear()

    # Create new ontology
    onto = get_ontology("http://test.org/onto.owl")

    with onto:
        # 1. Create base classes
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

        # Dictionary to store classes
        classes = {}

        # 2. Read CSV and create classes
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            # First pass: Create all classes
            unique_names = set()
            for row in rows:
                name = row['name']
                category = eval(row['category'])[0] if row['category'] else None

                if name not in unique_names:
                    unique_names.add(name)
                    # Normalize name for OWL compatibility
                    normalized_name = normalize_class_name(name)

                    # Determine parent class based on category
                    parent_class = None
                    if category == 'AffectedElement':
                        parent_class = AffectedElement
                    elif category == 'HazardElement':
                        parent_class = HazardElement
                    elif category == 'EnvironmentElement':
                        parent_class = EnvironmentElement
                    elif category == 'ResponsePlanElement':
                        parent_class = ResponsePlanElement
                    elif category == 'Item':
                        parent_class = Item
                    else:
                        parent_class = ScenarioElement

                    # Create class
                    new_class = types.new_class(normalized_name, (parent_class,))
                    classes[name] = new_class

            # Create base object properties
            associateWith = types.new_class('associateWith', (ObjectProperty,))
            consistComposition = types.new_class('consistComposition', (ObjectProperty,))
            hasEffectOn = types.new_class('hasEffectOn', (ObjectProperty,))

            # Second pass: Create properties
            processed_props = set()

            for row in rows:
                prop_name = row['property_name']
                domain_name = row['name']

                if row['relation_type'] == 'DataProperty':
                    if prop_name not in processed_props:
                        processed_props.add(prop_name)
                        # Create data property
                        prop = types.new_class(prop_name, (DataProperty,))
                        # Set domain
                        if domain_name in classes:
                            prop.domain = [classes[domain_name]]
                        # Convert range type
                        if row['range'] == 'String':
                            range_type = str
                        elif row['range'] == 'Real':
                            range_type = float
                        elif row['range'] == 'Bool':
                            range_type = bool
                        else:
                            range_type = str
                        prop.range = [range_type]
                else:
                    if prop_name not in processed_props:
                        processed_props.add(prop_name)
                        # Create object property
                        if row['relation_type'] == 'associateWith':
                            prop = types.new_class(prop_name, (associateWith,))
                        elif row['relation_type'] == 'consistComposition':
                            prop = types.new_class(prop_name, (consistComposition,))
                        elif row['relation_type'] == 'hasEffectOn':
                            prop = types.new_class(prop_name, (hasEffectOn,))
                        else:
                            continue

                        # Set domain and range
                        if domain_name in classes:
                            prop.domain = [classes[domain_name]]
                            # Find target class based on value if it exists
                            if row['value']:  # Use value field for range if available
                                value_class = row['value']
                                if value_class in classes:
                                    prop.range = [classes[value_class]]

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_owl)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Save ontology
    onto.save(file=output_owl, format="rdfxml")
    print(f"Ontology saved to: {output_owl}")


if __name__ == '__main__':
    create_ontology_from_csv('relations.csv', 'scenario.owl')