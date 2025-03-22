import hashlib
import re
import pandas as pd
from io import BytesIO

def get_file_hash(uploaded_file):
    """
    Generate a hash for a file to track changes
    
    Args:
        uploaded_file: The uploaded file object
        
    Returns:
        str: Hash of the file content
    """
    content = uploaded_file.getvalue()
    file_hash = hashlib.md5(content).hexdigest()
    return file_hash

def is_extraction_attempt(question):
    """
    Check if a question appears to be attempting to extract large content
    
    Args:
        question (str): The user's question
        
    Returns:
        bool: True if question seems to be an extraction attempt
    """
    extraction_patterns = [
        r"extract\s+(?:all|complete|entire|full|whole)",
        r"(?:show|give|provide)\s+(?:me|us)?\s+(?:all|complete|entire|full|whole)",
        r"(?:copy|paste)\s+(?:all|complete|entire|full|whole)",
        r"(?:next|previous|following|remaining|rest)\s+(?:part|section|text|content)",
        r"continue\s+(?:from|where\s+you\s+left\s+off)",
        r"what\s+(?:is|are|comes)\s+(?:after|before)"
    ]
    
    return any(re.search(pattern, question.lower()) for pattern in extraction_patterns)

def is_consecutive_query(current_query, query_history, similarity_threshold=0.7):
    """
    Detect if queries are attempting to iterate through content
    
    Args:
        current_query (str): Current user query
        query_history (list): List of previous queries
        similarity_threshold (float): Threshold for similarity detection
        
    Returns:
        bool: True if queries appear to be sequential extraction attempts
    """
    if not query_history:
        return False
    
    # Check for sequential patterns
    sequential_patterns = [
        r"continue",
        r"next",
        r"more",
        r"go on",
        r"proceed",
        r"then",
        r"after",
        r"following"
    ]
    
    # Check if current query contains sequential patterns
    is_sequential = any(re.search(pattern, current_query.lower()) for pattern in sequential_patterns)
    
    # If sequential patterns found, this might be an extraction attempt
    return is_sequential

def count_tokens(text):
    """
    Estimate the number of tokens in a text
    
    Args:
        text (str): The text to count tokens for
        
    Returns:
        int: Estimated token count
    """
    # Simple approximation: about 4 characters per token for English text
    return len(text) // 4

def truncate_text_to_tokens(text, max_tokens=1000):
    """
    Truncate text to stay within token limits
    
    Args:
        text (str): The text to truncate
        max_tokens (int): Maximum number of tokens
        
    Returns:
        str: Truncated text
    """
    # Approximate tokens
    if count_tokens(text) <= max_tokens:
        return text
    
    # Otherwise truncate to approximate character count
    char_limit = max_tokens * 4
    return text[:char_limit] + "..."

def extract_table_from_text(text):
    """
    Attempt to extract table data from text
    
    Args:
        text (str): Text potentially containing table data
        
    Returns:
        pandas.DataFrame or None: Extracted table if successful
    """
    # Look for common table patterns
    lines = text.strip().split('\n')
    
    # Check if text has pipe-separated table format
    if any('|' in line for line in lines):
        pipe_rows = [line for line in lines if '|' in line]
        
        # Clean up rows and split by pipes
        cleaned_rows = []
        for row in pipe_rows:
            cells = [cell.strip() for cell in row.split('|')]
            # Remove empty cells at the start and end (from leading/trailing pipes)
            if cells and not cells[0]:
                cells = cells[1:]
            if cells and not cells[-1]:
                cells = cells[:-1]
            if cells:
                cleaned_rows.append(cells)
        
        # Check if we have enough rows and consistent number of columns
        if len(cleaned_rows) >= 2:
            # Check if second row looks like a separator (----)
            if all(cell.strip().startswith('-') for cell in cleaned_rows[1]):
                # This is a markdown table, skip the separator row
                headers = cleaned_rows[0]
                data = cleaned_rows[2:]
                return pd.DataFrame(data, columns=headers)
            else:
                # Just a regular pipe-delimited table
                headers = cleaned_rows[0]
                data = cleaned_rows[1:]
                return pd.DataFrame(data, columns=headers)
    
    return None
