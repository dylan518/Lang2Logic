

import os
import unittest
import json
from langchain_community.chat_models import ChatOpenAI
from langchain.llms import OpenAI

#custom imports

from Lang2Logic.generator import Generator

class TestSchemaGenerator(unittest.TestCase):
    def setUp(self):
        self.test_gen = Generator("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")
    
    def test_schema_for_list_of_strings(self):
        # Using a simple question that should result in a list of strings schema
        question = "return a list of colors"
        schema = self.test_gen.generate_schema(question)
        generated_schema = schema.to_json()

        self.assertIsNotNone(generated_schema, "Failed to generate JSON schema")

        # Define the expected schema for a list of strings
        expected_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "array",
            "items": {
                "type": "string"
            }
        }

        try:
            generated_schema_dict = json.loads(generated_schema)
        except json.JSONDecodeError as e:
            self.fail(f"Invalid JSON: {e}")

        # Assert that the generated schema matches the expected schema
        self.assertEqual(generated_schema_dict, expected_schema, "Generated schema does not match the expected schema for a list of strings")


if __name__ == '__main__':
    unittest.main()
