import os
from openai import OpenAI

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
client = OpenAI(api_key=OPENAI_API_KEY)

def generate_navigation_suggestions(text, chunks, previous_question=None, previous_answer=None):
    """
    Generate smart navigation suggestions based on document content
    
    Args:
        text (str): Full document text
        chunks (list): Document chunks
        previous_question (str, optional): Previous user question
        previous_answer (str, optional): Previous answer
        
    Returns:
        list: List of suggested questions
    """
    # Sample the document to create an overview for suggestions
    document_sample = ""
    
    # Get a sample from different parts of the document
    if chunks:
        # Get beginning, middle and end chunks
        document_sample += chunks[0]["text"][:500] + "\n\n"
        
        if len(chunks) > 2:
            middle_idx = len(chunks) // 2
            document_sample += chunks[middle_idx]["text"][:500] + "\n\n"
        
        document_sample += chunks[-1]["text"][:500]
    
    # Context for generation
    context = f"Document overview:\n{document_sample}\n\n"
    
    # If we have previous interaction, include it
    if previous_question and previous_answer:
        context += f"Previous question: {previous_question}\n"
        context += f"Answer provided: {previous_answer}\n\n"
    
    prompt = context + """
    Based on this document overview and the previous interaction (if any), generate 6 insightful questions that would help an evaluator explore the document further. 
    
    The questions should:
    1. Be diverse and cover different aspects of the document
    2. Help explore key concepts, methodologies, results, and conclusions
    3. Be specific enough to get meaningful answers from the document content
    4. Not request large chunks of text or entire sections directly
    5. Focus on evaluation and understanding rather than extraction
    
    Format the response as a JSON array of strings with just the questions.
    """
    
    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an assistant that generates helpful navigation questions for document exploration. Your questions should be insightful and help evaluators understand the document deeply."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=500
        )
        
        # Parse response JSON
        import json
        response_content = response.choices[0].message.content
        questions_data = json.loads(response_content)
        
        # Extract questions array (handle different possible formats)
        if isinstance(questions_data, list):
            questions = questions_data
        elif "questions" in questions_data:
            questions = questions_data["questions"]
        else:
            # Try to find an array in the response
            for key, value in questions_data.items():
                if isinstance(value, list):
                    questions = value
                    break
            else:
                questions = []
        
        return questions[:6]  # Return up to 6 questions
        
    except Exception as e:
        print(f"Error generating navigation suggestions: {e}")
        # Fallback suggestions
        return [
            "What are the main findings or conclusions in this assignment?",
            "How does the methodology section approach the problem?",
            "What evidence supports the key arguments in this work?",
            "Are there any limitations discussed in the assignment?",
            "How does this work compare to existing research or approaches?",
            "What are the implications of these findings for the field?"
        ]

def identify_document_sections(chunks):
    """
    Identify the main sections of the document for navigation
    
    Args:
        chunks (list): Document chunks
        
    Returns:
        list: List of section dictionaries with titles and positions
    """
    # Simple section detection based on common heading patterns
    section_patterns = [
        r"^#+\s+(.+)$",  # Markdown headings
        r"^([A-Z][A-Za-z\s]+):$",  # Capitalized text with colon
        r"^([A-Z][A-Za-z\s]+)$",  # All-caps or capitalized standalone line
        r"^(\d+\.[\d\.]*\s+[A-Z][A-Za-z\s]+)$"  # Numbered sections
    ]
    
    sections = []
    current_page = 1
    
    for chunk in chunks:
        chunk_text = chunk["text"]
        page = chunk["page"]
        
        # Update current page
        if page != current_page:
            current_page = page
        
        # Look for section headers in the chunk
        lines = chunk_text.split("\n")
        for line in lines:
            for pattern in section_patterns:
                match = re.search(pattern, line.strip())
                if match:
                    section_title = match.group(1)
                    # Skip very short titles or common false positives
                    if len(section_title) > 3 and section_title.lower() not in ["note", "figure", "table"]:
                        sections.append({
                            "title": section_title,
                            "page": page,
                            "preview": chunk_text[:100] + "..."
                        })
    
    return sections
