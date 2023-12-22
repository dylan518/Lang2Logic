
import unittest
from unittest.mock import patch, mock_open
import json
from Lang2Logic.data_manager import DataManagement  # Adjust the import as per your project structure

class TestDataManagement(unittest.TestCase):

    def setUp(self):
        self.file_path = "app_data.json"
        self.test_data = {
            "response_process": {
                "prompt": "",
                "schema_generation": {"messages": [], "tries": 0, "success": False},
                "response_generation": {"messages": [], "tries": 0, "Response": None, "success": False}
            },
            "settings": {},
            "user_errors": [],
            "code_errors": [],
            "warnings": [],
            "logs": [],
            "draft_7_schema": None,
            "fatal_errors": [],
            "instructions": {
        "draft-7": "Given the desired output from the instructions generate a draft-7 schema. Example: instructions: create a list of strings where each string is a method in the a bankaccount class draft-7 schema/output: {\n  \"$schema\": \"http://json-schema.org/draft-07/schema#\",\n  \"description\": \"A list of method names for a BankAccount class\",\n  \"type\": \"array\",\n  \"items\": {\n    \"type\": \"string\"\n  }\n}"
    },
        }
        self.dm = DataManagement()

    def test_set_prompt(self):
        test_prompt = "Test prompt"
        self.dm.set_prompt(test_prompt)
        self.assertEqual(self.dm.get_prompt(), test_prompt)

    def test_error_handling_decorator(self):
        with patch.object(self.dm, 'log_fatal_error') as mock_log_fatal_error:
            @self.dm.error_handling
            def method_that_raises(self):
                raise ValueError("Test exception")

            # Try to catch the general Exception and assert its message
            try:
                method_that_raises(self.dm)
                self.fail("ValueError was expected but not raised")
            except Exception as e:
                # Check if the exception message is as expected
                self.assertIn("Test exception", str(e))
                mock_log_fatal_error.assert_called_once_with("Error in method_that_raises: Test exception")



    # Test for error handling decorator
    def test_error_handling_decorator(self):
        with patch.object(self.dm, 'log_fatal_error') as mock_log_fatal_error:
            @self.dm.error_handling
            def method_that_raises(self):
                raise ValueError("Test exception")

            # Expect any exception (not just ValueError)
            with self.assertRaises(Exception) as context:
                method_that_raises(self.dm)
            
            self.assertIn("Test exception", str(context.exception))
            mock_log_fatal_error.assert_called_once_with("Error in method_that_raises: Test exception")


    # Add additional tests to simulate different error scenarios

if __name__ == '__main__':
    unittest.main()
