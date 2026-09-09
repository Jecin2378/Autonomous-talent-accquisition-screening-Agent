import pytest
from models.schemas import (
    CandidateProfile, JobRequisition, Requirement, RequirementType,
    SkillCategory, Claim, Evidence, EvidenceType, ContradictionType,
    ContradictionFlag
)
from core.contradiction_detector import ContradictionDetector
from core.tradeoff_analyzer import TradeoffAnalyzer
from data.sample_data import get_sample_requisition


def test_1_contradictory_experience_duration():
    """TEST 1: Clearly contradictory experience duration."""
    candidate = CandidateProfile(
        id="A-07",
        full_name="Jordan Lee",
        email="jordan@dev.com",
        current_role="Software Engineering Intern",
        years_of_experience=1.0,
        raw_resume_text="""
Jordan Lee
5 years of Python experience

EXPERIENCE:
Software Engineering Intern | TechCorp (2024 - 2025)
- Assisted team with minor Python bug fixes.

EDUCATION:
B.Tech | University of Technology (2021 - 2025)
"""
    )
    
    contradictions = ContradictionDetector.analyze_candidate(candidate)
    
    assert len(contradictions) >= 1
    date_flags = [c for c in contradictions if c.type == ContradictionType.DATE_EXPERIENCE_CONTRADICTION]
    assert len(date_flags) == 1
    flag_item = date_flags[0]
    assert flag_item.flag == ContradictionFlag.CONTRADICTORY_UNSUPPORTED.value
    assert "5 years of Python experience" in flag_item.claim
    
    # Verify exact evidence from application is cited
    evidence_texts = [e.text for e in flag_item.evidence]
    assert any("2024 - 2025" in t or "2021 - 2025" in t for t in evidence_texts)
    print("\n[TEST 1 PASSED]: Date duration contradiction detected with cited timeline evidence.")


def test_2_resume_cover_note_conflict():
    """TEST 2: Resume and cover note conflict."""
    candidate = CandidateProfile(
        id="CAND-TEST2",
        full_name="Taylor Swiftly",
        email="taylor@backend.io",
        current_role="Backend Developer",
        years_of_experience=3.0,
        raw_resume_text="""
Taylor Swiftly
3 years of backend development experience.

EXPERIENCE:
Backend Developer | CloudCorp (2023 - 2026)
""",
        cover_note="""
Dear Hiring Manager,
I have 6 years of backend development experience across cloud infrastructure and microservices.
"""
    )

    contradictions = ContradictionDetector.analyze_candidate(candidate)
    cover_flags = [c for c in contradictions if c.type == ContradictionType.RESUME_COVER_NOTE_CONTRADICTION]
    
    assert len(cover_flags) == 1
    flag_item = cover_flags[0]
    assert flag_item.flag == ContradictionFlag.CONTRADICTORY_UNSUPPORTED.value
    
    # Verify evidence cited from both resume and cover note
    sources = [e.source for e in flag_item.evidence]
    assert "resume" in sources
    assert "cover_note" in sources
    print("\n[TEST 2 PASSED]: Resume vs cover note conflict detected citing both documents.")


def test_3_expert_claim_with_course_evidence():
    """TEST 3: Expert claim with only course evidence."""
    candidate = CandidateProfile(
        id="CAND-TEST3",
        full_name="Morgan Reed",
        email="morgan@k8s.io",
        current_role="DevOps Specialist",
        years_of_experience=2.0,
        raw_resume_text="""
Morgan Reed
Expert in Kubernetes

EXPERIENCE:
DevOps Assistant | CloudTech (2024 - 2026)
- Completed a Kubernetes course online.
"""
    )

    contradictions = ContradictionDetector.analyze_candidate(candidate)
    expert_flags = [c for c in contradictions if c.type == ContradictionType.EXPERTISE_EVIDENCE_CONTRADICTION]

    assert len(expert_flags) == 1
    flag_item = expert_flags[0]
    assert flag_item.flag == ContradictionFlag.UNSUPPORTED_CLAIM.value
    assert "Kubernetes course" in flag_item.evidence[0].text
    print("\n[TEST 3 PASSED]: Expert claim with course evidence flagged as unsupported.")


