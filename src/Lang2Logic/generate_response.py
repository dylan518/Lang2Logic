import json
import tempfile
import importlib.util
from langchain.prompts import PromptTemplate
from pydantic import ValidationError
from pathlib import Path
import subprocess
from langchain.output_parsers import OutputFixingParser, PydanticOutputParser, RetryWithErrorOutputParser


#custom imports
from .generate_draft_7 import SchemaGenerator
from .data_manager import DataManagement
from .response_schema import ResponseSchema




class ResponseGenerator:
    def __init__(self,llm_model,chat_model):
        self.llm_model = llm_model
        self.chat_model=chat_model
        self.schema_generator = SchemaGenerator(llm_model,chat_model)
        self.data_manager=DataManagement()
        self.generated_pydantic_model = None
        self.parser = None
        self.fixer = None

    def generate_parsers(self):
        if self.generated_pydantic_model:
            try:
                self.parser = PydanticOutputParser(pydantic_object=self.generated_pydantic_model)
                self.fixer = OutputFixingParser.from_llm(parser=self.parser, llm=self.chat_model)
                self.retry_parser=RetryWithErrorOutputParser.from_llm(parser=self.parser, llm=self.chat_model)
            except Exception as e:
                self.data_manager.log_message("code_error",f"Failed to generate parsers: {e}")
                self.data_manager.log_message("user_error",f"Failed to generate parsers: {e}")
                self.data_manager.log_fatal_error(f"Failed to generate parsers: {e}")
        else:
            self.data_manager.log_fatal_error("No generated model available for parsing.")
    
    def wrap_root_in_object(self,json_schema):
        """
        Takes a JSON schema and wraps the root element in an object if it's not already an object.
        """
        # Load the schema into a dictionary if it's a string
        try:
            if self.data_manager.validate_draft_7_schema(json_schema):
                schema_dict=self.data_manager.get_response_schema_dict(json_schema)
        except ValidationError as e:
            self.data_manager.log_message("code_error",f"Please contact dylanpwilson2005@gmail.com about this error. Wrong input type. Failed to load schema into dictionary during wraping of schema: {e}")
            self.data_manager.log_message("user_error",f"During conversion of schema to validator object an error occured please contact dylanpwilson2005@gmail.com abou the error. \n Error: {e}")
            self.data_manager.log_fatal_error(f"Failed to convert schema to validator object: {e}")
        # Check if the root type is already an object
        try:
            if schema_dict.get("type") == "object":
                return schema_dict

            # Extract $schema and any other top-level keys except for those defining the root type
            wrapped_schema = {key: value for key, value in schema_dict.items() if key != "type" and key != "properties" and key != "items"}
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
            self.data_manager.log_message("code_error",f"Please contact dylanpwilson2005@gmail.com about this error. Failed to remove root during wraping of schema: {e}")
            self.data_manager.log_message("user_error",f"During conversion of schema to validator object an error occured please contact dylanpwilson2005@gmail.com about the error. \n Error: {e}")
            self.data_manager.log_fatal_error(f"Failed to convert schema to validator object: {e}")


        return wrapped_schema



    def load_schema_to_pydantic(self, schema):
        """
        loads a schema into a pydantic model
        """
        #retrieve schema from data manager
        try:
            schema = self.data_manager.get_draft_7_schema()
            if not schema:
                self.data_manager.log_message("code_error","No schema provided to create validator.")
                self.data_manager.log_fatal_error("Please contact dylanpwilson2005@gmail.com regarding this bug. No schema provided to create validator.")
        except ValidationError as e:
            self.data_manager.log_message("code_error",f"Please contact Please contact dylanpwilson2005@gmail.com regarding this bug. Schema could not be retireved.")
        schema_dict = self.wrap_root_in_object(schema)

        # Write the schema to a temporary file as a pydantic model
        
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp_input:
            try:
                json.dump(schema_dict, temp_input)
                temp_input.flush()
                
                output_file = Path(temp_input.name).with_suffix('.py')
                # Run datamodel-codegen as a Python module
                subprocess.run([
                    'python', '-m', 'datamodel_code_generator',
                    '--input', temp_input.name,
                    '--input-file-type', 'jsonschema',
                    '--output', str(output_file)
                ], check=True)
            except Exception as e:
                self.data_manager.log_message("code_error",f"failed to generate pydantic model from schema: {e}")
                self.data_manager.log_message("user_error",f"failed to generate pydantic model from schema: {e}")
                self.data_manager.log_fatal_error(f"failed to generate pydantic model from schema ensure dependencies are up to date and check permisions")
            try:
                #execute the generated module and import the model
                spec = importlib.util.spec_from_file_location("generated_module", str(output_file))
                generated_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(generated_module)
                # Directly access the StringListModel class
                if hasattr(generated_module, 'Model'):
                    self.generated_pydantic_model = getattr(generated_module, 'Model')
                else:
                    self.generated_pydantic_model = None

                return self.generated_pydantic_model
            except Exception as e:
                self.data_manager.log_message("code_error",f"failed to import generated module: {e}")
                self.data_manager.log_message("user_error",f"failed to import generated module: {e}")
                self.data_manager.log_fatal_error(f"failed to import generated module. If problem persists please contact dylanpwilson2005@gmail.com")



    def construct_template(self):
        # Construct the prompt
        prompt = PromptTemplate(
            template="Return the desired value for this query in the correct format.\n{format_instructions}\n{query}\n",
            input_variables=["query"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
            )
        return prompt
    
    def un_wrap_dict(self,dict_object):
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
            self.data_manager.log_message("code_errors",f"Failed to convert to desired object: {e}")
            self.data_manager.log_fatal_error(f"Failed to generate response: {e}")
    
    def handle_output(self,parsed_output):
        if not parsed_output:
            self.data_manager.log_fatal_error("Parsed output is empty")
        try:
            dict_output = self.un_wrap_dict(parsed_output.model_dump())
            self.data_manager.log_schema_generation_message(dict_output)
            self.data_manager.set_response(dict_output)
            return dict_output
        except Exception as e:
            raise Exception (f"Failed to convert to desired object and handle parsed output: {e}")
    
        
    def retry_with_error(self,output):
        try:
            prompt=self.data_manager.get_prompt()
            if not prompt:
                self.data_manager.log_fatal_error("Failed to get prompt. Value is None")
        except ValueError as e:
            self.data_manager.log_fatal_error(f"Failed to get prompt: {e}")
        try:
            response=self.retry_parse(output, prompt)
            self.handle_output(response)
        except Exception as e:
            self.data_manager.log_fatal_error(f"Failed to retry parse: {e}")
        


        
    def retry_parse(self,output):
        try:
            parsed_output = self.parser.parse(output)
            dict_output=self.handle_output(parsed_output)
            return dict_output
        except ValueError as e:
            self.data_manager.log_message("warnings",f"Failed to parse output during schema generation\n Error: {e}\nResponse: {output}")
            try:
                fixed_output = self.fixer.parse(output)
                self.handle_output(fixed_output)
            except Exception as ex:
                self.data_manager.log_message("warnings",f"Failed to parse output after fixing output during schema generation. \n Error: {e}\nResponse: {output}")
                try:
                    self.retry_with_error(output)
                except Exception as ex:
                    self.data_manager.log_fatal_error(f"Failed to fix and parse output with prompt. \nOutput:{output} \n Error: {ex}")
        return None
        
        
    def generate(self,prompt,schema=None):
        if not self.data_manager.get_prompt():
            self.data_manager.log_fatal_error("No prompt provided")
        if schema:
            if not isinstance(schema, ResponseSchema):
                self.data_manager.log_message("code_errors",f"f{schema} is not a valid schema")
                self.data_manager.log_fatal_error("Invalid schema used as paramater for generate_response report error to dylanpwilson2005@gmail.com")
        else:
            self.data_manager.log_message("code_errors","No schema provided generating schema")
            self.data_manager.log_fatal_error("Nonetype. Invalid schema used as paramater for generate_response report error to dylanpwilson2005@gmail.com")
            
        # Load the schema into a Pydantic model
        self.load_schema_to_pydantic(schema)
        self.data_manager.log_message("logs","Schema loaded into Pydantic model\nSchema\n")
        #generate parsers
        self.generate_parsers()
        try:
            # Construct the query
            prompt = self.construct_template()
            #make request
            _input = prompt.format_prompt(query=self.data_manager.get_prompt())
        except Exception as e:
            self.data_manager.log_message("code_errors",f"Failed to construct query: {e}")
            self.data_manager.log_fatal_error(f"Failed to construct query: {e}")
            
        try:
            # Generate the response
            response = self.llm_model.generate(prompts=[_input.to_string()])
            
            # Extract the output text from the response
            if response.generations:
                output = response.generations[0][0].text  # Accessing the first Generation object's text
                self.data_manager.log_schema_generation_message(output)
                self.data_manager.log_schema_generation_message(output)
            else:
                output = ""
                self.data_manager.log_fatal_error("The language model did not generate output for the schema generation")
        except Exception as e:
            self.data_manager.log_message("warnings",f"Failed to generate response from language model: {e}")
            self.data_manager.log_fatal_error(f"Failed to generate response: {e}")
        
        return self.retry_parse(output)
     

    



