````md
# Code Analyzer

AI-powered repository analyzer built using Python, Django, LangChain, LangGraph, ChromaDB, and Tree-sitter.

---

## Clone Repository

```bash
git clone <repository-url>
```
---

## Move Into Project

```bash
cd code-analyzer
```
---

## Create Virtual Environment

```bash
python -m venv .venv
```

```bash
.venv\Scripts\activate
```
---

## Install Requirements

```bash
pip install -r requirements.txt
```
---

## Move Into Django Project

```bash
cd code_analyzer
```
---

## Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```
---

## Start Development Server

```bash
python manage.py runserver
```
---

## Open In Browser

```txt
http://127.0.0.1:8000
```

---

## Features

- Clone Git repositories
- Scan repository files
- Parse source code using Tree-sitter
- Generate semantic code chunks
- Store embeddings in ChromaDB
- AI-powered repository review
- Semantic code search
- Multi-language parsing support

---

## Tech Stack

### Backend

- Python
- Django
- LangChain
- LangGraph

### AI / Vector Database

- ChromaDB
- Sentence Transformers

### Parsing

- Tree-sitter

### Database

- SQLite
- PostgreSQL

---

## Future Improvements

- GitHub OAuth
- Multi-user repository workspace
- Repository chat assistant
- Code vulnerability detection
- AI architecture diagram generation
- Repository summarization
- PR review assistant

---
