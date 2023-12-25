from Lang2Logic.model_unwrap import SchemaModelUnwrapper
import unittest
from pydantic import BaseModel
from typing import List
from enum import Enum



# Mock Data Management class
class TestDataManagement:
    def log_fatal_error(self, message: str):
        print(f"Fatal Error: {message}")

# Test Enum
class Color(Enum):
    RED = 'red'
    GREEN = 'green'
    BLUE = 'blue'

# Pydantic Models for Testing
class TestModel(BaseModel):
    name: str
    age: int

class ColorModel(BaseModel):
    favorite_color: Color

class Address(BaseModel):
    city: str
    country: str

class Person(BaseModel):
    name: str
    address: Address

class HobbyModel(BaseModel):
    hobbies: List[str]

# JSON Schemas
test_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"}
    }
}

color_schema = {
    "type": "object",
    "properties": {
        "favorite_color": {"type": "string"}
    }
}

address_schema = {
    "type": "object",
    "properties": {
        "city": {"type": "string"},
        "country": {"type": "string"}
    }
}

person_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "address": address_schema
    }
}

hobby_schema = {
    "type": "object",
    "properties": {
        "hobbies": {
            "type": "array",
            "items": {"type": "string"}
        }
    }
}

# Unit Test Class
class TestSchemaModelUnwrapper(unittest.TestCase):
    def test_unwrap_simple_model(self):
        data_manager = TestDataManagement()
        unwrapper = SchemaModelUnwrapper(schema=test_schema, data_manager=data_manager)

        test_model = TestModel(name="John", age=30)
        result = unwrapper.unwrap(test_model)
        self.assertEqual(result, {"name": "John", "age": 30})

    def test_unwrap_with_enum(self):
        data_manager = TestDataManagement()
        unwrapper = SchemaModelUnwrapper(schema=color_schema, data_manager=data_manager)

        test_model = ColorModel(favorite_color=Color.RED)
        result = unwrapper.unwrap(test_model)
        self.assertEqual(result, {"favorite_color": "red"})

    def test_unwrap_with_nested_model(self):
        data_manager = TestDataManagement()
        unwrapper = SchemaModelUnwrapper(schema=person_schema, data_manager=data_manager)

        test_model = Person(name="Alice", address=Address(city="Wonderland", country="Fantasy"))
        result = unwrapper.unwrap(test_model)
        expected = {"name": "Alice", "address": {"city": "Wonderland", "country": "Fantasy"}}
        self.assertEqual(result, expected)

    def test_unwrap_with_array(self):
        data_manager = TestDataManagement()
        unwrapper = SchemaModelUnwrapper(schema=hobby_schema, data_manager=data_manager)

        test_model = HobbyModel(hobbies=["reading", "painting"])
        result = unwrapper.unwrap(test_model)
        self.assertEqual(result, {"hobbies": ["reading", "painting"]})

    def test_unwrap_with_invalid_model(self):
        data_manager = TestDataManagement()
        unwrapper = SchemaModelUnwrapper(schema=test_schema, data_manager=data_manager)

        test_model = "This is not a valid model"
        result = unwrapper.unwrap(test_model)
        self.assertIsNone(result)  # Assuming it returns None on error

if __name__ == '__main__':
    unittest.main()
