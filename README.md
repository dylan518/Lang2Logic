# Lang2Logic Python Package

## Introduction
Lang2Logic: Transforming Natural Language into Python Code with Ease.

## Overview
Lang2Logic is an innovative Python package designed for developers who need to translate natural language prompts into structured Python outputs. Utilizing advanced language processing algorithms, Lang2Logic simplifies generating Python code from verbal or written descriptions.

## Key Features
- **Natural Language to Python Conversion**: Converts natural language instructions into Python code, facilitating easier programming and automation.
- **Dynamic Schema Generation**: Automatically generates schema from natural language inputs, providing structured outputs like lists, dictionaries, etc.
- **Flexible API Integration**: User-friendly API for seamless integration with existing Python projects.

## Installation and Usage
```python
import os
from Lang2Logic.generator import Generator

# Initialize with API key
self.test_gen = Generator(os.environ.get("YOUR_API_KEY"))

# Generate schema from natural language
schema = self.test_gen.generate_schema("return a list of strings")

# Use schema for generating structured outputs
self.test_gen.generate("5 colors", schema)
# Output: ["red", "yellow", "green", "blue", "red"]
```

## Automatic Schema Generation
```python
self.test_gen.generate("return a list of strings with 5 colors")
# Output: ["color1", "color2", "color3", "color4", "color5"]
```

## Example Usage
### Classifying Decisions and Preferences
```python
schema = self.test_gen.generate_schema("return a dictionary with keys 'rational' and 'decision' (boolean)")

potential_buyers = []
for user in users_data_json["bios"]:
    decision = self.test_gen.generate(f"return true if this user might be interested in products related to rock climbing.\nUser Bio:\n{user['bio']}", schema)
    if decision["decision"]:
        potential_buyers.append(user)
```

## Roadmap
- Function Generation
- Optimized Logic for Increased Accuracy
- Code Parsing and LLM integration tools
- Python Agents

## Bug Reporting and Contributions
Found a bug or have a suggestion? Please contact dylanpwilson2005@gmail.com.

## License
Lang2Logic is available under a Creative Commons license and may not be used for commercial purposes without explicit consent from the author.
