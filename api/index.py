from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Secure Assignment Evaluator</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    text-align: center;
                }
                h1 {
                    color: #4e89ae;
                }
                .container {
                    background-color: #f5f5f5;
                    border-radius: 8px;
                    padding: 20px;
                    margin-top: 30px;
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
                }
                .alternative {
                    margin-top: 40px;
                    font-size: 0.9em;
                    color: #666;
                }
            </style>
        </head>
        <body>
            <h1>Secure Assignment Evaluator</h1>
            <p>A secure platform for evaluating assignments without the ability to extract content.</p>
            
            <div class="container">
                <h2>This app requires a different hosting platform</h2>
                <p>Streamlit applications don't work correctly on Vercel's serverless architecture.</p>
                <p>Please deploy this app using one of the recommended platforms:</p>
                <ul style="list-style-type: none; padding: 0;">
                    <li>Streamlit Cloud</li>
                    <li>Render</li>
                    <li>Heroku</li>
                    <li>DigitalOcean App Platform</li>
                </ul>
                
                <a href="https://github.com/yourusername/secure-assignment-evaluator" class="btn">View on GitHub</a>
            </div>
            
            <div class="alternative">
                <p>Need help deploying? Check the README.md file for detailed instructions.</p>
            </div>
        </body>
        </html>
        """.encode())
        return