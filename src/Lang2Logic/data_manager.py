import json
import os
from datetime import datetime
import warnings
from jsonschema import validate
import jsonschema
import functools

#custom imports
from .response_schema import ResponseSchema


class DataManagement:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(DataManagement, cls).__new__(cls)
            # Initialize instance variables here
            cls._instance.initialize(*args, **kwargs)
        return cls._instance

    def initialize(self):
        file_path_relative="app_data.json"
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.file_path = os.path.join(dir_path, file_path_relative)

        # Load data from the file
        self.data = self.load_data()
    
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
    def save_before_execution(method):
        """Decorator to save data to JSON before method execution."""
        def wrapper(self, *args, **kwargs):
            self.save_to_json()  # Save current state before changes
            return method(self, *args, **kwargs)  # Execute the actual method
        return wrapper
    
    @staticmethod
    def error_handling(method):
        """Decorator to catch errors and log them as fatal."""
        def wrapper(self, *args, **kwargs):
            try:
                return method(self, *args, **kwargs)
            except Exception as e:
                self.log_fatal_error(f"Error in {method.__name__}: {str(e)}")
                return None  # Re-raise the exception for further handling or termination
        return wrapper
    
    @file_operation_wrapper
    def load_data(self):
        # Check if the file exists
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"The file {self.file_path} does not exist. Please re-install the python package Lang2Logic as the app data cannot be found.")

        with open(self.file_path, 'r') as file:
            data = json.load(file)
        

        # Check if the instructions key exists and has data
        try:
            data.get('instructions')
        except KeyError:
            raise KeyError(f"Instructions key not found in the file. \nDATA: {data}")
        
        self.data=data

        return data

    @file_operation_wrapper
    def reset_data_except_instructions(self):
        self.load_data()
        instructions = self.data.get('instructions')
        self.data = self.initialize_data()
        self.data['instructions'] = instructions
        self.save_to_json()
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
            "instructions": None,
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
    

    @save_before_execution
    def log_fatal_error(self, error_message):

        timestamp = datetime.now().isoformat()
        error_entry = {"timestamp": timestamp, "error_message": error_message}
        self.data['fatal_errors'].append(error_entry)
        self.save_to_json()
        print(f"Fatal error encountered: {error_message}")
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
    
    def set_prompt(self, prompt):
        self.data['response_process']['prompt'] = prompt

    
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
        return self.data['draft_7_schema']
    
    @error_handling
    def validate_draft_7_schema(self,schema):
        schema=ResponseSchema(schema)
        return schema.validate()
    
    @error_handling
    def load_response_schema(self,schema):
        return ResponseSchema(schema)
    
    @error_handling
    def get_response_schema_dict(self,schema):
        return ResponseSchema(schema).to_dict()
    
    @error_handling
    def validate_response(self,response):
        if not self.get_draft_7_schema():
            raise ValueError("No schema has been generated yet")
        try:
            schema=ResponseSchema(self.get_draft_7_schema()).to_dict
        except:
            raise ValueError("Invalid schema")
        try:
            validate(instance=response, schema=schema)
            return True
        except jsonschema.exceptions.ValidationError as e:
            return False
        
    @error_handling
    def get_instruction_by_key(self, key):
        """Retrieve instruction data based on a specific key."""
        try:
            # Retrieve instructions from data
            instructions = self.data.get('instructions', {})

            # Check if the key exists in instructions
            if key in instructions:
                return instructions[key]
            else:
                raise KeyError(f"Key '{key}' not found in instructions.")
        
        except KeyError as e:
            print(f"Error: {e}")
            # Optionally, handle the KeyError further or re-raise it
            raise
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            # Handle any other exceptions
            raise