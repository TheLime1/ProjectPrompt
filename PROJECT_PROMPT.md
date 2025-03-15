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
    "project_prompt_generator.py",
    "README.md"
  ],
  "technology_stack": ["Python"],
  "dependencies": ["requests", "vertexai", "python-dotenv"],
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

`project_prompt_generator.py` is the main script.  `test/` contains test code (currently `token_calc.py`).  `README.md` provides a basic human-readable overview.  This `PROJECT_PROMPT.md` is for AI use only.

## Key File Details

### project_prompt_generator.py (Path: `project_prompt_generator.py`)

**Purpose:** Core logic for generating the AI-focused project prompt.

**Key Functionality:**
* Analyzes project directory structure.
* Identifies important files (using AI assistance or fallback methods).
* Reads file contents, respecting token limits.
* Generates `PROJECT_PROMPT.md` using Gemini API.
* Provides fallback prompt generation if API fails.

### README.md (Path: `README.md`)

**Purpose:**  High-level project overview (minimal for this early stage).

**Content Summary (AI-Parsed):**
* Project Title: `ProjectPrompt`
* Current Status: `soon`


## Technology Stack and Dependencies

* **Python:** Primary programming language.
* **requests:** For HTTP requests (Gemini API interaction).
* **vertexai:** Google Cloud's Vertex AI (tokenization, potentially other AI features).
* **python-dotenv:** For loading environment variables (Gemini API key).


## Architecture Overview

This project employs a simple, single-script architecture.  `project_prompt_generator.py` contains all the core functionality.  Future development might introduce a more modular design.


## AI Assistant Usage Notes:

* **Primary Focus:**  `project_prompt_generator.py` contains the most relevant logic.
* **Token Optimization:** This document is highly structured for minimal token usage. Use the JSON metadata and key file summaries for efficient querying.
* **Gemini Interaction:** The project uses the Gemini API.  The API key is expected in a `.env` file.



```