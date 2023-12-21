import json
from jsonschema import validate, Draft7Validator, ValidationError
from typing import Dict, Any, Union

class ResponseSchema:
    def __init__(self, input_data: Union[str, Dict[str, Any]]):
        # Handle input data based on its type
        if isinstance(input_data, str):
            # Attempt to load from JSON string
            try:
                self.schema = json.loads(input_data)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON string.")
        elif isinstance(input_data, dict):
            # Directly use the dictionary as schema
            self.schema = input_data
        else:
            raise TypeError("Input must be a JSON string or a dictionary.")

        # Validate the schema as a Draft 7 JSON Schema
        self.is_valid_schema = self.validate_schema()

    def validate_schema(self) -> bool:
        """ Validates if the provided schema is a valid Draft 7 JSON Schema. """
        try:
            Draft7Validator.check_schema(self.schema)
            return True
        except ValidationError as e:
            return False

    def to_dict(self) -> Dict[str, Any]:
        """ Returns the schema as a dictionary. """
        return self.schema

    def to_json(self) -> str:
        """ Converts the schema to a JSON string. """
        return json.dumps(self.schema, indent=4)