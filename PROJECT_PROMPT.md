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

This project aims to generate an optimized `PROJECT_PROMPT.md` file for AI assistants to enhance their understanding of a given codebase and prevent hallucinations during code generation. It prioritizes the logical architecture over implementation details.

## Logic Map

```mermaid
graph LR
    A[ProjectPromptGenerator.run()] --> B{README.md exists?}
    B -- Yes --> C[Read README.md]
    B -- No --> D[Analyze project structure]
    C --> D
    D --> E[Ask AI for important files]
    E --> F{AI Success?}
    F -- Yes --> G[Load AI selected files]
    F -- No --> H[Identify important files (fallback)]
    G --> I[Load files (token limit)]
    H --> I
    I --> J[Generate PROJECT_PROMPT.md]
```

## Core Business Logic and Domain Rules

1. **File Selection:** The application prioritizes files containing core business logic, workflows, application logic, entry points, and data models. It avoids style files, static assets, test files (unless demonstrating business logic), build configurations, and external libraries.  This selection is ideally done by an AI analyzing the file tree and README, but a fallback mechanism exists based on filename patterns.

2. **Token Limit:**  The application respects a token limit (`MAX_TOKENS = 1,800,000`) when loading file content.  It prioritizes the most important files and loads as many as possible within the limit, leaving a 5% buffer.

3. **Gemini API Interaction:** The application uses the Gemini API (`gemini-1.5-pro`) for two primary operations:
    - **File Selection Analysis:**  Given the file tree and README, the AI is asked to select the most important files.
    - **Project Prompt Generation:** The AI is provided with project information (name, file tree, selected file contents, README) and asked to generate the `PROJECT_PROMPT.md`.

4. **Fallback Mechanisms:** If the Gemini API call for file selection fails, a fallback mechanism identifies important files based on predefined filename patterns. If the prompt generation fails, a basic `PROJECT_PROMPT.md` is created containing the file tree and available file contents.

5. **Ignoring Files:** Files and directories matching specified patterns (including those from `.gitignore`) are excluded from processing.  These patterns target common directories for version control, IDE settings, build artifacts, dependencies, and various media/asset files.

## Data Models

The application primarily uses dictionaries and strings to represent project information.  The key data structures are:

- **`file_tree` (List[str]):** List of file paths relative to the project root.
- **`file_contents` (Dict[str, str]):** Dictionary mapping file paths to their content.
- **`important_files` (List[str]):**  List of file paths identified as important by the fallback mechanism.
- **`ai_selected_files` (List[str]):**  List of file paths selected by the AI.


## Key Decision Points and Business Rules

- **API Key:** Requires a Gemini API key (`GEMINI_API_KEY`) from a `.env` file.
- **Debug Mode:**  Controlled by the `DEBUG_AI_CALLS` environment variable.  If true, detailed logs and API responses are saved.
- **README Handling:**  If a `README.md` exists, its content is included in the information provided to the AI.
- **File Loading:** Files are loaded one by one until the token limit is approached.


## Scope and Boundaries

**In-scope:**

- Analyzing project structure and files to identify core logic.
- Generating AI-optimized documentation (`PROJECT_PROMPT.md`).
- Interacting with the Gemini API for intelligent file selection and prompt generation.
- Implementing fallback mechanisms for robustness.
- Managing token usage to stay within API limits.

**Out-of-scope:**

- Building or running the analyzed project.
- Code generation or modification (other than creating `PROJECT_PROMPT.md`).
- Implementing any functionality of the target project itself.
- Handling projects that exceed the token limit after applying optimization strategies.


## Implementation Details (For AI Reference Only)

The project is implemented in Python and uses the following key libraries:

- `vertexai`:  For tokenization (if available) and interaction with the Gemini API.
- `requests`: For making HTTP requests to the Gemini API.
- `os`, `pathlib`: For file system operations.
- `json`: For data serialization.
- `re`: For regular expressions (used in file filtering).
- `logging`: For logging and debugging.


This detailed PROJECT_PROMPT.md provides a structured understanding of the project's goals, logic, and data. It enables AI assistants to focus on relevant aspects, reduce hallucinations, and efficiently contribute to code generation or analysis tasks within the defined scope.
```