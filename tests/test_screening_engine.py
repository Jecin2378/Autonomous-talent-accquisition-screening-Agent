"""
Test suite for Evaluation 3: Core AI Screening Engine.
Validates:
1. SkillNormalizer (canonical mapping, equivalent recognition, non-equivalent isolation)
2. EvidenceVerifier (density calculation, keyword spam penalty, proof extraction)
3. TradeoffAnalyzer (multi-dimensional scoring, trade-off matrix, ranking)
4. PoolGapDetector (systemic skill shortages, must-have/preferred gaps, actionable recommendations)
5. ScreeningAgentEngine (orchestration, batch processing, pool gap reporting)
"""

import pytest
from models.schemas import (
    JobRequisition, Requirement, RequirementType, SkillCategory,
    CandidateProfile, Claim, Evidence, EvidenceType, CandidateScore
)
from core.skill_normalizer import SkillNormalizer
from core.evidence_verifier import EvidenceVerifier
from core.tradeoff_analyzer import TradeoffAnalyzer
from core.gap_detector import PoolGapDetector
from core.llm_engine import ScreeningAgentEngine
from data.sample_data import get_sample_requisition, get_sample_candidates


def test_eval3_skill_normalizer_canonical_and_equivalences():
    """Verify that skill normalization correctly standardizes variations and aliases."""
    assert SkillNormalizer.normalize("k8s") == "Kubernetes"
    assert SkillNormalizer.normalize("kubernetes") == "Kubernetes"
    assert SkillNormalizer.normalize("torch") == "PyTorch"
    assert SkillNormalizer.normalize("postgres") == "PostgreSQL"
    assert SkillNormalizer.normalize("postgresql") == "PostgreSQL"
    assert SkillNormalizer.normalize("py") == "Python"
    assert SkillNormalizer.normalize("tf") == "TensorFlow"

    # Equivalence verification
    assert SkillNormalizer.are_equivalent("k8s", "Kubernetes")
    assert SkillNormalizer.are_equivalent("py", "Python")
    assert SkillNormalizer.are_equivalent("torch", "PyTorch")

    # Non-equivalence protection
    assert not SkillNormalizer.are_equivalent("Docker", "Kubernetes")
    assert not SkillNormalizer.are_equivalent("AWS", "Azure")
    assert not SkillNormalizer.are_equivalent("MySQL", "MongoDB")


def test_eval3_evidence_verifier_density_and_spam_penalty():
    """Verify that EvidenceVerifier rewards verified claims and penalizes keyword stuffing."""
    # Candidate with verified metrics
    verified_candidate = CandidateProfile(
        id="CAND-VERIFIED",
        full_name="Verified Engineer",
        email="verified@test.com",
        current_role="Senior ML Engineer",
        years_of_experience=5.0,
        claims=[
            Claim(
                skill_name="Python",
                claimed_years=5.0,
                evidence_list=[
                    Evidence(
                        id="EV-1",
                        type=EvidenceType.TENURE_WORK_HISTORY,
                        description="5 years backend dev",
                        proof_snippet="5 years backend development in production Python",
                        confidence_score=0.95
                    )
                ]
            ),
            Claim(
                skill_name="Kubernetes",
                claimed_years=4.0,
                evidence_list=[
                    Evidence(
                        id="EV-2",
                        type=EvidenceType.METRIC_IMPACT,
                        description="Scaled 50 nodes to 100M requests",
                        proof_snippet="Scaled 50 node K8s cluster to 100M requests daily",
                        confidence_score=0.98
                    )
                ]
            )
        ]
    )

    _, density, spam_penalty = EvidenceVerifier.verify_candidate_profile(verified_candidate)
    assert density >= 90.0
    assert spam_penalty == 0.0

    # Keyword spammer candidate with 0 evidence
    spammer_candidate = CandidateProfile(
        id="CAND-SPAM",
        full_name="Keyword Spammer",
        email="spam@test.com",
        current_role="Consultant",
        years_of_experience=5.0,
        claims=[
            Claim(skill_name="Python", claimed_years=5.0, evidence_list=[]),
            Claim(skill_name="Kubernetes", claimed_years=5.0, evidence_list=[]),
            Claim(skill_name="PyTorch", claimed_years=5.0, evidence_list=[]),
            Claim(skill_name="Docker", claimed_years=5.0, evidence_list=[]),
        ]
    )

    _, spam_density, spam_pen = EvidenceVerifier.verify_candidate_profile(spammer_candidate)
    assert spam_density == 0.0
    assert spam_pen > 30.0  # Heavy keyword spam penalty applied


def test_eval3_tradeoff_analyzer_scoring_dimensions():
    """Verify multi-dimensional trade-off analysis generates clear score breakdown."""
    req = get_sample_requisition()
    candidates = get_sample_candidates()
    
    # Evaluate top candidate (Alex Chen)
    res_alex = TradeoffAnalyzer.evaluate_candidate(req, candidates[0])
    assert res_alex.score.overall_score > 80.0
    assert res_alex.score.evidence_density_score > 85.0
    assert res_alex.score.keyword_spam_penalty == 0.0
    assert isinstance(res_alex.tradeoff, object)
    assert len(res_alex.tradeoff.key_strengths) > 0
    assert "Evaluation Rationale" in res_alex.explainable_rationale

    # Evaluate keyword spam candidate (Bradley Vance)
    res_bradley = TradeoffAnalyzer.evaluate_candidate(req, candidates[1])
    assert res_bradley.score.keyword_spam_penalty > 0.0
    assert res_bradley.score.overall_score < res_alex.score.overall_score
    assert len(res_bradley.tradeoff.trade_off_risks) > 0


def test_eval3_pool_gap_detector():
    """Verify that PoolGapDetector finds missing must-haves and generates actionable recommendations."""
    req = get_sample_requisition()
    candidates = get_sample_candidates()

    engine = ScreeningAgentEngine()
    results = engine.evaluate_batch(req, candidates)

    pool_report = PoolGapDetector.analyze_pool_gaps(req, results)
    assert pool_report.job_id == req.id
    assert pool_report.total_candidates_evaluated == len(candidates)
    assert isinstance(pool_report.unmet_must_haves, list)
    assert isinstance(pool_report.unmet_preferred, list)
    assert len(pool_report.recruiter_actionable_recommendations) > 0
    assert "Evaluated" in pool_report.gap_analysis_summary


def test_eval3_screening_agent_engine_batch_and_ranking():
    """Verify end-to-end engine orchestrates parsing, ranking, and gap analysis."""
    req = get_sample_requisition()
    candidates = get_sample_candidates()

    engine = ScreeningAgentEngine()
    ranked_results = engine.evaluate_batch(req, candidates)

    assert len(ranked_results) == len(candidates)
    # Verify sorted descending by overall score
    scores = [r.score.overall_score for r in ranked_results]
    assert scores == sorted(scores, reverse=True)

    # Top candidate should be Alex Chen
    assert ranked_results[0].candidate_name == "Alex Chen"

    # Generate pool report via engine
    gap_report = engine.generate_pool_report(req, ranked_results)
    assert gap_report.total_candidates_evaluated == 4
