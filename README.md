# Secure Assignment Evaluation Platform

A secure platform for evaluating assignments that provides intelligent document analysis with robust content protection and data handling mechanisms.

## Features

- **Secure PDF Processing**: Upload and analyze PDF assignments without exposing raw content
- **AI-Powered Q&A**: Intelligent question-answering system that respects document confidentiality
- **Content Protection**: Prevents extraction attempts while providing meaningful insights
- **Chart & Table Analysis**: Provides AI-generated insights about visual elements without displaying raw data
- **Intuitive Sharing**: Easy assignment sharing between candidates and evaluators with clean, shareable IDs

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up your OpenAI API key as an environment variable: `OPENAI_API_KEY`
4. Run the application: `streamlit run app.py`

## Usage

### For Candidates:
- Upload your assignment PDF
- Share the generated assignment ID with evaluators

### For Evaluators:
- Enter the assignment ID shared by a candidate
- Use the Q&A system to explore the document
- Follow suggested questions or ask your own

## Dependencies

- streamlit
- pandas
- pdfplumber
- plotly
- nltk
- openai

## License

[MIT License](LICENSE)