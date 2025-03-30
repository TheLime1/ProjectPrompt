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

This project aims to generate optimized prompts for AI assistants to analyze codebases effectively.  It focuses on extracting core business logic and architectural information to minimize AI hallucinations and improve the quality of AI-driven code modifications.  This system prioritizes logical understanding over specific implementation details.  The application interacts with the Google Gemini API.

## Logic Map

```mermaid
graph LR
    A[ProjectPromptGenerator.run()] --> B{README.md exists?};
    B -- Yes --> C[Read README.md];
    B -- No --> D[Skip README.md];
    C --> E[Analyze Project Structure];
    D --> E;
    E --> F[Ask AI for Important Files];
    F --> G{AI Success?};
    G -- Yes --> H[Load AI Selected Files];
    G -- No --> I[Fallback: Identify Important Files];
    H --> J[Load Files (Token Limit)];
    I --> J;
    J --> K[Generate PROJECT_PROMPT.md];
    K --> L[Finalize Token Accounting];
```

## Core Business Logic and Domain Rules

1. **File Selection:** The system prioritizes files containing core business logic, workflows, application logic, entry points, and data models. It avoids style files, static assets, tests (unless demonstrating business logic), configuration files, and external libraries.
2. **Token Limit:** The system adheres to a strict token limit (`MAX_TOKENS = 1,800,000`) when loading file contents to send to the Gemini API.  A 5% buffer is maintained below this limit.
3. **Gemini API Interaction:** The `GeminiAPI` class handles communication with the Gemini API, including authentication, request formatting, response parsing, and token usage tracking.  Retry logic is implemented to handle rate limiting (429 errors).
4. **Fallback Mechanisms:** If the Gemini API call for file selection fails, a fallback mechanism identifies important files based on predefined patterns. A fallback `PROJECT_PROMPT.md` generation is also implemented if the main Gemini API call for documentation generation fails.
5. **Token Accounting:**  Detailed token usage is logged for each API call and file loaded, including input and output token counts.  This facilitates monitoring and optimization of token consumption.
6. **Error Handling:**  The system includes error handling for API requests, file reading, and other potential issues.  Error messages are logged for debugging purposes.
7. **Ignoring Files:**  Files and directories matching specific patterns (defined in `ignored_patterns` and from `.gitignore`) are excluded from the analysis.


## Data Models

This project doesn't have explicit data models in the traditional sense.  The primary data structure used is a dictionary representing project information:

```
{
    "name": "Project Name",
    "file_count": <integer>,
    "file_tree": <string>,
    "file_contents": {
        "file_path_1": "file_content_1",
        "file_path_2": "file_content_2",
        ...
    },
    "readme_content": <string> (optional)
}
```

## Key Decision Points

* **AI File Selection:** The AI is queried to identify important files.  This is a critical decision point that affects which files are included in the `PROJECT_PROMPT.md`.
* **Token Limit Handling:** The system must decide which files to include based on the token limit. This involves calculating token usage for each file and prioritizing files based on their perceived importance.
* **Fallback Logic:**  The system relies on fallback logic for important file selection and `PROJECT_PROMPT.md` generation if the Gemini API calls fail.  These decision points determine the system's robustness in the face of API issues.

## Scope and Boundaries

**In-scope:**

* Analyzing project structure and identifying important files.
* Generating an AI-focused `PROJECT_PROMPT.md` document.
* Interacting with the Google Gemini API.
* Implementing fallback mechanisms for API and file handling failures.

**Out-of-scope:**

* Building or deploying the project.
* Running tests or performing code analysis beyond file selection.
* Implementing any specific functionality within the analyzed projects (this tool is for analysis only).
* Supporting any LLM other than Google Gemini.


## Implementation Details (For AI, Reduced Priority)

The project is implemented in Python and uses several key libraries:

* `vertexai`: For tokenization and interaction with the Gemini API (if available).
* `requests`: For making HTTP requests to the Gemini API.
* Other standard libraries: `os`, `sys`, `json`, `time`, `logging`, `pathlib`, `datetime`, `dotenv`, `re`.


This simplified and structured PROJECT_PROMPT.md is designed to be highly parsable by AI, allowing efficient access to critical information without requiring extensive text processing. This minimized approach aims to improve the effectiveness of AI assistance within the specified scope and constraints. 
```