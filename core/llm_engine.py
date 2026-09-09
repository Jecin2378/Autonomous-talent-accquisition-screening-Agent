import json
import os
from typing import List, Optional
from models.schemas import JobRequisition, CandidateProfile, EvaluationResult, PoolGapReport, RequisitionAnalysisReport
from core.tradeoff_analyzer import TradeoffAnalyzer
from core.gap_detector import PoolGapDetector
from core.requirement_analyzer import RequirementAnalyzer
from core.groq_client import GroqClient
from parsers.document_parser import DocumentParser


class ScreeningAgentEngine:
    """
    Autonomous Screening Agent Orchestrator.
    Combines Groq LLM (ChatGPT OSS: openai/gpt-oss-120b), skill normalization,
    evidence cross-checking, and trade-off scoring.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        provider: str = "groq"
    ):
        self.groq_client = GroqClient(api_key=api_key, base_url=base_url, model=model)
        self.provider = provider if self.groq_client.is_configured() else "offline"

    def evaluate_single_candidate(self, requisition: JobRequisition, candidate: CandidateProfile) -> EvaluationResult:
        """Evaluates a single candidate profile against requisition."""
        return TradeoffAnalyzer.evaluate_candidate(requisition, candidate)

    def evaluate_candidate_file(self, requisition: JobRequisition, file_path: str, candidate_name: str = "Applicant") -> EvaluationResult:
        """Parses a resume file (PDF/TXT) using Groq AI extraction and runs full evaluation."""
        text = DocumentParser.extract_text_from_file(file_path)
        profile = self.groq_client.extract_candidate_profile(text, candidate_name=candidate_name)
        return self.evaluate_single_candidate(requisition, profile)

    def evaluate_candidate_bytes(self, requisition: JobRequisition, file_bytes: bytes, filename: str) -> EvaluationResult:
        """Parses in-memory uploaded resume bytes using Groq AI and runs full evaluation."""
        text = DocumentParser.extract_text_from_bytes(file_bytes, filename)
        name_hint = filename.rsplit(".", 1)[0].replace("_", " ").title()
        profile = self.groq_client.extract_candidate_profile(text, candidate_name=name_hint)
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
