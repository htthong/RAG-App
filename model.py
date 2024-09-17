from langchain_community.llms import Ollama
from langchain_community.llms import OpenAI
from langchain_community.chat_models import ChatOpenAI
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.document_loaders.recursive_url_loader import RecursiveUrlLoader
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain.vectorstores.Chroma import Chroma
from langchain_chroma import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)

from bs4 import BeautifulSoup as Soup
from langchain.utils.html import (PREFIXES_TO_IGNORE_REGEX,
                                  SUFFIXES_TO_IGNORE_REGEX)

from config import *
import logging
import sys
import fitz  # PyMuPDF

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


global conversation
conversation = None
did= 1
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

vector_store = Chroma(
    collection_name="collection",
    embedding_function=embeddings,
    persist_directory=INDEX_PERSIST_DIRECTORY
)

def load_pdf_content(pdf_path):
    """Load text content from a PDF file."""
    # text_content = ""
    text_content = []
    try:
        # Open the PDF file
        with fitz.open(pdf_path) as doc:
            # Extract text from each page
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                # text_content += page.get_text()
                text_content.append(page.get_text())
    except Exception as e:
        logging.error("Error loading PDF content from %s: %s", pdf_path, e)
    return text_content

def load_all_pdfs_from_folder(folder_path):
    """Load text content from all PDF files in a folder."""
    all_texts = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(folder_path, filename)
            logging.info("Loading PDF: %s", pdf_path)
            pdf_text = load_pdf_content(pdf_path)
            if pdf_text:
                # all_texts.append(pdf_text)
                all_texts = all_texts + pdf_text
            else:
                logging.warning("No text extracted from %s.", pdf_path)
    return all_texts

def init_index_pdf_folder():
    if not INIT_INDEX:
        logging.info("Continuing without initializing index.")
        return

    # Load data from all PDF files in the folder
    all_pdf_texts = load_all_pdfs_from_folder(PDF_FOLDER_PATH)
    # print(all_pdf_texts, file=open("outputs.txt",mode="w", encoding='utf-8'))
    if not all_pdf_texts:
        logging.error("No text extracted from any PDF in the folder.")
        return

    # Create a list of documents with the extracted text
    documents = all_pdf_texts

    logging.info("Index creating with `%d` documents", len(documents))

    # Split text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    documents = text_splitter.create_documents(documents)

    # Create embeddings with HuggingFace embedding model `all-MiniLM-L6-v2`
    # Then persist the vector index on vector db
    # embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    # embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

    # vectordb = Chroma.from_documents(
    #     documents=documents,
    #     # embedding=embeddings,
    #     embedding=embedding_function,
    #     persist_directory=INDEX_PERSIST_DIRECTORY
    # )
    global did
    vector_store.add_documents(
        documents=documents,
        id=did
    )
    did += 1
    # vectordb.persist()

def init_index_pdf_file(pdf_file_path):
    if not INIT_INDEX:
        logging.info("Continuing without initializing index.")
        return

    # Load data from all PDF files in the folder
    pdf_text = load_pdf_content(pdf_file_path)
    # print(all_pdf_texts, file=open("outputs.txt",mode="w", encoding='utf-8'))
    if not pdf_text:
        logging.error("No text extracted from any PDF in the folder.")
        return

    # Create a list of documents with the extracted text
    documents = pdf_text

    logging.info("Index creating with `%d` documents", len(documents))

    # Split text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    documents = text_splitter.create_documents(documents)

    # Create embeddings with HuggingFace embedding model `all-MiniLM-L6-v2`
    # Then persist the vector index on vector db
    # embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    # embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    global did
    vector_store.add_documents(
        documents=documents,
        id=did
    )
    did += 1


def init_index_url():
    if not INIT_INDEX:
        logging.info("continue without initializing index")
        return

    # scrape data from web
    documents = RecursiveUrlLoader(
        TARGET_URL,
        max_depth=4,
        extractor=lambda x: Soup(x, "html.parser").text,
        prevent_outside=True,
        use_async=True,
        timeout=600,
        check_response_status=True,
        # drop trailing / to avoid duplicate pages.
        link_regex=(
            f"href=[\"']{PREFIXES_TO_IGNORE_REGEX}((?:{SUFFIXES_TO_IGNORE_REGEX}.)*?)"
            r"(?:[\#'\"]|\/[\#'\"])"
        ),
    ).load()

    logging.info("index creating with `%d` documents", len(documents))

    # split text
    # this chunk_size and chunk_overlap effects to the prompt size
    # execeed promt size causes error `prompt size exceeds the context window size and cannot be processed`
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    documents = text_splitter.split_documents(documents)

    # create embeddings with huggingface embedding model `all-MiniLM-L6-v2`
    # then persist the vector index on vector db
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectordb = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=INDEX_PERSIST_DIRECTORY
    )
    vectordb.persist()


def init_conversation():
    global conversation

    # load index
    # embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    # vectordb = Chroma(persist_directory=INDEX_PERSIST_DIRECTORY,embedding_function=embeddings)
    vectordb = Chroma(persist_directory=INDEX_PERSIST_DIRECTORY,embedding_function=embeddings)
    

    # llama2 llm which runs with ollama
    # ollama expose an api for the llam in `localhost:11434`
    llm = Ollama(
        model="llama2",
        base_url="http://localhost:11434",
        verbose=True,
        temperature=0.7
    )

    # create conversation
    conversation = ConversationalRetrievalChain.from_llm(
        llm,
        retriever=vectordb.as_retriever(),
        return_source_documents=True,
        verbose=True,
    )


def reset_chromadb():
    global vector_store
    if vector_store.get()['ids']:
        vector_store.reset_collection()
    print("vector_store's ids", vector_store.get()['ids'])

def chat(question, user_id):
    global conversation

    chat_history = []
    response = conversation({"question": question, "chat_history": chat_history})
    answer = response['answer']

    logging.info("got response from llm - %s", answer)

    # TODO save history

    return answer
