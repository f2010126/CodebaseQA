# Agent Test Repo

Sanity: Ensure the LLM key (if needed) is present in the .env file
Added a fake repo to test the Agent

## How To Run
- Index the repo by running python ingest/build_index.py
The repo is chunked, embeddings made and saving FAISS index → vectorstore/

- Run the agent python main.py