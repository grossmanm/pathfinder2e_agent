import os
import re
import random
import sys


import fitz
from tqdm import tqdm
import pandas as pd
import numpy as np
from spacy.lang.en import English
from sentence_transformers import SentenceTransformer

old_stdout = sys.stdout

log_file = open("logs/message.log", "w")

sys.stdout = log_file

num_setences_per_chunk = 10

pdf_folder = 'text'

pdf_paths = [os.path.join(pdf_folder, f) for f in os.listdir(pdf_folder) if f.endswith('.pdf')]

def clean_text(text: str) -> str:
    text = text.replace("Malcolm Grossman", "")
    text = text.replace("<malcolmcgrossman@gmail.com>,", "")
    text = text.replace("Nov 20, 2024", "")
    text = text.replace("paizo.com,", "")
    text = text.replace("..", "")
    return text

def open_and_read_pdf(pdf_path: str) -> list[dict]:
    doc = fitz.open(pdf_path)
    pages = []
    for page_num, page in tqdm(enumerate(doc)):
        book_name = pdf_path.split("/")[1].replace(".pdf","")
        if (('playercore' in book_name or 'gmcore' in book_name) and page_num > 3) or page_num > 4:
            text = page.get_text()
            text = clean_text(text)
            pages.append({"book_name": book_name,
                        "page_number": page_num + 1, 
                        "text": text,
                        "parge_char_count": len(text),
                        "page_word_count": len(text.split(" ")),
                        "page_sentence_count_raw": len(text.split(". ")),
                        "page_token_count_estimate": len(text) // 4})
    return pages

# create function to split lists of texts recursively
def chunk_sentences(sentences: list[str], chunk_size: int) -> list[list[str]]:
    return [sentences[i:i + chunk_size] for i in range(0, len(sentences), chunk_size)]


nlp = English()
nlp.add_pipe("sentencizer")

all_pages = []
for pdf_path in pdf_paths:
    print(f"Processing {pdf_path}")
    pages = open_and_read_pdf(pdf_path)

    all_pages.extend(pages)

total_chars = sum(page['parge_char_count'] for page in all_pages)
total_words = sum(page['page_word_count'] for page in all_pages)
total_sentences = sum(page['page_sentence_count_raw'] for page in all_pages)
total_tokens_estimate = sum(page['page_token_count_estimate'] for page in all_pages)
print(f"Total characters: {total_chars}")
print(f"Total words: {total_words}")
print(f"Total sentences (raw estimate): {total_sentences}")
print(f"Total tokens (estimated): {total_tokens_estimate}")
print("-" * 40)
for item in tqdm(all_pages):
    item["sentences"] = list(nlp(item["text"]).sents)

    item["sentences"] = [str(sentence) for sentence in item["sentences"]]

    item["page_sentence_count"] = len(item["sentences"])



## Chunking logic
for item in tqdm(all_pages):
    item["sentence_chunks"] = chunk_sentences(item["sentences"], num_setences_per_chunk)
    item["num_sentence_chunks"] = len(item["sentence_chunks"])




# splitting each chunk into its own item
pages_and_chunks = []
for item in tqdm(all_pages):
    for setence_chunk in item["sentence_chunks"]:
        chunk_dict = {}
        chunk_dict["book_name"] = item["book_name"]
        chunk_dict["page_number"] = item["page_number"]
        
        joined_chunk = "".join(setence_chunk).replace("  ", "").strip()
        joined_chunk = re.sub(r'\n+', ' ', joined_chunk)  # Replace newlines with space
        joined_chunk = re.sub(r'\.([A-Z])', r'. \1', joined_chunk)  # Ensure space after periods if followed by a capital letter
        

        chunk_dict["sentence_chunk"] = joined_chunk

        chunk_dict["chunk_char_count"] = len(joined_chunk)
        chunk_dict["chunk_word_count"] = len(joined_chunk.split(" "))
        chunk_dict["chunk_sentence_count"] = len(setence_chunk)
        chunk_dict["chunk_token_count_estimate"] = len(joined_chunk) // 4
        pages_and_chunks.append(chunk_dict)



df = pd.DataFrame(pages_and_chunks)

min_token_length = 30
pages_and_chunks_over_min_token_len = df[df["chunk_token_count_estimate"] > min_token_length].to_dict(orient="records")


print(df.describe())

print(pages_and_chunks_over_min_token_len)
# Embedding our text chunks
sample = pages_and_chunks_over_min_token_len[:3]
embedding_model = SentenceTransformer(model_name_or_path='all-mpnet-base-v2', device='cpu')
for item in tqdm(pages_and_chunks_over_min_token_len):
    item["embedding"] = embedding_model.encode(item["sentence_chunk"])


text_chunk_embeddings_df = pd.DataFrame(pages_and_chunks_over_min_token_len)
text_chunk_embeddings_df.to_json("all_sentence_chunks.json", orient="records", indent=2)
sys.stdout = old_stdout
log_file.close()
