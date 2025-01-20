from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
import os
import requests
from PyPDF2 import PdfReader
from docx import Document
from pathlib import Path
import re
from transformers import pipeline
import nltk

app = FastAPI()

# Load the summarization model
try:
    summarizer = pipeline("summarization")
except Exception as e:
    print(f"Error loading summarization model: {e}")

# Directory to save uploaded files
UPLOAD_DIR = "uploads"
Path(UPLOAD_DIR).mkdir(exist_ok=True)

# Function to save uploaded files
def save_file(file: UploadFile) -> str:
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    return file_path

# Function to extract text from PDFs
def process_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Function to extract text from DOCX files
def process_docx(file_path: str) -> str:
    doc = Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

# Function to clean extracted text
def clean_text(text: str) -> str:
    text = re.sub(r'\[\d+\]', '', text)  # Removes citations
    text = re.sub(r'\(\d+\)', '', text)  # Removes in-text citations
    text = re.sub(r'\n+', '\n', text)     # Removes extra newlines
    return text.strip()                   # Strips leading/trailing whitespace

# Download and process arXiv papers
def fetch_arxiv_paper(url: str) -> str:
    arxiv_id = url.split('/')[-1]
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    
    response = requests.get(pdf_url)
    if response.status_code == 200:
        file_path = os.path.join(UPLOAD_DIR, f"arxiv_{arxiv_id}.pdf")
        with open(file_path, "wb") as f:
            f.write(response.content)
        return process_pdf(file_path)
    else:
        raise HTTPException(status_code=404, detail="Paper not found on arXiv")

# Function to extract specific sections based on keywords
def extract_sections(text: str):
    sections = {
        "Abstract": "",
        "Introduction": "",
        "Methodology": "",
        "Results": "",
        "Conclusion": ""
    }
    
    sentences = nltk.sent_tokenize(text)
    current_section = None
    
    for sentence in sentences:
        lower_sentence = sentence.lower()
        
        if "abstract" in lower_sentence:
            current_section = "Abstract"
            sentence = sentence.replace("Abstract:", "").replace("abstract:", "").strip()
        elif "introduction" in lower_sentence:
            current_section = "Introduction"
            sentence = sentence.replace("Introduction:", "").replace("introduction:", "").strip()
        elif "methodology" in lower_sentence or "methods" in lower_sentence:
            current_section = "Methodology"
            sentence = sentence.replace("Methodology:", "").replace("methodology:", "").replace("methods:", "").strip()
        elif "results" in lower_sentence:
            current_section = "Results"
            sentence = sentence.replace("Results:", "").replace("results:", "").strip()
        elif "conclusion" in lower_sentence:
            current_section = "Conclusion"
            sentence = sentence.replace("Conclusion:", "").replace("conclusion:", "").strip()
        
        if current_section:
            sections[current_section] += sentence + " "
    
    return {key: value.strip() for key, value in sections.items()}

# File upload endpoint (PDF, DOCX, or plain text)
@app.post("/upload-paper/")
async def upload_paper(file: UploadFile = File(...)):
    file_type = file.content_type
    file_path = save_file(file)
    
    if file_type == "application/pdf":
        raw_content = process_pdf(file_path)
    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        raw_content = process_docx(file_path)
    elif file_type == "text/plain":
        with open(file_path, "r") as f:
            raw_content = f.read()
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    cleaned_content = clean_text(raw_content)
    
    return JSONResponse(content={"file_name": file.filename, "cleaned_content": cleaned_content})

# arXiv submission endpoint
@app.post("/submit-arxiv/")
async def submit_arxiv(url: str = Form(...)):
    try:
        raw_content = fetch_arxiv_paper(url)
        cleaned_content = clean_text(raw_content)
        return JSONResponse(content={"source": url, "cleaned_content": cleaned_content})
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})

# Summarization endpoint
@app.post("/summarize/")
async def summarize_text(text: str = Form(...)):
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")
    
    try:
        summary = summarizer(text, max_length=130, min_length=30, do_sample=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during summarization: {str(e)}")

    return JSONResponse(content={"summary": summary[0]['summary_text']})

# File upload endpoint to extract sections
@app.post("/extract-sections/")
async def extract_sections_from_text(text: str = Form(...)):
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")
    
    sections = extract_sections(text)
    
    return JSONResponse(content=sections)
