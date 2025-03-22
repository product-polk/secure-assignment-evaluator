import streamlit as st
import os
import tempfile
from pdf_processor import extract_text_and_elements_from_pdf
from text_chunker import chunk_text
from secure_qa import answer_question
from visualization import extract_tables_and_visualize, extract_charts_and_visualize
from navigation import generate_navigation_suggestions
from utils import get_file_hash

st.set_page_config(
    page_title="Secure Assignment Evaluator",
    page_icon="📚",
    layout="wide",
)

# Initialize session state variables
if 'pdf_processed' not in st.session_state:
    st.session_state.pdf_processed = False
if 'pdf_text' not in st.session_state:
    st.session_state.pdf_text = ""
if 'pdf_chunks' not in st.session_state:
    st.session_state.pdf_chunks = []
if 'file_hash' not in st.session_state:
    st.session_state.file_hash = None
if 'tables' not in st.session_state:
    st.session_state.tables = []
if 'charts' not in st.session_state:
    st.session_state.charts = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'suggested_questions' not in st.session_state:
    st.session_state.suggested_questions = []

def main():
    st.title("Secure Assignment Evaluator")
    
    # Sidebar for PDF upload and options
    with st.sidebar:
        st.header("Upload Assignment")
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
        
        if uploaded_file is not None:
            # Process the PDF if it's new or different from the previous one
            file_hash = get_file_hash(uploaded_file)
            
            if st.session_state.file_hash != file_hash:
                with st.spinner("Processing PDF..."):
                    # Save the uploaded file to a temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        temp_file_path = tmp_file.name
                    
                    # Extract text and elements from the PDF
                    text, tables, charts = extract_text_and_elements_from_pdf(temp_file_path)
                    
                    # Clean up temporary file
                    os.unlink(temp_file_path)
                    
                    # Chunk the text
                    chunks = chunk_text(text)
                    
                    # Update session state
                    st.session_state.pdf_processed = True
                    st.session_state.pdf_text = text
                    st.session_state.pdf_chunks = chunks
                    st.session_state.file_hash = file_hash
                    st.session_state.tables = tables
                    st.session_state.charts = charts
                    st.session_state.chat_history = []
                    
                    # Generate initial navigation suggestions
                    st.session_state.suggested_questions = generate_navigation_suggestions(text, chunks)
                    
                st.success("PDF processed successfully!")
        
        if st.session_state.pdf_processed:
            st.write("PDF Statistics:")
            st.write(f"- Text length: {len(st.session_state.pdf_text)} characters")
            st.write(f"- Chunks: {len(st.session_state.pdf_chunks)}")
            st.write(f"- Tables: {len(st.session_state.tables)}")
            st.write(f"- Charts/Graphs: {len(st.session_state.charts)}")
    
    # Main content area
    if not st.session_state.pdf_processed:
        st.info("Please upload a PDF assignment to begin evaluation.")
        
        # Show information about the tool
        st.write("## About this Tool")
        st.write("""
        This secure assignment evaluation tool allows you to:
        - Ask questions about the assignment content
        - View tables and charts from the assignment
        - Get navigation suggestions to explore different sections
        - Gain insights without being able to extract the full content
        
        Upload a PDF to get started!
        """)
    else:
        # Create tabs for different functionalities
        tab1, tab2, tab3 = st.tabs(["Q&A Assistant", "Data Visualization", "Navigation Guide"])
        
        with tab1:
            st.header("Ask about the Assignment")
            
            # Display suggested questions
            if st.session_state.suggested_questions:
                st.write("#### Suggested Questions")
                cols = st.columns(2)
                for i, question in enumerate(st.session_state.suggested_questions[:6]):
                    col = cols[i % 2]
                    if col.button(question, key=f"suggested_{i}"):
                        # Use the suggested question
                        st.session_state.chat_history.append({"role": "user", "content": question})
                        with st.spinner("Thinking..."):
                            answer = answer_question(question, st.session_state.pdf_chunks)
                        st.session_state.chat_history.append({"role": "assistant", "content": answer})
                        
                        # Update suggested questions based on the answer
                        st.session_state.suggested_questions = generate_navigation_suggestions(
                            st.session_state.pdf_text,
                            st.session_state.pdf_chunks,
                            question,
                            answer
                        )
                        st.rerun()
            
            # Initialize the text input state if it doesn't exist
            if "question_text" not in st.session_state:
                st.session_state.question_text = ""
                
            # Create a callback to handle submission and clear input
            def handle_question_submit():
                # Get the question from session state
                user_question = st.session_state.question_input
                if user_question:
                    # Add to chat history
                    st.session_state.chat_history.append({"role": "user", "content": user_question})
                    
                    # Generate answer
                    with st.spinner("Generating answer..."):
                        answer = answer_question(user_question, st.session_state.pdf_chunks)
                    
                    # Add answer to chat history
                    st.session_state.chat_history.append({"role": "assistant", "content": answer})
                    
                    # Update suggested questions
                    st.session_state.suggested_questions = generate_navigation_suggestions(
                        st.session_state.pdf_text,
                        st.session_state.pdf_chunks,
                        user_question,
                        answer
                    )
                    
                    # Reset the input widget by clearing its value in session state
                    st.session_state.question_input = ""
            
            # Chat input with submit callback
            user_question = st.text_input(
                "Ask a question about the assignment:", 
                key="question_input", 
                on_change=handle_question_submit
            )
            
            # Add submit button (not strictly necessary with on_change)
            if st.button("Submit") and user_question:
                handle_question_submit()
            
            # Display chat history
            st.write("#### Conversation History")
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.write(f"**You:** {message['content']}")
                else:
                    st.write(f"**Assistant:** {message['content']}")
                st.divider()
        
        with tab2:
            st.header("Data Visualization")
            
            # Display tables
            if st.session_state.tables:
                st.subheader("Tables from the Assignment")
                for i, table in enumerate(st.session_state.tables):
                    with st.expander(f"Table {i+1}"):
                        extract_tables_and_visualize(table)
            else:
                st.info("No tables detected in the assignment.")
            
            # Display charts
            if st.session_state.charts:
                st.subheader("Charts from the Assignment")
                for i, chart in enumerate(st.session_state.charts):
                    with st.expander(f"Chart {i+1}"):
                        extract_charts_and_visualize(chart)
            else:
                st.info("No charts detected in the assignment.")
        
        with tab3:
            st.header("Assignment Navigation")
            
            # Show sections navigation
            st.subheader("Explore Assignment Sections")
            
            # Generate a structural overview of the document
            with st.spinner("Analyzing document structure..."):
                structure_prompt = "Based on the document chunks, identify the main sections or chapters of this assignment. List them in order."
                structure = answer_question(structure_prompt, st.session_state.pdf_chunks)
            
            st.write(structure)
            
            # Show key concepts
            st.subheader("Key Concepts")
            with st.spinner("Extracting key concepts..."):
                concepts_prompt = "What are the 5-7 most important concepts or ideas in this assignment? List each with a very brief description."
                concepts = answer_question(concepts_prompt, st.session_state.pdf_chunks)
            
            st.write(concepts)

if __name__ == "__main__":
    main()
