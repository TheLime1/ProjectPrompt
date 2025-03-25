# PROJECT_PROMPT - FOR AI ASSISTANTS ONLY

> **IMPORTANT**: This document is specifically designed for AI assistants to understand this codebase efficiently. 
> It is not intended for human developers. Developers should refer to README.md and other project documentation.
> This document focuses on the core logic flows and business rules to prevent hallucinations and improve AI response quality.

```markdown
# PROJECT_PROMPT - FOR AI ASSISTANTS ONLY

> **IMPORTANT**: This document is specifically designed for AI assistants to understand this codebase efficiently. 
> It is not intended for human developers. Developers should refer to README.md and other project documentation.
> This document focuses on the core logic flows and business rules to prevent hallucinations and improve AI response quality.

## Project Overview

**Name:** ProjectPrompt
**Purpose:** This project automatically generates a PROJECT_PROMPT.md file designed to help AI assistants understand the structure and logic of a given codebase.  This improves the accuracy and efficiency of AI-assisted code modifications.

## Logic Map

```mermaid
graph LR
    A[ProjectPromptGenerator.run()] --> B{README.md exists?};
    B -- Yes --> C[Read README.md];
    B -- No --> D[Log warning];
    C --> E[Analyze project structure];
    D --> E;
    E --> F[Ask AI for important files];
    F --> G{AI Selection Successful?};
    G -- Yes --> H[Load selected files];
    G -- No --> I[Fallback file selection];
    H --> J[Generate PROJECT_PROMPT.md];
    I --> H;
    J --> K[End];
```

## Data Model

This project does not have a persistent data model. It operates on in-memory data derived from the target project's file system and content. Key data elements include:

* **file_tree:** A list of file paths relative to the project root.
* **file_contents:** A dictionary mapping file paths to their content.
* **important_files:** A list of file paths deemed important by fallback logic, used if AI selection fails.
* **ai_selected_files:**  A list of file paths suggested by the AI as important for understanding the project.
* **readme_content:**  The content of README.md, if present.

## Core Business Logic and Domain Rules

1. **File Selection:**  The core logic involves selecting the most relevant files for AI analysis.  This is done by:
    * Asking an LLM (Gemini) to identify important files based on the file tree and README.md.
    * If the LLM fails to provide a valid list, a fallback mechanism identifies important files using regular expressions matching common file names and locations.
2. **File Content Loading:**  The content of the selected files is loaded into memory, respecting token limits to avoid exceeding the LLM's capacity.
3. **Prompt Generation:** The loaded file content and project metadata are structured into a JSON object and passed to the LLM to generate the PROJECT_PROMPT.md.
4. **Fallback Prompt Generation:** If the LLM fails to generate the PROJECT_PROMPT.md, a fallback mechanism creates a simplified version containing the file tree and a list of important files.
5. **Ignoring Files:** Certain files and directories (e.g., .git, .vscode, node_modules, image files) are excluded from analysis to reduce noise and focus on the core logic. The `.gitignore` file is used to extend the list of ignored files and directories.


## Key Decision Points and Business Rules

* **AI Selection vs. Fallback:** If the AI fails to provide a valid list of files, the system falls back to a rule-based selection method.
* **Token Limit:** File loading respects a predefined token limit to ensure the generated prompt does not exceed the LLM's capacity.
* **File Ignoring:** Files matching predefined patterns are consistently ignored.

## Component Interaction

1. **`project_prompt_generator.py`**: The main entry point orchestrates the process.
2. **`project_generator.py`**: Contains the core logic for file selection, content loading, and prompt generation.
3. **`gemini_api.py`**: Handles interaction with the Gemini API, including request formatting, error handling, and retries.
4. **`token_utils.py`**: Provides utility functions for token calculation and tokenizer retrieval.

## Out of Scope

This project does not include:

* Code analysis beyond file selection.
* Modification of the target codebase.
* Generation of documentation for human consumption.
* Support for all programming languages or project structures.

This document is designed to minimize AI hallucinations by providing a clear, concise, and structured representation of the project's core logic.  It prioritizes logical architecture over implementation details, guiding AI assistants towards relevant information and preventing them from generating solutions outside the project's scope.
```