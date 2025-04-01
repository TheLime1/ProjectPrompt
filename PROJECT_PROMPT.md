# PROJECT_PROMPT - TECHNICAL REFERENCE FOR AI ASSISTANTS

> **IMPORTANT**: This document is specifically designed as a technical reference for AI assistants.
> It contains precise variable names, routes, endpoints, and other technical details to prevent hallucinations.
> Human developers should refer to standard documentation.

```markdown
# PROJECT_PROMPT.json (AI Assistant Optimized)

## Project Overview

**Project Name:** ProjectPrompt
**Description:** A tool to generate optimized prompts for AI assistants based on codebase analysis.
**Purpose:** Enhance AI understanding of project structure and functionality for improved code generation and assistance.

## System Architecture

**Primary Components:**

1. **ProjectPromptGenerator:** Main entry point, orchestrates the prompt generation process.
2. **GeminiAPI:** Handles communication with the Google Gemini API for AI-powered analysis and prompt generation.
3. **VectorDatabaseManager:** Manages vector embeddings and similarity search for file selection.
4. **TokenUtils:** Provides token calculation utilities.

**Data Flow:**

1. **ProjectPromptGenerator** initializes **VectorDatabaseManager** to create file embeddings and **TokenUtils** for token counting.
2. **ProjectPromptGenerator** analyzes project structure and selects relevant files using the chosen file selection mode (vector, ai, or auto).
3. **ProjectPromptGenerator** generates an optimized prompt based on the selected files and their content using both local analysis and calls to the **GeminiAPI**.
4. **GeminiAPI** interacts with the Google Gemini API, sending prompts and receiving generated content.
5. **ProjectPromptGenerator** compiles the final `PROJECT_PROMPT.md` file.
6. **TokenUtils** tracks token usage and provides estimates for prompt sizes.
7. **Logger** records all operations and potential errors for debugging and analysis.

## Technical Reference

### File Selection Modes

| Mode     | Description                                                          | Dependencies                                   |
| -------- | -------------------------------------------------------------------- | --------------------------------------------- |
| `vector` | Semantic search of file contents using vector embeddings.             | `sentence-transformers`, `chromadb`          |
| `ai`     | AI-driven analysis of file tree structure (no content analysis).    | Google Gemini API                             |
| `auto`   | Rule-based heuristics based on file types, names, and content patterns. | None                                          |

### Configuration (.env)

| Variable                | Description                                                                  | Default Value                     |
| ----------------------- | ---------------------------------------------------------------------------- | --------------------------------- |
| `GEMINI_API_KEY`       | API key for Google Gemini.                                                  | (Required)                        |
| `FILE_SELECTION_MODE` | File selection mode.                                                           | `vector`                          |
| `INCLUDE_FILES`        | Comma-separated list of file patterns to always include.                      | (Empty)                           |
| `EXCLUDE_FILES`        | Comma-separated list of file patterns to always exclude.                      | (Empty)                           |
| `VECTOR_MODEL`         | Embedding model name for vector-based selection.                              | `all-MiniLM-L6-v2`                |
| `MAX_VECTOR_FILES`    | Maximum number of files to select with vector mode.                           | `20`                              |
| `MIN_SIMILARITY`       | Minimum similarity threshold for vector-based selection (0.0-1.0).              | `0.6`                             |
| `DEBUG_AI_CALLS`       | Enable debugging of AI API calls (saves prompts and responses).               | `false`                           |
| `LOG_LEVEL`            | Logging verbosity level (`DEBUG`, `INFO`, `WARNING`, `ERROR`).              | `INFO`                            |



### Constants (token_utils.py)

| Constant     | Value       | Description                                        |
|--------------|-------------|----------------------------------------------------|
| `MAX_TOKENS` | `1800000` | Maximum token limit for Gemini 1.5 Pro.           |


### Functions (token_utils.py)

```
calculate_tokens(text, tokenizer=None) -> int
get_tokenizer() -> Tokenizer
```


### Classes (vector_db.py)

```
VectorDatabaseManager(root_dir: str, api_key: Optional[str] = None, model_name: str = DEFAULT_MODEL)
    add_files(file_paths: List[str], file_contents: Dict[str, str]) -> bool
    query_similar_files(query: str, n_results: int = 10) -> List[Dict]
    get_related_files(file_path: str, n_results: int = 5) -> List[Dict]
```

### Classes (gemini_api.py)

```
GeminiAPI(api_key, debug_ai_calls=False)
    call_gemini_api(prompt, tokenizer=None, operation_name="API Call", source_file="", prompt_summary="") -> str
    log_token_accounting(input_tokens, output_tokens, prompt_summary="", operation_name="", source_file="") -> int
    finalize_token_accounting()
```



## Dependencies

- `requests`
- `sentence-transformers` (optional, for vector-based selection)
- `chromadb` (optional, for vector-based selection)
- `vertexai` (for tokenization, though fallback exists)
- `google.generativeai` (for fallback embedding)


## Conclusion

This PROJECT_PROMPT.json provides a structured and technically precise overview of the ProjectPrompt project for AI assistants. This format aims to minimize hallucinations and improve the accuracy of AI-generated code and suggestions by providing readily accessible information about key components, configuration options, and implementation details.
```