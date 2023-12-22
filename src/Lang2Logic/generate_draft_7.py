
import json
from typing import Optional, Union, List, Dict, Any

from pydantic import BaseModel, Field
from jsonschema import Draft7Validator, exceptions as jsonschema_exceptions

from langchain.llms import OpenAI
from langchain.output_parsers import OutputFixingParser, PydanticOutputParser, RetryWithErrorOutputParser
from langchain.prompts import PromptTemplate

#custom imports
from .data_manager import DataManagement



class SchemaProperty(BaseModel):
    # Basic JSON Schema fields
    type: Optional[Union[str, List[str]]] = None
    properties: Optional[Dict[str, 'SchemaProperty']] = None
    items: Optional[Union['SchemaProperty', List['SchemaProperty']]] = None
    additionalProperties: Union[bool, 'SchemaProperty'] = True
    required: Optional[List[str]] = None
    enum: Optional[List[Any]] = None
    const: Optional[Any] = None

    # String-specific fields
    maxLength: Optional[int] = None
    minLength: Optional[int] = None
    pattern: Optional[str] = None

    # Numeric-specific fields
    maximum: Optional[Union[int, float]] = None
    exclusiveMaximum: Optional[Union[int, float]] = None
    minimum: Optional[Union[int, float]] = None
    exclusiveMinimum: Optional[Union[int, float]] = None
    multipleOf: Optional[Union[int, float]] = None

    # Array-specific fields
    maxItems: Optional[int] = None
    minItems: Optional[int] = None
    uniqueItems: Optional[bool] = None

    # Object-specific fields
    maxProperties: Optional[int] = None
    minProperties: Optional[int] = None
    dependentRequired: Optional[Dict[str, List[str]]] = None
    dependentSchemas: Optional[Dict[str, 'SchemaProperty']] = None

    # Combining schemas
    allOf: Optional[List['SchemaProperty']] = None
    anyOf: Optional[List['SchemaProperty']] = None
    oneOf: Optional[List['SchemaProperty']] = None
    not_: Optional['SchemaProperty'] = Field(None, alias='not')

    # Annotations
    title: Optional[str] = None
    description: Optional[str] = None
    default: Optional[Any] = None
    examples: Optional[List[Any]] = None

    # Conditional subschemas (Draft-07)
    if_: Optional['SchemaProperty'] = Field(None, alias='if')
    then: Optional['SchemaProperty'] = None
    else_: Optional['SchemaProperty'] = Field(None, alias='else')

    # Draft-07 specific fields
    readOnly: Optional[bool] = None
    writeOnly: Optional[bool] = None
    contentMediaType: Optional[str] = None
    contentEncoding: Optional[str] = None
    comment: Optional[str] = Field(None, alias='$comment')

    class Config:
        extra = 'allow'
        populate_by_name = True

    def dict(self, **kwargs):
        return super().model_dump(by_alias=True, **kwargs)




