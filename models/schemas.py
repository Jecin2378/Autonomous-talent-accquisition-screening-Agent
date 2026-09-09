from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class RequirementType(str, Enum):
    MUST_HAVE = "MUST_HAVE"
    PREFERRED = "PREFERRED"


class SkillCategory(str, Enum):
    LANGUAGES = "LANGUAGES"
    FRAMEWORKS = "FRAMEWORKS"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    DATABASE = "DATABASE"
    DOMAIN = "DOMAIN"
    OTHER = "OTHER"


class EvidenceType(str, Enum):
    PROJECT_CODE = "PROJECT_CODE"
    METRIC_IMPACT = "METRIC_IMPACT"
    TENURE_WORK_HISTORY = "TENURE_WORK_HISTORY"
    CERTIFICATION = "CERTIFICATION"
    GITHUB_REPO = "GITHUB_REPO"
    PUBLICATION = "PUBLICATION"
    UNSUBSTANTIATED_KEYWORD = "UNSUBSTANTIATED_KEYWORD"


class Requirement(BaseModel):
    id: str
    title: str
    description: str
    category: SkillCategory = SkillCategory.OTHER
    type: RequirementType = RequirementType.MUST_HAVE
    min_years: float = 0.0
    weight: float = 1.0


class JobRequisition(BaseModel):
    id: str
    title: str
    department: str
    experience_level: str
    requirements: List[Requirement]
    raw_description: Optional[str] = ""


class Evidence(BaseModel):
    id: str
    type: EvidenceType
    description: str
    proof_snippet: str
    confidence_score: float = Field(ge=0.0, le=1.0, default=1.0)


class Claim(BaseModel):
    skill_name: str
    claimed_years: float = 0.0
    evidence_list: List[Evidence] = Field(default_factory=list)
    is_verified: bool = False
    verification_notes: str = ""


class CandidateProfile(BaseModel):
    id: str
    full_name: str
    email: str
    current_role: str
    years_of_experience: float
    claims: List[Claim] = Field(default_factory=list)
    raw_resume_text: str = ""
    repository_links: List[str] = Field(default_factory=list)


class CandidateScore(BaseModel):
    overall_score: float = Field(ge=0.0, le=100.0)
    evidence_density_score: float = Field(ge=0.0, le=100.0)
    requirement_match_score: float = Field(ge=0.0, le=100.0)
    skill_depth_score: float = Field(ge=0.0, le=100.0)
    keyword_spam_penalty: float = Field(ge=0.0, le=50.0, default=0.0)


class CandidateTradeoff(BaseModel):
    candidate_id: str
    candidate_name: str
    key_strengths: List[str]
    trade_off_risks: List[str]
    summary_verdict: str


class EvaluationResult(BaseModel):
    candidate_id: str
    candidate_name: str
    score: CandidateScore
    verified_skills: List[str]
    missing_must_haves: List[str]
    missing_preferred: List[str]
    unverified_claims: List[str]
    tradeoff: CandidateTradeoff
    explainable_rationale: str


class PoolGapReport(BaseModel):
    job_id: str
    job_title: str
    total_candidates_evaluated: int
    unmet_must_haves: List[str]
    unmet_preferred: List[str]
    gap_analysis_summary: str
    recruiter_actionable_recommendations: List[str]
