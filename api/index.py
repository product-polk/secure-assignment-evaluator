import os
import sys
import json
from http.server import BaseHTTPRequestHandler
import base64
import pandas as pd
import openai

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import project modules
try:
    from encryption import encrypt_data, decrypt_data, secure_file_path
    from secure_qa import answer_question
    from text_chunker import chunk_text, get_relevant_chunks
    from navigation import generate_navigation_suggestions
    from pdf_processor import extract_text_and_elements_from_pdf
except ImportError:
    pass

# Set OpenAI API key
openai.api_key = os.environ.get("OPENAI_API_KEY")

def vercel_handler(event):
    """
    Handle API requests for Vercel serverless functions
    """
    path = event.get('path', '/')
    method = event.get('httpMethod', 'GET')
    query_params = event.get('queryStringParameters', {}) or {}
    
    if method == 'GET':
        if path == '/' or path == '/index.html':
            return landing_page()
        elif path == '/api/evaluate':
            assignment_id = query_params.get('id')
            if assignment_id:
                return evaluator_page(assignment_id)
            else:
                return {"statusCode": 400, "body": json.dumps({"error": "Assignment ID required"})}
        elif path == '/api/upload':
            return upload_page()
        elif path == '/api/qa':
            assignment_id = query_params.get('id')
            question = query_params.get('question')
            if assignment_id and question:
                return qa_endpoint(assignment_id, question)
            else:
                return {"statusCode": 400, "body": json.dumps({"error": "Assignment ID and question required"})}
    
    # Default to landing page
    return landing_page()

def landing_page():
    """Generate landing page HTML"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Secure Assignment Evaluator</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #1d1e2e;
                color: #ffffff;
            }
            h1, h2 {
                color: #4e89ae;
            }
            .container {
                background-color: #252640;
                border-radius: 8px;
                padding: 20px;
                margin-top: 30px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .btn {
                display: inline-block;
                background-color: #4e89ae;
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 4px;
                font-weight: bold;
                margin-top: 20px;
                border: none;
                cursor: pointer;
                transition: background-color 0.3s;
            }
            .btn:hover {
                background-color: #3a6a8a;
            }
            .modes {
                display: flex;
                justify-content: space-around;
                flex-wrap: wrap;
                margin-top: 40px;
            }
            .mode-card {
                background-color: #252640;
                border-radius: 8px;
                padding: 30px;
                width: 45%;
                min-width: 300px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            @media (max-width: 768px) {
                .mode-card {
                    width: 100%;
                }
            }
        </style>
    </head>
    <body>
        <h1>Secure Assignment Evaluator</h1>
        <p>A secure platform for evaluating assignments without the ability to extract content.</p>
        
        <div class="modes">
            <div class="mode-card">
                <h2>I am a Candidate</h2>
                <p>Upload your assignment securely and share it with evaluators.</p>
                <a href="/api/upload" class="btn">Upload Assignment</a>
            </div>
            
            <div class="mode-card">
                <h2>I am an Evaluator</h2>
                <p>Enter an assignment ID to review and evaluate content.</p>
                <form action="/api/evaluate" method="get">
                    <input type="text" name="id" placeholder="Enter Assignment ID" 
                           style="padding: 10px; width: 100%; margin-bottom: 10px; border-radius: 4px; border: 1px solid #ccc;">
                    <button type="submit" class="btn">Evaluate Assignment</button>
                </form>
            </div>
        </div>
        
        <div style="margin-top: 50px; text-align: center; opacity: 0.7;">
            <p>All content is end-to-end encrypted for security.</p>
        </div>
    </body>
    </html>
    """
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/html"},
        "body": html
    }

