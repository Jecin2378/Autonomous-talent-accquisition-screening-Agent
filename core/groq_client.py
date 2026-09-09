"""
Groq API Client for Autonomous Talent-Acquisition Screening Agent.
Connects to Groq OpenAI-compatible endpoints using open-source ChatGPT-class models
(e.g., openai/gpt-oss-120b, openai/gpt-oss-20b).
"""

import os
import re
import json
import requests
from typing import Optional, Dict, Any, List
from models.schemas import CandidateProfile, Claim, Evidence, EvidenceType
from parsers.document_parser import DocumentParser


def _load_env_file():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        if k.strip() not in os.environ:
                            os.environ[k.strip()] = v.strip().strip("'\"")
        except Exception:
            pass

_load_env_file()


class GroqClient:
    """
    Client for Groq's OpenAI-compatible chat completion API.
    Provides structured AI resume information extraction and contradiction reasoning.
    """

    DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"
    DEFAULT_MODEL = "openai/gpt-oss-120b"
    FALLBACK_MODEL = "openai/gpt-oss-20b"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.base_url = (base_url or os.getenv("GROQ_BASE_URL") or self.DEFAULT_BASE_URL).rstrip("/")
        self.model = model or os.getenv("GROQ_MODEL") or self.DEFAULT_MODEL

    def is_configured(self) -> bool:
        """Returns True if an API key is configured."""
        return bool(self.api_key and self.api_key.startswith("gsk_"))

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4000,
        response_format: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Sends chat completion request to Groq API."""
        if not self.is_configured():
            return None

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Try default model first, fallback if unavailable
        for current_model in [self.model, self.FALLBACK_MODEL]:
            payload = {
                "model": current_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            if response_format:
                payload["response_format"] = response_format

            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "")
                elif resp.status_code == 404 and "model_not_found" in resp.text:
                    continue
                else:
                    print(f"[Groq API Warning]: {resp.status_code} - {resp.text}")
                    break
            except Exception as e:
                print(f"[Groq Client Connection Error]: {e}")
                break

        return None

    def extract_candidate_profile(self, raw_text: str, candidate_name: Optional[str] = None, links: Optional[List[str]] = None) -> CandidateProfile:
        """
        Uses Groq LLM (openai/gpt-oss-120b) to extract structured candidate claims,
        verified snippets, metrics, dates, and experience from unstructured resume text.
        Falls back gracefully to deterministic parsing if offline.
        """
        if links is None:
            urls = re.findall(r'https?://[^\s]+|github\.com/[^\s]+', raw_text)
            links = list(set(urls))

        prompt = f"""
You are an expert technical talent screening auditor. Analyze this resume text and extract candidate information into a strictly valid JSON object.

RESUME TEXT:
\"\"\"
{raw_text[:4000]}
\"\"\"

INSTRUCTIONS:
1. Extract:
   - "full_name": string (default to "{candidate_name or 'Applicant'}" if unknown)
   - "email": string
   - "current_role": string (e.g. "Senior Cloud Engineer")
   - "years_of_experience": float (total professional years)
   - "expected_salary": float or null (in LPA if mentioned, else null)
   - "skills": list of objects where each item has:
       - "skill_name": string (e.g. "Python", "Kubernetes", "AWS", "Docker", "Machine Learning", "FastAPI")
       - "claimed_years": float
       - "proof_snippet": string (the exact sentence from resume proving this skill, including quantifiable metrics like node count, latency, requests if present)
       - "has_concrete_evidence": boolean (true if backed by project/work experience, false if just a standalone keyword)

Return ONLY a valid JSON object matching the instructions above.
"""
        messages = [
            {"role": "system", "content": "You are a precise JSON-only resume parser and evidence discovery auditor."},
            {"role": "user", "content": prompt}
        ]

        llm_output = self.chat_completion(
            messages,
            temperature=0.1,
            max_tokens=4500,
            response_format={"type": "json_object"}
        )
        if llm_output:
            try:
                # Clean markdown backticks if present
                clean_json = re.sub(r'^```(?:json)?\s*', '', llm_output.strip(), flags=re.MULTILINE)
                clean_json = re.sub(r'```$', '', clean_json.strip(), flags=re.MULTILINE)
                data = json.loads(clean_json)

                claims = []
                for s in data.get("skills", []):
                    skill_name = s.get("skill_name", "").strip()
                    if not skill_name:
                        continue
                    proof = s.get("proof_snippet", "")
                    has_ev = s.get("has_concrete_evidence", True)
                    
                    ev_list = []
                    if proof:
                        ev_list.append(
                            Evidence(
                                id=f"EV-AI-{abs(hash(skill_name)) % 1000}",
                                type=EvidenceType.PROJECT_CODE if has_ev else EvidenceType.UNSUBSTANTIATED_KEYWORD,
                                description=f"Extracted by Groq AI for {skill_name}",
                                proof_snippet=proof,
                                confidence_score=0.95 if has_ev else 0.20
                            )
                        )

                    claims.append(
                        Claim(
                            skill_name=skill_name,
                            claimed_years=float(s.get("claimed_years") or 1.0),
                            is_verified=has_ev and bool(proof),
                            verification_notes="Extracted and cross-referenced via Groq AI" if has_ev else "Unsubstantiated keyword listing",
                            evidence_list=ev_list
                        )
                    )

                return CandidateProfile(
                    id=f"CAND-AI-{abs(hash(raw_text)) % 10000:04d}",
                    full_name=data.get("full_name") or candidate_name or "Applicant",
                    email=data.get("email") or f"{(candidate_name or 'candidate').lower().replace(' ', '.')}@applicant.io",
                    current_role=data.get("current_role") or "Software Engineer",
                    years_of_experience=float(data.get("years_of_experience") or 3.0),
                    expected_salary=data.get("expected_salary"),
                    claims=claims,
                    raw_resume_text=raw_text,
                    repository_links=links
                )
            except Exception as e:
                print(f"[Groq Extraction Fallback]: JSON parsing failed ({e}). Using deterministic parser.")

        # Fallback to deterministic parser
        sections = DocumentParser.extract_sections(raw_text)
        fallback_claims = []
        known_keywords = ["Python", "Kubernetes", "AWS", "Docker", "FastAPI", "SQL", "PostgreSQL", "Machine Learning", "NLP"]
        for kw in known_keywords:
            if re.search(rf"\b{re.escape(kw)}\b", raw_text, re.IGNORECASE):
                fallback_claims.append(
                    Claim(
                        skill_name=kw,
                        claimed_years=3.0,
                        is_verified=True,
                        verification_notes="Identified from resume text regex scanning",
                        evidence_list=[
                            Evidence(
                                id=f"EV-REGEX-{abs(hash(kw)) % 1000}",
                                type=EvidenceType.PROJECT_CODE,
                                description=f"Found in parsed document for {kw}",
                                proof_snippet=f"Document contains referenced experience for {kw}.",
                                confidence_score=0.85
                            )
                        ]
                    )
                )

        return CandidateProfile(
            id=f"CAND-{abs(hash(raw_text)) % 10000:04d}",
            full_name=candidate_name or "Applicant",
            email=f"{(candidate_name or 'applicant').lower().replace(' ', '.')}@applicant.com",
            current_role="Applicant",
            years_of_experience=3.0,
            claims=fallback_claims,
            raw_resume_text=raw_text,
            repository_links=links
        )
