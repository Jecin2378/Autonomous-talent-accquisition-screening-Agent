"""
Test Suite for Surprise Challenge: Requirement Conflict & Trade-Off Shortlisting.
Validates:
- TEST 1: No candidate fully qualifies ("No candidate fully satisfies all required criteria.")
- TEST 2: One candidate fully qualifies (Full satisfaction = True)
- TEST 3: Requirement coverage calculation (e.g. 5/10 = 50%)
- TEST 4: Restrictive intersection (combined intersection detected as restrictive)
- TEST 5: Requirement conflict detection (5+ years experience + Junior role)
- TEST 6: Unsupported claim (claim without evidence not treated as PASS)
- TEST 7: Contradictory evidence (timeline contradiction flags requirement)
- TEST 8: Preferred requirement (missing preferred does not block full required satisfaction)
"""

import pytest
from models.schemas import (
    JobRequisition, Requirement, RequirementType, SkillCategory,
    CandidateProfile, Claim, Evidence, EvidenceType, RequirementStatus,
    ConstraintType, ConflictType, ConflictSeverity
)
from core.requirement_analyzer import RequirementAnalyzer
from core.tradeoff_analyzer import TradeoffAnalyzer


def test_1_no_candidate_fully_qualifies():
    """TEST 1: When no candidate fully satisfies all required criteria."""
    req = JobRequisition(
        id="REQ-TEST1",
        title="Senior AI Platform Engineer",
        department="Engineering",
        experience_level="Senior",
        max_salary=8.0,
        requirements=[
            Requirement(id="R1", title="Software Experience", description="5+ years experience", category=SkillCategory.OTHER, min_years=5.0, type=RequirementType.MUST_HAVE, constraint_type=ConstraintType.NUMERIC_MIN),
            Requirement(id="R2", title="AI/ML", description="Strong AI/ML skills", category=SkillCategory.FRAMEWORKS, type=RequirementType.MUST_HAVE),
            Requirement(id="R3", title="Kubernetes", description="Kubernetes required", category=SkillCategory.INFRASTRUCTURE, type=RequirementType.MUST_HAVE),
            Requirement(id="R4", title="Salary", description="Salary <= 8 LPA", category=SkillCategory.OTHER, type=RequirementType.MUST_HAVE, constraint_type=ConstraintType.NUMERIC_MAX, target_value=8.0),
        ]
    )

    # Candidate A: 6 yrs, AI/ML, NO Kubernetes, salary 11 LPA (fails K8s and Salary)
    cand_a = CandidateProfile(
        id="CAND-A", full_name="Candidate A", email="a@test.com", current_role="ML Engineer",
        years_of_experience=6.0, expected_salary=11.0,
        claims=[
            Claim(skill_name="AI/ML", claimed_years=4.0, is_verified=True, evidence_list=[
                Evidence(id="E1", type=EvidenceType.PROJECT_CODE, description="ML models", proof_snippet="Trained deep learning transformer models", confidence_score=0.95)
            ])
        ]
    )

    # Candidate B: 2 yrs, AI/ML, Kubernetes, salary 7 LPA (fails 5+ yrs experience)
    cand_b = CandidateProfile(
        id="CAND-B", full_name="Candidate B", email="b@test.com", current_role="Junior ML Engineer",
        years_of_experience=2.0, expected_salary=7.0,
        claims=[
            Claim(skill_name="AI/ML", claimed_years=2.0, is_verified=True, evidence_list=[
                Evidence(id="E2", type=EvidenceType.PROJECT_CODE, description="ML models", proof_snippet="Built PyTorch models", confidence_score=0.9)
            ]),
            Claim(skill_name="Kubernetes", claimed_years=2.0, is_verified=True, evidence_list=[
                Evidence(id="E3", type=EvidenceType.PROJECT_CODE, description="K8s cluster", proof_snippet="Deployed Kubernetes clusters", confidence_score=0.9)
            ])
        ]
    )

    # Candidate C: 5 yrs, moderate AI/ML, Kubernetes, salary 9.5 LPA (fails Salary)
    cand_c = CandidateProfile(
        id="CAND-C", full_name="Candidate C", email="c@test.com", current_role="Cloud Engineer",
        years_of_experience=5.0, expected_salary=9.5,
        claims=[
            Claim(skill_name="AI/ML", claimed_years=2.0, is_verified=True, evidence_list=[
                Evidence(id="E4", type=EvidenceType.PROJECT_CODE, description="AI models", proof_snippet="Fine-tuned models", confidence_score=0.85)
            ]),
            Claim(skill_name="Kubernetes", claimed_years=4.0, is_verified=True, evidence_list=[
                Evidence(id="E5", type=EvidenceType.PROJECT_CODE, description="K8s infrastructure", proof_snippet="Managed production K8s", confidence_score=0.95)
            ])
        ]
    )

    report = RequirementAnalyzer.analyze_requisition_full(req, [cand_a, cand_b, cand_c])

    assert report.has_full_satisfaction is False
    assert "No candidate fully satisfies all required criteria." in report.satisfaction_verdict
    assert len(report.shortlist) == 3


