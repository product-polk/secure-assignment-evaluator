import streamlit as st
import os
import tempfile
import uuid
import json
import sys
from datetime import datetime
from pdf_processor import extract_text_and_elements_from_pdf
from text_chunker import chunk_text, simple_sent_tokenize
from secure_qa import answer_question
from visualization import extract_tables_and_visualize, extract_charts_and_visualize
from navigation import generate_navigation_suggestions
from utils import get_file_hash
from encryption import encrypt_data, decrypt_data, secure_file_path, encrypt_file, decrypt_file

# Handle Streamlit Cloud health check endpoint
# This is added to fix the "connection refused" error on Streamlit Cloud
if len(sys.argv) > 1 and sys.argv[1] == "healthz":
    print("Health check: OK")
    sys.exit(0)

# Use our custom sentence tokenizer instead of NLTK's
# This prevents NLTK from trying to load punkt_tab resource
try:
    import nltk.tokenize
    nltk.tokenize.sent_tokenize = simple_sent_tokenize
except ImportError:
    # NLTK not available, which is fine since we use our custom tokenizer
    pass

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
# New state variables for user modes and assignment sharing
if 'user_mode' not in st.session_state:
    st.session_state.user_mode = None  # 'candidate' or 'evaluator'
if 'assignment_id' not in st.session_state:
    st.session_state.assignment_id = None
# UI state management
if 'container_reset' not in st.session_state:
    st.session_state.container_reset = False
if 'assignments_dir' not in st.session_state:
    # Create a data directory for storing assignments if it doesn't exist
    data_dir = os.path.join(os.getcwd(), 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    st.session_state.assignments_dir = data_dir

def save_assignment_data():
    """Save processed assignment data for sharing"""
    # Import needed modules
    import os
    if not st.session_state.pdf_processed:
        return None
    
    # Create a custom JSON encoder for DataFrames
    class DataFrameEncoder(json.JSONEncoder):
        def default(self, o):
            # Convert DataFrame to dict
            if hasattr(o, 'to_dict'):
                return o.to_dict()
            # Let the base class handle other types
            return super().default(o)
    
    # Generate a unique ID if not already assigned
    if not st.session_state.assignment_id:
        # Create a shorter, more readable ID by using base64 encoding of random bytes
        import base64
        import os
        # Generate 6 random bytes (will result in 8 characters when base64 encoded)
        random_bytes = os.urandom(6)
        # Convert to base64 and remove any special characters
        short_id = base64.urlsafe_b64encode(random_bytes).decode('utf-8').replace('=', '')
        st.session_state.assignment_id = short_id
    
    # Deep copy and convert tables to a serializable format (safer approach)
    import copy
    import pandas as pd
    
    def convert_dataframes_to_dict(obj):
        """Recursively convert DataFrames to dictionaries in nested structures"""
        if isinstance(obj, pd.DataFrame):
            return obj.to_dict()
        elif isinstance(obj, dict):
            return {k: convert_dataframes_to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_dataframes_to_dict(item) for item in obj]
        else:
            return obj
    
    # Create serializable copies of tables and charts
    serializable_tables = convert_dataframes_to_dict(copy.deepcopy(st.session_state.tables))
    serializable_charts = convert_dataframes_to_dict(copy.deepcopy(st.session_state.charts))
    
    # Create assignment data with serializable components
    assignment_data = {
        'id': st.session_state.assignment_id,
        'timestamp': datetime.now().isoformat(),
        'pdf_text': st.session_state.pdf_text,
        'pdf_chunks': st.session_state.pdf_chunks,
        'tables': serializable_tables,
        'charts': serializable_charts,
        'file_hash': st.session_state.file_hash
    }
    
    # Save to encrypted file using secure file path
    assignment_path = secure_file_path(st.session_state.assignment_id)
    
    # Convert to JSON string with custom encoder
    json_data = json.dumps(assignment_data, cls=DataFrameEncoder)
    
    # Encrypt the data
    encrypted_data = encrypt_data(assignment_data, st.session_state.assignment_id)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(assignment_path), exist_ok=True)
    
    # Write encrypted data
    with open(assignment_path, 'wb') as f:
        f.write(encrypted_data)
    
    return st.session_state.assignment_id

