# Firbase Cloud Functions
- __texVerse_ai_QA__: the _function_ to get user questions, convert them to vectors, search for similar text chunks in the Pinecone database as the context for LLM, and finally return the answer from the GPT.
- Tutorial on Firebase Cloud Functions: https://firebase.google.com/docs/functions/get-started?gen=2nd. 
    - After editing the function deploy using: `firebase deploy --only functions`