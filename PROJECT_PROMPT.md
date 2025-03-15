# PROJECT_PROMPT - FOR AI ASSISTANTS ONLY

> **IMPORTANT**: This document is specifically designed for AI assistants to understand this codebase efficiently. 
> It is not intended for human developers. Developers should refer to README.md and other project documentation.
> The structure and content of this file are optimized to improve AI reasoning and reduce token usage.

```markdown
# PROJECT_PROMPT - FOR AI ASSISTANTS ONLY

> **IMPORTANT**: This document is specifically designed for AI assistants to understand this codebase efficiently. 
> It is not intended for human developers. Developers should refer to README.md and other project documentation.
> The structure and content of this file are optimized to improve AI reasoning and reduce token usage.

```json
{
  "name": "ProjectPrompt",
  "primary_purpose": "Generates AI-ready project documentation.",
  "status": "Early development",
  "key_files": [
    "project_prompt_generator.py"
  ],
  "technology_stack": ["Python"],
  "dependencies": [
    "requests", 
    "vertexai", 
    "python-dotenv"
  ],
  "architecture": "Single Python script with helper functions."
}
```

## File Structure and Relationships

```
ProjectPrompt/
├── PROJECT_PROMPT.md
├── README.md
├── project_prompt_generator.py
└── test/
    └── token_calc.py
```

`project_prompt_generator.py` is the main script.  `test/token_calc.py` contains test code. `README.md` provides a basic human-readable overview. This `PROJECT_PROMPT.md` is exclusively for AI use.


## Key File Details

### project_prompt_generator.py (Path: `project_prompt_generator.py`)

**Purpose:** Core logic for generating the AI-focused project prompt.

**Key Functionality:**

* Analyzes project directory structure.
* Identifies important files (using AI assistance or fallback methods).
* Reads file contents, respecting token limits.
* Generates `PROJECT_PROMPT.md` using Gemini API.
* Provides fallback prompt generation if API fails.  Uses Vertex AI for tokenization if available, otherwise estimates.
* Includes logging to file and console.
* Ignores common patterns (`.git`, `.vscode`, image files, etc.) and patterns from `.gitignore`


## Technology Stack and Dependencies

* **Python:** Primary programming language.
* **requests:** For HTTP requests (Gemini API interaction).
* **vertexai:** Google Cloud's Vertex AI (tokenization).
* **python-dotenv:** For loading environment variables (Gemini API key from `.env`).

## Architecture Overview

This project employs a simple, single-script architecture. `project_prompt_generator.py` contains all the core functionality.


## AI Assistant Usage Notes

* **Primary Focus:** `project_prompt_generator.py` contains the most relevant logic.
* **Token Optimization:** This document is highly structured for minimal token usage. Use the JSON metadata and key file summaries for efficient querying.
* **Gemini Interaction:** The project uses the Gemini API.  The `call_gemini_api` function handles API calls. The API key is expected in a `.env` file as `GEMINI_API_KEY`.  Set `DEBUG_AI_CALLS=true` in `.env` for detailed logging of API interactions.
* **Test Code:** `test/token_calc.py` is related to token calculation.



```


Key improvements for AI efficiency in this version:

* **JSON metadata:** Provides a concise, structured summary of the project.
* **Reduced redundancy:** Eliminated duplicated information and unnecessary explanations.
* **Simplified file structure description:**  More compact representation.
* **Concise key file summaries:** Focus on essential information for AI.
* **Clearer AI usage notes:** Actionable guidance for AI assistants.
* **Reduced overall length:**  Shorter text means fewer tokens.
* **Specific function names and environment variables:**  Makes it easier for AI to locate and understand key elements.


This optimized `PROJECT_PROMPT.md` provides a much more efficient way for AI assistants to understand the project's key aspects without processing excessive text. It facilitates quicker code understanding, faster query responses, and reduced token consumption.