def upload_page():
    """Generate upload page HTML"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Upload Assignment | Secure Assignment Evaluator</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #1d1e2e;
                color: #ffffff;
            }
            h1, h2 {
                color: #4e89ae;
            }
            .container {
                background-color: #252640;
                border-radius: 8px;
                padding: 30px;
                margin-top: 30px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .btn {
                display: inline-block;
                background-color: #4e89ae;
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 4px;
                font-weight: bold;
                margin-top: 20px;
                border: none;
                cursor: pointer;
            }
            .btn:hover {
                background-color: #3a6a8a;
            }
            input[type="file"] {
                margin: 20px 0;
                padding: 10px;
                width: 100%;
                background-color: #333;
                color: white;
                border-radius: 4px;
            }
            .note {
                background-color: rgba(78, 137, 174, 0.1);
                padding: 15px;
                border-radius: 4px;
                margin-top: 20px;
                border-left: 4px solid #4e89ae;
            }
        </style>
    </head>
    <body>
        <h1>Upload Assignment</h1>
        
        <div class="container">
            <h2>Candidate Upload</h2>
            <p>Upload your assignment as a PDF file. It will be securely encrypted and a unique ID will be generated for sharing.</p>
            
            <form action="/api/upload" method="post" enctype="multipart/form-data">
                <input type="file" name="pdf_file" accept=".pdf" required>
                <p>Note: Maximum file size is 10MB</p>
                <button type="submit" class="btn">Upload & Generate ID</button>
            </form>
            
            <div class="note">
                <p><strong>Important:</strong> Your file will be encrypted and can only be accessed by those who have the assignment ID.</p>
            </div>
        </div>
        
        <a href="/" class="btn" style="margin-top: 30px; background-color: #555;">Back to Home</a>
    </body>
    </html>
    """
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/html"},
        "body": html
    }

