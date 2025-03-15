import os
import re
import json
import requests
from pathlib import Path
import subprocess
import time
from dotenv import load_dotenv

# Add token calculation imports 
try:
    from vertexai.preview import tokenization
    TOKENIZER_AVAILABLE = True
except ImportError:
    TOKENIZER_AVAILABLE = False
    print("  ⚠️ vertexai package not available. Token calculation will be estimated.")

# Maximum tokens for Gemini 1.5 Pro
MAX_TOKENS = 1800000

class ProjectPromptGenerator:
    def __init__(self, api_key=None):
        # Load API key from .env file if not provided
        if api_key is None:
            load_dotenv()
            self.api_key = os.getenv("GEMINI_API_KEY")
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY not found in .env file")
        else:
            self.api_key = api_key
            
        self.root_dir = os.getcwd()
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
            r"\.pdf$", r"\.zip$", r"\.tar$", r"\.gz$"
        ]
        
        # Initialize tokenizer if available
        if TOKENIZER_AVAILABLE:
            self.tokenizer = tokenization.get_tokenizer_for_model("gemini-1.5-pro")
        else:
            self.tokenizer = None
        
        # Add patterns from .gitignore if it exists
        self.add_gitignore_patterns()
        
    def add_gitignore_patterns(self):
        """Read patterns from .gitignore and add them to ignored_patterns"""
        gitignore_path = os.path.join(self.root_dir, ".gitignore")
        if os.path.exists(gitignore_path):
            print("  📄 Reading .gitignore file...")
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
            
            print(f"  ✓ Added {gitignore_count} patterns from .gitignore")
        else:
            print("  ⚠️ No .gitignore file found")
        
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
        print("  🤖 Asking AI to identify important files to examine...")
        
        # Create a prompt with README content and file tree
        file_tree_str = self.generate_file_tree_string()
        
        prompt = f"""
You are an expert developer analyzing a project. I need you to identify which files are the most important to examine
in order to understand this project's structure, purpose, and functionality.

Here is the project's README.md (if available):
{self.readme_content if self.readme_exists else "No README.md found."}

Here is the project's file structure:
{file_tree_str}

Based on this information, list ONLY the filenames (with paths) of the most important files to examine.
DO NOT include any explanation, commentary, or analysis.
Just provide a list of the most important files, one per line, based on the following criteria:
1. Configuration files that define the project setup
2. Main entry point files
3. Core functionality files
4. Files that explain the project architecture

Example response format:
src/main.py
config.json
lib/core.py
        """
        
        try:
            response = self.call_gemini_api(prompt)
            file_list = response.strip().split('\n')
            
            # Clean up file paths from response
            file_list = [f.strip() for f in file_list if f.strip()]
            
            # Filter to only include files that actually exist in our file tree
            valid_files = []
            for file in file_list:
                # Normalize path separators for comparison
                normalized_file = file.replace('/', os.sep).replace('\\', os.sep)
                if normalized_file in self.file_tree:
                    valid_files.append(normalized_file)
                else:
                    # Try to find the closest match
                    for existing_file in self.file_tree:
                        if normalized_file in existing_file or existing_file.endswith(normalized_file):
                            valid_files.append(existing_file)
                            break
            
            self.ai_selected_files = valid_files
            print(f"  ✓ AI identified {len(self.ai_selected_files)} important files")
            for file in self.ai_selected_files:
                print(f"    - {file}")
                
            return valid_files
        except Exception as e:
            print(f"  ✗ Error asking AI for important files: {str(e)}")
            # Fallback: identify important files automatically
            print("  ⚠️ Falling back to automatic important file detection")
            self.identify_important_files_fallback()
            return self.important_files
    
    def calculate_tokens(self, text):
        """Calculate the number of tokens in a text string"""
        if self.tokenizer is not None:
            try:
                result = self.tokenizer.count_tokens(text)
                return result.total_tokens
            except Exception as e:
                print(f"  ⚠️ Error calculating tokens: {str(e)}")
                # Fallback to estimation
                return len(text) // 4  # Rough estimate: ~4 chars per token
        else:
            # If tokenizer not available, make a rough estimate
            return len(text) // 4
    
    def load_files_under_token_limit(self):
        """Load file contents while staying under token limit"""
        print("  📊 Calculating token usage and loading files...")
        
        if not self.ai_selected_files:
            print("  ⚠️ No AI-selected files available, using important files")
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
        total_tokens = self.calculate_tokens(base_json)
        print(f"  ℹ️ Base project info: {total_tokens:,} tokens")
        
        # Add files until we approach the token limit
        file_contents = {}
        for file_path in files_to_load:
            content = self.read_file_content(file_path)
            content_tokens = self.calculate_tokens(content)
            
            if total_tokens + content_tokens <= MAX_TOKENS * 0.95:  # Leave 5% buffer
                file_contents[file_path] = content
                total_tokens += content_tokens
                print(f"  ✓ Added {file_path}: {content_tokens:,} tokens (Total: {total_tokens:,})")
            else:
                print(f"  ✗ Skipping {file_path}: Would exceed token limit")
                break
                
        self.file_contents = file_contents
        print(f"  ✓ Loaded {len(file_contents)} files with {total_tokens:,} tokens (Limit: {MAX_TOKENS:,})")
        return file_contents
    
    def run(self):
        print("🔍 Starting Project Prompt Generator")
        print("Step 1: Checking for README.md...")
        self.check_readme()
        
        print("Step 2: Analyzing project structure...")
        self.analyze_project_structure()
        
        print("Step 3: Getting AI input on important files...")
        self.ask_ai_for_important_files()
        
        print("Step 4: Loading file contents within token limits...")
        self.load_files_under_token_limit()
        
        print("Step 5: Generating PROJECT_PROMPT.md for AI assistants...")
        self.generate_project_prompt()
        
        print("✅ Complete! PROJECT_PROMPT.md has been created for AI assistants.")
        
    def check_readme(self):
        """Check if README.md exists"""
        readme_path = os.path.join(self.root_dir, "README.md")
        if os.path.exists(readme_path):
            self.readme_exists = True
            print("  ✓ README.md found")
            
            # Read README content for later use
            with open(readme_path, 'r', encoding='utf-8') as f:
                self.readme_content = f.read()
                print(f"  ℹ️ README.md contains {len(self.readme_content)} characters")
        else:
            print("  ✗ README.md not found")
    
    def analyze_project_structure(self):
        """Analyze the project structure and create a file tree"""
        print("  📂 Scanning directory structure...")
        
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
        
        print(f"  ✓ Found {len(self.file_tree)} files")
    
    def identify_important_files_fallback(self):
        """Identify important files in the project as a fallback if AI selection fails"""
        print("  🔍 Identifying important files with fallback method...")
        
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
                print(f"  ✓ Important: {file_path}")
        
        print(f"  ✓ Identified {len(self.important_files)} important files")
    
    def read_file_content(self, file_path):
        """Read the entire content of a file"""
        full_path = os.path.join(self.root_dir, file_path)
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
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
        data_tokens = self.calculate_tokens(data_str)
        print(f"  ℹ️ Data being sent to Gemini: {data_tokens:,} tokens")
        
        prompt = f"""
You are an expert developer who is analyzing a project to create a specialized document ONLY FOR AI ASSISTANTS (not for human developers).
Based on the following project information, create a detailed PROJECT_PROMPT.md that:
1. Describes the purpose, structure, and main features of the project in a way that helps AI assistants understand the codebase
2. Outlines the technology stack and dependencies in a format optimized for AI reasoning
3. Highlights the most important files and their purposes to improve AI's contextual understanding
4. Provides information about file relationships and architecture to help AI assistants navigate the project
5. Uses a structure and format specifically designed to reduce token usage and improve AI efficiency when working with the codebase

Here is the project information:
{data_str}

Important: The resulting document is EXCLUSIVELY for AI consumption, not for human developers (developers will use README.md instead).
Focus on structuring information to optimize AI understanding, reasoning, and search capabilities.

Format the documentation with proper Markdown, including:
- Clear, AI-optimized sections
- Code relationship diagrams where helpful for AI understanding
- Important file paths formatted for easy AI parsing
- A structured, hierarchical organization to minimize token usage during AI reasoning tasks

The documentation should help AI tools understand the project context quickly and efficiently, saving tokens and improving response quality.
        """
        
        # Call Gemini API
        print("  🤖 Calling Gemini API to generate AI-focused documentation...")
        try:
            response = self.call_gemini_api(prompt)
            markdown_content = response.strip()
            
            # Add a clear header explaining the purpose of this file
            ai_header = """# PROJECT_PROMPT - FOR AI ASSISTANTS ONLY

> **IMPORTANT**: This document is specifically designed for AI assistants to understand this codebase efficiently. 
> It is not intended for human developers. Developers should refer to README.md and other project documentation.
> The structure and content of this file are optimized to improve AI reasoning and reduce token usage.

"""
            markdown_content = ai_header + markdown_content
            
            # Write to PROJECT_PROMPT.md
            with open(os.path.join(self.root_dir, "PROJECT_PROMPT.md"), 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print("  ✓ AI-focused PROJECT_PROMPT.md created successfully")
            return markdown_content
        except Exception as e:
            print(f"  ✗ Error generating AI documentation: {str(e)}")
            
            # Create a basic version in case the API fails
            self.create_fallback_project_prompt()
    
    def call_gemini_api(self, prompt):
        """Call the Gemini API to generate documentation"""
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"
        headers = {
            "Content-Type": "application/json",
        }
        
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        
        # Include API key as query parameter
        params = {
            "key": self.api_key
        }
        
        response = requests.post(url, headers=headers, json=data, params=params)
        
        if response.status_code == 200:
            result = response.json()
            # Extract the text from the response
            if "candidates" in result and len(result["candidates"]) > 0:
                if "content" in result["candidates"][0] and "parts" in result["candidates"][0]["content"]:
                    parts = result["candidates"][0]["content"]["parts"]
                    if len(parts) > 0 and "text" in parts[0]:
                        return parts[0]["text"]
            
            raise Exception(f"Unexpected response format: {json.dumps(result)}")
        else:
            raise Exception(f"API Error: {response.status_code} - {response.text}")
    
    def create_fallback_project_prompt(self):
        """Create a basic PROJECT_PROMPT.md for AI assistants in case the API call fails"""
        print("  ⚠️ Creating fallback AI-focused PROJECT_PROMPT.md...")
        
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
        
        print("  ✓ Fallback AI-focused PROJECT_PROMPT.md created")


if __name__ == "__main__":
    try:
        generator = ProjectPromptGenerator()
        generator.run()
    except ValueError as e:
        print(f"Error: {e}")
        print("Please create a .env file in the project root with GEMINI_API_KEY=your_api_key")