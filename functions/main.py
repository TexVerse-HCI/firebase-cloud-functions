# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn
from firebase_admin import initialize_app
from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv
import os
load_dotenv()

initialize_app()

@https_fn.on_request()
def texVerse_ai_QA(req: https_fn.Request) -> https_fn.Response:
    """HTTP Cloud Function."""

    # handle CORS
    if req.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return https_fn.Response('', status=204, headers=headers)
    headers = {
        'Access-Control-Allow-Origin': '*'
    }

    # Grab the text parameter.
    original = req.args.get("text")
    if original is None:
        return https_fn.Response("No text parameter provided", status=400, headers=headers)
    
    print("question:" + original)

    openai_client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE")
    )

    print(openai_client)

    # use OpenAI API text-embedding-3-small to get embeddings for a question
    response = openai_client.embeddings.create(
        input=original,
        model="text-embedding-3-small" 
    )
    question_vector = response.data[0].embedding

    # use Pinecone to search for the most relevant papers
    pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
    index_name = "textiles-hci-01" 
    index = pc.Index(index_name)

    # search for the most relevant papers
    # index.query(vector=[0.1, 0.2, 0.3], top_k=10, namespace='my_namespace')
    query_results = index.query(
        top_k=5, # top 5 most relevant papers
        vector=question_vector, 
        includeValues=True,
        includeMetadata=True,
        namespace="pdf"
        # filter: { genre: { '$eq': 'action' }}
        )  

    # get the metadata of the most relevant papers
    # print(query_results)
    # contexts = [item['metadata']['abstract'] for item in query_results['matches']]
    contexts = [item['metadata']['text'] for item in query_results['matches']]
    dois = [item['doi'] for item in query_results['matches']]

    # combine the contexts and the question
    context_combined = "\n".join(contexts)
    chat_input = f"Context: {context_combined}\nQuestion: {original}"

    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo", 
        messages=[
            {"role": "system", "content": "You are a helpful research assistant and an expert in textile research and HCI research."},
            {"role": "user", "content": chat_input}
        ],
        #   prompt=chat_input,
        max_tokens=1000 # limit the response to 1000 tokens
    )

    # get the answer
    answer = response.choices[0].message.content

    # include the DOIs of the most relevant papers
    answer = f"{answer}\n\n ### DOIs of the most relevant papers:\n" + "\n - ".join(dois)

    print(answer)
    
    return https_fn.Response(answer, headers=headers)


@https_fn.on_request()
def showmessage(req: https_fn.Request) -> https_fn.Response:
    """Take the text parameter passed to this HTTP endpoint and insert it into
    a new document in the messages collection."""
    # Grab the text parameter.
    original = req.args.get("text")
    if original is None:
        return https_fn.Response("No text parameter provided", status=400)

    # Send back a message that we've successfully written the message
    return https_fn.Response(f"original: {original}")