def test_2_one_candidate_fully_qualifies():
    """TEST 2: When at least one candidate fully qualifies."""
    req = JobRequisition(
        id="REQ-TEST2",
        title="MLOps Engineer",
        department="AI",
        experience_level="Senior",
        max_salary=12.0,
        requirements=[
            Requirement(id="R1", title="Python", description="Python development", category=SkillCategory.LANGUAGES, min_years=4.0, type=RequirementType.MUST_HAVE),
            Requirement(id="R2", title="Kubernetes", description="Kubernetes", category=SkillCategory.INFRASTRUCTURE, min_years=3.0, type=RequirementType.MUST_HAVE),
        ]
    )

    qualified_cand = CandidateProfile(
        id="CAND-QUAL", full_name="Qualified Engineer", email="q@test.com", current_role="Senior MLOps",
        years_of_experience=5.0, expected_salary=10.0,
        claims=[
            Claim(skill_name="Python", claimed_years=5.0, is_verified=True, evidence_list=[
                Evidence(id="EQ1", type=EvidenceType.TENURE_WORK_HISTORY, description="Python tenure", proof_snippet="5 years production Python services", confidence_score=0.95)
            ]),
            Claim(skill_name="Kubernetes", claimed_years=4.0, is_verified=True, evidence_list=[
                Evidence(id="EQ2", type=EvidenceType.METRIC_IMPACT, description="K8s cluster", proof_snippet="Managed 50-node Kubernetes cluster serving 100M requests", confidence_score=0.98)
            ])
        ]
    )

    report = RequirementAnalyzer.analyze_requisition_full(req, [qualified_cand])

    assert report.has_full_satisfaction is True
    assert "FULL REQUIREMENT SATISFACTION: At least one candidate satisfies all required criteria." in report.satisfaction_verdict


def test_3_requirement_coverage():
    """TEST 3: Requirement coverage (e.g. 5 of 10 candidates satisfy experience -> 50%)."""
    req = JobRequisition(
        id="REQ-TEST3",
        title="Software Engineer",
        department="Engineering",
        experience_level="Mid-Level",
        requirements=[
            Requirement(id="R1", title="Software Experience", description="5+ years experience", category=SkillCategory.OTHER, min_years=5.0, type=RequirementType.MUST_HAVE, constraint_type=ConstraintType.NUMERIC_MIN)
        ]
    )

    candidates = []
    # 5 candidates with 5+ years experience
    for i in range(5):
        candidates.append(CandidateProfile(id=f"C-{i}", full_name=f"Candidate {i}", email=f"c{i}@test.com", current_role="Dev", years_of_experience=5.5))
    # 5 candidates with under 5 years
    for i in range(5, 10):
        candidates.append(CandidateProfile(id=f"C-{i}", full_name=f"Candidate {i}", email=f"c{i}@test.com", current_role="Dev", years_of_experience=2.0))

    matrix_rows = RequirementAnalyzer.evaluate_candidate_matrix(req, candidates)
    coverage_items, _, _, _ = RequirementAnalyzer.calculate_coverage_and_intersections(req, matrix_rows)

    exp_cov = next(c for c in coverage_items if c.title == "Software Experience")
    assert exp_cov.satisfied_count == 5
    assert exp_cov.total_candidates == 10
    assert exp_cov.coverage_pct == 50.0


