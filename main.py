import json
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
from openai import OpenAI

load_dotenv()

app = FastAPI(title="Sudhan Career AI")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None

PROFILE = {
    "name": "Sudhan",
    "target_titles": [
        "Production Operator", "Process Plant Operator", "Commissioning Operator",
        "Field Operator", "Wellhead Operator", "Senior Wellhead Operator",
        "Senior Control Room Operator", "Senior Production Operator"
    ],
    "industry": "Oil & Gas",
    "experience_years": 15,
    "qualification": "Diploma in Mechanical Engineering",
    "experience": [
        "Oil and gas field/process operations",
        "Offshore operations",
        "Gas injection operations",
        "Gas compression",
        "Amine sweetening",
        "Glycol dehydration",
        "Gas-oil separation",
        "H2S safety awareness and operational response",
        "Field rounds, process monitoring and equipment operation"
    ],
    "career_direction": "Move toward senior operator / production supervisor responsibilities."
}

SEARCH_TITLES = [
    "production operator oil gas",
    "process plant operator oil gas",
    "commissioning operator oil gas",
    "field operator oil gas",
    "wellhead operator oil gas",
    "senior wellhead operator oil gas",
    "senior control room operator oil gas",
    "senior production operator oil gas",
    "production technician oil gas",
    "operations technician oil gas",
]

COUNTRIES = [
    "UAE", "Saudi Arabia", "Qatar", "Kuwait", "Oman", "Bahrain",
    "Iraq", "United States", "Canada", "Norway", "United Kingdom",
    "Australia", "Malaysia", "Indonesia", "Brunei", "Nigeria",
    "Angola", "Brazil", "Guyana", "Kazakhstan", "Azerbaijan"
]

