import os
import json
import requests
import time
from datetime import datetime
from logger_config import logger, DEBUG_API_CALLS_DIR, run_log_dir
from token_utils import calculate_tokens, MAX_TOKENS

class GeminiAPI:
    def __init__(self, api_key, debug_ai_calls=False):
        self.api_key = api_key
        self.debug_ai_calls = debug_ai_calls
        self.root_dir = os.getcwd()
        # Create debug directory if needed
        if self.debug_ai_calls:
            os.makedirs(DEBUG_API_CALLS_DIR, exist_ok=True)
            logger.info(f"Debug AI calls directory created at: {DEBUG_API_CALLS_DIR}")
        
        # Create a token accounting file with simple precise header
        self.token_accounting_file = os.path.join(run_log_dir, "token_accounting.txt")
        with open(self.token_accounting_file, 'w', encoding='utf-8') as f:
            f.write("TOKEN ACCOUNTING SUMMARY\n")
            f.write("=======================\n\n")
            f.write("Date: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n")
            f.write("TIMESTAMP           | FILE OR PROMPT                             | TYPE             | INPUT TOKENS | OUTPUT TOKENS | TOTAL TOKENS\n")
            f.write("--------------------|-------------------------------------------|------------------|--------------|---------------|-------------\n")
        logger.info(f"Token accounting file created at: {self.token_accounting_file}")
        
        # Initialize prompt counter and token totals
        self.prompt_counter = 1
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        
        # Initialize sequential counter for file naming
        self.sequence_counter = 1
    
    def log_token_accounting(self, input_tokens, output_tokens, prompt_summary="", operation_name="", source_file=""):
        """Log token usage to the accounting file with focus on files and prompts"""
        total_tokens = input_tokens + output_tokens
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Keep track of totals
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        
        # Determine if this is a file or a prompt entry
        if source_file and "prompt" not in source_file.lower():
            # This is a file entry
            file_name = os.path.basename(source_file)
            entry_type = "File"
            entry_name = file_name
        else:
            # This is a prompt entry
            entry_type = f"Prompt #{self.prompt_counter}"
            self.prompt_counter += 1
            # Create a concise name for the prompt
            if prompt_summary:
                entry_name = prompt_summary[:40]
            else:
                entry_name = f"{operation_name[:40]}" if operation_name else f"API Call #{self.prompt_counter-1}"
        
        # Truncate long names for better formatting
        entry_name = (entry_name[:40] + "...") if len(entry_name) > 43 else entry_name.ljust(43)
        entry_type = entry_type[:16].ljust(16)
        
        with open(self.token_accounting_file, 'a', encoding='utf-8') as f:
            f.write(f"{timestamp} | {entry_name} | {entry_type} | {input_tokens:>12,d} | {output_tokens:>13,d} | {total_tokens:>13,d}\n")
        
        logger.info(f"Token accounting: {entry_type.strip()} - {entry_name.strip()} - Input: {input_tokens:,}, Output: {output_tokens:,}, Total: {total_tokens:,}")
        return total_tokens
    
    def finalize_token_accounting(self):
        """Write the grand total row to the token accounting file"""
        total_tokens = self.total_input_tokens + self.total_output_tokens
        
        with open(self.token_accounting_file, 'a', encoding='utf-8') as f:
            f.write("--------------------|-------------------------------------------|------------------|--------------|---------------|-------------\n")
            f.write(f"GRAND TOTAL        | All Files and Prompts                      | {self.prompt_counter-1} Prompts      | {self.total_input_tokens:>12,d} | {self.total_output_tokens:>13,d} | {total_tokens:>13,d}\n")
        
        logger.info(f"TOKEN ACCOUNTING SUMMARY - Total Input: {self.total_input_tokens:,}, Total Output: {self.total_output_tokens:,}, Grand Total: {total_tokens:,}")
    
    def call_gemini_api(self, prompt, tokenizer=None, operation_name="API Call", source_file="", prompt_summary=""):
        """Call the Gemini API to generate documentation"""
        logger.info("Calling Gemini API")
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
        
        # Calculate tokens for entire request including prompt
        prompt_tokens = calculate_tokens(prompt, tokenizer)
        logger.info(f"Making API request to Gemini (prompt length: {len(prompt):,} characters, approximately {prompt_tokens:,} tokens)")
        
        # Auto-generate prompt summary if not provided
        if not prompt_summary:
            # Get first line that's not empty
            for line in prompt.splitlines():
                line = line.strip()
                if line:
                    prompt_summary = line
                    break
            
            # If still no summary, use the first 50 characters
            if not prompt_summary:
                prompt_summary = prompt[:50]
        
        if prompt_tokens > MAX_TOKENS:
            logger.error(f"Prompt exceeds max token limit: {prompt_tokens:,} > {MAX_TOKENS:,}")
            raise Exception(f"Prompt exceeds token limit ({prompt_tokens:,} > {MAX_TOKENS:,})")
        
        start_time = time.time()
        
        # Log the full prompt if debug mode is enabled
        if self.debug_ai_calls:
            # Write the prompt to a file with sequential numbering
            prompt_file = os.path.join(DEBUG_API_CALLS_DIR, f"{self.sequence_counter:02d}-prompt.txt")
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(f"Operation: {operation_name}\n")
                f.write(f"Source file: {source_file}\n")
                f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Tokens: {prompt_tokens:,}\n")
                f.write("\n--- PROMPT CONTENT ---\n\n")
                f.write(prompt)
            
            logger.info(f"DEBUG: Full prompt saved to {prompt_file}")
            print(f"\n[DEBUG] Full prompt saved to {prompt_file}")
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                response = requests.post(url, headers=headers, json=data, params=params)
                end_time = time.time()
                duration = end_time - start_time
                
                logger.info(f"Received API response (status: {response.status_code}, duration: {duration:.2f} seconds)")
                
                # Handle rate limiting (429 errors)
                if response.status_code == 429:
                    error_data = response.json() if response.text else {"error": {"message": "Rate limit exceeded"}}
                    error_msg = f"API Error: {response.status_code} - {json.dumps(error_data)}"
                    logger.error(error_msg)
                    
                    # Log the error response if debug mode is enabled
                    if self.debug_ai_calls:
                        # Write the error response to a file with sequential numbering
                        error_file = os.path.join(DEBUG_API_CALLS_DIR, f"{self.sequence_counter:02d}-error.txt")
                        with open(error_file, 'w', encoding='utf-8') as f:
                            f.write(f"Status Code: {response.status_code}\n\n{response.text}")
                        
                        logger.error(f"DEBUG: HTTP error saved to {error_file}")
                        print(f"\n[DEBUG] HTTP error saved to {error_file}")
                    
                    if prompt_tokens <= MAX_TOKENS:
                        # Wait and retry if we're within token limits but just hitting quota
                        wait_time = 60  # seconds
                        logger.warning(f"Token quota exceeded. Waiting {wait_time} seconds before retry...")
                        
                        # Print countdown every 10 seconds
                        for remaining in range(wait_time, 0, -10):
                            logger.info(f"Waiting... (time left: {remaining} seconds)")
                            print(f"Waiting... (time left: {remaining} seconds)")
                            time.sleep(min(10, remaining))
                        
                        retry_count += 1
                        logger.info(f"Retrying API call (attempt {retry_count} of {max_retries})")
                        continue
                    else:
                        # Token count too high, can't retry
                        # Increment sequence counter even for failed attempts
                        self.sequence_counter += 1
                        raise Exception(f"Token quota exceeded and prompt is too large ({prompt_tokens:,} > {MAX_TOKENS:,})")
                
                # Save the full response if debug mode is enabled
                if self.debug_ai_calls and response.status_code == 200:
                    # Write the raw response to a file with sequential numbering
                    response_file = os.path.join(DEBUG_API_CALLS_DIR, f"{self.sequence_counter:02d}-response.json")
                    with open(response_file, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    
                    logger.info(f"DEBUG: Full API response saved to {response_file}")
                    print(f"\n[DEBUG] Full API response saved to {response_file}")
                
                if response.status_code == 200:
                    result = response.json()
                    # Extract the text from the response
                    if "candidates" in result and len(result["candidates"]) > 0:
                        if "content" in result["candidates"][0] and "parts" in result["candidates"][0]["content"]:
                            parts = result["candidates"][0]["content"]["parts"]
                            if len(parts) > 0 and "text" in parts[0]:
                                response_text = parts[0]["text"]
                                response_tokens = calculate_tokens(response_text, tokenizer)
                                logger.info(f"Extracted response text (length: {len(response_text):,} characters, approximately {response_tokens:,} tokens)")
                                
                                # Log to token accounting with focus on prompt details
                                self.log_token_accounting(
                                    input_tokens=prompt_tokens,
                                    output_tokens=response_tokens, 
                                    prompt_summary=prompt_summary,
                                    operation_name=operation_name,
                                    source_file=source_file
                                )
                                
                                # Save the extracted text response if debug mode is enabled
                                if self.debug_ai_calls:
                                    # Write the extracted text to a file with sequential numbering
                                    text_file = os.path.join(DEBUG_API_CALLS_DIR, f"{self.sequence_counter:02d}-extracted_text.txt")
                                    with open(text_file, 'w', encoding='utf-8') as f:
                                        f.write(f"Operation: {operation_name}\n")
                                        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                                        f.write(f"Tokens: {response_tokens:,}\n")
                                        f.write("\n--- RESPONSE CONTENT ---\n\n")
                                        f.write(response_text)
                                    
                                    logger.info(f"DEBUG: Extracted text saved to {text_file}")
                                    print(f"\n[DEBUG] Extracted text saved to {text_file}")
                                
                                # Increment sequence counter for the next interaction
                                self.sequence_counter += 1
                                
                                return response_text
                    
                    error_msg = f"Unexpected response format: {json.dumps(result)[:100]}..."
                    logger.error(error_msg)
                    
                    # Log the full response on error if debug mode is enabled
                    if self.debug_ai_calls:
                        # Write the error response to a file with sequential numbering
                        error_file = os.path.join(DEBUG_API_CALLS_DIR, f"{self.sequence_counter:02d}-error_response.json")
                        with open(error_file, 'w', encoding='utf-8') as f:
                            f.write(json.dumps(result, indent=2))
                        
                        logger.error(f"DEBUG: Error response saved to {error_file}")
                        print(f"\n[DEBUG] Error response saved to {error_file}")
                    
                    # Increment sequence counter even for failed attempts
                    self.sequence_counter += 1
                    raise Exception(error_msg)
                else:
                    error_msg = f"API Error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    
                    # Log the error response if debug mode is enabled
                    if self.debug_ai_calls:
                        # Write the error response to a file with sequential numbering
                        error_file = os.path.join(DEBUG_API_CALLS_DIR, f"{self.sequence_counter:02d}-http_error.txt")
                        with open(error_file, 'w', encoding='utf-8') as f:
                            f.write(f"Status Code: {response.status_code}\n\n{response.text}")
                        
                        logger.error(f"DEBUG: HTTP error saved to {error_file}")
                        print(f"\n[DEBUG] HTTP error saved to {error_file}")
                    
                    # Increment sequence counter even for failed attempts
                    self.sequence_counter += 1
                    raise Exception(error_msg)
            except Exception as e:
                if retry_count < max_retries - 1 and "quota exceeded" in str(e).lower():
                    # Only retry if it's a quota issue
                    retry_count += 1
                    wait_time = 60  # seconds
                    logger.warning(f"API call failed with quota error. Retrying in {wait_time} seconds... (attempt {retry_count} of {max_retries})")
                    
                    # Print countdown every 10 seconds
                    for remaining in range(wait_time, 0, -10):
                        logger.info(f"Waiting... (time left: {remaining} seconds)")
                        print(f"Waiting... (time left: {remaining} seconds)")
                        time.sleep(min(10, remaining))
                else:
                    logger.error(f"Exception during API call: {str(e)}")
                    # Increment sequence counter even for failed attempts
                    self.sequence_counter += 1
                    raise
        
        # If we got here, all retries failed
        # Increment sequence counter even for failed attempts
        self.sequence_counter += 1
        raise Exception(f"Failed to call Gemini API after {max_retries} attempts")