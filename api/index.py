import os
import sys
import json
from http.server import BaseHTTPRequestHandler

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

# No OpenAI import is needed in this simplified version
# We'll run API calls from the main Streamlit app instead

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
            .note-box {
                background-color: rgba(255, 193, 7, 0.2);
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin-top: 30px;
                border-radius: 4px;
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
        
        <div class="note-box">
            <h3>⚠️ Limited Functionality Notice</h3>
            <p>This is a simplified landing page for the Secure Assignment Evaluator.</p>
            <p>Due to the serverless architecture limitations of Vercel, this version has restricted functionality:</p>
            <ul>
                <li>Assignment uploads are not supported here</li>
                <li>The AI-powered Q&A functionality is limited</li>
                <li>Secure PDF processing cannot be performed</li>
            </ul>
            <p><strong>Please visit our <a href="https://secure-assignment-evaluator.streamlit.app" style="color: #4e89ae;">main application</a> for full functionality.</strong></p>
        </div>
        
        <div class="modes">
            <div class="mode-card">
                <h2>About This Tool</h2>
                <p>The Secure Assignment Evaluator allows evaluators to review assignments without being able to extract the full content.</p>
                <p>It provides AI-powered analysis of documents, tables, and charts while maintaining content security.</p>
                <a href="https://secure-assignment-evaluator.streamlit.app" class="btn">Go to Full Application</a>
            </div>
            
            <div class="mode-card">
                <h2>Key Features</h2>
                <ul>
                    <li>Secure PDF processing with content protection</li>
                    <li>AI-powered question answering about documents</li>
                    <li>Table and chart analysis without content extraction</li>
                    <li>End-to-end encryption for all uploaded files</li>
                    <li>Easy sharing with simple assignment IDs</li>
                </ul>
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
            .note-box {
                background-color: rgba(255, 193, 7, 0.2);
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin-top: 30px;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <h1>Upload Assignment</h1>
        
        <div class="note-box">
            <h3>⚠️ Feature Not Available</h3>
            <p>Assignment uploads are not supported on this platform due to serverless architecture limitations.</p>
            <p>To upload and share assignments, please use our main application.</p>
            <p><a href="https://secure-assignment-evaluator.streamlit.app" class="btn">Go to Full Application</a></p>
        </div>
        
        <div class="container">
            <h2>About Assignment Uploads</h2>
            <p>The full version of Secure Assignment Evaluator allows you to:</p>
            <ul>
                <li>Upload PDF assignments securely</li>
                <li>Receive a shareable assignment ID</li>
                <li>Share the ID with evaluators</li>
                <li>Benefit from end-to-end encryption</li>
            </ul>
            <p>All content is fully encrypted and cannot be accessed without the assignment ID.</p>
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
            .btn {{
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
            }}
            .btn:hover {{
                background-color: #3a6a8a;
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
            .note-box {{
                background-color: rgba(255, 193, 7, 0.2);
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin-top: 30px;
                border-radius: 4px;
            }}
        </style>
    </head>
    <body>
        <h1>Assignment Evaluation</h1>
        <p>Assignment ID: <strong>{assignment_id}</strong></p>
        
        <div class="note-box">
            <h3>⚠️ Feature Not Available</h3>
            <p>Assignment evaluation and Q&A are not supported on this platform due to serverless architecture limitations.</p>
            <p>To evaluate assignments and use the full AI-powered Q&A functionality, please use our main application.</p>
            <p><a href="https://secure-assignment-evaluator.streamlit.app" class="btn">Go to Full Application</a></p>
        </div>
        
        <div class="container">
            <h2>About Assignment Evaluation</h2>
            <p>The full version of Secure Assignment Evaluator allows you to:</p>
            <ul>
                <li>Ask questions about the assignment content</li>
                <li>Receive AI-generated insights about tables and charts</li>
                <li>Navigate through different sections of the document</li>
                <li>Evaluate the quality and structure of the work</li>
                <li>All without the ability to extract the full content</li>
            </ul>
            <p>Please visit our main application to evaluate this assignment.</p>
        </div>
        
        <div style="margin-top: 20px;">
            <a href="/" class="btn-secondary">Back to Home</a>
        </div>
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
        # For the Vercel serverless version, we can't process files directly
        # Instead, we'll redirect users to use the main Streamlit application
        
        answer = """This assignment requires secure processing that can't be handled in this environment.
        
Please use the main application at https://secure-assignment-evaluator.streamlit.app to process assignments with full functionality.

This limited version is provided as a landing page only. For evaluation and detailed interaction, please use the main application."""
        
        suggestions = [
            "What is the main topic of this assignment?",
            "What methodology is used in this work?",
            "What are the key findings or conclusions?",
            "Are there any charts or tables in this document?",
            "How well is the literature review done?"
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