def load_assignment_data(assignment_id):
    """Load assignment data from ID"""
    # Import needed modules
    import os
    # Get secure file path for this assignment ID
    assignment_path = secure_file_path(assignment_id)
    
    if not os.path.exists(assignment_path):
        return False
    
    try:
        # Read encrypted data
        with open(assignment_path, 'rb') as f:
            encrypted_data = f.read()
        
        # Decrypt the data
        assignment_data = decrypt_data(encrypted_data, assignment_id)
        
        # Import pandas here to avoid issues if it's not at the top level
        import pandas as pd
        
        def convert_dicts_to_dataframes(obj):
            """Recursively convert dictionaries to DataFrames in nested structures where appropriate"""
            if isinstance(obj, dict):
                # Check if this dict should be a DataFrame (has 'orient' indication or proper structure)
                if any(k in obj for k in ['index', 'columns', 'data']) or len(obj) > 0:
                    try:
                        # Try to convert to DataFrame if it has proper structure
                        return pd.DataFrame.from_dict(obj)
                    except (ValueError, TypeError):
                        # Not a valid DataFrame format, continue with recursive conversion
                        return {k: convert_dicts_to_dataframes(v) for k, v in obj.items()}
                else:
                    return {k: convert_dicts_to_dataframes(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_dicts_to_dataframes(item) for item in obj]
            else:
                return obj
        
        # Load data into session state
        st.session_state.pdf_text = assignment_data['pdf_text']
        st.session_state.pdf_chunks = assignment_data['pdf_chunks']
        
        # Recursively convert dictionaries to DataFrames where needed
        tables = assignment_data['tables']
        for table in tables:
            if 'df' in table and isinstance(table['df'], dict):
                # This is a specific case where we know it should be a DataFrame
                table['df'] = pd.DataFrame.from_dict(table['df'])
            else:
                # Apply recursive conversion for other nested structures
                table = convert_dicts_to_dataframes(table)
        st.session_state.tables = tables
        
        charts = assignment_data['charts']
        for chart in charts:
            if 'data' in chart and isinstance(chart['data'], dict):
                # This is a specific case where we know it should be a DataFrame
                chart['data'] = pd.DataFrame.from_dict(chart['data'])
            else:
                # Apply recursive conversion for other nested structures
                chart = convert_dicts_to_dataframes(chart)
        st.session_state.charts = charts
        
        st.session_state.file_hash = assignment_data['file_hash']
        st.session_state.pdf_processed = True
        st.session_state.assignment_id = assignment_id
        
        # Generate initial suggested questions if needed
        if not st.session_state.suggested_questions:
            initial_prompt = "Based on the content of this assignment, what are 6 important questions an evaluator might ask to assess the quality of the work?"
            initial_response = answer_question(initial_prompt, st.session_state.pdf_chunks)
            
            import re
            questions = re.findall(r'\d+\.\s(.*?)(?=\d+\.|$)', initial_response, re.DOTALL)
            if questions:
                st.session_state.suggested_questions = [q.strip() for q in questions if q.strip()]
            else:
                # If regex fails, use the lines as questions
                lines = initial_response.split('\n')
                st.session_state.suggested_questions = [line.strip() for line in lines if line.strip() and not line.startswith("Here") and not line.startswith("These")]
        
        return True
    except Exception as e:
        st.error(f"Error loading assignment: {e}")
        return False

def display_chat_interface():
    """Display improved chat interface for Q&A interactions"""
    st.write("#### Ask about the Assignment")
    
    # Initialize session state variables
    if "submit_question" not in st.session_state:
        st.session_state.submit_question = False
    
    # Create a callback to handle form submission
    def handle_submit():
        # Get the question from session state
        question = st.session_state.question_input
        
        # Only process if there's an actual question
        if question:
            # Add to chat history
            st.session_state.chat_history.append({"role": "user", "content": question})
            
            # Set a flag for processing after form
            st.session_state.submit_question = True
            st.session_state.current_question = question
            
            # Clear the input field by setting session state
            st.session_state.question_input = ""
    
    # Display chat history in a more visually appealing way
    if st.session_state.chat_history:
        st.write("#### Conversation")
        for i, message in enumerate(st.session_state.chat_history):
            if message["role"] == "user":
                # User message with light blue background and improved text styling
                st.markdown(
                    f"""
                    <div style="background-color: #e6f3ff; padding: 10px; border-radius: 10px; margin-bottom: 10px; color: #000000;">
                        <strong style="color: #000000;">You:</strong><br>
                        <span style="color: #000000;">{message['content']}</span>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
            else:
                # Assistant message with light gray background and improved text styling
                st.markdown(
                    f"""
                    <div style="background-color: #f0f0f0; padding: 10px; border-radius: 10px; margin-bottom: 10px; color: #000000;">
                        <strong style="color: #000000;">Assistant:</strong><br>
                        <span style="color: #000000;">{message['content']}</span>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
    
    # Set up form with on_change callback
    with st.form(key="question_form", clear_on_submit=True):
        st.text_input(
            "Ask a question about the assignment:", 
            key="question_input",
            placeholder="Type your question here..."
        )
        submit_cols = st.columns([3, 1])
        with submit_cols[1]:
            submit_button = st.form_submit_button(
                "Submit Question", 
                on_click=handle_submit,
                use_container_width=True
            )
    
    # Display suggested questions after the input form
    if st.session_state.suggested_questions:
        st.write("#### Suggested Questions")
        suggestion_cols = st.columns(2)
        for i, question in enumerate(st.session_state.suggested_questions[:6]):
            col = suggestion_cols[i % 2]
            if col.button(question, key=f"suggested_{i}", use_container_width=True):
                # Use the suggested question
                st.session_state.chat_history.append({"role": "user", "content": question})
                
                # Show a "thinking" message
                thinking_placeholder = st.empty()
                thinking_placeholder.markdown(
                    """
                    <div style="background-color: #f0f0f0; padding: 10px; border-radius: 10px; margin-bottom: 10px; color: #000000;">
                        <strong style="color: #000000;">Assistant:</strong><br>
                        <span style="color: #000000;">Thinking... <span class="blinking">▌</span></span>
                    </div>
                    <style>
                    .blinking {
                        animation: blinker 1s linear infinite;
                    }
                    @keyframes blinker {
                        50% { opacity: 0; }
                    }
                    </style>
                    """, 
                    unsafe_allow_html=True
                )
                
                # Generate the answer
                answer = answer_question(question, st.session_state.pdf_chunks)
                
                # Replace the thinking message with the real answer
                thinking_placeholder.empty()
                
                # Add to chat history
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                
                # Update suggested questions based on the answer
                st.session_state.suggested_questions = generate_navigation_suggestions(
                    st.session_state.pdf_text,
                    st.session_state.pdf_chunks,
                    question,
                    answer
                )
                st.rerun()
    
    # Process submitted question after the form
    if st.session_state.submit_question and hasattr(st.session_state, 'current_question'):
        # Get the question
        question = st.session_state.current_question
        
        # Reset the submission flag
        st.session_state.submit_question = False
        
        # Show a "thinking" message
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown(
            """
            <div style="background-color: #f0f0f0; padding: 10px; border-radius: 10px; margin-bottom: 10px; color: #000000;">
                <strong style="color: #000000;">Assistant:</strong><br>
                <span style="color: #000000;">Thinking... <span class="blinking">▌</span></span>
            </div>
            <style>
            .blinking {
                animation: blinker 1s linear infinite;
            }
            @keyframes blinker {
                50% { opacity: 0; }
            }
            </style>
            """, 
            unsafe_allow_html=True
        )
        
        # Generate answer
        answer = answer_question(question, st.session_state.pdf_chunks)
        
        # Remove the thinking message
        thinking_placeholder.empty()
        
        # Add answer to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        
        # Update suggested questions
        st.session_state.suggested_questions = generate_navigation_suggestions(
            st.session_state.pdf_text,
            st.session_state.pdf_chunks,
            question,
            answer
        )
        
        # Clear the current question
        if hasattr(st.session_state, 'current_question'):
            delattr(st.session_state, 'current_question')
            
        # Rerun to refresh the UI with new messages
        st.rerun()

def evaluation_interface():
    """Main evaluation interface with tabs"""
    # Create tabs for different functionalities
    tab1, tab2, tab3 = st.tabs(["Q&A Assistant", "Data Visualization", "Navigation Guide"])
    
    with tab1:
        st.header("Ask about the Assignment")
        # Use the improved chat interface
        display_chat_interface()
    
    with tab2:
        st.header("Data Visualization")
        
        # Display tables
        if st.session_state.tables:
            st.subheader("Tables from the Assignment")
            for i, table in enumerate(st.session_state.tables):
                with st.expander(f"Table {i+1} (Page {table['page']})"):
                    extract_tables_and_visualize(table)
        else:
            st.info("No tables detected in the assignment.")
        
        # Display charts
        if st.session_state.charts:
            st.subheader("Charts from the Assignment")
            for i, chart in enumerate(st.session_state.charts):
                with st.expander(f"Chart {i+1} (Page {chart['page']})"):
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

def select_user_mode():
    """Show mode selection screen"""
    st.title("Secure Assignment Evaluator")
    
    st.write("### Choose Your Role")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("##### I'm submitting an assignment")
        if st.button("Candidate Mode", use_container_width=True):
            st.session_state.user_mode = 'candidate'
            st.rerun()
    
    with col2:
        st.info("##### I'm evaluating an assignment")
        if st.button("Evaluator Mode", use_container_width=True):
            st.session_state.user_mode = 'evaluator'
            st.rerun()
    
    st.markdown("---")
    st.write("### About This Application")
    st.write("""
    This secure assignment evaluation platform allows:
    
    **For Candidates:**
    - Upload your assignment (PDF format)
    - Generate a secure sharing link for evaluators
    - Your original content remains protected
    
    **For Evaluators:**
    - Access assignments via secure links
    - Ask questions about the assignment content
    - View secure insights about tables and charts
    - Navigate through the assignment with AI guidance
    - Evaluate quality without extracting content
    """)

def candidate_mode():
    """Interface for candidates uploading assignments"""
    # Import needed modules
    import os
    
    # Clear the screen and start fresh
    st.empty()
    
    # Put mode switching in sidebar with better organization
    with st.sidebar:
        st.title("Navigation")
        if st.button("Switch to Evaluator Mode", use_container_width=True):
            # Clear UI state variables as needed
            if 'pdf_processed' in st.session_state:
                st.session_state.pdf_processed = False
            if 'chat_history' in st.session_state:
                st.session_state.chat_history = []
            if 'suggested_questions' in st.session_state:
                st.session_state.suggested_questions = []
            
            # Set mode and reset flag
            st.session_state.user_mode = 'evaluator'
            st.session_state.container_reset = True
            st.rerun()
    
    # Main content area
    st.title("Assignment Submission")
    
    # Upload section
    st.write("### Upload Your Assignment")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file is not None:
        # Process the PDF if it's new or different from the previous one
        file_hash = get_file_hash(uploaded_file)
        
        if st.session_state.file_hash != file_hash:
            with st.spinner("Processing your assignment..."):
                # Get the raw PDF data
                pdf_data = uploaded_file.getvalue()
                
                # Save the uploaded file to a temporary file for processing
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(pdf_data)
                    pdf_path = tmp_file.name
                
                # Extract text and other elements from the PDF
                text, tables, charts = extract_text_and_elements_from_pdf(pdf_path)
                
                # Clean up the temporary file
                os.unlink(pdf_path)
                
                # Generate a unique ID for this assignment if not already assigned
                if not st.session_state.assignment_id:
                    import base64
                    import os
                    # Generate 6 random bytes (will result in 8 characters when base64 encoded)
                    random_bytes = os.urandom(6)
                    # Convert to base64 and remove any special characters
                    short_id = base64.urlsafe_b64encode(random_bytes).decode('utf-8').replace('=', '')
                    st.session_state.assignment_id = short_id
                
                # Encrypt and store the original PDF file
                encrypted_pdf = encrypt_file(pdf_data, st.session_state.assignment_id)
                pdf_storage_path = os.path.join(
                    st.session_state.assignments_dir, 
                    f"{st.session_state.assignment_id}_pdf.enc"
                )
                with open(pdf_storage_path, 'wb') as f:
                    f.write(encrypted_pdf)
                
                # Process text into chunks for better handling
                chunks = chunk_text(text)
                
                # Update the session state
                st.session_state.pdf_text = text
                st.session_state.pdf_chunks = chunks
                st.session_state.file_hash = file_hash
                st.session_state.pdf_processed = True
                st.session_state.tables = tables
                st.session_state.charts = charts
                st.session_state.chat_history = []
                
                # Initialize suggested questions
                initial_prompt = "Based on the content of this assignment, what are 6 important questions an evaluator might ask to assess the quality of the work?"
                with st.spinner("Analyzing assignment content..."):
                    initial_response = answer_question(initial_prompt, chunks)
                    # Extract questions from the response
                    import re
                    questions = re.findall(r'\d+\.\s(.*?)(?=\d+\.|$)', initial_response, re.DOTALL)
                    if questions:
                        st.session_state.suggested_questions = [q.strip() for q in questions if q.strip()]
                    else:
                        # If regex fails, use the lines as questions
                        lines = initial_response.split('\n')
                        st.session_state.suggested_questions = [line.strip() for line in lines if line.strip() and not line.startswith("Here") and not line.startswith("These")]
            
            st.success("Assignment processed successfully!")
    
    # Show sharing options if file is processed
    if st.session_state.pdf_processed:
        st.write("### Share with Evaluators")
        st.info("Generate a secure link that evaluators can use to access and evaluate your assignment without extracting the content.")
        
        if st.button("Generate Sharing Link"):
            assignment_id = save_assignment_data()
            if assignment_id:
                # Create sharing link
                share_url = f"/?assignment_id={assignment_id}"
                st.success("Assignment ready for sharing!")
                st.code(share_url, language="text")
                st.write("Share this link with your evaluators. They'll be able to assess your work securely.")
                
                # Instructions
                st.write("#### Next Steps:")
                st.write("1. Copy the link above")
                st.write("2. Send it to your evaluators")
                st.write("3. They'll be able to evaluate your assignment through our secure interface")
                st.write("4. Your original content remains protected against extraction")
        
        # Preview option
        if st.button("Preview Evaluator View"):
            st.session_state.user_mode = 'evaluator'
            st.session_state.container_reset = True
            st.rerun()

def evaluator_mode():
    """Interface for evaluators reviewing assignments"""
    # Import needed modules
    import os
    
    # Clear the screen and start fresh
    st.empty()
    
    # Put mode switching in sidebar with better organization
    with st.sidebar:
        st.title("Navigation")
        if st.button("Switch to Candidate Mode", use_container_width=True):
            # Clear UI state variables as needed
            if 'pdf_processed' in st.session_state:
                st.session_state.pdf_processed = False
            if 'chat_history' in st.session_state:
                st.session_state.chat_history = []
            if 'suggested_questions' in st.session_state:
                st.session_state.suggested_questions = []
            
            # Set mode and reset flag
            st.session_state.user_mode = 'candidate'
            st.session_state.container_reset = True
            st.rerun()
    
    # Main content area
    st.title("Assignment Evaluation")
    
    # Check for assignment ID in URL parameters
    query_params = st.query_params
    if "assignment_id" in query_params and query_params["assignment_id"]:
        assignment_id = query_params["assignment_id"]
        if st.session_state.assignment_id != assignment_id:
            with st.spinner("Loading assignment..."):
                if load_assignment_data(assignment_id):
                    st.success("Assignment loaded successfully!")
                else:
                    st.error("Could not load the assignment. The link may be invalid or expired.")
    
    # Assignment ID input option
    if not st.session_state.pdf_processed:
        st.write("### Enter Assignment ID")
        st.info("Enter the assignment ID shared by the candidate.")
        
        with st.form("assignment_id_form"):
            input_id = st.text_input("Assignment ID:")
            submit_id = st.form_submit_button("Load Assignment")
            
            if submit_id and input_id:
                with st.spinner("Loading assignment..."):
                    if load_assignment_data(input_id):
                        st.success("Assignment loaded successfully!")
                        st.rerun()
                    else:
                        st.error("Could not load the assignment. The ID may be invalid or expired.")
    
    # Main evaluation interface
    if not st.session_state.pdf_processed:
        st.info("Please load an assignment using the assignment ID to begin evaluation.")
        
        # Show information about the tool
        st.write("## About this Evaluation Tool")
        st.write("""
        This secure assignment evaluation tool allows you to:
        - Ask questions about the assignment content
        - View insights about tables and charts from the assignment
        - Get navigation suggestions to explore different sections
        - Evaluate quality without being able to extract the full content
        
        Enter an assignment ID to get started!
        """)
    else:
        # Display assignment loaded confirmation
        st.sidebar.success("✅ Assignment loaded")
        
        # Main evaluation interface with tabs
        evaluation_interface()

def main():
    """Main function to determine which interface to show"""
    # Import needed modules
    import os
    # Check if we need to reset containers due to mode switch
    if st.session_state.container_reset:
        # Create a container that will replace previous UI elements
        for i in range(20):
            st.empty()
        
        # Reset session state variables to clean slate
        variables_to_reset = [
            'chat_history', 'suggested_questions'
        ]
        
        for var in variables_to_reset:
            if var in st.session_state:
                if isinstance(st.session_state[var], list):
                    st.session_state[var] = []
                elif isinstance(st.session_state[var], dict):
                    st.session_state[var] = {}
                elif isinstance(st.session_state[var], bool):
                    st.session_state[var] = False
                elif isinstance(st.session_state[var], (int, float)):
                    st.session_state[var] = 0
                elif isinstance(st.session_state[var], str):
                    st.session_state[var] = ""
        
        # Reset the flag for next iteration
        st.session_state.container_reset = False
    
    # Determine which mode to display
    if st.session_state.user_mode is None:
        select_user_mode()
    elif st.session_state.user_mode == 'candidate':
        candidate_mode()
    elif st.session_state.user_mode == 'evaluator':
        evaluator_mode()

if __name__ == "__main__":
    main()