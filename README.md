# Sudhan Career AI

A starter personal career-agent web app for worldwide oil & gas job discovery, job matching, and ATS-focused CV generation.

## Important
This is a working starter/MVP, not a universal job-site scraper. Job sites have different APIs, robots rules, authentication, and terms. The app uses web search through the OpenAI Responses API for discovery and keeps application submission as a human-approved step.

## Run

1. Install Python 3.11+.
2. Create a virtual environment.
3. `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and add your OpenAI API key.
5. `uvicorn app.main:app --reload`
6. Open http://127.0.0.1:8000

## What it does

- Searches the web for oil & gas operator jobs worldwide.
- Searches multiple title variants.
- Filters obvious duplicates.
- Uses AI to extract job details and match against your profile.
- Generates an ATS-friendly, truthful CV from a master profile.
- Provides direct job links for you to review/apply.

Do not let an AI invent qualifications, certifications, employers, equipment experience, or salary information.
