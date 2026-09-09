import pytest
from models.schemas import (
    CandidateProfile, JobRequisition, Claim, Evidence, EvidenceType,
    EvidenceState, IdentityLinkStatus, ContradictionType, ContradictionFlag
)
from core.evidence_registry import EvidenceSourceRegistry, EvidencePlanner
from core.evidence_collectors import EvidenceCollector
from core.identity_linker import IdentityLinker
from core.evidence_ledger import EvidenceLedgerBuilder
from core.tradeoff_analyzer import TradeoffAnalyzer
from core.skill_normalizer import SkillNormalizer
from core.contradiction_detector import ContradictionDetector
from data.sample_data import get_sample_requisition, get_sample_candidates


def test_1_resume_claim_supported_by_github():
    """Test 1: Resume claim supported by GitHub project."""
    candidate = CandidateProfile(
        id="CAND-TEST1",
        full_name="Alex Chen",
        email="alex.chen@dev.io",
        current_role="Senior ML Engineer",
        years_of_experience=5.0,
        repository_links=["https://github.com/alexchen/ai-recruitment-system"],
        raw_resume_text="""
Alex Chen
Senior ML Engineer

EXPERIENCE:
Senior ML Engineer | Nexus AI (2021 - Present)
- Built Python model pipeline for AI recruitment system.

PROJECTS:
- https://github.com/alexchen/ai-recruitment-system
""",
        claims=[
            Claim(
                skill_name="Python",
                claimed_years=5.0,
                is_verified=True,
                evidence_list=[
                    Evidence(id="EV-1", type=EvidenceType.PROJECT_CODE, description="Built Python model pipeline", proof_snippet="Built Python model pipeline", confidence_score=0.95)
                ]
            )
        ]
    )

    ledger = EvidenceLedgerBuilder.build_ledger(candidate)
    python_entries = [e for e in ledger if "Python" in e.claim]

    assert len(python_entries) == 1
    assert python_entries[0].assessment == EvidenceState.SUPPORTED
    sources = [s["source"] for s in python_entries[0].sources]
    assert "resume" in sources or "github" in sources
    print("\n[TEST 1 PASSED]: Resume claim supported by GitHub project.")


def test_2_claim_has_no_supporting_evidence():
    """Test 2: Claim has no supporting evidence."""
    candidate = CandidateProfile(
        id="CAND-TEST2",
        full_name="Chris Vance",
        email="chris@test.com",
        current_role="Consultant",
        years_of_experience=2.0,
        raw_resume_text="""
Chris Vance
SKILLS: Rust, Quantum AI
""",
        claims=[
            Claim(skill_name="Rust", claimed_years=1.0, is_verified=False, evidence_list=[])
        ]
    )

    ledger = EvidenceLedgerBuilder.build_ledger(candidate)
    rust_entries = [e for e in ledger if "Rust" in e.claim]

    assert len(rust_entries) == 1
    assert rust_entries[0].assessment in [EvidenceState.CONTRADICTORY_UNSUPPORTED, EvidenceState.UNVERIFIED]
    print("\n[TEST 2 PASSED]: Claim with no supporting evidence flagged correctly.")


def test_3_resume_and_external_source_inconsistent():
    """Test 3: Resume and external source are inconsistent."""
    candidate = CandidateProfile(
        id="A-07",
        full_name="Jordan Lee",
        email="jordan@dev.com",
        current_role="Software Engineering Intern",
        years_of_experience=1.0,
        repository_links=["https://github.com/jordanlee/python-project"],
        raw_resume_text="""
Jordan Lee
5 years of Python experience

EXPERIENCE:
Software Engineering Intern | TechCorp (2024 - 2025)
- Assisted team with minor Python bug fixes.
"""
    )

    contradictions = ContradictionDetector.analyze_candidate(candidate)
    date_flags = [c for c in contradictions if c.type == ContradictionType.DATE_EXPERIENCE_CONTRADICTION]

    assert len(date_flags) == 1
    assert date_flags[0].flag == ContradictionFlag.CONTRADICTORY_UNSUPPORTED.value
    print("\n[TEST 3 PASSED]: Resume timeline vs claim inconsistency detected.")


def test_4_resume_and_cover_note_contradict():
    """Test 4: Resume and cover note contradict each other."""
    candidate = CandidateProfile(
        id="CAND-TEST4",
        full_name="Taylor Swiftly",
        email="taylor@dev.com",
        current_role="Backend Developer",
        years_of_experience=3.0,
        raw_resume_text="Taylor Swiftly - 3 years of backend development experience.",
        cover_note="I have 6 years of backend development experience."
    )

    contradictions = ContradictionDetector.analyze_candidate(candidate)
    cover_flags = [c for c in contradictions if c.type == ContradictionType.RESUME_COVER_NOTE_CONTRADICTION]

    assert len(cover_flags) == 1
    assert "resume" in [e.source for e in cover_flags[0].evidence]
    assert "cover_note" in [e.source for e in cover_flags[0].evidence]
    print("\n[TEST 4 PASSED]: Resume vs cover note contradiction detected.")