def test_4_job_title_vs_responsibilities_mismatch():
    """TEST 4: Job title vs responsibilities mismatch."""
    candidate = CandidateProfile(
        id="CAND-TEST4",
        full_name="Sam Vance",
        email="sam@lead.io",
        current_role="Senior Software Engineer",
        years_of_experience=4.0,
        raw_resume_text="""
Sam Vance
Senior Software Engineer

EXPERIENCE:
Senior Software Engineer | Enterprise Corp (2024 - 2026)
- Completed basic assigned tasks under supervision.
"""
    )

    contradictions = ContradictionDetector.analyze_candidate(candidate)
    mismatch_flags = [c for c in contradictions if c.type == ContradictionType.TITLE_RESPONSIBILITY_MISMATCH]

    assert len(mismatch_flags) == 1
    flag_item = mismatch_flags[0]
    assert flag_item.flag == ContradictionFlag.CONTRADICTORY_UNSUPPORTED.value
    assert "Completed basic assigned tasks under supervision" in flag_item.evidence[1].text
    print("\n[TEST 4 PASSED]: Title vs responsibility mismatch detected.")


def test_5_valid_candidate_no_contradiction():
    """TEST 5: Valid candidate with no contradiction."""
    candidate = CandidateProfile(
        id="CAND-TEST5",
        full_name="Alex Chen",
        email="alex@valid.io",
        current_role="Staff MLOps Lead",
        years_of_experience=6.0,
        raw_resume_text="""
Alex Chen - Staff MLOps Lead
6 years of production machine learning experience.

EXPERIENCE:
Staff MLOps Engineer | Nexus Tech (2022 - Present)
- Architected Kubernetes multi-region cluster (50+ nodes) serving 120M requests/day.
- Optimized PyTorch model serving pipelines using vLLM.

Senior Backend Engineer | DataCorp (2020 - 2022)
- Built Python ingestion services handling 50k events/sec.
"""
    )

    contradictions = ContradictionDetector.analyze_candidate(candidate)
    
    # Filtering for major contradictions
    major_contradictions = [c for c in contradictions if c.flag == ContradictionFlag.CONTRADICTORY_UNSUPPORTED.value]
    assert len(major_contradictions) == 0
    print("\n[TEST 5 PASSED]: Valid candidate passes without contradiction flags.")


def test_6_different_terminology_not_a_contradiction():
    """TEST 6: Different terminology but NOT a contradiction."""
    candidate = CandidateProfile(
        id="CAND-TEST6",
        full_name="Maria Garcia",
        email="maria@ai.org",
        current_role="Senior Infrastructure Engineer",
        years_of_experience=5.0,
        raw_resume_text="""
Maria Garcia
Senior Infrastructure Engineer

EXPERIENCE:
Senior Cloud Engineer | CloudScale Inc (2022 - Present)
- Deployed Torch deep learning models on microservice clusters using K8s and Helm.
- Maintained PostgreSQL database with pgvector extension.
"""
    )

    req = get_sample_requisition() # Asks for PyTorch, Kubernetes, PostgreSQL
    result = TradeoffAnalyzer.evaluate_candidate(req, candidate)

    # Confirm Torch and K8s mapped to PyTorch and Kubernetes without contradiction flags!
    assert "PyTorch / Deep Learning" in result.verified_skills or "Torch" in result.verified_skills or any("PyTorch" in s or "Torch" in s for s in result.verified_skills)
    
    contradictions = ContradictionDetector.analyze_candidate(candidate)
    norm_contradictions = [c for c in contradictions if "k8s" in c.claim.lower() or "torch" in c.claim.lower()]
    assert len(norm_contradictions) == 0
    print("\n[TEST 6 PASSED]: Synonym terminology (Torch/K8s) correctly normalized without contradiction flags.")


def test_7_missing_evidence_marked_as_unsupported_not_contradiction():
    """TEST 7: Missing evidence where system says 'insufficient evidence' rather than 'contradiction'."""
    candidate = CandidateProfile(
        id="CAND-TEST7",
        full_name="Chris Paul",
        email="chris@test.io",
        current_role="Developer",
        years_of_experience=3.0,
        raw_resume_text="""
Chris Paul - Developer

SKILLS SUMMARY:
Python, Rust, Docker
""",
        claims=[
            Claim(skill_name="Rust", claimed_years=1.0, is_verified=False, evidence_list=[])
        ]
    )

    contradictions = ContradictionDetector.analyze_candidate(candidate)
    rust_flags = [c for c in contradictions if "Rust" in c.claim]

    assert len(rust_flags) == 1
    flag_item = rust_flags[0]
    assert flag_item.flag == ContradictionFlag.UNSUPPORTED_CLAIM.value
    assert "insufficiently supported" in flag_item.assessment.lower()
    print("\n[TEST 7 PASSED]: Missing evidence correctly marked as unsupported/insufficient evidence.")
