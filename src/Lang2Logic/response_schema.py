import json
from jsonschema import validate, ValidationError
from typing import Union, Dict, Any

class ResponseSchema:
    def __init__(self, data: Union[str, Dict[str, Any], 'ResponseSchema']):
        # If the data is another ResponseSchema instance, use its schema and data
        if isinstance(data, ResponseSchema):
            self.schema = data.schema
            self.data = data.data
        # If the data is a string, attempt to parse it as JSON
        elif isinstance(data, str):
            try:
                loaded_data = json.loads(data)
                self.schema = loaded_data.get('schema', {})
                self.data = loaded_data.get('data', {})
            except json.JSONDecodeError:
                # If not JSON, treat as invalid input
                raise ValueError("String input must be valid JSON.")
        # If the data is a dictionary, assume it's a combination of schema and data
        elif isinstance(data, dict):
            self.schema = data.get('schema', {})
            self.data = data.get('data', {})
        else:
            raise TypeError("Data must be a JSON string, dictionary, or ResponseSchema instance")

        # Automatically validate upon initialization
        self.validate()

    def validate(self) -> bool:
        """ Validates the data against the stored schema. """
        try:
            validate(instance=self.data, schema=self.schema)
            print("Validation successful.")
            return True
        except ValidationError as e:
            print(f"Validation error: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """ Returns the data as a dictionary, ensuring nested ResponseSchema objects are converted. """
        if isinstance(self.data, ResponseSchema):
            return self.data.to_dict()  # Recursively convert nested ResponseSchema objects
        return self.data

    def to_json(self) -> str:
        """ Converts the data to a JSON string. """
        return json.dumps(self.data)

    def pretty_print(self):
        """ Pretty prints the data. """
        print(json.dumps(self.data, indent=4))
    