HTML = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sudhan Career AI</title>
<style>
body{font-family:Arial,sans-serif;max-width:1100px;margin:30px auto;padding:0 16px;background:#f6f7f9;color:#18202a}
h1{margin-bottom:4px}.muted{color:#657080}.card{background:white;padding:18px;margin:14px 0;border-radius:12px;box-shadow:0 2px 10px #0001}
button{padding:11px 16px;border:0;border-radius:8px;background:#111827;color:white;cursor:pointer}
input,textarea{width:100%;box-sizing:border-box;padding:10px;border:1px solid #ccd2da;border-radius:8px;margin:6px 0 12px}
.job{border-left:4px solid #111827}.score{font-weight:bold}.pill{display:inline-block;padding:4px 8px;background:#eef1f5;border-radius:999px;margin:3px;font-size:12px}
a{color:#0b57d0}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}@media(max-width:700px){.grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<h1>Sudhan Career AI</h1>
<div class="muted">Worldwide Oil & Gas job discovery + AI matching + ATS CV</div>

<div class="card">
<h2>1. Search worldwide jobs</h2>
<p>Searches multiple operator-title variants and countries, then asks AI to extract and match the results.</p>
<form method="post" action="/search">
<button>Search Jobs Now</button>
</form>
</div>

<div class="card">
<h2>2. Build ATS CV</h2>
<form method="post" action="/ats">
<label>Paste the job description</label>
<textarea name="job_description" rows="12" required></textarea>
<button>Generate ATS CV</button>
</form>
</div>

<div class="card">
<h2>Your profile</h2>
<div class="grid">
<div><b>Experience:</b> 15 years</div>
<div><b>Qualification:</b> Diploma in Mechanical Engineering</div>
</div>
<p>{skills}</p>
</div>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
def home():
    skills = " ".join(f'<span class="pill">{s}</span>' for s in PROFILE["experience"])
    return HTML.format(skills=skills)

def search_web(query: str) -> str:
    if not client:
        raise RuntimeError("OPENAI_API_KEY is not configured.")
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5"),
        tools=[{"type": "web_search"}],
        input=f"""Search the public web for current job vacancies matching this query:
{query}

Return concise factual results only. Prefer direct employer career pages and legitimate job boards.
Do not invent salary, location, employer, dates, or links."""
    )
    return response.output_text

def analyse_jobs(raw: str) -> list[dict[str, Any]]:
    if not client:
        raise RuntimeError("OPENAI_API_KEY is not configured.")
    prompt = f"""You are a job-data extraction and matching engine.

Candidate:
{json.dumps(PROFILE, indent=2)}

Search results:
{raw}

Extract only jobs that are plausibly relevant to the candidate's oil & gas operator profile.
Return JSON only as:
{{
 "jobs":[
   {{
     "title":"...",
     "company":"...",
     "location":"...",
     "country":"...",
     "salary":"Published salary only; otherwise Not stated",
     "url":"direct application/job URL if present, otherwise empty",
     "posted":"if stated",
     "match_score":0,
     "matched_skills":["..."],
     "gaps":["..."],
     "reason":"short factual explanation"
   }}
 ]
}}
Do not invent missing facts. match_score is an internal fit score, not an ATS score.
"""
    r = client.responses.create(model=os.getenv("OPENAI_MODEL", "gpt-5"), input=prompt)
    text = r.output_text
    match = re.search(r'\{.*\}', text, re.S)
    if not match:
        return []
    try:
        data = json.loads(match.group(0))
        return data.get("jobs", [])
    except json.JSONDecodeError:
        return []

@app.post("/search", response_class=HTMLResponse)
def search():
    if not client:
        return HTMLResponse("<h2>Configure OPENAI_API_KEY in .env first.</h2>", status_code=500)
    chunks = []
    # Keep the first MVP bounded. Expand with a scheduled worker later.
    for title in SEARCH_TITLES:
        chunks.append(search_web(f'"{title}" current vacancy worldwide oil gas'))
    jobs = analyse_jobs("\n\n---RESULT SET---\n".join(chunks))
    jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    cards = []
    for j in jobs:
        link = f'<a href="{j.get("url","")}" target="_blank">Open job</a>' if j.get("url") else "No direct link found"
        cards.append(f"""<div class="card job">
<h2>{j.get('title','Unknown')}</h2>
<b>{j.get('company','Unknown')}</b> — {j.get('location','Unknown')}<br>
Salary: {j.get('salary','Not stated')}<br>
<span class="score">Profile match: {j.get('match_score',0)}%</span><br>
<p>{j.get('reason','')}</p>
<p>Matched: {', '.join(j.get('matched_skills',[]))}</p>
<p>Gaps: {', '.join(j.get('gaps',[]))}</p>
{link}
</div>""")
    return HTMLResponse("<h1>Job Results</h1>" + "".join(cards) +
                        '<p><a href="/">← Back</a></p>')

@app.post("/ats", response_class=HTMLResponse)
def ats(job_description: str = Form(...)):
    if not client:
        return HTMLResponse("<h2>Configure OPENAI_API_KEY in .env first.</h2>", status_code=500)
    prompt = f"""Create an ATS-friendly CV for this candidate.

Candidate profile:
{json.dumps(PROFILE, indent=2)}

Target job description:
{job_description}

Rules:
1. Never invent a qualification, certification, employer, job title, responsibility, software, equipment or achievement.
2. Use exact keywords from the job description only when they are supported by the candidate profile.
3. Keep the CV plain-text friendly: no tables, columns, graphics or icons.
4. Produce: Professional Summary, Core Skills, Professional Experience, Education, Certifications (only if supplied).
5. Clearly mark unsupported requirements as gaps outside the CV.
6. Do not claim an ATS score as a fact. After the CV, provide an 'ATS keyword coverage' section listing matched and missing keywords."""
    r = client.responses.create(model=os.getenv("OPENAI_MODEL", "gpt-5"), input=prompt)
    return HTMLResponse("<div class='card'><h1>ATS CV Draft</h1><pre style='white-space:pre-wrap'>" +
                        r.output_text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;") +
                        "</pre><p><a href='/'>← Back</a></p></div>")

@app.get("/health")
def health():
    return JSONResponse({"status": "ok"})