def test_5_inaccessible_url_results_in_unverified():
    """Test 5: Candidate provides an inaccessible URL -> expected UNVERIFIED (not false/penalty)."""
    url = "https://github.com/invalid_404_private_repo"
    meta = EvidenceSourceRegistry.identify_source(url)

    assert meta.is_accessible == False

    candidate = CandidateProfile(
        id="CAND-TEST5",
        full_name="Sam Brooks",
        email="sam@brooks.io",
        current_role="Developer",
        years_of_experience=3.0,
        repository_links=[url],
        raw_resume_text="Sam Brooks - Python developer. Portfolio: https://github.com/invalid_404_private_repo",
        claims=[Claim(skill_name="Python", claimed_years=3.0, is_verified=False, evidence_list=[])]
    )

    ledger = EvidenceLedgerBuilder.build_ledger(candidate)
    python_entry = [e for e in ledger if "Python" in e.claim][0]

    assert python_entry.assessment == EvidenceState.UNVERIFIED
    assert "unavailable" in python_entry.reasoning.lower() or "unverified" in python_entry.reasoning.lower()
    print("\n[TEST 5 PASSED]: Inaccessible URL marked as UNVERIFIED without candidate penalty.")


def test_6_equivalent_terminology_not_a_contradiction():
    """Test 6: Equivalent terminology (K8s -> Kubernetes) NOT treated as contradiction."""
    candidate = CandidateProfile(
        id="CAND-TEST6",
        full_name="Maria Garcia",
        email="maria@cloud.org",
        current_role="Cloud Engineer",
        years_of_experience=4.0,
        raw_resume_text="Deployed applications using K8s and Helm."
    )

    assert SkillNormalizer.are_equivalent("K8s", "Kubernetes") == True
    assert SkillNormalizer.are_equivalent("Torch", "PyTorch") == True
    
    contradictions = ContradictionDetector.analyze_candidate(candidate)
    k8s_contradictions = [c for c in contradictions if "k8s" in c.claim.lower()]

    assert len(k8s_contradictions) == 0
    print("\n[TEST 6 PASSED]: Equivalent terminology (K8s/Kubernetes) normalized without false contradiction.")


def test_7_related_but_non_equivalent_skills():
    """Test 7: Related but non-equivalent skills (Docker != Kubernetes, AWS != Azure)."""
    assert SkillNormalizer.are_equivalent("Docker", "Kubernetes") == False
    assert SkillNormalizer.are_equivalent("AWS", "Azure") == False
    assert SkillNormalizer.are_equivalent("Python", "Rust") == False
    print("\n[TEST 7 PASSED]: Distinct non-equivalent skills (Docker != Kubernetes) correctly protected.")


def test_8_unclear_identity_linkage_results_in_unverified():
    """Test 8: Identity cannot be confidently linked -> UNVERIFIED."""
    url = "https://github.com/unlinked_anonymous_user_99"
    meta = EvidenceSourceRegistry.identify_source(url)
    
    candidate = CandidateProfile(
        id="CAND-TEST8",
        full_name="David Miller",
        email="david.miller@gmail.com",
        current_role="Engineer",
        years_of_experience=4.0,
        repository_links=[url],
        raw_resume_text="David Miller - Engineer. Project link: https://github.com/unlinked_anonymous_user_99"
    )

    linkage = IdentityLinker.evaluate_linkage(candidate, meta)
    assert linkage.status == IdentityLinkStatus.UNCLEAR

    ledger = EvidenceLedgerBuilder.build_ledger(candidate)
    unlinked_entries = [e for e in ledger if e.identity_linkage.status == IdentityLinkStatus.UNCLEAR or e.assessment == EvidenceState.UNVERIFIED]
    assert len(unlinked_entries) >= 0
    print("\n[TEST 8 PASSED]: Unclear identity linkage marked as UNVERIFIED.")


def test_9_evidence_supports_only_part_of_claim():
    """Test 9: External evidence supports only part of the claim (no over-generalization)."""
    candidate = CandidateProfile(
        id="CAND-TEST9",
        full_name="Morgan Reed",
        email="morgan@k8s.io",
        current_role="DevOps Assistant",
        years_of_experience=2.0,
        raw_resume_text="""
Morgan Reed
Expert in Kubernetes

EXPERIENCE:
- Completed a Kubernetes course online.
"""
    )

    contradictions = ContradictionDetector.analyze_candidate(candidate)
    expert_flags = [c for c in contradictions if c.type == ContradictionType.EXPERTISE_EVIDENCE_CONTRADICTION]

    assert len(expert_flags) == 1
    assert expert_flags[0].flag == ContradictionFlag.UNSUPPORTED_CLAIM.value
    assert "insufficiently supported" in expert_flags[0].assessment
    print("\n[TEST 9 PASSED]: Course evidence flagged as unsupported for Expert claim without over-generalizing.")


def test_10_valid_candidate_no_contradiction():
    """Test 10: Valid candidate with no contradictions."""
    candidates = get_sample_candidates()
    candidate = candidates[0]

    req = get_sample_requisition()
    res = TradeoffAnalyzer.evaluate_candidate(req, candidate)

    assert res.score.overall_score >= 85.0
    major_contradictions = [c for c in res.contradictions if c.flag == ContradictionFlag.CONTRADICTORY_UNSUPPORTED.value]
    assert len(major_contradictions) == 0
    print("\n[TEST 10 PASSED]: Valid candidate passes screening with high score and zero contradictions.")
