import logging
from logger_config import logger

# Add token calculation imports 
try:
    from vertexai.preview import tokenization
    TOKENIZER_AVAILABLE = True
    logger.info("Tokenizer available: using vertexai package for accurate token counting")
except ImportError:
    TOKENIZER_AVAILABLE = False
    logger.warning("vertexai package not available. Token calculation will be estimated.")

# Maximum tokens for Gemini 1.5 Pro
MAX_TOKENS = 1800000
logger.info(f"Maximum token limit set to {MAX_TOKENS:,}")

def calculate_tokens(text, tokenizer=None):
    """Calculate the number of tokens in a text string"""
    if tokenizer is not None:
        try:
            result = tokenizer.count_tokens(text)
            logger.debug(f"Token calculation: {result.total_tokens:,} tokens for text length {len(text):,}")
            return result.total_tokens
        except Exception as e:
            logger.error(f"Error calculating tokens: {str(e)}")
            # Fallback to estimation
            estimated = len(text) // 4
            logger.warning(f"Using estimated token count: {estimated:,}")
            return estimated
    else:
        # If tokenizer not available, make a rough estimate
        estimated = len(text) // 4
        logger.debug(f"Estimated token count: {estimated:,} for text length {len(text):,}")
        return estimated

def get_tokenizer():
    """Get a tokenizer if available"""
    if TOKENIZER_AVAILABLE:
        return tokenization.get_tokenizer_for_model("gemini-1.5-pro")
    return None