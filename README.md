# ProjectPrompt

ProjectPrompt is a tool that analyzes your codebase and creates specialized prompts for AI assistants to better understand your project's structure and functionality.

## Features

- **Intelligent File Selection**: Multiple strategies to identify the most important files in your project
- **Vector Database Integration**: Semantic search to find functionally related files
- **Automatic Context Creation**: Generates AI-optimized context for better code understanding
- **Token Optimization**: Prioritizes content to maximize the value of your token budget
- **Detailed Logging**: Keeps track of token usage and AI interactions

## Roadmap:

- [x] Enhanced file picking with vector database integration
- [x] Make the prompt more technical ("logic","little from everything")
- [x] Vector database for semantic file selection
- [x] Improve logging
- [x] Better token calculation (logging too)
- [ ] Make it a pip package

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/TheLime1/ProjectPrompt.git
   cd ProjectPrompt
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Copy the example configuration file:
   ```
   cp .env.example .env
   ```

4. Add your Google Gemini API key to the `.env` file:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

## Usage

Run the project prompt generator:

```
python project_prompt_generator.py
```

The tool will:
1. Analyze your project structure
2. Select important files using the configured selection method
3. Generate a `PROJECT_PROMPT.md` file optimized for AI assistants

## File Selection Modes

ProjectPrompt supports multiple file selection strategies:

1. **Vector-based Selection** (default):  
   Uses a vector database with embeddings to understand file contents semantically.
   Requires `sentence-transformers` and `chromadb` packages.

2. **AI-based Selection**:  
   Uses the Gemini API to analyze the file tree structure (without examining file contents).

3. **Automatic Selection**:  
   Uses rule-based heuristics based on file types, names, and content patterns.

## Configuration

You can configure ProjectPrompt by editing the `.env` file:

```properties
# File selection mode: "vector", "ai", or "auto"
FILE_SELECTION_MODE=vector

# Custom file inclusion patterns (comma-separated)
INCLUDE_FILES=main.py,config.json,src/core/

# Custom file exclusion patterns (comma-separated)
EXCLUDE_FILES=tests/,__pycache__/
```

See `.env.example` for all available configuration options.

## License

[MIT License](LICENSE)
