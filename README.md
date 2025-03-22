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

## Deployment

This project is configured for deployment on Vercel with the following:
- Python 3.11 runtime
- Streamlit web framework
- Required dependencies in deployment_requirements.txt
- Configuration in vercel.json

Visit [talktomysubmission.com](https://talktomysubmission.com) to see it in action!