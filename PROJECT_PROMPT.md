# PROJECT_PROMPT - FOR AI ASSISTANTS ONLY

> **IMPORTANT**: This document is specifically designed for AI assistants to understand this codebase efficiently. 
> It is not intended for human developers. Developers should refer to README.md and other project documentation.
> This document focuses on the core logic flows and business rules to prevent hallucinations and improve AI response quality.

```markdown
# PROJECT_PROMPT - FOR AI ASSISTANTS ONLY

> **IMPORTANT**: This document is specifically designed for AI assistants to understand this codebase efficiently. 
> It is not intended for human developers. Developers should refer to README.md and other project documentation.
> This document focuses on the core logic flows and business rules to prevent hallucinations and improve AI response quality.

## Project Overview: ProjectPrompt

This project aims to generate optimized prompts for AI assistants to understand codebases, thereby reducing hallucinations and enhancing AI-driven code modifications.  It analyzes the project's file structure, identifies key files based on predefined criteria and AI assistance, extracts their contents, and constructs a structured PROJECT_PROMPT.md file.

## Logic Map

```mermaid
graph LR
    A[ProjectPromptGenerator.run()] --> B{README.md exists?};
    B -- Yes --> C[Read README.md];
    B -- No --> D[Skip README.md];
    C --> E[Analyze Project Structure];
    D --> E;
    E --> F[AI File Selection];
    F --> G[Load File Contents (Token Limit)];
    G --> H[Generate PROJECT_PROMPT.md];
    H --> I[Finalize Token Accounting];
```

## Core Business Logic and Domain Rules

1. **File Selection:** Prioritizes files containing core business logic, workflows, application logic, entry points, and data models.  Avoids style files, assets, tests (unless demonstrating business logic), configurations, and external libraries.  Uses AI for intelligent selection and a fallback mechanism based on filename patterns if AI selection fails.

2. **Token Limit:** Adheres to a strict token limit (1,800,000) when loading file contents to prevent exceeding API limits.  Prioritizes loading the most important files.

3. **Prompt Generation:** Constructs a PROJECT_PROMPT.md containing structured information about the project including the file tree, important file contents, and logical architecture. This prompt is optimized for AI understanding, not human readability.

4. **Token Accounting:** Logs all API interactions and file loads, calculating token usage for each operation to maintain transparency and aid in efficient resource utilization.


## Data Model

The core data managed within this project is represented by a dictionary stored in the `project_data` variable within `project_generator.py`. This dictionary contains the following key-value pairs:

* `"name"`: The project's name (string).
* `"file_count"`:  Total number of files in the project (integer).
* `"file_tree"`: String representation of the project's file tree.
* `"file_contents"`: Dictionary where keys are file paths (string) and values are the file contents (string).
* `"readme_content"`: Content of README.md (string, optional - only if present).

## Key Decision Points and Business Rules

* **AI File Selection Success:** If the AI successfully identifies important files, those are prioritized.  Otherwise, a fallback method using regular expressions selects important files based on file name patterns.
* **Token Limit Exceeded:** If including a file's content exceeds the token limit, the file is skipped, and a warning is logged.
* **API Call Failure:** If the Gemini API call fails during PROJECT_PROMPT.md generation, a fallback mechanism creates a simplified PROJECT_PROMPT.md file.

## Component Interaction

* `project_prompt_generator.py`: Main entry point. Instantiates and runs the `ProjectPromptGenerator`.
* `project_generator.py`: Contains the core logic for analyzing project structure, interacting with the Gemini API, and generating PROJECT_PROMPT.md.
* `gemini_api.py`: Handles communication with the Google Gemini API, including token accounting and error handling.
* `token_utils.py`: Provides utility functions for calculating tokens and obtaining the tokenizer.

## Scope and Boundaries

**In-scope:**  Analyzing project structure, identifying important files, generating an AI-optimized PROJECT_PROMPT.md, and managing token usage.

**Out-of-scope:** Implementing code modifications suggested by AI, providing human-readable documentation, analyzing code semantics beyond file selection, supporting other AI models besides Gemini.


## Implementation Details (For AI Reference Only)

The code uses Python 3 and relies on several libraries, including `os`, `re`, `json`, `time`, `pathlib`, `datetime`, `dotenv`, `requests`, and potentially `vertexai`.  It employs regular expressions for file filtering, JSON for data serialization, and the Gemini API for prompt generation.

The code maintains detailed logging for debugging and token accounting. It has error handling for API issues and fallback mechanisms for AI file selection and prompt generation failures.
```