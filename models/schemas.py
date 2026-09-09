from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RequirementType(str, Enum):
    MUST_HAVE = "MUST_HAVE"
    PREFERRED = "PREFERRED"


class SkillCategory(str, Enum):
    LANGUAGES = "LANGUAGES"
    FRAMEWORKS = "FRAMEWORKS"
    INFRASTRUCTURE ="INFRASTRUCTURE"
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


class ContradictionType(str, Enum):
    SKILL_EXPERIENCE_CONTRADICTION = "SKILL_EXPERIENCE_CONTRADICTION"
    RESUME_COVER_NOTE_CONTRADICTION = "RESUME_COVER_NOTE_CONTRADICTION"
    TITLE_RESPONSIBILITY_MISMATCH = "TITLE_RESPONSIBILITY_MISMATCH"
    EXPERTISE_EVIDENCE_CONTRADICTION = "EXPERTISE_EVIDENCE_CONTRADICTION"
    DATE_EXPERIENCE_CONTRADICTION = "DATE_EXPERIENCE_CONTRADICTION"
    SECTION_CONTRADICTION = "SECTION_CONTRADICTION"
    GENERAL_CONTRADICTION = "GENERAL_CONTRADICTION"


class ContradictionFlag(str, Enum):
    CONTRADICTORY_UNSUPPORTED = "CONTRADICTORY / UNSUPPORTED CLAIM"
    UNSUPPORTED_CLAIM = "UNSUPPORTED CLAIM"


class EvidenceSourceType(str, Enum):
    GITHUB = "GITHUB"
    GITLAB = "GITLAB"
    BITBUCKET = "BITBUCKET"
    LEETCODE = "LEETCODE"
    CODEFORCES = "CODEFORCES"
    HACKERRANK = "HACKERRANK"
    CODECHEF = "CODECHEF"
    KAGGLE = "KAGGLE"
    HUGGINGFACE = "HUGGINGFACE"
    PORTFOLIO = "PORTFOLIO"
    RESEARCH = "RESEARCH"
    CERTIFICATION = "CERTIFICATION"
    OTHER = "OTHER"


class EvidenceState(str, Enum):
    SUPPORTED = "SUPPORTED"
    UNVERIFIED = "UNVERIFIED"
    CONTRADICTORY_UNSUPPORTED = "CONTRADICTORY / UNSUPPORTED"


class IdentityLinkStatus(str, Enum):
    STRONG = "strong"
    POSSIBLE = "possible"
    UNCLEAR = "unclear"


class ConstraintType(str, Enum):
    NUMERIC_MIN = "NUMERIC_MIN"
    NUMERIC_MAX = "NUMERIC_MAX"
    EXACT_LEVEL = "EXACT_LEVEL"
    SKILL_PRESENCE = "SKILL_PRESENCE"
    SKILL_STRENGTH = "SKILL_STRENGTH"
    BOOLEAN = "BOOLEAN"
    PREFERRED = "PREFERRED"


class RequirementStatus(str, Enum):
    PASS = "PASS"
    PARTIAL = "PARTIAL"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTORY = "CONTRADICTORY"


class ConflictType(str, Enum):
    EXPERIENCE_LEVEL_CONFLICT = "EXPERIENCE_LEVEL_CONFLICT"
    SKILL_CONSTRAINT_CONFLICT = "SKILL_CONSTRAINT_CONFLICT"
    COMPENSATION_CONSTRAINT = "COMPENSATION_CONSTRAINT"
    REQUIREMENT_INTERSECTION_TOO_RESTRICTIVE = "REQUIREMENT_INTERSECTION_TOO_RESTRICTIVE"
    GENERAL_CONFLICT = "GENERAL_CONFLICT"


class ConflictSeverity(str, Enum):
    POTENTIAL_CONFLICT = "POTENTIAL_CONFLICT"
    HIGH_RESTRICTION = "HIGH_RESTRICTION"
    COMPATIBLE = "COMPATIBLE"
    UNCLEAR = "UNCLEAR"


class Requirement(BaseModel):
    id: str
    title: str
    description: str
    category: SkillCategory = SkillCategory.OTHER
    type: RequirementType = RequirementType.MUST_HAVE
    min_years: float = 0.0
    weight: float = 1.0
    constraint_type: Optional[ConstraintType] = None
    target_value: Optional[Any] = None
    comparison_operator: Optional[str] = None
    evidence_needed: Optional[str] = None
    is_hard_requirement: bool = True


