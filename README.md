
# Code-QA

This project is a lightweight **code-aware agent** that can answer questions about a repository.

It enables **natural language querying over a local codebase** and retrieves relevant code snippets to support answers.**

The end goal is to add functionality till an orchestration pattern is required. I want to know the most an AI agent can do within the bounds of good design practises. 

---

## Overview

**RAG-powered Agentic AI system** that combines:

- Semantic code retrieval  
- LLM reasoning loop  
- Tool-based execution  

to create an interactive  AI assistant for repositories.

---

## Retrieval Layer (RAG)

Code is embedded into a vector store using **FAISS**.  
Currently, the codebase must be **manually indexed before running the agent**.

### Workflow:
- Code is converted into embeddings and stored
- A retriever fetches relevant chunks based on semantic similarity
- The LLM uses retrieved context to generate grounded answers

---

## Agent (ReAct Pattern)

The system uses an **agent loop** based on the ReAct pattern:

```

Thought → Action → Action Input → Observation → Final Answer

```

### Available Tool:
- `search_codebase(query)` → retrieves relevant code snippets

### Agent Behavior:
The agent dynamically decides:
- when to search the codebase  
- what query to use  

---

## 🧩 Design Pattern / Architecture

### Layered Architecture

```

User Query
↓
Agent (ReAct loop)
↓
Tool Layer (search_codebase)
↓
Retriever (Vector DB)
↓
Embedded Codebase (FAISS)

```

---

## System Workflow

1. User asks a question  
2. Agent analyzes the query (Thought step)  
3. Agent calls `search_codebase`  
4. Retriever fetches relevant code chunks  
5. Agent receives observations  
6. Agent generates final answer  

---

## Tech Stack

- LangChain  
- Google Gemini (`ChatGoogleGenerativeAI`)  
- FAISS (Vector Store for embeddings)  
- Python `unittest` (testing)  
- LangSmith (prompt management)  

---

## Summary

This project is a modular AI system combining:

- Retrieval (RAG)
- Reasoning (Agent loop)
- Execution (Tools)

to build a practical **AI-powered code assistant**. 

---
## Future Improvements
- Switch to tool-calling agent (more stable than ReAct)
- Better chunking strategy, say, AST (Abstract Syntax Tree), maybe a code graph
- Enable hybrid retrieval combining semantic search (embeddings) and keyword search (function names, variables)
- Add support for querying **remote repositories (e.g., GitHub)** 
- Evaluation - define metrics
- Packaging
- CI/CD
- Add support for more file formats. Currently only .py is supported. 
