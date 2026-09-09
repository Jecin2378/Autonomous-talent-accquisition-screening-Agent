import json
import os
from typing import List, Optional
from models.schemas import JobRequisition, CandidateProfile, EvaluationResult, PoolGapReport, RequisitionAnalysisReport
from core.tradeoff_analyzer import TradeoffAnalyzer
from core.gap_detector import PoolGapDetector
from core.requirement_analyzer import RequirementAnalyzer
from parsers.document_parser import DocumentParser


class ScreeningAgentEngine:
    """
    Autonomous Screening Agent Orchestrator.
    Combines NLP parsing, skill normalization, evidence cross-checking, and trade-off scoring.
    """

    def __init__(self, api_key: Optional[str] = None, provider: str = "offline"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.provider = provider if self.api_key else "offline"

    def evaluate_single_candidate(self, requisition: JobRequisition, candidate: CandidateProfile) -> EvaluationResult:
        """Evaluates a single candidate profile against requisition."""
        return TradeoffAnalyzer.evaluate_candidate(requisition, candidate)

    def evaluate_candidate_file(self, requisition: JobRequisition, file_path: str, candidate_name: str = "Applicant") -> EvaluationResult:
        """Parses a resume file (PDF/TXT) and runs full evaluation."""
        text = DocumentParser.extract_text_from_file(file_path)
        sections = DocumentParser.extract_sections(text)
        
        # Build candidate profile
        profile = CandidateProfile(
            id=f"CAND-{abs(hash(file_path)) % 10000:04d}",
            full_name=candidate_name,
            email=f"{candidate_name.lower().replace(' ', '.')}@applicant.com",
            current_role="Applicant",
            years_of_experience=3.5, # Default estimation if unstructured
            raw_resume_text=text,
            repository_links=sections["links"].split("\n") if sections["links"] else []
        )
        return self.evaluate_single_candidate(requisition, profile)

    def evaluate_batch(self, requisition: JobRequisition, candidates: List[CandidateProfile]) -> List[EvaluationResult]:
        """Evaluates a batch of candidate profiles and ranks them by evidence-backed score."""
        results = [self.evaluate_single_candidate(requisition, c) for c in candidates]
        # Rank by overall score descending
        results.sort(key=lambda r: r.score.overall_score, reverse=True)
        return results

    def generate_pool_report(self, requisition: JobRequisition, results: List[EvaluationResult]) -> PoolGapReport:
        """Generates pool-wide gap detection report."""
        return PoolGapDetector.analyze_pool_gaps(requisition, results)

    def analyze_requisition_and_shortlist(
        self,
        requisition: JobRequisition,
        candidates: List[CandidateProfile]
    ) -> RequisitionAnalysisReport:
        """
        Runs comprehensive Requisition Conflict Analysis, Candidate Requirement Matrix,
        Coverage & Restrictive Intersection Analysis, and Closest-Fit Shortlisting.
        """
        return RequirementAnalyzer.analyze_requisition_full(requisition, candidates)
