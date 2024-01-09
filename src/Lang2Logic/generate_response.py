import json
import tempfile
import importlib.util
from langchain.prompts import PromptTemplate
from pydantic import ValidationError
from pathlib import Path
import subprocess
from pydantic import BaseModel
from typing import Type, Any, List
from typing import ForwardRef, _eval_type, List, Dict
import traceback
import sys
from langchain.output_parsers import OutputFixingParser, PydanticOutputParser, RetryWithErrorOutputParser

#custom imports
from .generate_draft_7 import SchemaGenerator
from .data_manager import DataManagement
from .response_schema import ResponseSchema


class ResponseGenerator:

    def __init__(self, llm_model, chat_model):
        self.llm_model = llm_model
        self.chat_model = chat_model
        self.schema_generator = SchemaGenerator(llm_model, chat_model)
        self.data_manager = DataManagement()
        self.generated_pydantic_model = None
        self.parser = None
        self.fixer = None

    def generate_parsers(self):
        if self.generated_pydantic_model:
            try:
                self.parser = PydanticOutputParser(
                    pydantic_object=self.generated_pydantic_model)
                self.fixer = OutputFixingParser.from_llm(parser=self.parser,
                                                         llm=self.chat_model)
                self.retry_parser = RetryWithErrorOutputParser.from_llm(
                    parser=self.parser, llm=self.chat_model)
            except Exception as e:
                self.data_manager.log_message(
                    "code_error", f"Failed to generate parsers: {e}")
                self.data_manager.log_message(
                    "user_error", f"Failed to generate parsers: {e}")
                self.data_manager.log_fatal_error(
                    f"Failed to generate parsers: {e}")
        else:
            self.data_manager.log_fatal_error(
                "No generated model available for parsing.")

    def wrap_root_in_object(self, json_schema):
        """
        Takes a JSON schema and wraps the root element in an object if it's not already an object.
        """
        # Load the schema into a dictionary if it's a string
        try:
            if self.data_manager.validate_draft_7_schema(json_schema):
                schema_dict = self.data_manager.get_response_schema_dict(
                    json_schema)
        except ValidationError as e:
            self.data_manager.log_message(
                "code_error",
                f"Please contact dylanpwilson2005@gmail.com about this error. Wrong input type. Failed to load schema into dictionary during wraping of schema: {e}"
            )
            self.data_manager.log_message(
                "user_error",
                f"During conversion of schema to validator object an error occured please contact dylanpwilson2005@gmail.com abou the error. \n Error: {e}"
            )
            self.data_manager.log_fatal_error(
                f"Failed to convert schema to validator object: {e}")
        # Check if the root type is already an object
        try:
            if schema_dict.get("type") == "object":
                return schema_dict

            # Extract $schema and any other top-level keys except for those defining the root type
            wrapped_schema = {
                key: value
                for key, value in schema_dict.items()
                if key != "type" and key != "properties" and key != "items"
            }
            wrapped_schema.update({
                "type": "object",
                "properties": {
                    "root": {
                        "type": schema_dict.get("type"),
                        "properties": schema_dict.get("properties"),
                        "items": schema_dict.get("items")
                    }
                },
                "required": ["root"]
            })
        except Exception as e:
            self.data_manager.log_message(
                "code_error",
                f"Please contact dylanpwilson2005@gmail.com about this error. Failed to remove root during wraping of schema: {e}"
            )
            self.data_manager.log_message(
                "user_error",
                f"During conversion of schema to validator object an error occured please contact dylanpwilson2005@gmail.com about the error. \n Error: {e}"
            )
            self.data_manager.log_fatal_error(
                f"Failed to convert schema to validator object: {e}")

        return wrapped_schema

    def load_schema_to_pydantic(self, schema):
        """
        loads a schema into a pydantic model
        """
        #retrieve schema from data manager
        try:
            schema = self.data_manager.get_draft_7_schema()
            if not schema:
                self.data_manager.log_message(
                    "code_error", "No schema provided to create validator.")
                self.data_manager.log_fatal_error(
                    "Please contact dylanpwilson2005@gmail.com regarding this bug. No schema provided to create validator."
                )
        except ValidationError as e:
            self.data_manager.log_message(
                "code_error",
                f"Please contact Please contact dylanpwilson2005@gmail.com regarding this bug. Schema could not be retireved.Error{e}"
            )
        schema = ResponseSchema(schema)
        schema_dict = self.wrap_root_in_object(schema.to_dict())

        try:
            with tempfile.NamedTemporaryFile(mode='w+',
                                             suffix='.json',
                                             delete=False) as temp_input:
                json.dump(schema_dict, temp_input)
                temp_input.flush()

                output_file = Path(temp_input.name).with_suffix('.py')
                subprocess.run([
                    sys.executable, '-m', 'datamodel_code_generator',
                    '--input', temp_input.name, '--input-file-type',
                    'jsonschema', '--output',
                    str(output_file)
                ],
                               check=True)
                print(f"Generated Pydantic models at: {output_file}")
        except Exception as e:
            self.data_manager.log_message(
                "code_error", f"Failed to generate Pydantic models: {e}")
            self.data_manager.log_message(
                "user_error", f"Failed to generate Pydantic models: {e}")
            self.data_manager.log_fatal_error(
                "Failed to generate Pydantic models. Ensure dependencies are up to date and check permissions."
            )
            return None
        self.generated_pydantic_model = self.import_generated_models(
            output_file)
        print(self.generated_pydantic_model)

        return self.generated_pydantic_model

    def import_generated_models(self, output_file):
        try:
            # Execute the entire Python file
            namespace = {}
            with open(output_file, "r") as file:
                exec(file.read(), namespace)

            # Collect only Pydantic models from the namespace
            all_models: Dict[str, Type[BaseModel]] = {
                name: cls
                for name, cls in namespace.items()
                if isinstance(cls, type) and issubclass(cls, BaseModel)
            }
            print(f"ALL MODELS{all_models}")
            top_level_model = self.find_top_level_model(all_models)
            if top_level_model:
                top_level_model.update_forward_refs()
            if not top_level_model:
                self.data_manager.log_fatal_error("failed to get top level")

            print(top_level_model.schema())

            return top_level_model
        except Exception as e:
            self.data_manager.log_fatal_error(
                f"Error importing generated models: {e}TRACEBACK{traceback.format_exc()}"
            )
            return None

    def find_top_level_model(self, all_models: Dict[str, Type[BaseModel]]):
        referenced_models = set()
        print(f"all_models{all_models}")

        # Collect all models that are referenced in other models
        all_models.pop('BaseModel', None)
        for model in all_models.values():
            for field_name, field in model.__fields__.items():
                print(field)
                field_type = self.get_field_type(field)
                if field_type in all_models.values():
                    referenced_models.add(field_type)
                if hasattr(field_type, '__args__'):
                    for arg in getattr(field_type, '__args__', []):
                        if arg in all_models.values():
                            referenced_models.add(arg)
        print(all_models.values())
        # Identify top-level models (not referenced by any other model)
        top_level_models = [
            model for model in all_models.values()
            if model not in referenced_models
        ]

        return top_level_models[0] if top_level_models else None

    def construct_template(self):
        # Construct the prompt
        print(f"parser{self.parser}")
        prompt = PromptTemplate(
            template=
            "Return the desired value for this query in the correct format.\n{format_instructions}\n{query}\n",
            input_variables=["query"],
            partial_variables={
                "format_instructions": self.parser.get_format_instructions()
            },
        )
        return prompt

    def get_field_type(self, field: Any) -> Type[Any]:
        if hasattr(field, 'type_'):
            return field.type_
        elif hasattr(field, 'outer_type_'):
            return field.outer_type_
        else:
            return type(field)

    def un_wrap_dict(self, dict_object):
        """
        Extracts internal data from a Pydantic model dump.
        If the model dump contains a 'root' key, it returns the value of 'root'.
        Otherwise, it returns the entire model dump.
        """
        try:
            if 'root' in dict_object and isinstance(dict_object['root'], list):
                return dict_object['root']
            return dict_object
        except Exception as e:
            self.data_manager.log_message(
                "code_errors", f"Failed to convert to desired object: {e}")
            self.data_manager.log_fatal_error(
                f"Failed to generate response: {e}")

    def handle_output(self, parsed_output):
        if not parsed_output:
            self.data_manager.log_fatal_error("Parsed output is empty")
        try:
            dict_output = self.un_wrap_dict(parsed_output.dict())
            self.data_manager.log_schema_generation_message(dict_output)
            self.data_manager.set_response(dict_output)
            self.data_manager.set_schema_generation_success(True)
            return dict_output
        except Exception as e:
            raise Exception(
                f"Failed to convert to desired object and handle parsed output: {e}"
            )

    def retry_with_error(self, output):
        try:
            prompt = self.data_manager.get_prompt()
            if not prompt:
                self.data_manager.log_fatal_error(
                    "Failed to get prompt. Value is None")
        except ValueError as e:
            self.data_manager.log_fatal_error(f"Failed to get prompt: {e}")
        try:
            _input = prompt.format_prompt(query=self.data_manager.get_prompt())
            response = self.retry_parser.parse_with_prompt(output, _input)
            self.handle_output(response)
        except Exception as e:
            self.data_manager.log_fatal_error(
                f"Failed to retry parse: {e} TRACEBACK: TRACEBACK{traceback.format_exc()}"
            )

    def retry_parse(self, output):
        try:
            parsed_output = self.parser.parse(output)
            dict_output = self.handle_output(parsed_output)
            return dict_output
        except ValueError as e:
            self.data_manager.add_try_schema_generation()
            self.data_manager.log_message(
                "warnings",
                f"Failed to parse output during schema generation\n Error: {e}\nResponse: {output}"
            )
            try:
                fixed_output = self.fixer.parse(output)
                dict_output = self.handle_output(fixed_output)
                return dict_output
            except Exception as ex:
                self.data_manager.add_try_schema_generation()
                self.data_manager.log_message(
                    "warnings",
                    f"Failed to parse output after fixing output during schema generation. \n Error: {e}\nResponse: {output}"
                )
                try:
                    self.retry_with_error(output)
                except Exception as ex:
                    self.data_manager.add_try_schema_generation()
                    self.data_manager.set_schema_generation_success(False)
                    self.data_manager.log_fatal_error(
                        f"Failed to fix and parse output with prompt. \nOutput:{output} \n Error: {ex}"
                    )
        return None

    def generate(self, prompt, schema=None):
        if not self.data_manager.get_prompt():
            self.data_manager.log_fatal_error("No prompt provided")
        if schema:
            if not isinstance(schema, ResponseSchema):
                self.data_manager.log_message(
                    "code_errors", f"f{schema} is not a valid schema")
                self.data_manager.log_fatal_error(
                    "Invalid schema used as paramater for generate_response report error to dylanpwilson2005@gmail.com"
                )
        else:
            self.data_manager.log_message(
                "code_errors", "No schema provided generating schema")
            self.data_manager.log_fatal_error(
                "Nonetype. Invalid schema used as paramater for generate_response report error to dylanpwilson2005@gmail.com"
            )

        # Load the schema into a Pydantic model
        self.load_schema_to_pydantic(schema)
        self.data_manager.log_message(
            "logs", "Schema loaded into Pydantic model\nSchema\n")
        #generate parsers
        self.generate_parsers()
        try:
            # Construct the query
            prompt = self.construct_template()
            #make request
        except Exception as e:
            self.data_manager.log_message("code_errors",
                                          f"Failed to construct query: {e}")
            self.data_manager.log_fatal_error(
                f"Failed to construct query: {e}")

        try:
            # Generate the response
            _input = prompt.format_prompt(query=self.data_manager.get_prompt())
            response = self.chat_model.invoke(_input.to_string(),
                                              max_tokens=3000)

            # Generate the respons
            print(response.content)
            return self.retry_parse(response.content)
        except Exception as e:
            self.data_manager.log_message(
                "warnings",
                f"Failed to generate response from language model: {e}")
            self.data_manager.log_fatal_error(
                f"Failed to generate response: {e}TRACEBACK{traceback.format_exc()}"
            )
