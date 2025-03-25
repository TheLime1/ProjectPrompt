import os
import json
import requests
import time
from datetime import datetime
from logger_config import logger, DEBUG_API_CALLS_DIR
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
    
    def call_gemini_api(self, prompt, tokenizer=None):
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
        
        if prompt_tokens > MAX_TOKENS:
            logger.error(f"Prompt exceeds max token limit: {prompt_tokens:,} > {MAX_TOKENS:,}")
            raise Exception(f"Prompt exceeds token limit ({prompt_tokens:,} > {MAX_TOKENS:,})")
        
        start_time = time.time()
        
        # Log the full prompt if debug mode is enabled
        if self.debug_ai_calls:
            # Create a debug file for this specific request with a timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Write the prompt to a file
            prompt_file = os.path.join(DEBUG_API_CALLS_DIR, f"prompt_{timestamp}.txt")
            with open(prompt_file, 'w', encoding='utf-8') as f:
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
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        
                        # Write the error response to a file
                        error_file = os.path.join(DEBUG_API_CALLS_DIR, f"http_error_{timestamp}.txt")
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
                        raise Exception(f"Token quota exceeded and prompt is too large ({prompt_tokens:,} > {MAX_TOKENS:,})")
                
                # Save the full response if debug mode is enabled
                if self.debug_ai_calls and response.status_code == 200:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    # Write the raw response to a file
                    response_file = os.path.join(DEBUG_API_CALLS_DIR, f"response_{timestamp}.json")
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
                                logger.info(f"Extracted response text (length: {len(response_text):,} characters)")
                                
                                # Save the extracted text response if debug mode is enabled
                                if self.debug_ai_calls:
                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    
                                    # Write the extracted text to a file
                                    text_file = os.path.join(DEBUG_API_CALLS_DIR, f"extracted_text_{timestamp}.txt")
                                    with open(text_file, 'w', encoding='utf-8') as f:
                                        f.write(response_text)
                                    
                                    logger.info(f"DEBUG: Extracted text saved to {text_file}")
                                    print(f"\n[DEBUG] Extracted text saved to {text_file}")
                                
                                return response_text
                    
                    error_msg = f"Unexpected response format: {json.dumps(result)[:100]}..."
                    logger.error(error_msg)
                    
                    # Log the full response on error if debug mode is enabled
                    if self.debug_ai_calls:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        
                        # Write the error response to a file
                        error_file = os.path.join(DEBUG_API_CALLS_DIR, f"error_response_{timestamp}.json")
                        with open(error_file, 'w', encoding='utf-8') as f:
                            f.write(json.dumps(result, indent=2))
                        
                        logger.error(f"DEBUG: Error response saved to {error_file}")
                        print(f"\n[DEBUG] Error response saved to {error_file}")
                    
                    raise Exception(error_msg)
                else:
                    error_msg = f"API Error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    
                    # Log the error response if debug mode is enabled
                    if self.debug_ai_calls:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        
                        # Write the error response to a file
                        error_file = os.path.join(DEBUG_API_CALLS_DIR, f"http_error_{timestamp}.txt")
                        with open(error_file, 'w', encoding='utf-8') as f:
                            f.write(f"Status Code: {response.status_code}\n\n{response.text}")
                        
                        logger.error(f"DEBUG: HTTP error saved to {error_file}")
                        print(f"\n[DEBUG] HTTP error saved to {error_file}")
                    
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
                    raise
        
        # If we got here, all retries failed
        raise Exception(f"Failed to call Gemini API after {max_retries} attempts")