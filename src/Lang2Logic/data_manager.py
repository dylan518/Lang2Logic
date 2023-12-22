import json
import os
from datetime import datetime
import warnings
from jsonschema import validate
from jsonschema import Draft7Validator

import jsonschema
import functools

#custom imports
from .response_schema import ResponseSchema

class DataManagement:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(DataManagement, cls).__new__(cls)
            cls._instance.initialize(*args, **kwargs)
        return cls._instance


    def initialize(self):
        file_path_relative="app_data.json"
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.file_path = os.path.join(dir_path, file_path_relative)
        self.data=None
        self.reset_data_except_instructions()
        # Load data from the file
        
    
    def file_operation_wrapper(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            try:
                return method(self, *args, **kwargs)
            except FileNotFoundError:
                raise FileNotFoundError(f"Error retrieving app data. File not found: {self.file_path}")
            except json.JSONDecodeError as e:
                raise ValueError(f"Error decoding JSON data in file: {self.file_path}. Error: {e}")
            except Exception as e:
                raise Exception(f"Error during file operation ({self.file_path}): {str(e)}")
        return wrapper


    
    @staticmethod
    def error_handling(method):
        """Decorator to catch errors and log them as fatal."""
        def wrapper(self, *args, **kwargs):
            try:
                return method(self, *args, **kwargs)
            except Exception as e:
                self.log_fatal_error(f"Error in {method.__name__}: {str(e)}")
                raise  # Re-raise the exception for further handling or termination
        return wrapper
    
    def reset_data_except_instructions(self):
        self.data = self.initialize_data()

    @file_operation_wrapper
    def initialize_data(self):
        return {
            "response_process": {
                "prompt": "",
                "schema_generation": {
                    "messages": [],
                    "tries": 0,
                    "success": False
                },
                "response_generation": {
                    "messages": [],
                    "tries": 0,
                    "Response": None,
                    "success": False
                }
            },
            "settings": {},
            "user_errors": [],
            "code_errors": [],
            "warnings": [],
            "logs": [],
            "instructions": {
        "draft-7": "Given the desired output from the instructions generate a draft-7 schema. Example: instructions: create a list of strings where each string is a method in the a bankaccount class draft-7 schema/output: {\n  \"$schema\": \"http://json-schema.org/draft-07/schema#\",\n  \"description\": \"A list of method names for a BankAccount class\",\n  \"type\": \"array\",\n  \"items\": {\n    \"type\": \"string\"\n  }\n}"
    },
            "fatal_errors": [],
            "draft_7_schema": None
        }
    @file_operation_wrapper
    def save_to_json(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"The app data could not be found. {self.file_path} does not exist.")
        try:
            with open(self.file_path, 'w') as file:
                json.dump(self.data, file, indent=4)
        except Exception as e:
            raise OSError(f"Failed to save data to JSON. Error: {e}\n Data: {self.data}\n File path: {self.file_path}")
    

    def log_fatal_error(self, error_message):

        timestamp = datetime.now().isoformat()
        error_entry = {"timestamp": timestamp, "error_message": error_message}
        self.data['fatal_errors'].append(error_entry)
        raise Exception(error_message)
    
    @error_handling
    def log_message(self, message_type, message):
        valid_message_types = ['user_errors', 'code_errors', 'warnings', 'logs']
        if message_type not in valid_message_types:
            warnings.warn(f"Warning: Invalid message type '{message_type}'. Valid types are {valid_message_types}.")
            return

        timestamp = datetime.now().isoformat()
        entry = {"timestamp": timestamp, "message": message}

        if message_type in self.data:
            self.data[message_type].append(entry)
        else:
            self.data[message_type] = [entry]

    # Methods allowing edit and read access to data
    @error_handling
    def set_prompt(self, prompt):
        self.data['response_process']['prompt'] = prompt

    @error_handling
    def get_prompt(self):
        return self.data['response_process']["prompt"]

    @error_handling
    def log_schema_generation_message(self, message):
        self.data['response_process']['schema_generation']['messages'].append(message)

    @error_handling
    def increment_schema_generation_tries(self):
        self.data['response_process']['schema_generation']['tries'] += 1

    @error_handling
    def set_schema_generation_success(self, success):
        self.data['response_process']['schema_generation']['success'] = success

    @error_handling
    def log_response_generation_message(self, message):
        self.data['response_process']['response_generation']['messages'].append(message)

    @error_handling
    def increment_response_generation_tries(self):
        self.data['response_process']['response_generation']['tries'] += 1

    @error_handling
    def set_response_generation_success(self, success):
        self.data['response_process']['response_generation']['success'] = success

    # Methods for settings
    @error_handling
    def update_setting(self, key, value):
        self.data['settings'][key] = value
    
    @error_handling
    def get_setting(self, key):
        return self.data['settings'].get(key)
    
    @error_handling
    def set_draft_7_schema(self, schema):
        self.data['draft_7_schema'] = ResponseSchema(schema).to_dict()
    
    @error_handling
    def get_draft_7_schema(self):
        return ResponseSchema(self.data['draft_7_schema'])
    
    @error_handling
    def validate_draft_7_schema(self,schema):
        schema=ResponseSchema(schema)
        return schema.validate_schema()
    
    @error_handling
    def load_response_schema(self,schema):
        return ResponseSchema(schema)
    
    @error_handling
    def get_response(self,schema):
        return self.data['response_process']['response_generation']['Response']
    
    @error_handling
    def set_response(self,Response):
        self.data['response_process']['response_generation']['Response']=Response

    @error_handling
    def get_response_schema_dict(self,schema):
        return ResponseSchema(schema).to_dict()
    
    @error_handling
    def validate_response(self,response):
        if not self.get_draft_7_schema():
            raise ValueError("No schema has been generated yet")
        try:
            schema=ResponseSchema(self.get_draft_7_schema())
        except:
            raise ValueError("Invalid schema")
        if schema.validate_schema():
            return True
        else:
            return False
        
    @error_handling
    def get_instruction_by_key(self, key):
        """Retrieve instruction data based on a specific key."""
        try:
            # Retrieve instructions from data
            instructions = self.data["instructions"]

            # Check if the key exists in instructions
            if key in instructions:
                return instructions[key]
            else:
                raise KeyError(f"Key '{key}' not found in instructions.")
        
        except KeyError as e:
            
            # Optionally, handle the KeyError further or re-raise it
            raise KeyError(f"Error: {e}")
        except Exception as e:
            # Handle any other exceptions
            raise Exception(f"Error: {e}")