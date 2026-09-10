"""
Unit and Integration Tests for Domain Role Selection, Project-to-Skill Verification,
and GitHub Project Repository Auditing.
"""

import pytest
from models.schemas import (
    CandidateProfile, Claim, Evidence, EvidenceType,
    JobRequisition, RequirementType, SkillCategory, RequirementStatus
)
from core.domain_requisitions import (
    get_available_domains, get_requisition_by_domain,
    get_fullstack_requisition, get_backend_requisition,
    get_frontend_requisition, get_cloud_requisition,
    get_devops_requisition, get_conflict_requisition
)
from core.project_verifier import ProjectVerifier
from core.tradeoff_analyzer import TradeoffAnalyzer
from core.requirement_analyzer import RequirementAnalyzer


class TestDomainRequisitions:
    """Tests for multi-domain recruiter role configurations."""

    def test_all_domains_registered(self):
        domains = get_available_domains()
        assert len(domains) >= 6
        assert any("Full Stack" in d for d in domains)
        assert any("Backend" in d for d in domains)
        assert any("Frontend" in d for d in domains)
        assert any("Cloud" in d for d in domains)
        assert any("DevOps" in d for d in domains)

    def test_fullstack_requisition_structure(self):
        req = get_fullstack_requisition()
        assert req.id == "REQ-FULLSTACK-2026"
        must_haves = [r for r in req.requirements if r.type == RequirementType.MUST_HAVE]
        assert len(must_haves) == 3
        titles = [r.title for r in must_haves]
        assert "React / Modern Frontend" in titles
        assert "Node.js / Python Backend" in titles
        assert "PostgreSQL / Relational Database" in titles

    def test_backend_requisition_structure(self):
        req = get_backend_requisition()
        assert req.id == "REQ-BACKEND-2026"
        must_haves = [r for r in req.requirements if r.type == RequirementType.MUST_HAVE]
        assert len(must_haves) == 3
        titles = [r.title for r in must_haves]
        assert "Python Programming" in titles
        assert "PostgreSQL & Database Optimization" in titles

    def test_frontend_requisition_structure(self):
        req = get_frontend_requisition()
        assert req.id == "REQ-FRONTEND-2026"
        titles = [r.title for r in req.requirements]
        assert "React / UI Frameworks" in titles
        assert "TypeScript / Modern JavaScript" in titles

    def test_cloud_requisition_structure(self):
        req = get_cloud_requisition()
        assert req.id == "REQ-CLOUD-2026"
        titles = [r.title for r in req.requirements]
        assert "AWS Cloud Architecture" in titles
        assert "Terraform / Infrastructure as Code" in titles

    def test_devops_requisition_structure(self):
        req = get_devops_requisition()
        assert req.id == "REQ-DEVOPS-2026"
        titles = [r.title for r in req.requirements]
        assert "CI/CD Pipeline Automation" in titles
        assert "Kubernetes / Cluster Administration" in titles

    def test_get_requisition_by_domain_fallback(self):
        req1 = get_requisition_by_domain("🌐 Full Stack Development")
        assert req1.id == "REQ-FULLSTACK-2026"

        req2 = get_requisition_by_domain("Unknown Role")
        assert isinstance(req2, JobRequisition)


