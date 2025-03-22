import re
import nltk
from nltk.tokenize import sent_tokenize

# Download necessary NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

def chunk_text(text, max_chunk_size=1000, overlap=200):
    """
    Split text into overlapping chunks
    
    Args:
        text (str): The document text to chunk
        max_chunk_size (int): Maximum size of each chunk
        overlap (int): Number of characters to overlap between chunks
        
    Returns:
        list: List of chunk dictionaries with text and metadata
    """
    chunks = []
    
    # Split text by pages first (if page markers are present)
    pages = re.split(r'---\s*Page\s+\d+\s*---', text)
    pages = [p for p in pages if p.strip()]  # Remove empty pages
    
    # If no pages were detected, treat the whole text as a single page
    if not pages:
        pages = [text]
    
    current_position = 0
    
    for page_idx, page_text in enumerate(pages):
        # Skip empty pages
        if not page_text.strip():
            continue
            
        page_position = 0
        
        # Split the page into sentences
        sentences = sent_tokenize(page_text)
        
        current_chunk = ""
        current_chunk_sentences = []
        
        for sentence in sentences:
            # If adding this sentence exceeds the max chunk size and we already have content,
            # save the current chunk and start a new one with overlap
            if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
                # Create chunk with metadata
                chunk_data = {
                    "text": current_chunk,
                    "page": page_idx + 1,
                    "start_char": current_position + page_position - len(current_chunk),
                    "end_char": current_position + page_position,
                    "sentences": current_chunk_sentences
                }
                chunks.append(chunk_data)
                
                # Start a new chunk with overlap
                # Find overlap by counting back from the end
                overlap_text = ""
                overlap_sentences = []
                remaining_overlap = min(overlap, len(current_chunk))
                
                for s in reversed(current_chunk_sentences):
                    if len(s) <= remaining_overlap:
                        overlap_text = s + overlap_text
                        overlap_sentences.insert(0, s)
                        remaining_overlap -= len(s)
                        if remaining_overlap <= 0:
                            break
                
                current_chunk = overlap_text
                current_chunk_sentences = overlap_sentences
            
            # Add the sentence to the current chunk
            current_chunk += sentence
            current_chunk_sentences.append(sentence)
        
        # Don't forget to add the last chunk of the page
        if current_chunk:
            chunk_data = {
                "text": current_chunk,
                "page": page_idx + 1,
                "start_char": current_position + page_position - len(current_chunk),
                "end_char": current_position + page_position,
                "sentences": current_chunk_sentences
            }
            chunks.append(chunk_data)
        
        # Update the current position with the page length
        current_position += len(page_text)
    
    return chunks

def identify_chunk_topics(chunks):
    """
    Identify the main topics or themes for each chunk
    
    Args:
        chunks (list): List of text chunks
        
    Returns:
        list: List of chunks with topic information added
    """
    # Simple keyword-based topic identification
    topic_keywords = {
        "introduction": ["introduction", "overview", "background", "begin", "start"],
        "methodology": ["method", "approach", "procedure", "technique", "algorithm"],
        "results": ["result", "finding", "outcome", "analysis", "data", "figure", "table"],
        "discussion": ["discuss", "implication", "interpret", "meaning", "significance"],
        "conclusion": ["conclusion", "summary", "future work", "recommend", "end"],
        "reference": ["reference", "citation", "bibliography", "cite", "source"],
        "code": ["function", "class", "method", "variable", "code", "algorithm", "pseudo"]
    }
    
    for chunk in chunks:
        chunk_topics = []
        text_lower = chunk["text"].lower()
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                chunk_topics.append(topic)
        
        # Add a generic topic if none found
        if not chunk_topics:
            chunk_topics = ["content"]
        
        chunk["topics"] = chunk_topics
    
    return chunks

def get_relevant_chunks(query, chunks, top_k=3):
    """
    Simple keyword-based retrieval to find chunks relevant to a query
    
    Args:
        query (str): The user's question or query
        chunks (list): List of text chunks
        top_k (int): Number of chunks to return
        
    Returns:
        list: Top k most relevant chunks
    """
    # This is a simple keyword matching approach
    # A production system would use embeddings and vector similarity
    
    query_words = set(re.findall(r'\b\w+\b', query.lower()))
    
    # Score each chunk by the count of query words it contains
    chunk_scores = []
    for i, chunk in enumerate(chunks):
        chunk_text = chunk["text"].lower()
        # Count the query words that appear in the chunk
        matching_words = sum(1 for word in query_words if word in chunk_text)
        # Score is the count of matching words
        chunk_scores.append((i, matching_words))
    
    # Sort by score in descending order
    chunk_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Return the top_k chunks
    top_chunks = [chunks[idx] for idx, score in chunk_scores[:top_k] if score > 0]
    
    # If no matching chunks, return the first chunk as a fallback
    if not top_chunks and chunks:
        top_chunks = [chunks[0]]
    
    return top_chunks
