# Secure Assignment Evaluator

A secure platform designed for evaluating assignments without the ability to extract full content. This tool allows candidates to upload assignments and share them with evaluators using secure, encrypted storage.

## Features

- **Secure Content Processing**: Evaluators can analyze assignments without being able to extract the full content
- **Intelligent Q&A**: Ask questions about assignment content with AI-powered responses
- **Secure Chart & Table Analysis**: Get insights on charts and tables without revealing raw data
- **End-to-End Encryption**: All files and assignment data are encrypted to ensure privacy
- **User-Friendly Sharing**: Generate easy-to-share links with secure assignment IDs

## Setup Instructions

1. Clone this repository
2. Install dependencies: `pip install -r deployment_requirements.txt`
3. Set your OpenAI API key as an environment variable: `OPENAI_API_KEY=your_key_here`
4. Run the Streamlit app: `streamlit run app.py`

## Deployment Options

### Important Note About Vercel

Streamlit applications are not well-suited for Vercel's serverless architecture. For a fully functional deployment, we recommend using one of the following platforms:

### 1. Streamlit Cloud (Recommended)

1. Push your project to GitHub
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Connect your GitHub repository
4. Add your `OPENAI_API_KEY` as a secret
5. Deploy

### 2. Render

1. Create a `render.yaml` file:
```yaml
services:
  - type: web
    name: secure-assignment-evaluator
    env: python
    buildCommand: pip install -r deployment_requirements.txt
    startCommand: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
    envVars:
      - key: OPENAI_API_KEY
        sync: false
```
2. Create an account on [Render](https://render.com)
3. Connect your GitHub repository
4. Deploy using the `render.yaml` configuration

### 3. Heroku

1. Create a `Procfile`:
```
web: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```
2. Deploy using the Heroku CLI or GitHub integration

### 4. Digital Ocean App Platform

1. Create an account on [Digital Ocean](https://www.digitalocean.com/products/app-platform/)
2. Connect your GitHub repository
3. Configure as a Python application
4. Set the build command: `pip install -r deployment_requirements.txt`
5. Set the run command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
6. Add your `OPENAI_API_KEY` environment variable

For more detailed instructions, see the respective platform's documentation.