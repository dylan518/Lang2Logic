

import os
import unittest
import json
from langchain_community.chat_models import ChatOpenAI
from langchain.llms import OpenAI
from jsonschema import Draft7Validator

#custom imports

from Lang2Logic.generator import Generator

class TestSchemaGenerator(unittest.TestCase):
    def setUp(self):
        self.test_gen = Generator("YOUR API KEY HERE")
    
    def test_schema_for_list_of_strings(self):
        # Using a simple question that should result in a list of strings schema
        question = "return a list of colors"
        generated_schema = self.test_gen.generate_schema(question)

        self.assertIsNotNone(generated_schema, "Failed to generate JSON schema")

        # Define the expected schema for a list of strings
        expected_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "array",
            "items": {
                "type": "string"
            }
        }
        print(generated_schema)
        # Assert that the generated schema matches the expected schema
        try:
            Draft7Validator.check_schema(generated_schema)
            valid=True
        except Exception as e:
            valid=False
        self.assertEqual(valid, True, "Generated schema does not match the expected schema for a list of strings")


if __name__ == '__main__':
    unittest.main()

