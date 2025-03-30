# PROJECT_PROMPT - TECHNICAL REFERENCE FOR AI ASSISTANTS

> **IMPORTANT**: This document is specifically designed as a technical reference for AI assistants.
> It contains precise variable names, routes, endpoints, and other technical details to prevent hallucinations.
> Human developers should refer to standard documentation.

```markdown
# PROJECT_PROMPT.json (AI Assistant Optimized)

## Project Overview

**Project Name:** ProjectPrompt
**Description:** A tool to generate optimized prompts for AI assistants based on codebase analysis.
**Purpose:** Improve AI understanding of project structure and functionality, minimizing hallucinations and maximizing token efficiency.

## System Architecture

**Core Components:**

* **project_prompt_generator.py:** Main entry point, orchestrates the prompt generation process.
* **gemini_api.py:** Handles interactions with the Google Gemini API, including token management and request retries.
* **vector_db.py:** Manages the vector database for semantic file selection (ChromaDB).
* **token_utils.py:** Provides token calculation functions using `vertexai` or estimations.
* **project_generator.py:** (Not provided in source code, assumed core component). Likely handles file selection logic and prompt construction.

**Data Flow:**

1. `project_prompt_generator.py` initiates the process.
2. File selection occurs based on `FILE_SELECTION_MODE` (.env): `vector`, `ai`, or `auto`.
    * `vector`: Utilizes `vector_db.py` and semantic search.
    * `ai`: Calls Gemini API for analysis.
    * `auto`: Uses heuristics.
3. Selected files are passed to the prompt generator (`project_generator.py`).
4. `project_generator.py` constructs the prompt.
5. `gemini_api.py` sends the prompt to the Gemini API and receives the response.
6. `token_utils.py` manages token counting throughout.

## Technical Reference

### Environment Variables (.env)

| Variable Name           | Description                                                                                      | Default Value     |
|-------------------------|--------------------------------------------------------------------------------------------------|-----------------|
| `GEMINI_API_KEY`        | API key for Google Gemini. **REQUIRED.**                                                        |                 |
| `FILE_SELECTION_MODE` | File selection strategy: `vector`, `ai`, `auto`.                                               | `vector`         |
| `INCLUDE_FILES`        | Comma-separated list of file paths to always include.                                            |                 |
| `EXCLUDE_FILES`        | Comma-separated list of file paths to always exclude.                                            |                 |
| `VECTOR_MODEL`         | Embedding model for vector-based selection (e.g., `all-MiniLM-L6-v2`).                           | `all-MiniLM-L6-v2` |
| `MAX_VECTOR_FILES`     | Maximum number of files selected via vector search.                                             | `20`            |
| `MIN_SIMILARITY`       | Minimum similarity threshold for vector search.                                               | `0.6`           |
| `DEBUG_AI_CALLS`      | Set to `true` to save prompts and responses for debugging.                                      | `false`        |
| `LOG_LEVEL`            | Logging verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR`.                                          |                 |


### Constants (token_utils.py)

| Constant Name | Value      | Description                                        |
|---------------|-------------|----------------------------------------------------|
| `MAX_TOKENS`  | `1800000` | Maximum token limit for Gemini 1.5 Pro API calls. |


### Functions (gemini_api.py)

```python
GeminiAPI.call_gemini_api(prompt, tokenizer=None, operation_name="API Call", source_file="", prompt_summary="") 
# Returns: str (API response text)
# Parameters:
#   prompt (str): The prompt to send to the API.
#   tokenizer: (Optional) Tokenizer object.
#   operation_name (str): Name of the operation for logging.
#   source_file (str): Path to the source file for logging.
#   prompt_summary (str): Summary of the prompt for logging.

GeminiAPI.log_token_accounting(input_tokens, output_tokens, prompt_summary="", operation_name="", source_file="")
# Returns: int (total tokens)
# Parameters:
#  input_tokens (int)
#  output_tokens (int)
#  prompt_summary (str)
#  operation_name (str)
#  source_file (str)

GeminiAPI.finalize_token_accounting()
# Returns: None

# ... other GeminiAPI functions ...
```

### Functions (token_utils.py)

```python
calculate_tokens(text, tokenizer=None)
# Returns: int (estimated or calculated token count)
# Parameters:
#   text (str)
#   tokenizer (Optional)


get_tokenizer() 
# Returns: tokenizer object or None
```


### Functions (vector_db.py)

```python
#... VectorDatabaseManager methods: add_files, query_similar_files, get_related_files.  Refer to source for parameters/returns.
```


### Classes

* `GeminiAPI` (gemini_api.py)
* `VectorDatabaseManager` (vector_db.py)

### Dependencies

* `google.generativeai` (Gemini API)
* `vertexai` (Tokenization)
* `sentence-transformers` (Embeddings - optional)
* `chromadb` (Vector database - optional)
* `requests` (HTTP requests)


## File Relationships

* `project_prompt_generator.py` uses `gemini_api.py`, `vector_db.py`, `project_generator.py` (assumed).
* `gemini_api.py` uses `token_utils.py`.
* `vector_db.py` can use `sentence-transformers`, `chromadb`, and `google.generativeai`.

## Data Structures

* Vector database (ChromaDB) stores file embeddings and metadata.
* `.env` file stores configuration parameters.


## AI Assistant Instructions

This document provides a comprehensive technical overview of the ProjectPrompt project. When working with this codebase, please refer to this document for precise information about:

* Variable names and constants
* Function signatures and parameters
* Class hierarchies and relationships
* API endpoints and parameters
* File paths and relationships
* Configuration options

Using this information will significantly reduce hallucinations and improve the accuracy of your suggestions and code completions.  Consult the "Technical Reference" section for quick lookup of specific elements.  Pay particular attention to the `FILE_SELECTION_MODE` in the `.env` file as it determines the core logic for selecting project files.  If `FILE_SELECTION_MODE` is set to `vector`, prioritize information from the `vector_db.py` file and relevant dependencies like `chromadb` and the embedding model in use (`VECTOR_MODEL`).
```