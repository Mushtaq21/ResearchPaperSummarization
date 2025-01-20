# Research Paper Summarization

A FastAPI-based project to upload and summarize scientific research papers, supporting various formats like PDF, DOCX, and plain text. Includes text cleaning, section extraction, and summarization using Hugging Face Transformers.

## Features
- **Upload Papers**: Handle PDF, DOCX, or plain text uploads.
- **arXiv Integration**: Fetch and process papers using arXiv URLs.
- **Text Preprocessing**: Clean extracted content for better readability.
- **Section Extraction**: Identify key sections like Abstract, Introduction, and Conclusion.
- **Summarization**: Generate concise summaries using pre-trained language models.

## Technologies Used
- **FastAPI**: For building the API.
- **PyPDF2 & python-docx**: For text extraction from PDFs and DOCX.
- **Transformers**: For summarization using models like GPT-Neo.
- **nltk**: For natural language processing tasks.
- **Requests**: For fetching papers from arXiv.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ResearchPaperSummarization.git
   cd ResearchPaperSummarization
