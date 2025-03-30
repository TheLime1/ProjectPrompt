import os
import re
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from logger_config import logger, run_log_dir
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
            
        # Check for custom file selection mode in environment
        self.file_selection_mode = os.getenv("FILE_SELECTION_MODE", "ai").lower()
        logger.info(f"File selection mode: {self.file_selection_mode}")

        self.include_files = os.getenv("INCLUDE_FILES", "").split(",") if os.getenv("INCLUDE_FILES") else []
        if self.include_files:
            self.include_files = [f.strip() for f in self.include_files]
            logger.info(f"Custom include files: {self.include_files}")
            
        self.exclude_files = os.getenv("EXCLUDE_FILES", "").split(",") if os.getenv("EXCLUDE_FILES") else []
        if self.exclude_files:
            self.exclude_files = [f.strip() for f in self.exclude_files]
            logger.info(f"Custom exclude files: {self.exclude_files}")
            
        self.root_dir = os.getcwd()
        logger.info(f"Working directory: {self.root_dir}")
        self.file_tree = []
        self.important_files = []
        self.ai_selected_files = []
        self.file_contents = {}
        self.file_stats = {}  # Track stats like size, modified date, etc.
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
            # Call the API with enhanced token accounting information
            response = self.api_client.call_gemini_api(
                prompt, 
                self.tokenizer, 
                operation_name="File Selection Analysis",
                source_file="project_generator.py",
                prompt_summary="Identify important project files"
            )
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
        
        # Log base project info to token accounting
        self.api_client.log_token_accounting(
            input_tokens=total_tokens,
            output_tokens=0,
            prompt_summary="Base project information",
            operation_name="Project Setup",
            source_file=""
        )
        
        # Add files until we approach the token limit
        file_contents = {}
        for file_path in files_to_load:
            content = self.read_file_content(file_path)
            content_tokens = calculate_tokens(content, self.tokenizer)
            
            if total_tokens + content_tokens <= MAX_TOKENS * 0.95:  # Leave 5% buffer
                file_contents[file_path] = content
                total_tokens += content_tokens
                logger.info(f"Added {file_path}: {content_tokens:,} tokens (Total: {total_tokens:,})")
                
                # Log each file to token accounting
                self.api_client.log_token_accounting(
                    input_tokens=content_tokens,
                    output_tokens=0,
                    source_file=file_path
                )
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
        
        logger.info("Step 3: Selecting important files...")
        self.select_important_files()
        
        logger.info("Step 4: Loading file contents within token limits...")
        self.load_files_under_token_limit()
        
        logger.info("Step 5: Generating PROJECT_PROMPT.md for AI assistants...")
        self.generate_project_prompt()
        
        # Add the grand total row to the token accounting
        logger.info("Step 6: Finalizing token accounting with totals...")
        self.api_client.finalize_token_accounting()
        
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
Your task is to create an optimized PROJECT_PROMPT.json file that will prevent AI hallucinations and make AI tools focus precisely on the project scope.

## TECHNICAL EXTRACTION REQUIREMENTS

This document must be highly technical and focus on extracting critical details that developers and AI tools need repeatedly:

1. EXTRACT SPECIFIC TECHNICAL ELEMENTS:
   - All important variable names, constants, and their values/types
   - Route names and URL patterns (e.g., in web frameworks like Symphony, Express, Flask)
   - API endpoints with their HTTP methods and parameters
   - Database table/collection names and their relationships
   - Function signatures with parameter types and return values
   - Configuration values and environment variables
   - Class hierarchies and inheritance relationships
   - Key component dependencies and their versions

2. CREATE KEY-VALUE REFERENCE TABLES:
   - Create organized, searchable tables of routes, variables, and constants
   - Format these as structured JSON objects or markdown tables for quick lookup
   - Include context about where each element is defined and used

3. ORGANIZE BY TECHNICAL DOMAIN:
   - Group related elements by technical categories (Routes, Models, Controllers, etc.)
   - Create clear cross-references between related components
   - Maintain consistent naming conventions for easy searching

4. CREATE TECHNICAL DIAGRAMS:
   - Flow diagrams showing request/response cycles
   - Entity relationships and data flows
   - Component interaction patterns
   - Execution order of key operations

Remember, the primary goal is to help AI tools:
- Use exact variable/route names instead of hallucinating them
- Understand precise technical implementation details
- Have reference tables they can consult for accuracy
- Minimize guesswork when suggesting code modifications

Here is the project information:
{data_str}

## OUTPUT FORMAT GUIDELINES

1. Format your response as plain text optimized for AI parsing
2. Create clear section headers with distinctive markers
3. Use structured lists, tables, or JSON for technical reference data
4. Organize information hierarchically from system-level to implementation details
5. Include a "Technical Reference" section with exact names of key elements

The resulting document will serve as a precise technical reference for AI tools to understand the project's implementation details,
reducing token waste and improving the quality of AI completions by preventing hallucinations about variable names, routes, and other critical technical elements.
        """
        
        # Call Gemini API
        logger.info("Calling Gemini API to generate AI-focused technical documentation")
        try:
            response = self.api_client.call_gemini_api(
                prompt, 
                self.tokenizer, 
                operation_name="Project Prompt Generation",
                source_file="project_generator.py",
                prompt_summary="Generate technical PROJECT_PROMPT for AI assistants"
            )
            content = response.strip()
            
            # Add a clear header explaining the purpose of this file
            ai_header = """# PROJECT_PROMPT - TECHNICAL REFERENCE FOR AI ASSISTANTS

> **IMPORTANT**: This document is specifically designed as a technical reference for AI assistants.
> It contains precise variable names, routes, endpoints, and other technical details to prevent hallucinations.
> Human developers should refer to standard documentation.

