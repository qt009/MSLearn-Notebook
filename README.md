# MSLearn-Notebook

Scrapes Microsoft Learn certification study content and generates PDF study notebooks. React frontend, FastAPI backend.

## Tech Stack

- **Backend**: FastAPI, httpx, BeautifulSoup, Pydantic
- **Frontend**: React (TBD)

## Supported Certifications

| ID | Certification |
|----|--------------|
| `az-900` | Azure Fundamentals |
| `az-104` | Azure Administrator Associate |
| `az-204` | Azure Developer Associate |

## Getting Started

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/certifications` | List supported certifications |
| `POST` | `/api/scrape/{cert_id}` | Start a scrape job |
| `GET` | `/api/jobs/{job_id}` | Poll job status |
| `GET` | `/api/health` | Health check |

## Project Structure

```
backend/
  app/
    api/          # Routes, schemas, dependency injection
    domain/       # Models, enums, exceptions
    scraper/      # Crawler, HTML parsers
    services/     # Business logic, job tracking
    storage/      # File-based persistence
```