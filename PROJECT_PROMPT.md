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

This project aims to generate an optimized `PROJECT_PROMPT.md` file for AI assistants to understand the structure and logic of a given codebase. This generated file is intended to improve the accuracy and efficiency of AI-driven code modifications by minimizing hallucinations and focusing on relevant files and logic.

## Logic Map

```mermaid
graph LR
    A[ProjectPromptGenerator.run()] --> B{README.md exists?};
    B -- Yes --> C[Read README.md];
    B -- No --> D[Analyze project structure];
    C --> D;
    D --> E[Ask AI for important files];
    E --> F{AI Success?};
    F -- Yes --> G[Load selected files];
    F -- No --> H[Fallback file selection];
    G --> I[Generate PROJECT_PROMPT.md];
    H --> G;
    I --> J[End];
```

## Core Business Logic and Domain Rules

1. **Project Analysis:** The core logic revolves around analyzing a project's directory structure, identifying key files (with AI assistance or fallback mechanisms), extracting their content, and summarizing the project's architecture and logic within the `PROJECT_PROMPT.md`.

2. **File Selection:**  The application prioritizes files containing core business logic, workflows, data models, and main entry points.  It de-prioritizes style files, static assets, test files (unless demonstrating business logic), build configuration, and external libraries.

3. **Token Management:**  The application carefully manages token usage to stay within the API limits.  It calculates token counts for files and prompts and selectively includes files in `PROJECT_PROMPT.md` based on available token budget.

4. **AI Interaction:** The application interacts with a Large Language Model (LLM) via the Gemini API.  It constructs prompts to request the LLM to identify important files and generate the AI-focused documentation.

5. **Fallback Mechanisms:**  If the AI-driven file selection or documentation generation fails, the application employs fallback methods to ensure a basic `PROJECT_PROMPT.md` is still generated.  This fallback relies on predefined file patterns and includes a simplified representation of the project.

## Data Models and Relationships

There are no explicit data models persisted in this project.  The primary data structures are in-memory representations of:

- **File Tree:** A list of file paths relative to the project root.
- **File Contents:** A dictionary mapping file paths to their string content.
- **Project Information:** A dictionary containing metadata about the project (name, file count, etc.).

These data structures are used to construct the prompt sent to the LLM and to generate the final `PROJECT_PROMPT.md` file.

## Key Decision Points and Business Rules

- **AI File Selection Success:** If the LLM successfully identifies important files, these files are prioritized for inclusion in `PROJECT_PROMPT.md`. Otherwise, the fallback file selection logic is triggered.
- **Token Limit:** The application continuously monitors token usage.  If including a file would exceed the predefined token limit, the file is skipped.
- **Gemini API Availability:** The application relies on the Gemini API. If the API call fails (e.g., due to network issues or rate limiting), the application resorts to generating a fallback `PROJECT_PROMPT.md`.

## Scope and Boundaries

**In-scope:**
- Analyzing project file structure.
- Identifying important files.
- Generating AI-focused documentation (`PROJECT_PROMPT.md`).
- Managing token usage within API limits.
- Providing fallback mechanisms for core functionalities.

**Out-of-scope:**
- Code execution or analysis beyond file identification.
- Project-specific logic interpretation beyond identifying key files and workflows.
- Implementing AI-driven code changes.
- Supporting other LLMs besides Gemini.


## Implementation Details (For AI Reference Only)

The code is written in Python and uses the following key libraries:

- `os`, `sys`, `pathlib`: File system operations.
- `re`: Regular expressions for file pattern matching.
- `json`: JSON serialization and deserialization.
- `requests`: HTTP requests for Gemini API interaction.
- `vertexai`: (If available) Tokenization for accurate token counting.
- `logging`: Logging for debugging and status updates.
- `dotenv`: Environment variable loading.


This detailed `PROJECT_PROMPT.md` is designed to guide AI assistants, enabling them to work more efficiently with the ProjectPrompt codebase by focusing on the core logic and avoiding hallucinations.
```