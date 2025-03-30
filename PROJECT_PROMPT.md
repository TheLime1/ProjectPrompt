# PROJECT_PROMPT - TECHNICAL REFERENCE FOR AI ASSISTANTS

> **IMPORTANT**: This document is specifically designed as a technical reference for AI assistants.
> It contains precise variable names, routes, endpoints, and other technical details to prevent hallucinations.
> Human developers should refer to standard documentation.

# PROJECT_PROMPT - TECHNICAL REFERENCE FOR AI ASSISTANTS

> **IMPORTANT**: This document is specifically designed as a technical reference for AI assistants.
> It contains precise variable names, routes, endpoints, and other technical details to prevent hallucinations.
> Human developers should refer to standard documentation.

## Project Overview

**Name:** ProjectPrompt
**Purpose:** Generate optimized prompts for AI coding assistants based on project code.
**Main Functionality:** Analyzes project structure, identifies important files with AI assistance or fallback methods, extracts technical details, and generates a PROJECT_PROMPT.md/json file for AI tools.

## File Structure Map

```
Project File Structure:
├── PROJECT_PROMPT.md
├── README.md
├── gemini_api.py
├── project_generator.py
├── project_prompt_generator.py
├── token_utils.py
└── test/
    └── token_calc.py

```

## Technical Reference: Key Components

### 1. Project Generator (`project_generator.py`)

**Class:** `ProjectPromptGenerator`

**Key Variables:**

| Variable Name          | Type             | Description                                                            | Defined In                                          |
|-----------------------|-----------------|--------------------------------------------------------------------|------------------------------------------------------|
| `api_key`            | `str`           | Gemini API key.                                                        | `__init__`                                           |
| `debug_ai_calls`    | `bool`          | Flag to enable detailed logging of AI interactions.                   | `__init__`                                           |
| `root_dir`           | `str`           | Project root directory.                                                 | `__init__`                                           |
| `file_tree`          | `list`          | List of file paths in the project.                                 | `analyze_project_structure`                         |
| `important_files`    | `list`          | List of automatically identified important files (fallback).         | `identify_important_files_fallback`                  |
| `ai_selected_files` | `list`          | List of files selected by the AI as important.                     | `ask_ai_for_important_files`                        |
| `file_contents`      | `dict`          | Dictionary of file paths and their contents.                           | `load_files_under_token_limit`                      |
| `readme_exists`      | `bool`          | Flag indicating if a README.md file exists.                         | `check_readme`                                      |
| `readme_content`     | `str`           | Content of the README.md file.                                     | `check_readme`                                      |
| `ignored_patterns`   | `list`          | List of regex patterns for files/directories to ignore.             | `__init__` and `add_gitignore_patterns`              |
| `tokenizer`          | `Tokenizer`     | Tokenizer object for Gemini.                                         | `__init__`                                           |
| `api_client`        | `GeminiAPI`     | Instance of the GeminiAPI client.                                  | `__init__`                                           |



**Key Methods:**

| Method Name                          | Description                                                                            |
|------------------------------------|------------------------------------------------------------------------------------|
| `__init__(self, api_key=None)`      | Constructor: Initializes the generator, loads API key, sets up logging and ignores. |
| `add_gitignore_patterns(self)`      | Reads and adds ignore patterns from .gitignore.                                       |
| `generate_file_tree_string(self)` | Creates a string representation of the file tree.                                 |
| `ask_ai_for_important_files(self)` | Queries the AI to identify important files.                                       |
| `load_files_under_token_limit(self)` | Loads file contents, respecting the token limit.                                    |
| `run(self)`                         | Main execution method for the generator.                                             |
| `check_readme(self)`               | Checks for README.md and loads its content.                                           |
| `analyze_project_structure(self)`  | Analyzes project structure and builds the file tree.                             |
| `read_file_content(self, file_path)` | Reads and returns the content of a given file.                                      |
| `generate_project_prompt(self)`    | Generates the PROJECT_PROMPT.md/json file.                                   |
|`create_fallback_project_prompt(self)`| Creates a basic PROJECT_PROMPT.txt if API fails.                                   |



### 2. Gemini API Client (`gemini_api.py`)

**Class:** `GeminiAPI`

**Key Variables:**

| Variable Name          | Type      | Description                                                                     |
|-----------------------|-----------|------------------------------------------------------------------------------|
| `api_key`            | `str`      | Gemini API key.                                                                |
| `debug_ai_calls`    | `bool`     | Flag to enable saving full API requests and responses.                         |
|`token_accounting_file`| `str`      | Path to the token usage log file.                                          |
| `prompt_counter`      | `int`      | Counter for API prompts.                                                        |
| `total_input_tokens` | `int`      | Total input tokens sent to the API.                                              |
| `total_output_tokens`| `int`      | Total output tokens received from the API.                                      |


**Key Methods:**

| Method Name                              | Description                                                                          |
|----------------------------------------|--------------------------------------------------------------------------------------|
| `__init__(self, api_key, debug_ai_calls=False)` | Constructor: Initializes API client, sets up debug logging, creates accounting file.|
| `log_token_accounting(...)`            | Records token usage for API calls and file processing.                               |
|`finalize_token_accounting(self)`        | Adds a grand total row for tokens to accounting file.                                |
| `call_gemini_api(...)`                  | Makes a call to the Gemini API. Handles retries and rate limiting.             |

### 3. Token Utilities (`token_utils.py`)

**Constants:**

| Constant Name    | Value       | Description                                                     |
|-----------------|-------------|-----------------------------------------------------------------|
| `MAX_TOKENS`   | 1,800,000  | Maximum token limit for Gemini requests.                         |
|`TOKENIZER_AVAILABLE`| `bool`     | Indicates whether vertexai tokenizer is available.           |


**Functions:**

| Function Name                  | Description                                                     |
|-------------------------------|-----------------------------------------------------------------|
| `calculate_tokens(text, tokenizer=None)` | Calculates or estimates the number of tokens in a text string.  |
| `get_tokenizer()`              | Returns a Gemini tokenizer object if available.                 |


## Technical Diagrams

(Due to the text-based nature of this output, complex diagrams cannot be included. However, the structured information above should allow an AI assistant to reconstruct conceptual diagrams if needed.)


## AI Technical Assistance Guidelines

When working with this codebase:

- Use exact variable names, routes, function signatures as listed in the technical reference.
- Reference the precise technical details to avoid hallucinations.
- Respect the existing architectural patterns when suggesting code modifications.

This technical reference was automatically generated to help AI assistants understand the project's implementation details.