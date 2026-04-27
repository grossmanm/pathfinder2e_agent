import random

import torch
import numpy as np
import pandas as pd 
from sentence_transformers import util, SentenceTransformer
from time import perf_counter as timer
import fitz
import matplotlib.pyplot as plt
from openai import OpenAI


df = pd.read_json("data/all_sentence_chunks.json")

### RAG 

# convert embedding column back to np array
df['embedding'] = df['embedding'].apply(lambda x: np.array(x))

# Convert our embeddings into a torch.tensor
embeddings = torch.tensor(np.stack(df['embedding'].tolist(), axis=0))

# convert to flaot32
embeddings = embeddings.to(torch.float32)

# covert texts and embeddings df to list of dicts
pages_and_chunks = df.to_dict(orient="records")


# create model
embedding_model = SentenceTransformer(model_name_or_path='all-mpnet-base-v2', device='cpu')
"""

# Define query
query = "How do I create a new character?"
print(f"Query: {query}")

# embed the query
query_embedding = embedding_model.encode(query, convert_to_tensor=True)


### get cosine similarities

start_time = timer()
dot_scores = util.dot_score(a=query_embedding, b=embeddings)[0]
end_time = timer()
print(f"[INFO] Time to get scores{end_time - start_time:.4f} seconds")

# get top 5 results
top_results = torch.topk(dot_scores, k=5)
indices = top_results[1].cpu().numpy().tolist()
scores = top_results[0].cpu().numpy().tolist()

#for idx, score in zip(indices, scores):
#    print(f"Score: {score:.4f}")
#    print(pages_and_chunks[idx]["sentence_chunk"])
#    print(f"--- From Book: {pages_and_chunks[idx]['book_name']} Page: {pages_and_chunks[idx]['page_number']}")
#    print("-" * 40)

# open pdf and load target
pdf_path = f"text/{pages_and_chunks[indices[0]]['book_name']}.pdf"
page = pages_and_chunks[indices[0]]['page_number']-1  # zero indexed

doc = fitz.open(pdf_path)
page = doc.load_page(page)  # number of page

# get the image of the page
img = page.get_pixmap(dpi=300)

# save the image
img.save("output/output.png")

doc.close()

# covert the pixmap to numpy array
img_array = np.frombuffer(img.samples_mv, dtype=np.uint8).reshape(img.height, img.width, img.n)

# display the image
plt.figure(figsize=(13, 10))
plt.imshow(img_array)
plt.title(f"Query: {query} | Most relevant page:", fontsize=16)
plt.axis('off')
plt.show()
"""
### similarity functions

def dot_product(a, b):
    return np.dot(a, b)

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


# functionizing semantic search
def retrieve_relevant_resources(query: str,
                                embeddings: torch.Tensor,
                                model: SentenceTransformer=embedding_model,
                                n_results: int = 5,
                                print_time: bool = True):
    
    """ 
    Embeds a query and retrieves the most relevant resources based on cosine similarity.
    """

    # embed the query
    query_embedding = model.encode(query, convert_to_tensor=True)

    # get dot product scores on embeddings
    start_time = timer()
    dot_scores = util.dot_score(a=query_embedding, b=embeddings)[0]
    end_time = timer()

    if print_time:
        print(f"[INFO] Time to get scores{end_time - start_time:.4f} seconds")

    scores, indices = torch.topk(dot_scores, k=n_results)

    return scores, indices


def get_top_results_and_scores(query:str,
                                 embeddings: torch.Tensor,
                                 pages_and_chunks: list[dict]= pages_and_chunks,
                                 n_results_to_return: int = 5,
                                 verbose: bool = True):
    """
    Finds relevant passages given a query and prints them out with their scores.
    """
    scores, indices = retrieve_relevant_resources(query=query,
                                                 embeddings=embeddings,
                                                 n_results=n_results_to_return)
    for score, idx in zip(scores, indices):
        if verbose:
            print(f"Score: {score:.4f}")
            print(pages_and_chunks[idx]["sentence_chunk"])
            print(f"--- From Book: {pages_and_chunks[idx]['book_name']} Page: {pages_and_chunks[idx]['page_number']}")
            print("-" * 40)
    return scores, indices


query = "What is the fortitude save for a level 5 fighter?"


print(f"Input: \n{query}")

# format and prompt context items

def prompt_formatter(query: str, context_items: list[dict], embeddings) -> str:

    scores, indices = get_top_results_and_scores(query=query,
                                                 embeddings=embeddings,
                                                 n_results_to_return=10,
                                                 verbose=False)
    context= ""
    for score, idx in zip(scores, indices):
        context_item = context_items[idx]
        context += "- " + context_item["sentence_chunk"] + "\n From the book " + context_item["book_name"] + " on page " + str(context_item["page_number"]) + "\n"
    base_prompt = """Based on the folowing context items, please answer the following query. If you do not know the answer, please say "I don't know". 
    Do not make up an answer. Be concise and to the point. Provide references to the page number and book name of the context item.
    Context Items:
    {context}
    Query: {query}
    Answer:
    """
    prompt = base_prompt.format(context=context, query=query)
    
    return prompt

input_text = prompt_formatter(query=query, context_items=pages_and_chunks, embeddings=embeddings)
print(f"Formatted Prompt: \n{input_text}")
# Create prompt template for GPT-5

dialouge_template = {"role": "user", 
                     "content":input_text}

chat_completion = client.responses.create(
    model="gpt-5",
    input=input_text)


print(f"{chat_completion.output_text}")
