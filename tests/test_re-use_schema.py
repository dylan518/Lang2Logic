
import unittest
import json
from jsonschema import validate, Draft7Validator
from jsonschema.exceptions import ValidationError

# Custom imports
from Lang2Logic.generator import Generator
from Lang2Logic.response_schema import ResponseSchema

class TestSchemaUsage(unittest.TestCase):

    def setUp(self):
        api_key = "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"
        self.test_gen = Generator(api_key)
        self.schema=None
    def test_schema_is_valid_json(self):
        self.schema = self.test_gen.generate_schema("create a list of integers max length 5")
        print(type(self.schema))
        print(self.schema)

        try:
            json.loads(self.schema.to_json())  # Ensures schema is valid JSON
        except json.JSONDecodeError:
            self.fail("Generated schema is not valid JSON.")

        # Validate the generated schema
        try:
            self.assertTrue(self.schema.validate_schema(), "Generated schema is not valid.")
        except ValidationError as e:
            self.fail(f"Schema validation failed: {e}")

        response = self.test_gen.generate("return integers 1-5",self.schema)
        expected = [1, 2, 3, 4, 5]  # Define the expected output
        self.assertEqual(response, expected, "The generated list does not match the expected list.")

    def tearDown(self):
        pass




# If there's any teardown needed (usually not necessary for simple cases)
    

if __name__ == '__main__':
    unittest.main()