def test_4_restrictive_intersection():
    """TEST 4: Individual coverages moderate/low, but combined intersection is highly restrictive (1/10)."""
    req = JobRequisition(
        id="REQ-TEST4",
        title="Specialist Engineer",
        department="AI",
        experience_level="Senior",
        requirements=[
            Requirement(id="R1", title="Software Experience", description="5+ years", category=SkillCategory.OTHER, min_years=5.0, type=RequirementType.MUST_HAVE, constraint_type=ConstraintType.NUMERIC_MIN),
            Requirement(id="R2", title="AI/ML", description="AI/ML", category=SkillCategory.FRAMEWORKS, type=RequirementType.MUST_HAVE),
            Requirement(id="R3", title="Kubernetes", description="Kubernetes", category=SkillCategory.INFRASTRUCTURE, type=RequirementType.MUST_HAVE),
        ]
    )

    candidates = []
    # Candidate 0: Meets ALL THREE (Experience, AI/ML, Kubernetes)
    candidates.append(CandidateProfile(
        id="C-0", full_name="All Three", email="0@test.com", current_role="Lead", years_of_experience=6.0,
        claims=[
            Claim(skill_name="AI/ML", is_verified=True, evidence_list=[Evidence(id="e1", type=EvidenceType.PROJECT_CODE, description="ML", proof_snippet="ML models in PyTorch", confidence_score=0.9)]),
            Claim(skill_name="Kubernetes", is_verified=True, evidence_list=[Evidence(id="e2", type=EvidenceType.PROJECT_CODE, description="K8s", proof_snippet="K8s clusters", confidence_score=0.9)])
        ]
    ))

    # Candidates 1-4: Meet Experience and AI/ML only (4 candidates)
    for i in range(1, 5):
        candidates.append(CandidateProfile(
            id=f"C-{i}", full_name=f"Exp+AI {i}", email=f"{i}@test.com", current_role="Dev", years_of_experience=5.5,
            claims=[Claim(skill_name="AI/ML", is_verified=True, evidence_list=[Evidence(id=f"e{i}", type=EvidenceType.PROJECT_CODE, description="ML", proof_snippet="ML models in PyTorch", confidence_score=0.9)])]
        ))

    # Candidates 5-7: Meet AI/ML and Kubernetes only, but only 2 yrs exp (3 candidates)
    for i in range(5, 8):
        candidates.append(CandidateProfile(
            id=f"C-{i}", full_name=f"AI+K8s {i}", email=f"{i}@test.com", current_role="Junior", years_of_experience=2.0,
            claims=[
                Claim(skill_name="AI/ML", is_verified=True, evidence_list=[Evidence(id=f"ea{i}", type=EvidenceType.PROJECT_CODE, description="ML", proof_snippet="ML models in PyTorch", confidence_score=0.9)]),
                Claim(skill_name="Kubernetes", is_verified=True, evidence_list=[Evidence(id=f"ek{i}", type=EvidenceType.PROJECT_CODE, description="K8s", proof_snippet="K8s clusters", confidence_score=0.9)])
            ]
        ))

    # Candidates 8-9: Neither (2 candidates)
    for i in range(8, 10):
        candidates.append(CandidateProfile(id=f"C-{i}", full_name=f"Neither {i}", email=f"{i}@test.com", current_role="QA", years_of_experience=2.0))

    matrix_rows = RequirementAnalyzer.evaluate_candidate_matrix(req, candidates)
    cov_items, inter_items, _, _ = RequirementAnalyzer.calculate_coverage_and_intersections(req, matrix_rows)

    # Verify individual coverages
    exp_item = next(c for c in cov_items if c.title == "Software Experience")
    assert exp_item.satisfied_count == 5  # 5/10 = 50%

    # Full intersection
    full_inter = next(item for item in inter_items if "Full Intersection" in item.combination_name)
    assert full_inter.satisfied_count == 1
    assert full_inter.coverage_pct == 10.0
    assert full_inter.is_restrictive is True


def test_5_requirement_conflict():
    """TEST 5: Requirement conflict between 5+ years experience and Junior-level position."""
    req = JobRequisition(
        id="REQ-CONFLICT",
        title="Junior Software Engineer",
        department="Engineering",
        experience_level="Junior-Level",
        requirements=[
            Requirement(id="R1", title="Software Development Experience", description="5+ years software development experience required", min_years=5.0, type=RequirementType.MUST_HAVE, constraint_type=ConstraintType.NUMERIC_MIN),
            Requirement(id="R2", title="Python", description="Python programming", type=RequirementType.MUST_HAVE)
        ]
    )

    conflicts = RequirementAnalyzer.detect_requisition_conflicts(req)
    assert len(conflicts) > 0
    exp_conflict = next(c for c in conflicts if c.conflict_type == ConflictType.EXPERIENCE_LEVEL_CONFLICT)
    assert exp_conflict.severity == ConflictSeverity.POTENTIAL_CONFLICT
    assert "normally targets candidates with lower experience" in exp_conflict.reason