class JobRequisition(BaseModel):
    id: str
    title: str
    department: str
    experience_level: str
    requirements: List[Requirement]
    raw_description: Optional[str] = ""
    max_salary: Optional[float] = None
    salary_currency: Optional[str] = "LPA"
    target_role_level: Optional[str] = None


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
    cover_note: Optional[str] = ""
    repository_links: List[str] = Field(default_factory=list)
    expected_salary: Optional[float] = None
    current_level: Optional[str] = None
    location: Optional[str] = None
    willing_to_relocate: Optional[bool] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CandidateScore(BaseModel):
    overall_score: float = Field(ge=0.0, le=100.0)
    evidence_density_score: float = Field(ge=0.0, le=100.0)
    requirement_match_score: float = Field(ge=0.0, le=100.0)
    skill_depth_score: float = Field(ge=0.0, le=100.0)
    keyword_spam_penalty: float = Field(ge=0.0, le=50.0, default=0.0)


class EvidenceReference(BaseModel):
    source: str
    text: str


class ContradictionResult(BaseModel):
    candidate_id: str
    flag: str
    type: ContradictionType
    claim: str
    evidence: List[EvidenceReference]
    assessment: str
    confidence: str = "reduced"


class EvidenceSourceMetadata(BaseModel):
    source_name: str
    source_type: EvidenceSourceType
    url: str
    supported_claim_types: List[str]
    is_accessible: bool = True
    notes: str = ""


class IdentityLinkage(BaseModel):
    status: IdentityLinkStatus
    reasons: List[str]
    confidence_score: float = 1.0


class EvidenceLedgerEntry(BaseModel):
    claim: str
    sources: List[Dict[str, str]]
    assessment: EvidenceState
    confidence: str = "high" # "high", "moderate", "reduced"
    identity_linkage: IdentityLinkage
    reasoning: str = ""


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
    contradictions: List[ContradictionResult] = Field(default_factory=list)
    evidence_ledger: List[EvidenceLedgerEntry] = Field(default_factory=list)
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


class RequirementConflict(BaseModel):
    conflict_type: ConflictType
    severity: ConflictSeverity
    title: str
    conflicting_requirements: List[str]
    reason: str


class RequirementCoverageItem(BaseModel):
    requirement_id: str
    title: str
    is_required: bool
    satisfied_count: int
    total_candidates: int
    coverage_pct: float
    status: str # "LOW_COVERAGE", "MODERATE_COVERAGE", "HIGH_COVERAGE"


class RequirementIntersectionItem(BaseModel):
    combination_name: str
    requirements: List[str]
    satisfied_count: int
    total_candidates: int
    coverage_pct: float
    is_restrictive: bool = False
    notes: str = ""


class CandidateRequirementCell(BaseModel):
    requirement_id: str
    requirement_title: str
    status: RequirementStatus
    reason: str = ""
    is_must_have: bool = True


class CandidateMatrixRow(BaseModel):
    candidate_id: str
    candidate_name: str
    cells: Dict[str, RequirementStatus]
    cell_details: List[CandidateRequirementCell] = Field(default_factory=list)
    required_satisfied: int = 0
    required_total: int = 0
    preferred_satisfied: int = 0
    preferred_total: int = 0
    satisfies_all_required: bool = False


class ShortlistCandidate(BaseModel):
    candidate_id: str
    candidate_name: str
    rank: int = 1
    strengths: List[str] = Field(default_factory=list)
    unmet_requirements: List[str] = Field(default_factory=list)
    partial_requirements: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)
    unsupported_claims: List[str] = Field(default_factory=list)
    tradeoffs: List[str] = Field(default_factory=list)
    evidence_confidence: str = "High" # "High", "Moderate", "Reduced"
    required_criteria_met: int = 0
    required_criteria_total: int = 0
    preferred_criteria_met: int = 0
    preferred_criteria_total: int = 0
    overall_assessment: str = ""
    secondary_score: Optional[float] = None


class RequisitionAnalysisReport(BaseModel):
    requisition_id: str
    requisition_title: str
    conflicts_detected: List[RequirementConflict] = Field(default_factory=list)
    coverage_items: List[RequirementCoverageItem] = Field(default_factory=list)
    intersection_items: List[RequirementIntersectionItem] = Field(default_factory=list)
    has_full_satisfaction: bool = False
    satisfaction_verdict: str = ""
    pool_gaps_summary: str = ""
    matrix_rows: List[CandidateMatrixRow] = Field(default_factory=list)
    shortlist: List[ShortlistCandidate] = Field(default_factory=list)
