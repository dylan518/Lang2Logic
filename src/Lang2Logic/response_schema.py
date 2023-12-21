import json
from jsonschema import validate, ValidationError
from typing import Union, Dict, Any

class ResponseSchema:
    def __init__(self, data: Union[str, Dict[str, Any], 'ResponseSchema'], schema: Dict[str, Any]):
        self.schema = schema

        # Handle if the data is another ResponseSchema instance
        if isinstance(data, ResponseSchema):
            self.data = data.data
        elif isinstance(data, str):
            try:
                self.data = json.loads(data)  # Attempt to parse JSON string
            except json.JSONDecodeError:
                # If not JSON, treat as a regular string
                self.data = data
        elif isinstance(data, dict):
            self.data = data
        else:
            raise TypeError("Data must be a JSON string, string, dictionary, or ResponseSchema instance")

        self.validate()  # Automatically validate upon initialization

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
    