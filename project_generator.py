import os
import re
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from logger_config import logger
from token_utils import calculate_tokens, get_tokenizer, MAX_TOKENS
from gemini_api import GeminiAPI

class ProjectPromptGenerator:
    def __init__(self, api_key=None):
        logger.info("Initializing ProjectPromptGenerator")
        # Load API key from .env file if not provided
        if api_key is None:
            load_dotenv()
            self.api_key = os.getenv("GEMINI_API_KEY")
            if not self.api_key:
                logger.error("GEMINI_API_KEY not found in .env file")
                raise ValueError("GEMINI_API_KEY not found in .env file")
            else:
                logger.info("API key loaded from .env file")
        else:
            self.api_key = api_key
            logger.info("Using provided API key")
        
        # Check for debug flag in environment
        self.debug_ai_calls = os.getenv("DEBUG_AI_CALLS", "false").lower() == "true"
        if self.debug_ai_calls:
            logger.info("DEBUG_AI_CALLS is enabled - detailed logging of AI requests and responses will be shown")
        else:
            logger.info("DEBUG_AI_CALLS is disabled - set DEBUG_AI_CALLS=true in .env to see detailed AI communication")
            
        self.root_dir = os.getcwd()
        logger.info(f"Working directory: {self.root_dir}")
        self.file_tree = []
        self.important_files = []
        self.ai_selected_files = []
        self.file_contents = {}
        self.readme_exists = False
        self.readme_content = ""
        self.project_summary = ""
        self.ignored_patterns = [
            r"\.git", r"\.vscode", r"\.idea", r"__pycache__", r"node_modules",
            r"\.jpg$", r"\.jpeg$", r"\.png$", r"\.gif$", r"\.svg$", r"\.ico$", 
            r"\.woff$", r"\.woff2$", r"\.ttf$", r"\.eot$", r"\.mp3$", r"\.mp4$",
            r"\.pdf$", r"\.zip$", r"\.tar$", r"\.gz$",
            # Exclude any folder with these names anywhere in the path
            r"vendor", r"cache", r"log",
            r"dist", r"build", r"tmp", r"temp", r"coverage"
        ]
        logger.info(f"Initialized with {len(self.ignored_patterns)} default ignore patterns")
        
        # Initialize tokenizer
        self.tokenizer = get_tokenizer()
        if self.tokenizer:
            logger.info("Tokenizer initialized for model: gemini-1.5-pro")
        else:
            logger.info("Using estimated token counting")
        
        # Initialize API client
        self.api_client = GeminiAPI(self.api_key, self.debug_ai_calls)
        
        # Add patterns from .gitignore if it exists
        self.add_gitignore_patterns()
        
    def add_gitignore_patterns(self):
        """Read patterns from .gitignore and add them to ignored_patterns"""
        gitignore_path = os.path.join(self.root_dir, ".gitignore")
        if os.path.exists(gitignore_path):
            logger.info("Reading .gitignore file")
            gitignore_count = 0
            
            with open(gitignore_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    # Skip empty lines and comments
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Convert gitignore pattern to regex pattern
                    # Handle basic pattern types
                    pattern = line
                    
                    # Remove leading slash if present (indicates project root)
                    if pattern.startswith('/'):
                        pattern = pattern[1:]
                    
                    # Handle directory indicator (trailing slash)
                    is_dir = pattern.endswith('/')
                    if is_dir:
                        pattern = pattern[:-1]
                    
                    # Escape special regex characters
                    pattern = re.escape(pattern)
                    
                    # Convert gitignore glob patterns to regex
                    # Replace * with .* (any characters)
                    pattern = pattern.replace('\\*', '.*')
                    
                    # Replace ? with . (any single character)
                    pattern = pattern.replace('\\?', '.')
                    
                    # Handle directory specific pattern
                    if is_dir:
                        self.ignored_patterns.append(f"^{pattern}$|^{pattern}/|/{pattern}/")
                    else:
                        # For files, match either the exact name or path ending with this name
                        self.ignored_patterns.append(f"^{pattern}$|/{pattern}$")
                    
                    gitignore_count += 1
            
            logger.info(f"Added {gitignore_count} patterns from .gitignore")
        else:
            logger.warning("No .gitignore file found")
        
    def generate_file_tree_string(self):
        """Generate a string representation of the file tree"""
        tree_str = "Project File Structure:\n"
        
        # Group files by directory
        dirs = {}
        for file_path in sorted(self.file_tree):
            parts = file_path.split(os.sep)
            if len(parts) == 1:  # Root level file
                dirs.setdefault('', []).append(parts[0])
            else:
                dir_path = os.path.dirname(file_path)
                filename = os.path.basename(file_path)
                dirs.setdefault(dir_path, []).append(filename)
        
        # Generate tree structure string
        def print_dir(dir_name, files, prefix=""):
            result = ""
            if dir_name:
                result += f"{prefix}└── {dir_name}/\n"
                new_prefix = prefix + "    "
            else:
                new_prefix = prefix
            
            for i, file in enumerate(sorted(files)):
                is_last = i == len(files) - 1
                if is_last:
                    result += f"{new_prefix}└── {file}\n"
                else:
                    result += f"{new_prefix}├── {file}\n"
            return result
        
        # Start with root level files
        if '' in dirs:
            for i, file in enumerate(sorted(dirs[''])):
                is_last = i == len(dirs['']) - 1 and len(dirs) == 1
                if is_last:
                    tree_str += f"└── {file}\n"
                else:
                    tree_str += f"├── {file}\n"
            dirs.pop('')
        
        # Process directories (sort by path depth to ensure proper nesting)
        sorted_dirs = sorted(dirs.items(), key=lambda x: x[0].count(os.sep))
        for dir_path, files in sorted_dirs:
            parent_prefix = ""
            for i in range(dir_path.count(os.sep)):
                parent_prefix += "    "
            
            tree_str += print_dir(os.path.basename(dir_path), files, parent_prefix)
        
        return tree_str
    
    def ask_ai_for_important_files(self):
        """Ask the AI which files are important to examine more closely"""
        logger.info("Asking AI to identify important files")
        
        # Create a prompt with README content and file tree
        file_tree_str = self.generate_file_tree_string()
        
        prompt = f"""
You are an expert developer analyzing a project. I need you to identify which files are the most important to examine
in order to understand this project's structure, purpose, and functionality, with special emphasis on the core business logic.

The purpose of this analysis is to help AI coding assistants understand the project scope precisely to reduce hallucinations 
and improve the efficiency of AI completions. Focus on files that reveal the core logical flows and business rules.

Here is the project's README.md (if available):
{self.readme_content if self.readme_exists else "No README.md found."}

Here is the project's file structure:
{file_tree_str}

Based on this information, list ONLY the filenames (with paths) of the most important files to examine.
DO NOT include any explanation, commentary, or analysis.
Just provide a list of the most important files, one per line, prioritizing:

1. Files containing core business logic and domain rules
2. Files that define key workflows and processes
3. Files with critical application logic (not just configuration or UI)
4. Main entry point files that show how the application logic flows
5. Files that define data models and their relationships

Avoid focusing too much on:
- Style files (CSS, SCSS)
- Static assets 
- Test files (unless they clearly demonstrate business logic)
- Build configuration files
- External libraries

Example response format:
src/main.py
lib/core.py
models/user.py
services/authentication.py
        """
        
        logger.debug(f"AI prompt for file selection: {prompt[:100]}...")
        
        try:
            response = self.api_client.call_gemini_api(prompt, self.tokenizer)
            file_list = response.strip().split('\n')
            
            # Clean up file paths from response
            file_list = [f.strip() for f in file_list if f.strip()]
            logger.info(f"AI suggested {len(file_list)} files")
            
            # Filter to only include files that actually exist in our file tree
            valid_files = []
            for file in file_list:
                # Normalize path separators for comparison
                normalized_file = file.replace('/', os.sep).replace('\\', os.sep)
                if normalized_file in self.file_tree:
                    valid_files.append(normalized_file)
                    logger.info(f"AI selected file (direct match): {normalized_file}")
                else:
                    # Try to find the closest match
                    found = False
                    for existing_file in self.file_tree:
                        if normalized_file in existing_file or existing_file.endswith(normalized_file):
                            valid_files.append(existing_file)
                            logger.info(f"AI selected file (partial match): {existing_file} for {normalized_file}")
                            found = True
                            break
                    if not found:
                        logger.warning(f"AI suggested file not found in project: {normalized_file}")
            
            self.ai_selected_files = valid_files
            logger.info(f"AI identified {len(self.ai_selected_files)} valid important files")
                
            return valid_files
        except Exception as e:
            logger.error(f"Error asking AI for important files: {str(e)}")
            # Fallback: identify important files automatically
            logger.warning("Falling back to automatic important file detection")
            self.identify_important_files_fallback()
            return self.important_files
    
    def load_files_under_token_limit(self):
        """Load file contents while staying under token limit"""
        logger.info("Calculating token usage and loading files")
        
        if not self.ai_selected_files:
            logger.warning("No AI-selected files available, using important files")
            files_to_load = self.important_files
        else:
            files_to_load = self.ai_selected_files
            
        # Start with basic project information
        base_info = {
            "name": os.path.basename(self.root_dir),
            "file_count": len(self.file_tree),
            "file_tree": self.generate_file_tree_string(),
        }
        
        if self.readme_exists:
            base_info["readme_content"] = self.readme_content
            
        base_json = json.dumps(base_info, indent=2)
        total_tokens = calculate_tokens(base_json, self.tokenizer)
        logger.info(f"Base project info: {total_tokens:,} tokens")
        
        # Add files until we approach the token limit
        file_contents = {}
        for file_path in files_to_load:
            content = self.read_file_content(file_path)
            content_tokens = calculate_tokens(content, self.tokenizer)
            
            if total_tokens + content_tokens <= MAX_TOKENS * 0.95:  # Leave 5% buffer
                file_contents[file_path] = content
                total_tokens += content_tokens
                logger.info(f"Added {file_path}: {content_tokens:,} tokens (Total: {total_tokens:,})")
            else:
                logger.warning(f"Skipping {file_path}: Would exceed token limit ({total_tokens + content_tokens:,} > {MAX_TOKENS:,})")
                break
                
        self.file_contents = file_contents
        logger.info(f"Loaded {len(file_contents)} files with {total_tokens:,} tokens (Limit: {MAX_TOKENS:,})")
        return file_contents
    
    def run(self):
        logger.info("Starting Project Prompt Generator")
        start_time = time.time()
        
        logger.info("Step 1: Checking for README.md...")
        self.check_readme()
        
        logger.info("Step 2: Analyzing project structure...")
        self.analyze_project_structure()
        
        logger.info("Step 3: Getting AI input on important files...")
        self.ask_ai_for_important_files()
        
        logger.info("Step 4: Loading file contents within token limits...")
        self.load_files_under_token_limit()
        
        logger.info("Step 5: Generating PROJECT_PROMPT.md for AI assistants...")
        self.generate_project_prompt()
        
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Complete! PROJECT_PROMPT.md has been created for AI assistants (Duration: {duration:.2f} seconds)")
        
    def check_readme(self):
        """Check if README.md exists"""
        readme_path = os.path.join(self.root_dir, "README.md")
        if os.path.exists(readme_path):
            self.readme_exists = True
            logger.info("README.md found")
            
            # Read README content for later use
            with open(readme_path, 'r', encoding='utf-8') as f:
                self.readme_content = f.read()
                logger.info(f"README.md contains {len(self.readme_content):,} characters")
        else:
            logger.warning("README.md not found")
    
    def analyze_project_structure(self):
        """Analyze the project structure and create a file tree"""
        logger.info("Scanning directory structure...")
        
        def should_ignore(path):
            return any(re.search(pattern, path) for pattern in self.ignored_patterns)
        
        # Walk through directory and collect files/folders
        for root, dirs, files in os.walk(self.root_dir):
            # Filter out directories we want to ignore
            dirs[:] = [d for d in dirs if not should_ignore(os.path.join(root, d))]
            
            rel_path = os.path.relpath(root, self.root_dir)
            if rel_path == '.':
                for file in files:
                    if not should_ignore(file):
                        self.file_tree.append(file)
            else:
                for file in files:
                    file_path = os.path.join(rel_path, file)
                    if not should_ignore(file_path):
                        self.file_tree.append(file_path)
        
        logger.info(f"Found {len(self.file_tree)} files")
    
    def identify_important_files_fallback(self):
        """Identify important files in the project as a fallback if AI selection fails"""
        logger.info("Identifying important files with fallback method")
        
        # Patterns for important files
        important_patterns = [
            # Configuration files
            r"package\.json$", r"setup\.py$", r"requirements\.txt$", r"Gemfile$", 
            r"composer\.json$", r"\.gitignore$", r"\.env\.example$", r"Dockerfile$",
            r"docker-compose\.yml$", r"\.eslintrc", r"tsconfig\.json$", r"webpack\.config\.js$",
            
            # Main entry points
            r"index\.(js|ts|py|php|html)$", r"app\.(js|ts|py|php)$", r"main\.(js|ts|py|php)$", 
            
            # Documentation
            r"README\.md$", r"CONTRIBUTING\.md$", r"LICENSE$",
            
            # Common source directories (limit to a few files per directory)
            r"^src/", r"^app/", r"^lib/", r"^core/", r"^controllers/", r"^models/",
            r"^views/", r"^templates/", r"^public/", r"^tests/", r"^docs/"
        ]
        
        # Clear previous list if any
        self.important_files = []
        
        # Identify files that match the important patterns
        for file_path in self.file_tree:
            if any(re.search(pattern, file_path) for pattern in important_patterns):
                self.important_files.append(file_path)
                logger.info(f"Important: {file_path}")
        
        logger.info(f"Identified {len(self.important_files)} important files")
    
    def read_file_content(self, file_path):
        """Read the entire content of a file"""
        full_path = os.path.join(self.root_dir, file_path)
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return f"Error reading file: {str(e)}"
    
    def generate_project_prompt(self):
        """Generate the PROJECT_PROMPT.md file using Gemini API specifically for AI assistants"""
        # Prepare project data with file contents
        project_data = {
            "name": os.path.basename(self.root_dir),
            "file_count": len(self.file_tree),
            "file_tree": self.generate_file_tree_string(),
            "file_contents": self.file_contents,
        }
        
        if self.readme_exists:
            project_data["readme_content"] = self.readme_content
        
        # Convert project data to a string for the prompt
        data_str = json.dumps(project_data, indent=2)
        
        # Calculate tokens for verification
        data_tokens = calculate_tokens(data_str, self.tokenizer)
        logger.info(f"Data being sent to Gemini: {data_tokens:,} tokens")
        
        prompt = f"""
You are an expert developer who is analyzing a project to create a specialized document ONLY FOR AI ASSISTANTS (not for human developers).
Your task is to create an optimized PROJECT_PROMPT.md file that will prevent AI hallucinations and make AI tools focus precisely on the project scope.

Based on the following project information, create a detailed PROJECT_PROMPT.md that:
1. Maps the core business logic and domain rules of the application in a highly structured format
2. Creates clear logical flow diagrams showing how different components interact
3. Identifies key decision points and business rules that govern application behavior
4. Explains data models and their relationships in a way that minimizes AI confusion
5. Prioritizes information that reveals the project's logical architecture over implementation details

Remember, the primary goal is to help AI tools:
- Understand precisely what the application does (preventing hallucination)
- Identify the scope and boundaries of the system (preventing unnecessary solutions)
- Focus on the right components when suggesting changes (increasing efficiency)
- Make code changes that align with existing business logic (maintaining consistency)

Here is the project information:
{data_str}

IMPORTANT GUIDELINES:
1. Structure this document specifically for AI reasoning, not human reading
2. Organize information hierarchically from high-level logic to implementation details
3. Use precise, consistent terminology throughout the document
4. Create clear boundaries around what's in-scope vs. out-of-scope
5. Include a "Logic Map" section that visually represents key workflows using markdown formatting

The resulting document will serve as a reference for AI tools to understand the project scope precisely, 
reducing token waste and improving the quality of AI completions by preventing hallucinations.
        """
        
        # Call Gemini API
        logger.info("Calling Gemini API to generate AI-focused documentation")
        try:
            response = self.api_client.call_gemini_api(prompt, self.tokenizer)
            markdown_content = response.strip()
            
            # Add a clear header explaining the purpose of this file
            ai_header = """# PROJECT_PROMPT - FOR AI ASSISTANTS ONLY

> **IMPORTANT**: This document is specifically designed for AI assistants to understand this codebase efficiently. 
> It is not intended for human developers. Developers should refer to README.md and other project documentation.
> This document focuses on the core logic flows and business rules to prevent hallucinations and improve AI response quality.

"""
            markdown_content = ai_header + markdown_content
            
            # Write to PROJECT_PROMPT.md
            with open(os.path.join(self.root_dir, "PROJECT_PROMPT.md"), 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            logger.info("AI-focused PROJECT_PROMPT.md created successfully")
            return markdown_content
        except Exception as e:
            logger.error(f"Error generating AI documentation: {str(e)}")
            
            # Create a basic version in case the API fails
            self.create_fallback_project_prompt()
    
    def create_fallback_project_prompt(self):
        """Create a basic PROJECT_PROMPT.md for AI assistants in case the API call fails"""
        logger.warning("Creating fallback AI-focused PROJECT_PROMPT.md")
        
        project_name = os.path.basename(self.root_dir)
        file_count = len(self.file_tree)
        
        content = f"""# PROJECT_PROMPT - FOR AI ASSISTANTS ONLY

> **IMPORTANT**: This document is specifically designed for AI assistants to understand this codebase efficiently. 
> It is not intended for human developers. Developers should refer to README.md and other project documentation.
> The structure and content of this file are optimized to improve AI reasoning and reduce token usage.

## Project Overview
This is the AI-optimized documentation for {project_name}. The project contains {file_count} files.

## File Structure Map
```
{self.generate_file_tree_string()}
```

## Important Files
The following files are considered most important for understanding the project architecture:

"""
        files_to_list = self.ai_selected_files if self.ai_selected_files else self.important_files
        for file in files_to_list:
            content += f"- `{file}`\n"
        
        content += "\n## File Contents\n"
        
        for file_path, file_content in self.file_contents.items():
            content += f"\n### `{file_path}`\n"
            content += "```\n"
            # Only truncate if extremely large to keep the fallback file reasonable
            if len(file_content) > 5000:
                content += file_content[:5000]
                content += "\n... (truncated, full content available in source file)"
            else:
                content += file_content
            content += "\n```\n"
        
        content += """
## AI Assistance Guidelines
When working with this codebase:
- Focus on the key files identified above
- Reference the file structure to understand the organization
- Use the file contents provided for context

This documentation was automatically generated to help AI assistants better understand the project context quickly and efficiently while saving tokens.
"""
        
        with open(os.path.join(self.root_dir, "PROJECT_PROMPT.md"), 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("Fallback AI-focused PROJECT_PROMPT.md created")