def evaluator_page(assignment_id):
    """Generate evaluator page HTML"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Evaluate Assignment | Secure Assignment Evaluator</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                max-width: 1000px;
                margin: 0 auto;
                padding: 20px;
                background-color: #1d1e2e;
                color: #ffffff;
            }}
            h1, h2, h3 {{
                color: #4e89ae;
            }}
            .container {{
                background-color: #252640;
                border-radius: 8px;
                padding: 20px;
                margin-top: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .chat-container {{
                height: 400px;
                overflow-y: auto;
                padding: 15px;
                background-color: #1a1a2e;
                border-radius: 4px;
                margin-bottom: 15px;
            }}
            .message {{
                padding: 10px 15px;
                border-radius: 18px;
                margin-bottom: 10px;
                max-width: 80%;
                white-space: pre-wrap;
            }}
            .user-message {{
                background-color: #4e89ae;
                color: white;
                margin-left: auto;
                border-top-right-radius: 4px;
            }}
            .system-message {{
                background-color: #333;
                color: white;
                margin-right: auto;
                border-top-left-radius: 4px;
            }}
            .input-group {{
                display: flex;
                margin-top: 15px;
            }}
            #question-input {{
                flex: 1;
                padding: 12px;
                border-radius: 4px 0 0 4px;
                border: none;
                background-color: #333;
                color: white;
            }}
            .btn {{
                background-color: #4e89ae;
                color: white;
                padding: 12px 20px;
                border: none;
                border-radius: 0 4px 4px 0;
                cursor: pointer;
                font-weight: bold;
            }}
            .btn-secondary {{
                background-color: #555;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin-right: 10px;
                font-size: 14px;
            }}
            .suggested-questions {{
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin-top: 15px;
            }}
            .suggested-question {{
                background-color: #333;
                color: white;
                padding: 8px 12px;
                border-radius: 16px;
                font-size: 14px;
                cursor: pointer;
                border: 1px solid #4e89ae;
            }}
            .suggested-question:hover {{
                background-color: #4e89ae;
            }}
            #loader {{
                display: none;
                margin-top: 15px;
                text-align: center;
            }}
            .loading-spinner {{
                border: 4px solid rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                border-top: 4px solid #4e89ae;
                width: 30px;
                height: 30px;
                animation: spin 1s linear infinite;
                margin: 0 auto;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>
    <body>
        <h1>Assignment Evaluation</h1>
        <p>Assignment ID: <strong>{assignment_id}</strong></p>
        
        <div class="container">
            <h2>Ask Questions About This Assignment</h2>
            <p>You can ask questions about the content of the assignment. The AI will generate answers based on the encrypted content without revealing the full text.</p>
            
            <div id="chat-container" class="chat-container">
                <div class="message system-message">Hello! I'm here to help you evaluate this assignment. What would you like to know about it?</div>
            </div>
            
            <div id="suggested-questions" class="suggested-questions">
                <div class="suggested-question">What is the main topic of this assignment?</div>
                <div class="suggested-question">What methodology is used in this work?</div>
                <div class="suggested-question">What are the key findings or conclusions?</div>
                <div class="suggested-question">Are there any charts or tables in this document?</div>
                <div class="suggested-question">How well is the literature review done?</div>
            </div>
            
            <div class="input-group">
                <input type="text" id="question-input" placeholder="Type your question here...">
                <button id="submit-btn" class="btn">Ask</button>
            </div>
            
            <div id="loader">
                <p>Thinking...</p>
                <div class="loading-spinner"></div>
            </div>
        </div>
        
        <div style="margin-top: 20px;">
            <a href="/" class="btn-secondary">Back to Home</a>
        </div>
        
        <script>
            const chatContainer = document.getElementById('chat-container');
            const questionInput = document.getElementById('question-input');
            const submitBtn = document.getElementById('submit-btn');
            const loader = document.getElementById('loader');
            const suggestedQuestions = document.querySelectorAll('.suggested-question');
            
            // Assignment ID from URL
            const assignmentId = '{assignment_id}';
            
            // Add event listeners
            submitBtn.addEventListener('click', handleSubmit);
            questionInput.addEventListener('keypress', function(e) {{
                if (e.key === 'Enter') {{
                    handleSubmit();
                }}
            }});
            
            // Suggested questions click handler
            suggestedQuestions.forEach(question => {{
                question.addEventListener('click', function() {{
                    questionInput.value = this.textContent;
                    handleSubmit();
                }});
            }});
            
            function handleSubmit() {{
                const question = questionInput.value.trim();
                if (question === '') return;
                
                // Add user message to chat
                addMessage(question, 'user');
                
                // Clear input and show loader
                questionInput.value = '';
                loader.style.display = 'block';
                
                // Send question to API
                fetch(`/api/qa?id=${{assignmentId}}&question=${{encodeURIComponent(question)}}`)
                    .then(response => response.json())
                    .then(data => {{
                        // Hide loader
                        loader.style.display = 'none';
                        
                        if (data.error) {{
                            addMessage(`Error: ${{data.error}}`, 'system');
                        }} else {{
                            addMessage(data.answer, 'system');
                            
                            // Update suggested questions if available
                            if (data.suggestions && data.suggestions.length > 0) {{
                                updateSuggestedQuestions(data.suggestions);
                            }}
                        }}
                    }})
                    .catch(error => {{
                        loader.style.display = 'none';
                        addMessage(`Error: Could not get a response. Please try again.`, 'system');
                        console.error('Error:', error);
                    }});
            }}
            
            function addMessage(text, sender) {{
                const messageElement = document.createElement('div');
                messageElement.classList.add('message');
                messageElement.classList.add(sender + '-message');
                messageElement.textContent = text;
                
                chatContainer.appendChild(messageElement);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }}
            
            function updateSuggestedQuestions(questions) {{
                const container = document.getElementById('suggested-questions');
                container.innerHTML = '';
                
                questions.forEach(question => {{
                    const element = document.createElement('div');
                    element.classList.add('suggested-question');
                    element.textContent = question;
                    element.addEventListener('click', function() {{
                        questionInput.value = this.textContent;
                        handleSubmit();
                    }});
                    
                    container.appendChild(element);
                }});
            }}
        </script>
    </body>
    </html>
    """
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/html"},
        "body": html
    }

def qa_endpoint(assignment_id, question):
    """
    Handle Q&A API requests
    """
    try:
        # In a real implementation, we would decrypt and process data from storage
        # For now, return a mock response
        
        answer = f"I would provide an analysis of your question about '{question}', but I need to access the actual encrypted data which is not available in this serverless function environment."
        
        suggestions = [
            "What are the key arguments made in this assignment?",
            "How does the author support their thesis?",
            "What methodology is used in this research?",
            "What are the limitations of this study?",
            "How does this compare to other work in the field?"
        ]
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "answer": answer,
                "suggestions": suggestions
            })
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse query parameters
        query_params = {}
        if '?' in self.path:
            path, query_string = self.path.split('?', 1)
            for param in query_string.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    query_params[key] = value
        else:
            path = self.path
            
        # Create event object for vercel_handler
        event = {
            'path': path,
            'httpMethod': 'GET',
            'queryStringParameters': query_params
        }
        
        # Process the request
        response = vercel_handler(event)
        
        # Send response
        self.send_response(response.get('statusCode', 200))
        for header, value in response.get('headers', {}).items():
            self.send_header(header, value)
        self.end_headers()
        
        # Send response body
        self.wfile.write(response.get('body', '').encode())