def test_6_unsupported_claim():
    """TEST 6: Candidate claims Kubernetes but has no supporting evidence (UNSUPPORTED / UNVERIFIED)."""
    req = JobRequisition(
        id="REQ-TEST6",
        title="DevOps Engineer",
        department="Infra",
        experience_level="Senior",
        requirements=[
            Requirement(id="R1", title="Kubernetes", description="Kubernetes experience required", category=SkillCategory.INFRASTRUCTURE, type=RequirementType.MUST_HAVE)
        ]
    )

    candidate = CandidateProfile(
        id="CAND-UNSUP", full_name="Unsubstantiated Candidate", email="unsup@test.com", current_role="Consultant",
        years_of_experience=5.0,
        claims=[
            Claim(skill_name="Kubernetes", claimed_years=4.0, is_verified=False, evidence_list=[])
        ]
    )

    matrix_rows = RequirementAnalyzer.evaluate_candidate_matrix(req, [candidate])
    status = matrix_rows[0].cells.get("Kubernetes")
    assert status in [RequirementStatus.UNSUPPORTED, RequirementStatus.UNKNOWN]
    assert status != RequirementStatus.PASS


def test_7_contradictory_evidence():
    """TEST 7: Candidate claims 5 years experience but timeline shows internship only (CONTRADICTORY)."""
    req = JobRequisition(
        id="REQ-TEST7",
        title="Backend Engineer",
        department="Eng",
        experience_level="Senior",
        requirements=[
            Requirement(id="R1", title="Software Development Experience", description="5+ years software development", category=SkillCategory.OTHER, min_years=5.0, type=RequirementType.MUST_HAVE, constraint_type=ConstraintType.NUMERIC_MIN)
        ]
    )

    candidate = CandidateProfile(
        id="CAND-CONTRA", full_name="Contradiction Candidate", email="contra@test.com", current_role="Intern",
        years_of_experience=5.0, # Inflated claim
        raw_resume_text="""
Contradiction Candidate
5 years of software development experience.

EXPERIENCE:
Software Engineering Intern | TechCorp (2024 - 2025)
- Assisted senior team on API maintenance.

EDUCATION:
B.Tech Computer Science (2021 - 2025)
"""
    )

    matrix_rows = RequirementAnalyzer.evaluate_candidate_matrix(req, [candidate])
    status = matrix_rows[0].cells.get("Software Development Experience")
    assert status == RequirementStatus.CONTRADICTORY


def test_8_preferred_requirement():
    """TEST 8: Candidate satisfies all required criteria (Python), but not preferred (AWS). Can still achieve full required satisfaction."""
    req = JobRequisition(
        id="REQ-TEST8",
        title="Python Backend Developer",
        department="Eng",
        experience_level="Mid",
        requirements=[
            Requirement(id="R1", title="Python", description="Python backend", type=RequirementType.MUST_HAVE),
            Requirement(id="R2", title="AWS", description="AWS cloud preferred", type=RequirementType.PREFERRED, category=SkillCategory.INFRASTRUCTURE)
        ]
    )

    candidate = CandidateProfile(
        id="CAND-PREF", full_name="Python Specialist", email="py@test.com", current_role="Python Dev",
        years_of_experience=4.0,
        claims=[
            Claim(skill_name="Python", claimed_years=4.0, is_verified=True, evidence_list=[
                Evidence(id="E-py", type=EvidenceType.PROJECT_CODE, description="Python APIs", proof_snippet="Built FastAPI async services", confidence_score=0.95)
            ])
            # No AWS claim
        ]
    )

    report = RequirementAnalyzer.analyze_requisition_full(req, [candidate])

    assert report.has_full_satisfaction is True
    assert "FULL REQUIREMENT SATISFACTION" in report.satisfaction_verdict
    # Candidate meets must-have Python, but AWS is not marked as a required failure
    row = report.matrix_rows[0]
    assert row.satisfies_all_required is True
    assert row.cells.get("Python") == RequirementStatus.PASS
    assert row.cells.get("AWS") != RequirementStatus.PASS
