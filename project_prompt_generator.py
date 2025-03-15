import os
import re
import json
import requests
from pathlib import Path
import subprocess
import time
from dotenv import load_dotenv

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
        self.readme_exists = False
        self.project_summary = ""
        self.ignored_patterns = [
            r"\.git", r"\.vscode", r"\.idea", r"__pycache__", r"node_modules",
            r"\.jpg$", r"\.jpeg$", r"\.png$", r"\.gif$", r"\.svg$", r"\.ico$", 
            r"\.woff$", r"\.woff2$", r"\.ttf$", r"\.eot$", r"\.mp3$", r"\.mp4$",
            r"\.pdf$", r"\.zip$", r"\.tar$", r"\.gz$"
        ]
        
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
        
    def run(self):
        print("🔍 Starting Project Prompt Generator")
        print("Step 1: Checking for README.md...")
        self.check_readme()
        
        print("Step 2: Analyzing project structure...")
        self.analyze_project_structure()
        
        print("Step 3: Identifying important files...")
        self.identify_important_files()
        
        print("Step 4: Generating PROJECT_PROMPT.md for AI assistants...")
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
    
    def identify_important_files(self):
        """Identify important files in the project"""
        print("  🔍 Identifying important files...")
        
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
            
            # Common source directories
            r"^src/", r"^app/", r"^lib/", r"^core/", r"^controllers/", r"^models/",
            r"^views/", r"^templates/", r"^public/", r"^tests/", r"^docs/"
        ]
        
        # Identify files that match the important patterns
        for file_path in self.file_tree:
            if any(re.search(pattern, file_path) for pattern in important_patterns):
                self.important_files.append(file_path)
                print(f"  ✓ Important: {file_path}")
        
        print(f"  ✓ Identified {len(self.important_files)} important files")
    
    def read_file_content(self, file_path, max_chars=1000):
        """Read the content of a file with size limit"""
        full_path = os.path.join(self.root_dir, file_path)
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(max_chars)
                if len(content) == max_chars:
                    content += "\n... (truncated)"
                return content
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def generate_project_summary(self):
        """Generate a summary of the project"""
        project_info = {
            "name": os.path.basename(self.root_dir),
            "file_count": len(self.file_tree),
            "important_files": self.important_files,
            "readme_exists": self.readme_exists,
        }
        
        # Add content of important files (limited to prevent overwhelming)
        file_contents = {}
        for file_path in self.important_files[:5]:  # Limit to first 5 important files
            file_contents[file_path] = self.read_file_content(file_path)
        
        project_info["file_contents"] = file_contents
        
        if self.readme_exists:
            project_info["readme_content"] = self.readme_content
        
        return project_info
    
    def generate_project_prompt(self):
        """Generate the PROJECT_PROMPT.md file using Gemini API specifically for AI assistants"""
        project_summary = self.generate_project_summary()
        
        # Convert project summary to a string for the prompt
        summary_str = json.dumps(project_summary, indent=2)
        
        prompt = f"""
You are an expert developer who is analyzing a project to create a specialized document ONLY FOR AI ASSISTANTS (not for human developers).
Based on the following project information, create a detailed PROJECT_PROMPT.md that:
1. Describes the purpose, structure, and main features of the project in a way that helps AI assistants understand the codebase
2. Outlines the technology stack and dependencies in a format optimized for AI reasoning
3. Highlights the most important files and their purposes to improve AI's contextual understanding
4. Provides information about file relationships and architecture to help AI assistants navigate the project
5. Uses a structure and format specifically designed to reduce token usage and improve AI efficiency when working with the codebase

Here is the project information:
{summary_str}

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
            self.create_fallback_project_prompt(project_summary)
    
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
    
    def create_fallback_project_prompt(self, project_summary):
        """Create a basic PROJECT_PROMPT.md for AI assistants in case the API call fails"""
        print("  ⚠️ Creating fallback AI-focused PROJECT_PROMPT.md...")
        
        project_name = project_summary.get("name", "Project")
        file_count = project_summary.get("file_count", 0)
        important_files = project_summary.get("important_files", [])
        
        content = f"""# PROJECT_PROMPT - FOR AI ASSISTANTS ONLY

> **IMPORTANT**: This document is specifically designed for AI assistants to understand this codebase efficiently. 
> It is not intended for human developers. Developers should refer to README.md and other project documentation.
> The structure and content of this file are optimized to improve AI reasoning and reduce token usage.

## Project Overview
This is the AI-optimized documentation for {project_name}. The project contains {file_count} files.

## File Structure Map
The following files are considered most important for understanding the project architecture:

"""
        for file in important_files:
            content += f"- `{file}`\n"
        
        content += """
## Important Relationships
The files above have the following relationships and dependencies (for AI navigation):
- Project structure follows standard conventions
- Main configuration files at root level
- Code is organized by functionality

## AI Assistance Guidelines
When working with this codebase:
- Focus on the key files identified above
- Check for configuration files first
- Reference README.md for developer-focused documentation

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