class TestProjectSkillVerification:
    """Tests verifying candidate project experience against claimed and required skills."""

    @pytest.fixture
    def sample_project_backed_candidate(self) -> CandidateProfile:
        resume_text = """
        John Doe - Senior Software Engineer
        GitHub: https://github.com/johndoe/react-fastapi-ecommerce
        
        EXPERIENCE:
        Senior Engineer | Acme Corp (2022 - 2026)
        • Architected and built high-performance React frontends with TypeScript, cutting bundle size by 40%.
        • Engineered asynchronous Python FastAPI backend services handling 10k req/s.
        • Optimized PostgreSQL database queries and connection pools, reducing latency by 35%.
        
        PROJECTS:
        Cloud Microservices Platform (https://github.com/johndoe/microservices-demo)
        • Deployed Docker containers and automated CI/CD deployment pipelines using GitHub Actions.
        
        SKILLS:
        React, TypeScript, Python, FastAPI, PostgreSQL, Docker, Kubernetes
        """
        return CandidateProfile(
            id="cand_john",
            full_name="John Doe",
            email="john@example.com",
            current_role="Senior Software Engineer",
            years_of_experience=4.5,
            raw_resume_text=resume_text,
            claims=[
                Claim(
                    skill_name="React",
                    claimed_years=4.0,
                    is_verified=True,
                    evidence_list=[Evidence(id="e1", type=EvidenceType.PROJECT_CODE, description="React app", proof_snippet="built high-performance React frontends", confidence_score=0.9)]
                ),
                Claim(
                    skill_name="Python",
                    claimed_years=4.0,
                    is_verified=True,
                    evidence_list=[Evidence(id="e2", type=EvidenceType.PROJECT_CODE, description="FastAPI app", proof_snippet="Engineered asynchronous Python FastAPI backend", confidence_score=0.95)]
                ),
                Claim(
                    skill_name="Kubernetes",
                    claimed_years=1.0,
                    is_verified=False,
                    evidence_list=[]  # Keyword only in skills list
                )
            ],
            repository_links=["https://github.com/johndoe/react-fastapi-ecommerce"]
        )

    def test_verify_skills_against_projects(self, sample_project_backed_candidate):
        req = get_fullstack_requisition()
        verifications = ProjectVerifier.verify_skills_against_projects(sample_project_backed_candidate, req)

        assert len(verifications) > 0
        v_map = {v.skill_name: v for v in verifications}

        # React / Frontend should be project backed
        react_v = next((v for k, v in v_map.items() if "react" in k.lower()), None)
        assert react_v is not None
        assert react_v.is_project_backed is True
        assert react_v.metric_impact is not None or "built" in react_v.proof_snippet.lower()

        # Python should be project backed
        python_v = next((v for k, v in v_map.items() if "python" in k.lower()), None)
        assert python_v is not None
        assert python_v.is_project_backed is True

        # Kubernetes was only listed in SKILLS section with no project verbs/context
        k8s_v = next((v for k, v in v_map.items() if "kubernetes" in k.lower()), None)
        if k8s_v:
            assert k8s_v.is_project_backed is False

    def test_verify_github_projects_with_link(self, sample_project_backed_candidate):
        audit = ProjectVerifier.verify_github_projects(
            sample_project_backed_candidate,
            claimed_skills=["React", "Python", "FastAPI", "PostgreSQL", "Docker"]
        )
        assert audit.github_url != ""
        assert audit.username == "johndoe"
        assert len(audit.repos) > 0
        assert audit.is_verified is True
        assert len(audit.skills_substantiated) > 0

    def test_verify_github_projects_without_link(self):
        cand_no_gh = CandidateProfile(
            id="cand_nogh",
            full_name="Jane Smith",
            email="jane@example.com",
            current_role="Developer",
            years_of_experience=3.0,
            raw_resume_text="Jane Smith resume without any git links.",
            claims=[Claim(skill_name="Python", is_verified=True)],
            repository_links=[]
        )
        audit = ProjectVerifier.verify_github_projects(cand_no_gh, ["Python"])
        assert audit.is_verified is False
        assert audit.github_url == ""
        assert "No GitHub" in audit.audit_verdict


class TestFullDomainScreeningIntegration:
    """Tests evaluating candidate against specific domain requisitions and generating shortlists."""

    def test_screening_against_frontend_role(self):
        req = get_frontend_requisition()
        cand = CandidateProfile(
            id="cand_fe",
            full_name="Frontend Specialist",
            email="fe@example.com",
            current_role="Senior UI Developer",
            years_of_experience=5.0,
            raw_resume_text="""
            Senior UI Developer
            GitHub: https://github.com/fe-specialist/react-tailwind-design-system
            
            • Built interactive React UI components and custom hooks using TypeScript.
            • Implemented Redux state management and optimized Core Web Vitals to 98.
            • Designed responsive layouts with Tailwind CSS.
            """,
            claims=[
                Claim(skill_name="React", is_verified=True, evidence_list=[Evidence(id="e1", type=EvidenceType.PROJECT_CODE, description="UI", proof_snippet="Built interactive React UI", confidence_score=0.9)]),
                Claim(skill_name="TypeScript", is_verified=True, evidence_list=[Evidence(id="e2", type=EvidenceType.PROJECT_CODE, description="TS", proof_snippet="custom hooks using TypeScript", confidence_score=0.9)]),
                Claim(skill_name="State Management", is_verified=True, evidence_list=[Evidence(id="e3", type=EvidenceType.PROJECT_CODE, description="Redux", proof_snippet="Implemented Redux state management", confidence_score=0.9)])
            ],
            repository_links=["https://github.com/fe-specialist/react-tailwind-design-system"]
        )

        res = TradeoffAnalyzer.evaluate_candidate(req, cand)
        assert res.score.overall_score >= 70.0
        assert res.project_verifications is not None
        assert res.github_audit is not None
        assert res.github_audit.is_verified is True

        matrix_rows = RequirementAnalyzer.evaluate_candidate_matrix(req, [cand], [res])
        assert len(matrix_rows) == 1
        shortlist = RequirementAnalyzer.generate_closest_fit_shortlist(req, [cand], matrix_rows, [res])
        assert len(shortlist) == 1
        assert shortlist[0].project_verifications is not None
        assert shortlist[0].github_audit is not None

