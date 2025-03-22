import os
import re
from text_chunker import get_relevant_chunks
from openai import OpenAI

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
client = OpenAI(api_key=OPENAI_API_KEY)

# Define content restriction constants
MAX_QUOTE_LENGTH = 150  # Maximum characters for direct quotes
MAX_CONSECUTIVE_QUOTES = 3  # Maximum number of consecutive direct quote requests allowed

# Tracking consecutive quotes for security
consecutive_quote_requests = 0
previous_chunks_provided = []

def answer_question(question, chunks):
    """
    Generate a secure answer to a question based on provided document chunks
    
    Args:
        question (str): User's question
        chunks (list): List of text chunks from the document
        
    Returns:
        str: Answer to the question
    """
    global consecutive_quote_requests, previous_chunks_provided
    
    # Check if this is a request for direct content extraction
    extraction_patterns = [
        r"extract\s+(?:all|complete|entire|full|whole)\s+(?:text|content|document|assignment|pdf)",
        r"(?:show|give|provide)\s+(?:me|us)?\s+(?:all|complete|entire|full|whole)\s+(?:text|content|document|assignment|pdf)",
        r"(?:copy|paste)\s+(?:all|complete|entire|full|whole)\s+(?:text|content|document|assignment|pdf)",
        r"(?:show|give|provide)\s+(?:me|us)?\s+(?:the\s+)?(?:next|previous|following|remaining|rest)\s+(?:part|section|text|content)",
        r"continue\s+(?:from|where\s+you\s+left\s+off)",
        r"(?:what|show)\s+(?:is|are|comes)\s+(?:after|before)\s+[\"\'].*?[\"\']"
    ]
    
    if any(re.search(pattern, question.lower()) for pattern in extraction_patterns):
        return (
            "I'm not able to extract or display large portions of the assignment content directly. "
            "This restriction helps protect the assignment's intellectual property. "
            "However, I can answer specific questions about the content, explain concepts, "
            "summarize sections, or analyze particular elements. "
            "Please try asking a more specific question about the assignment."
        )
    
    # Get relevant chunks for the question
    relevant_chunks = get_relevant_chunks(question, chunks)
    
    # Check for consecutive similar chunk requests (potential extraction attempt)
    chunk_overlap = set([c["text"] for c in relevant_chunks]) & set(previous_chunks_provided)
    if chunk_overlap and consecutive_quote_requests >= MAX_CONSECUTIVE_QUOTES:
        consecutive_quote_requests = 0  # Reset counter
        return (
            "I've noticed multiple consecutive requests for similar content sections. "
            "To protect the assignment's integrity, I'll need to limit direct content extraction. "
            "Please try asking a different question or request an analysis rather than direct text."
        )
    
    # Update tracking variables
    previous_chunks_provided = [c["text"] for c in relevant_chunks]
    consecutive_quote_requests += 1 if chunk_overlap else 0
    
    # Prepare context from relevant chunks
    context = ""
    for chunk in relevant_chunks:
        context += f"\n{chunk['text']}\n"
    
    # Construct the prompt for the AI
    system_prompt = """
    You are a secure academic assistant helping evaluate an assignment. Follow these strict rules:
    
    1. Answer ONLY based on the provided context. If the answer is not in the context, say "I don't have information about that in this assignment."
    2. Do not use any external knowledge beyond the provided context.
    3. Keep direct quotes from the assignment to under 150 characters and always put them in quotation marks.
    4. Prefer paraphrasing over quoting whenever possible.
    5. Never provide complete code solutions or full paragraphs from the assignment.
    6. If asked to extract large sections of content, refuse and explain the policy.
    7. Format and structure your answer to be easily readable.
    
    Remember, your purpose is to help evaluate the quality of work while protecting the assignment content.
    """
    
    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Question: {question}\n\nContext from the assignment:\n{context}"}
            ],
            temperature=0.3,
            max_tokens=800
        )
        
        answer = response.choices[0].message.content
        
        # Post-processing to enforce quote length limits
        quote_pattern = r'\"([^\"]{' + str(MAX_QUOTE_LENGTH) + r',})\"'
        long_quotes = re.findall(quote_pattern, answer)
        
        for long_quote in long_quotes:
            truncated_quote = long_quote[:MAX_QUOTE_LENGTH-3] + "..."
            answer = answer.replace(f'"{long_quote}"', f'"{truncated_quote}"')
        
        return answer
        
    except Exception as e:
        return f"Error generating answer: {str(e)}. Please try again or reformulate your question."

def check_content_extraction_attempt(questions, threshold=0.7):
    """
    Check if a series of questions appear to be attempting content extraction
    
    Args:
        questions (list): List of previous questions
        threshold (float): Similarity threshold for detection
        
    Returns:
        bool: True if extraction attempt detected
    """
    # Simple extraction pattern detection
    sequential_patterns = [
        r"continue",
        r"next part",
        r"more details",
        r"next section",
        r"go on",
        r"proceed",
        r"then what",
        r"what follows",
        r"what happens next"
    ]
    
    # Count how many questions match extraction patterns
    extraction_attempts = sum(
        1 for q in questions[-3:] 
        if any(re.search(pattern, q.lower()) for pattern in sequential_patterns)
    )
    
    # If more than threshold of recent questions match patterns, flag as extraction attempt
    return extraction_attempts / min(3, len(questions)) >= threshold

def summarize_without_extraction(text, max_summary_length=300):
    """
    Create a summary of text that doesn't reveal too much content
    
    Args:
        text (str): Text to summarize
        max_summary_length (int): Maximum length of summary
        
    Returns:
        str: Secure summary
    """
    system_prompt = """
    Create a high-level summary of the following text. Focus on general concepts and ideas rather than specific details. 
    Do not include any direct quotes longer than a few words. Make the summary abstract enough that the original text 
    cannot be reconstructed from it, while still conveying the main points.
    """
    
    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=max_summary_length
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error generating summary: {str(e)}"
