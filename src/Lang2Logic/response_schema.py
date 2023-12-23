import json
from jsonschema import validate, Draft7Validator, ValidationError
from typing import Dict, Any, Union
from jsonschema.exceptions import SchemaError
from jsonschema.exceptions import ValidationError


class ResponseSchema:
    def __init__(self, input_data: Union[str, Dict[str, Any], 'ResponseSchema']):
        if isinstance(input_data, str):
            try:
                self.schema = json.loads(input_data)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON string.")
        elif isinstance(input_data, dict):
            self.schema = input_data
        elif isinstance(input_data, ResponseSchema):
            self.schema = input_data.schema
        else:
            raise TypeError("Input must be a JSON string, a dictionary, or a ResponseSchema instance.")

        # Validate the schema as a Draft 7 JSON Schema
        try:
            self.is_valid_schema=self.validate_schema()
        except ValidationError as e:
            self.is_valid_schema = False
    def validate_schema(self) -> bool:
        """ Validates if the provided schema is a valid Draft 7 JSON Schema. """
        try:
            Draft7Validator.check_schema(self.schema)
            return True
        except ValidationError as e:
            return False
        except SchemaError as e:
            return False
        except Exception as e:
            return False
        

    def to_dict(self) -> Dict[str, Any]:
        """ Returns the schema as a dictionary. """
        return self.schema

    
    def to_json(self) -> str:
        """ Converts the schema to a JSON string. """
        try:
            return json.dumps(self.schema, indent=4)
        except Exception as e:
            raise ValueError(f"Failed to convert schema to JSON string: {e}")
    
    def save_to_json(self, key: str, filepath: str) -> None:
        """ Saves the schema as a JSON file, appending under a specified key. """
        try:
            # Read existing data from the file
            existing_data = {}
            try:
                with open(filepath, "r", encoding='utf-8') as f:
                    existing_data = json.load(f)
            except FileNotFoundError:
                # File does not exist, will be created
                pass
            except json.JSONDecodeError:
                # File is empty or not valid JSON, will be overwritten
                pass

            # Update the existing data with the new schema under the specified key
            existing_data[key] = self.schema

            # Saving the updated data back to the file
            with open(filepath, "w", encoding='utf-8') as f:
                json.dump(existing_data, f, indent=4)
        except Exception as e:
            raise ValueError(f"Failed to save schema to JSON file: {e}")
