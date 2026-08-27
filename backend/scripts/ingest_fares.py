import os
import shutil
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "data", "chroma_fares")
TEMP_PDF_DIR = os.path.join(BASE_DIR, "temp_pdfs")

# NTC Fares Page
NTC_URL = "https://www.ntc.gov.lk/Bus_info/bus_fares.php"
BASE_DOMAIN = "https://www.ntc.gov.lk"

def run_ingestion():
    # Load env for OPENAI_API_KEY
    load_dotenv(os.path.join(BASE_DIR, ".env"))

    # 1. Clear existing database
    if os.path.exists(DB_DIR):
        print(f"Clearing existing Chroma DB at {DB_DIR}...")
        shutil.rmtree(DB_DIR)
        
    if not os.path.exists(TEMP_PDF_DIR):
        os.makedirs(TEMP_PDF_DIR)
        
    print(f"Fetching bus fare page: {NTC_URL}", flush=True)
    # NTC site may have SSL issues or block requests without user agent
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(NTC_URL, verify=False, headers=headers, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    pdf_links = []
    
    # Find all links ending with .pdf
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.lower().endswith('.pdf'):
            full_url = urljoin(BASE_DOMAIN, href)
            if full_url not in pdf_links:
                pdf_links.append(full_url)
                
    if not pdf_links:
        print("No PDF links found on the page!", flush=True)
        return {"status": "error", "message": "No PDF links found"}
        
    print(f"Found {len(pdf_links)} PDFs to download.", flush=True)
    
    all_documents = []
    
    # 2. Download and Parse PDFs
    for url in pdf_links:
        print(f"Downloading {url}...", flush=True)
        filename = os.path.basename(url)
        # handle url encoding spaces
        from urllib.parse import unquote
        filename = unquote(filename)
        filepath = os.path.join(TEMP_PDF_DIR, filename)
        
        try:
            r = requests.get(url, verify=False, headers=headers, timeout=30)
            r.raise_for_status()
            with open(filepath, 'wb') as f:
                f.write(r.content)
                
            print(f"Parsing {filename}...")
            loader = PyPDFLoader(filepath)
            docs = loader.load()
            all_documents.extend(docs)
        except Exception as e:
            print(f"Failed to process {url}: {e}")
            
    if not all_documents:
        return {"status": "error", "message": "Failed to parse any PDFs."}
        
    # 3. Chunking and Embedding
    print(f"Total pages loaded: {len(all_documents)}. Splitting text...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(all_documents)
    
    print(f"Generated {len(chunks)} chunks. Storing to Chroma DB...")
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB_DIR
    )
    
    print("Ingestion complete!")
    
    # Clean up temp
    shutil.rmtree(TEMP_PDF_DIR)
    
    return {"status": "success", "message": f"Successfully ingested {len(pdf_links)} PDFs into Chroma DB."}

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    run_ingestion()