class Draft7Schema(BaseModel):
    _raw_data: Optional[Dict[str, Any]] = None
    # Core keywords
    id_: Optional[str] = Field(default=None, alias='$id', format='uri-reference')
    ref_: Optional[str] = Field(None, alias='$ref')
    comment_: Optional[str] = Field(None, alias='$comment')

    # Other schema fields
    type: Optional[Union[str, List[str]]] = None
    properties: Optional[Dict[str, SchemaProperty]] = None
    additionalProperties: Union[bool, SchemaProperty] = True
    required: Optional[List[str]] = None
    patternProperties: Optional[Dict[str, 'SchemaProperty']] = None
    dependencies: Optional[Dict[str, Union[List[str], 'SchemaProperty']]] = None
    minProperties: Optional[int] = None
    maxProperties: Optional[int] = None

    # String validation keywords
    minLength: Optional[int] = None
    maxLength: Optional[int] = None
    pattern: Optional[str] = None
    format: Optional[str] = None  # Includes the new formats from Draft-07

    # Number validation keywords
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    exclusiveMinimum: Optional[float] = None
    exclusiveMaximum: Optional[float] = None
    multipleOf: Optional[float] = None

    # Array validation keywords
    items: Optional[Union['SchemaProperty', List['SchemaProperty']]] = None
    additionalItems: Union[bool, 'SchemaProperty'] = True
    minItems: Optional[int] = None
    maxItems: Optional[int] = None
    uniqueItems: Optional[bool] = None

    # Conditional subschemas (Draft-07)
    if_: Optional['SchemaProperty'] = Field(None, alias='if')
    then: Optional['SchemaProperty'] = None
    else_: Optional['SchemaProperty'] = Field(None, alias='else')

    # Draft-07 specific keywords
    readOnly: Optional[bool] = None
    writeOnly: Optional[bool] = None
    contentMediaType: Optional[str] = None
    contentEncoding: Optional[str] = None

    # Annotations
    title: Optional[str] = None
    description: Optional[str] = None
    default: Optional[Any] = None
    examples: Optional[List[Any]] = None

    # Keywords for hypermedia environments
    links: Optional[List[Dict[str, Any]]] = None  # For hyper-schema links

    # Additional class configuration
    class Config:
        extra = 'allow'
        populate_by_name = True
        json_encoders = {
            'SchemaProperty': lambda v: v.dict(by_alias=True,)
        }

    def dict(self, **kwargs):
        return super().model_dump(**kwargs, by_alias=True,exclude_none=True)

    def __init__(self, **data):
        # Perform JSON Schema Draft-7 validation on the input data
        try:
            Draft7Validator.check_schema(data)
        except jsonschema_exceptions.SchemaError as e:
            raise ValueError(f"Schema validation error: {e.message}") from e

        # Call the super __init__ to handle usual Pydantic initialization
        super().__init__(**data)

    def to_json(self, **kwargs):
        return super().model_dump_json(by_alias=True, exclude_none=True, **kwargs)
    







class SchemaGenerator:

    def __init__(self,llm_model,chat_model):
        self.data_manager=DataManagement()
        self.llm_model =llm_model
        self.chat_model=chat_model
        self.parser = PydanticOutputParser(pydantic_object=Draft7Schema)
        self.fixer = OutputFixingParser.from_llm(parser=self.parser, llm=self.chat_model)
        self.retry_parser=RetryWithErrorOutputParser.from_llm(parser=self.parser, llm=self.chat_model)
        self.data_manager=DataManagement()

    def construct_template(self):
        instructions=self.data_manager.get_instruction_by_key("draft-7")
        # Construct the prompt
        prompt = PromptTemplate(
            template="Based off of this task: \n{query}\nRequest: \n{format_instructions}\n",
            input_variables=["query"],
            partial_variables={
                "format_instructions": instructions
            },
        )
        return prompt
    def validate_schema(self,output):
        if not self.data_manager.validate_draft_7_schema(output):
            self.data_manager.log_message("code_errors",f"The validation allowed a non-valid response please contact dylanpwilson2005@gmail.com regarding the bug. fixed_output: {output} schema: {self.data_manager.get_draft_7_schema()}")
            self.data_manager.log_fatal_error("The validation allowed a non-valid response please contact dylanpwilson2005@gmail.com regarding the bug")
            return False
        return True
    
    def handle_output(self,output):
        dict_output=output.dict()
        if not dict_output:
            raise ValueError("Schema is empty")  
        self.data_manager.log_schema_generation_message(str(dict_output))
        if not self.validate_schema(dict_output):
            raise ValueError("Invalid schema")            
        self.data_manager.set_draft_7_schema(dict_output)
        return dict_output
    
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
        
    def generate_draft_7(self):
        try:
            # Construct the query
            prompt = self.construct_template()
            #make request
            _input = prompt.format_prompt(query=self.data_manager.get_prompt())
            prompt=self.data_manager.get_prompt()
            if not _input or not prompt:
                self.data_manager.log_fatal_error("Failed to get prompt")
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
    



        

