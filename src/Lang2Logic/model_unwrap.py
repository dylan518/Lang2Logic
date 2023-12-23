import json
from pydantic import BaseModel
from typing import Any, Dict, List, Union
from .data_manager import DataManagement
import re
from datetime import datetime
from typing import Any, Dict
from urllib.parse import urlparse
from enum import Enum

class SchemaModelUnwrapper:
    def __init__(self, schema: Dict[str, Any], data_manager: Any):
        """
        Initializes the SchemaModelUnwrapper with a given JSON Schema and a data manager for logging.

        :param schema: Dict[str, Any] - The JSON Schema defining the structure and types.
        :param data_manager: Any - An object responsible for logging and managing data.
        """
        try:
            if not isinstance(schema, dict):
                raise ValueError("Schema must be a dictionary.")

            self.schema = schema
            self.data_manager = data_manager

            # Additional initialization code can be added here
            # For example, validating the schema if necessary

        except Exception as e:
            self.data_manager.log_fatal_error(f"Failed to initialize SchemaModelUnwrapper: {e}")
    
    def _handle_enum(self, value: Enum) -> Any:
        """
        Converts an Enum to its representative value.
        """
        if isinstance(value, Enum):
            return value.value
        return value
    

    def _resolve_reference(self, reference: str) -> Dict[str, Any]:
        """
        Resolves '$ref' references in the schema.
        """
        parts = reference.lstrip('#/').split('/')
        ref_schema = self.schema
        for part in parts:
            ref_schema = ref_schema.get(part, {})
            if not ref_schema:
                break
        return ref_schema
    def unwrap(self, model: BaseModel) -> Any:
        """
        Unwraps a Pydantic model into a Python structure based on the schema.
        """
        try:
            return self._recursive_unwrap(model, self.schema)
        except Exception as e:
            self.data_manager.log_fatal_error(f"Error in unwrapping model: {e}")
            return None
    
    def _recursive_unwrap(self, model: Any, schema: Dict[str, Any]) -> Any:
        """
        Recursively processes the model, handling nested structures.
        """
        if isinstance(model, Enum):
            return self._handle_enum(model)
    
        if '$ref' in schema:
            ref_schema = self._resolve_reference(schema['$ref'])
            return self._recursive_unwrap(model, ref_schema)

        if isinstance(model, BaseModel):
            # Unwrap a Pydantic model into a dictionary
            model_dict = model.model_dump()
            return {key: self._recursive_unwrap(value, schema['properties'][key])
                    for key, value in model_dict.items()}
        elif isinstance(model, list):
            # Unwrap each item in the list
            item_schema = schema.get('items', {})
            return [self._recursive_unwrap(item, item_schema) for item in model]
        elif isinstance(model, dict):
            # Unwrap each value in the dictionary
            return {key: self._recursive_unwrap(value, schema['properties'].get(key, {}))
                    for key, value in model.items()}
        else:
            # Delegate type conversion to the convert_type function
            return self._convert_type(model, schema)

    def _convert_type(self, value: Any, schema: Dict[str, Any]) -> Any:
        schema_type = schema.get('type', 'string')
        schema_format = schema.get('format', '')

        # Handle string types with various formats
        if schema_type == 'string':
            if schema_format == 'date':
                return datetime.strptime(value, '%Y-%m-%d').date() if value else None
            elif schema_format == 'time':
                return datetime.strptime(value, '%H:%M:%S').time() if value else None
            elif schema_format in ['uri', 'iri', 'uri-reference', 'iri-reference', 'uri-template']:
                return urlparse(value).geturl() if value else None
            elif schema_format == 'email' or schema_format == 'idn-email':
                # Simple email validation
                return value if re.match(r'[^@]+@[^@]+\.[^@]+', value) else None
            elif schema_format == 'hostname' or schema_format == 'idn-hostname':
                return value if re.match(r'^[a-zA-Z0-9.-]+$', value) else None
            elif schema_format == 'json-pointer' or schema_format == 'relative-json-pointer':
                return value  # Assuming value is a valid JSON pointer string
            elif schema_format == 'regex':
                return re.compile(value) if value else None
            else:
                return str(value)
        # Handle number and integer types
        elif schema_type in ['number', 'integer']:
            # Convert to appropriate numeric type
            return float(value) if schema_type == 'number' else int(value)


        elif schema_type == 'boolean':
            return bool(value)

        elif schema_type == 'object':
            # Convert to dictionary if it's not already one
            if isinstance(value, dict):
                return value
            elif isinstance(value, BaseModel):
                # Unwrap Pydantic model into dict
                return value.model_dump()
            else:
                raise ValueError(f"Cannot convert type to object/dict: {type(value)}")

        elif schema_type == 'array':
            return value

        elif schema_type == 'null':
            return None

        # Add more type conversions as needed
        return value