"""
            content = ai_header + content
            
            # Write to PROJECT_PROMPT.json if it's JSON formatted, otherwise use .txt for plain text
            file_extension = ".json" if content.strip().startswith("{") else ".md"
            project_root_file = os.path.join(self.root_dir, f"PROJECT_PROMPT{file_extension}")
            with open(project_root_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            # Also save a copy in the current log directory
            log_file = os.path.join(run_log_dir, f"PROJECT_PROMPT{file_extension}")
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"AI-focused technical PROJECT_PROMPT{file_extension} created successfully at {project_root_file}")
            logger.info(f"Copy saved to log directory at {log_file}")
            return content
        except Exception as e:
            logger.error(f"Error generating AI documentation: {str(e)}")
            
            # Create a basic version in case the API fails
            self.create_fallback_project_prompt()
    
    def create_fallback_project_prompt(self):
        """Create a basic technical PROJECT_PROMPT for AI assistants in case the API call fails"""
        logger.warning("Creating fallback technical AI-focused PROJECT_PROMPT.txt")
        
        project_name = os.path.basename(self.root_dir)
        file_count = len(self.file_tree)
        
        content = f"""# PROJECT_PROMPT - TECHNICAL REFERENCE FOR AI ASSISTANTS

> **IMPORTANT**: This document is specifically designed as a technical reference for AI assistants.
> It contains precise variable names, routes, endpoints, and other technical details to prevent hallucinations.
> Human developers should refer to standard documentation.

## Project Overview
Technical reference for {project_name}. The project contains {file_count} files.

## File Structure Map
```
{self.generate_file_tree_string()}
```

## Technical Reference: Important Files
The following files are considered most important for understanding the project architecture:

"""
        files_to_list = self.ai_selected_files if self.ai_selected_files else self.important_files
        for file in files_to_list:
            content += f"- `{file}`\n"
        
        content += "\n## Technical Reference: Key Variables and Constants\n"
        
        # Extract some basic technical information from files
        technical_details = self.extract_basic_technical_details()
        for category, items in technical_details.items():
            content += f"\n### {category}\n"
            if items:
                for item in items:
                    content += f"- {item}\n"
            else:
                content += "No items identified in this category.\n"
        
        content += "\n## Technical Reference: File Contents\n"
        
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
## AI Technical Assistance Guidelines
When working with this codebase:
- Use exact variable names, routes and function signatures as listed in the technical reference
- Reference the precise technical details to avoid hallucinations
- Respect the existing architectural patterns when suggesting code modifications

This technical reference was automatically generated to help AI assistants understand the project's implementation details.
"""
        
        # Write to PROJECT_PROMPT.txt (plaintext for fallback)
        project_root_file = os.path.join(self.root_dir, "PROJECT_PROMPT.txt")
        with open(project_root_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        # Also save a copy in the current log directory
        log_file = os.path.join(run_log_dir, "PROJECT_PROMPT.txt")
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Fallback technical AI-focused PROJECT_PROMPT.txt created at {project_root_file}")
        logger.info(f"Copy saved to log directory at {log_file}")
    
    def extract_basic_technical_details(self):
        """Extract basic technical details from files for the fallback prompt"""
        technical_details = {
            "Functions": [],
            "Routes": [],
            "Constants": [],
            "Classes": [],
            "API Endpoints": [],
            "Configuration Values": []
        }
        
        # Simple regex patterns to identify common technical elements
        import re
        patterns = {
            "Functions": r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)",
            "Routes": r"@(?:app|router)\.(?:route|get|post|put|delete)\s*\(\s*['\"]([^'\"]+)['\"]",
            "Constants": r"([A-Z][A-Z0-9_]*)\s*=\s*([^,;]+)",
            "Classes": r"class\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            "API Endpoints": r"(?:api|endpoints|url)\s*\(\s*['\"]([^'\"]+)['\"]",
        }
        
        for file_path, content in self.file_contents.items():
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # Extract elements based on file type
            if file_ext in ['.py', '.js', '.ts', '.php', '.rb', '.java']:
                # Extract functions
                for match in re.finditer(patterns["Functions"], content):
                    fn_name = match.group(1)
                    params = match.group(2).strip()
                    technical_details["Functions"].append(f"`{fn_name}({params})` in {file_path}")
                
                # Extract classes
                for match in re.finditer(patterns["Classes"], content):
                    class_name = match.group(1)
                    technical_details["Classes"].append(f"`{class_name}` in {file_path}")
                
                # Extract constants
                for match in re.finditer(patterns["Constants"], content):
                    const_name = match.group(1)
                    const_value = match.group(2).strip()
                    if len(const_value) > 30:  # Truncate long values
                        const_value = const_value[:30] + "..."
                    technical_details["Constants"].append(f"`{const_name} = {const_value}` in {file_path}")
            
            # Extract routes
            if file_ext in ['.py', '.js', '.ts', '.php', '.rb']:
                for match in re.finditer(patterns["Routes"], content):
                    route = match.group(1)
                    technical_details["Routes"].append(f"`{route}` in {file_path}")
                
                for match in re.finditer(patterns["API Endpoints"], content):
                    endpoint = match.group(1)
                    technical_details["API Endpoints"].append(f"`{endpoint}` in {file_path}")
            
            # Extract config values from common config files
            if 'config' in file_path.lower() or file_path.endswith(('.env', '.ini', '.cfg', '.conf')):
                # Simple pattern to catch key = value pairs
                for match in re.finditer(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*[=:]\s*([^,;\n]+)", content):
                    key = match.group(1)
                    value = match.group(2).strip()
                    if len(value) > 30:  # Truncate long values
                        value = value[:30] + "..."
                    technical_details["Configuration Values"].append(f"`{key} = {value}` in {file_path}")
        
        return technical_details