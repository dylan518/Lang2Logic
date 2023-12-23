import json
from Lang2Logic.generator import Generator
from Lang2Logic.generate_response import ResponseGenerator
from Lang2Logic.response_schema import ResponseSchema
from pydantic import BaseModel
from enum import Enum
from typing import Any, Dict, List, Type


def read_text_file(file_path):
    """
    Reads the contents of a text file and returns it as a string.

    Args:
    file_path (str): The path to the text file.

    Returns:
    str: The contents of the file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return "File not found."
    except Exception as e:
        return f"An error occurred: {e}"
    
def read_json_file(file_path):
    """
    Reads the contents of a JSON file and returns it as a dictionary.

    Args:
    file_path (str): The path to the JSON file.

    Returns:
    dict: The contents of the file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return "File not found."
    except Exception as e:
        return f"An error occurred: {e}"

def append_to_json(file_path, new_data):
    """
    Appends new data to an existing JSON file. If the file doesn't exist, it creates a new one.

    Args:
    file_path (str): The path to the JSON file.
    new_data (dict): The new data to be added to the JSON file.
    """
    try:
        # Read the existing data
        data=read_json_file(file_path)
        # Update with new data
        data.update(new_data)

        # Write the updated data back to the file
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4)

        print("JSON file updated successfully.")
    except json.JSONDecodeError:
        print("Error: The file is not a valid JSON file.")
    except Exception as e:
        print(f"An error occurred: {e}")



gen = Generator("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")
schema=gen.generate_schema(read_text_file("C:\\Users\\dylan\\Documents\\GitHub\\Lang2Logic\\tests\\schema_prompt.txt"))
print(f"IS VALID {schema.validate_schema()}")
prompts=["write the gpt tool dictionary for a function that takes in bash command, runs it and returns the output of the command. Just outline the gpt-structure as definded schema.", "Write a tool dictionary for a function that allows gpt to upload files to itself. Just outline the gpt-structure as definded schema no need to implement.", "Write a function that allows gpt to run python code. Just outline the gpt-structure as definded schema no need to implement."]
titles=["run_bash_command", "upload_files", "run_python_code"]
for i in range(len(prompts)):
    print(f"Schema:{schema}")
    try:
        function_schema=gen.generate(prompts[i],schema)

    except Exception as e:
        print(f"An error occurred: {e}")
        continue
    print(f"Function Schema:{function_schema}")
    function_schema=ResponseSchema(function_schema)
    function_schema.save_to_json(key=titles[i], filepath='C:\\Users\\dylan\Documents\\GitHub\\Lang2Logic\\tests\\file.json')