import os
from langchain_community.chat_models import ChatOpenAI
from langchain.llms import OpenAI
import warnings



#custom imports
from .generate_draft_7 import SchemaGenerator
from .generate_response import ResponseGenerator
from .response_schema import ResponseSchema
from .data_manager import DataManagement
from .model_unwrap import SchemaModelUnwrapper


#suprress warnings
# Suppress PydanticDeprecatedSince20 warnings from pydantic module
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic.*")

# Suppress UserWarning from langchain_community.llms.openai module
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_community.llms.openai")

# Suppress DeprecationWarning from langchain_core.prompts.prompt module
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain_core.prompts.prompt")

# Suppress PydanticDeprecatedSince20 warnings from langchain.output_parsers.pydantic module
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain.output_parsers.pydantic")

# Suppress PydanticDeprecatedSince20 warnings from langchain.output_parsers.pydantic module
warnings.filterwarnings("ignore", category=DeprecationWarning, 
                        message=".*`pydantic.config.Extra` is deprecated.*",
                        module='pydantic.*')


# Suppress PydanticDeprecatedSince20 warnings from pydantic.main module
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic.main")



class Generator:
    def __init__(self, api_key):
        self.data_manager=DataManagement()
        self.data_manager.reset_data_except_instructions()
        if not api_key:
            self.data_manager.log_fatal_error("API key must be used to initialize the generator")
                                            
        if not isinstance(api_key, str):
            self.data_manager.log_fatal_error("API key must be a string")
        try:
            os.environ["OPENAI_API_KEY"] = api_key
            self.chat_model = ChatOpenAI(temperature=0, model_name='gpt-4-1106-preview')
            self.llm_model = OpenAI(temperature=0, model_name='gpt-4-1106-preview')
        except Exception as e:
            self.data_manager.log_fatal_error(f"Failed to initialize models: {e}")
        self.schema_generator = SchemaGenerator(self.llm_model, self.chat_model)
        self.ResponseGenerator = ResponseGenerator(self.llm_model, self.chat_model)
    
    def check_input_as_string(self, input):
        if not isinstance(input, str):
            self.data_manager.log_fatal_error("Input must be a string")

        if len(input) > 800000:
            self.data_manager.log_fatal_error("Input must be less than 800000 characters")

        return input

    def set_schema(self, schema):
        Unverified_Schema= ResponseSchema(schema)
        if Unverified_Schema.validate_schema():
            self.data_manager.set_draft_7_schema(Unverified_Schema)
            return True
        else:
            return False 
    
    
    def generate_schema(self, query):
        self.data_manager.reset_data_except_instructions()
        self.data_manager.set_prompt(query)
        self.schema_generator.generate_draft_7()
        schema=ResponseSchema(self.data_manager.get_draft_7_schema())
        self.data_manager.pretty_print()
        return schema
    
    def generate(self, query, schema=None):
        if schema is not None:
            self.data_manager.reset_data_except_instructions()
            self.data_manager.set_prompt(query)
            if not self.set_schema(schema):
                self.data_manager.log_fatal_error("Invalid schema used as parameter for generate_response")
        else:
            schema=self.generate_schema(query)
        model=self.ResponseGenerator.generate(query,schema)
        try:
            schema=ResponseSchema(self.data_manager.get_draft_7_schema()).to_dict()
            unwrapper=SchemaModelUnwrapper(schema=schema, data_manager=self.data_manager)
            return unwrapper.unwrap(model)
        except Exception as e:
            self.data_manager.log_fatal_error(f"Failed to unwrap model: {e}")
            
         

