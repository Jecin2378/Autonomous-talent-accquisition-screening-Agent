"""
Sample dataset generator for hackathon demo.
Provides pre-populated job requisitions and candidate profiles with contrasting evidence profiles.
"""

from typing import List
from models.schemas import (
    JobRequisition, Requirement, RequirementType, SkillCategory,
    CandidateProfile, Claim, Evidence, EvidenceType
)


def get_sample_requisition() -> JobRequisition:
    """Returns a realistic Senior AI/ML Platform Engineer requisition."""
    return JobRequisition(
        id="REQ-AI-2026",
        title="Senior AI Platform & MLOps Engineer",
        department="AI Infrastructure",
        experience_level="Senior (5+ Years)",
        raw_description="""
We are seeking a Senior AI Platform Engineer to build scalable distributed training and inference pipelines.

Key Responsibilities:
- Design and maintain Kubernetes-based ML model deployment clusters.
- Build Python & PyTorch model pipelines with automated monitoring.
- Optimize PostgreSQL & Vector DB queries for real-time RAG services.
- Implement CI/CD pipelines with high test coverage and observability.

Requirements:
- MUST HAVE: Python (4+ years), PyTorch/TensorFlow (3+ years), Kubernetes/K8s (3+ years).
- MUST HAVE: Demonstrated evidence of high-scale production deployment (e.g. latency metrics, cluster sizes).
- PREFERRED: Vector Databases (Qdrant, Milvus, PGVector), FastAPI, Distributed Training (Ray/Deepspeed).
""",
        requirements=[
            Requirement(
                id="REQ-1",
                title="Python Programming",
                description="Advanced Python development with async frameworks",
                category=SkillCategory.LANGUAGES,
                type=RequirementType.MUST_HAVE,
                min_years=4.0,
                weight=1.5
            ),
            Requirement(
                id="REQ-2",
                title="PyTorch / Deep Learning",
                description="Model fine-tuning and inference pipeline architecture",
                category=SkillCategory.FRAMEWORKS,
                type=RequirementType.MUST_HAVE,
                min_years=3.0,
                weight=1.5
            ),
            Requirement(
                id="REQ-3",
                title="Kubernetes / Infrastructure",
                description="K8s cluster management, Helm charts, and container orchestration",
                category=SkillCategory.INFRASTRUCTURE,
                type=RequirementType.MUST_HAVE,
                min_years=3.0,
                weight=1.5
            ),
            Requirement(
                id="REQ-4",
                title="Vector Database & RAG",
                description="Experience with PGVector, Qdrant, or Milvus search indexing",
                category=SkillCategory.DATABASE,
                type=RequirementType.PREFERRED,
                min_years=1.0,
                weight=1.0
            ),
            Requirement(
                id="REQ-5",
                title="Distributed Training (Ray/DeepSpeed)",
                description="Multi-GPU model orchestration and memory optimization",
                category=SkillCategory.FRAMEWORKS,
                type=RequirementType.PREFERRED,
                min_years=1.0,
                weight=1.0
            )
        ]
    )


def get_sample_candidates() -> List[CandidateProfile]:
    """Returns 4 contrasting candidate profiles for demonstration."""
    return [
        # Candidate 1: Verified Evidence-Backed Senior
        CandidateProfile(
            id="CAND-001",
            full_name="Alex Chen",
            email="alex.chen@dev.io",
            current_role="Staff MLOps Lead",
            years_of_experience=6.0,
            repository_links=["https://github.com/alexchen/ml-k8s-operator", "https://github.com/alexchen/vllm-benchmark"],
            raw_resume_text="""
Alex Chen - Staff MLOps Lead
6 years of production machine learning experience.

EXPERIENCE:
Staff MLOps Engineer | Nexus Tech (2022 - Present)
- Architected Kubernetes multi-region cluster (50+ nodes) serving 120M inference requests/day with 99.98% uptime.
- Optimized PyTorch model serving pipelines using vLLM, reducing P99 latency from 140ms to 32ms.
- Integrated PGVector database for enterprise retrieval pipeline, scaling to 10M embedding vectors.

Senior Backend Engineer | DataCorp (2020 - 2022)
- Built Python (FastAPI/AsyncIO) ingestion services handling 50k events/sec.
- Managed Docker and Kubernetes deployments across 4 staging/prod environments.

PROJECTS:
- Open-Source PyTorch Kubernetes Operator: 1.4k GitHub stars.
- Benchmark Suite for LLM Quantization.
""",
            claims=[
                Claim(
                    skill_name="Python",
                    claimed_years=6.0,
                    is_verified=True,
                    evidence_list=[
                        Evidence(
                            id="EV-101",
                            type=EvidenceType.TENURE_WORK_HISTORY,
                            description="6 years continuous professional tenure",
                            proof_snippet="Staff MLOps Engineer (2022-Present), Senior Backend Engineer (2020-2022)",
                            confidence_score=0.95
                        ),
                        Evidence(
                            id="EV-102",
                            type=EvidenceType.PROJECT_CODE,
                            description="Built Python FastAPI async ingestion services at 50k events/sec",
                            proof_snippet="Built Python (FastAPI/AsyncIO) ingestion services handling 50k events/sec",
                            confidence_score=0.98
                        )
                    ]
                ),
                Claim(
                    skill_name="PyTorch",
                    claimed_years=4.0,
                    is_verified=True,
                    evidence_list=[
                        Evidence(
                            id="EV-103",
                            type=EvidenceType.METRIC_IMPACT,
                            description="Reduced PyTorch inference P99 latency from 140ms to 32ms",
                            proof_snippet="Optimized PyTorch model serving pipelines using vLLM, reducing P99 latency from 140ms to 32ms",
                            confidence_score=0.98
                        ),
                        Evidence(
                            id="EV-104",
                            type=EvidenceType.GITHUB_REPO,
                            description="Created Open-Source PyTorch K8s Operator with 1.4k stars",
                            proof_snippet="https://github.com/alexchen/ml-k8s-operator",
                            confidence_score=0.95
                        )
                    ]
                ),
                Claim(
                    skill_name="Kubernetes",
                    claimed_years=5.0,
                    is_verified=True,
                    evidence_list=[
                        Evidence(
                            id="EV-105",
                            type=EvidenceType.METRIC_IMPACT,
                            description="Managed 50+ node multi-region K8s cluster serving 120M requests/day",
                            proof_snippet="Architected Kubernetes multi-region cluster (50+ nodes) serving 120M inference requests/day",
                            confidence_score=0.99
                        )
                    ]
                ),
                Claim(
                    skill_name="PGVector / Vector DB",
                    claimed_years=2.0,
                    is_verified=True,
                    evidence_list=[
                        Evidence(
                            id="EV-106",
                            type=EvidenceType.PROJECT_CODE,
                            description="Integrated PGVector database for 10M embeddings",
                            proof_snippet="Integrated PGVector database for enterprise retrieval pipeline, scaling to 10M embedding vectors",
                            confidence_score=0.92
                        )
                    ]
                )
            ]
        ),

        # Candidate 2: Keyword Spammer (Unsubstantiated Claims)
        CandidateProfile(
            id="CAND-002",
            full_name="Bradley Vance",
            email="bradley.vance@techgurus.net",
            current_role="Technology Consultant",
            years_of_experience=5.0,
            repository_links=[],
            raw_resume_text="""
Bradley Vance - Senior Technology Consultant & AI Specialist

SKILLS SUMMARY:
Python, PyTorch, TensorFlow, Kubernetes, K8s, Docker, Ray, DeepSpeed, PGVector, Qdrant, Milvus, Rust, C++, Apache Spark, Quantum Machine Learning, LLM Fine-Tuning, Distributed Systems, ML Ops.

EXPERIENCE:
Technology Consultant | Global IT Advisory (2021 - Present)
- Attended weekly strategy sessions regarding AI adoption.
- Researched industry trends in PyTorch, Kubernetes, and Cloud technologies.
- Prepared slide decks summarizing technology landscapes.

IT Support Analyst | Systems Corp (2019 - 2021)
- Managed internal ticket queues and desktop setup.
- Configured network printers and user access permissions.
""",
            claims=[
                Claim(
                    skill_name="Python",
                    claimed_years=5.0,
                    is_verified=False,
                    verification_notes="Claimed in skills header, but work history only references slide deck creation",
                    evidence_list=[
                        Evidence(
                            id="EV-201",
                            type=EvidenceType.UNSUBSTANTIATED_KEYWORD,
                            description="Keyword listed in summary without project evidence or code artifacts",
                            proof_snippet="SKILLS SUMMARY: Python, PyTorch, TensorFlow...",
                            confidence_score=0.20
                        )
                    ]
                ),
                Claim(
                    skill_name="PyTorch",
                    claimed_years=4.0,
                    is_verified=False,
                    verification_notes="Unsubstantiated claim. Only researched trends, no hands-on code",
                    evidence_list=[
                        Evidence(
                            id="EV-202",
                            type=EvidenceType.UNSUBSTANTIATED_KEYWORD,
                            description="No evidence of model training, fine-tuning, or code repos",
                            proof_snippet="Researched industry trends in PyTorch...",
                            confidence_score=0.15
                        )
                    ]
                ),
                Claim(
                    skill_name="Kubernetes",
                    claimed_years=4.0,
                    is_verified=False,
                    verification_notes="Unverified keyword listing without cluster management experience",
                    evidence_list=[]
                )
            ]
        ),

        # Candidate 3: Equivalent Skill Terminology (Normalizable)
        CandidateProfile(
            id="CAND-003",
            full_name="Maria Garcia",
            email="maria.garcia@ai-labs.org",
            current_role="Senior Infrastructure Engineer",
            years_of_experience=5.5,
            repository_links=["https://github.com/mgarcia/torch-cluster-scaling"],
            raw_resume_text="""
Maria Garcia - Senior Infrastructure Engineer

EXPERIENCE:
Senior Cloud Engineer | CloudScale Inc (2022 - Present)
- Deployed Torch deep learning models on microservice clusters using K8s and Helm.
- Maintained PostgreSQL with pgvector extension for high-performance semantic search indexing.
- Automated python script pipelines for GPU memory profiling.

Systems Engineer | NextGen Solutions (2019 - 2022)
- Managed Linux server infrastructure and containerized workloads with Docker and K8s.
""",
            claims=[
                Claim(
                    skill_name="Python",
                    claimed_years=5.5,
                    is_verified=True,
                    evidence_list=[
                        Evidence(
                            id="EV-301",
                            type=EvidenceType.PROJECT_CODE,
                            description="Automated Python profiling scripts across GPU workloads",
                            proof_snippet="Automated python script pipelines for GPU memory profiling",
                            confidence_score=0.90
                        )
                    ]
                ),
                Claim(
                    skill_name="Torch", # Synonym for PyTorch
                    claimed_years=3.5,
                    is_verified=True,
                    evidence_list=[
                        Evidence(
                            id="EV-302",
                            type=EvidenceType.PROJECT_CODE,
                            description="Deployed Torch deep learning models on microservice clusters",
                            proof_snippet="Deployed Torch deep learning models on microservice clusters using K8s and Helm",
                            confidence_score=0.92
                        )
                    ]
                ),
                Claim(
                    skill_name="K8s", # Synonym for Kubernetes
                    claimed_years=4.5,
                    is_verified=True,
                    evidence_list=[
                        Evidence(
                            id="EV-303",
                            type=EvidenceType.TENURE_WORK_HISTORY,
                            description="Managed containerized workloads with K8s and Helm across 4+ years",
                            proof_snippet="Deployed Torch models... using K8s and Helm",
                            confidence_score=0.94
                        )
                    ]
                )
            ]
        ),

        # Candidate 4: Junior / High Potential Trade-off Candidate
        CandidateProfile(
            id="CAND-004",
            full_name="David Kim",
            email="david.kim@stanford.edu",
            current_role="Junior ML Engineer",
            years_of_experience=2.0,
            repository_links=["https://github.com/davidkim/ray-deepspeed-benchmarks"],
            raw_resume_text="""
David Kim - Junior ML Engineer

EXPERIENCE:
Machine Learning Engineer | AI Research Startup (2024 - Present)
- Benchmarked distributed training pipelines using Ray and DeepSpeed across 8x H100 GPU nodes.
- Fine-tuned PyTorch open-weight LLMs (Llama 3, Mistral) with FlashAttention-2.
- Written Python data parsers for clean training data generation.

EDUCATION:
B.S. in Computer Science | Stanford University (2024)
- Published paper on Distributed LLM Training Optimization.
""",
            claims=[
                Claim(
                    skill_name="Python",
                    claimed_years=2.0,
                    is_verified=True,
                    evidence_list=[
                        Evidence(
                            id="EV-401",
                            type=EvidenceType.PROJECT_CODE,
                            description="Written Python data parsers for training data generation",
                            proof_snippet="Written Python data parsers for clean training data generation",
                            confidence_score=0.88
                        )
                    ]
                ),
                Claim(
                    skill_name="PyTorch",
                    claimed_years=2.0,
                    is_verified=True,
                    evidence_list=[
                        Evidence(
                            id="EV-402",
                            type=EvidenceType.PROJECT_CODE,
                            description="Fine-tuned PyTorch LLMs with FlashAttention-2",
                            proof_snippet="Fine-tuned PyTorch open-weight LLMs (Llama 3, Mistral) with FlashAttention-2",
                            confidence_score=0.90
                        )
                    ]
                ),
                Claim(
                    skill_name="Distributed Training (Ray/DeepSpeed)",
                    claimed_years=1.5,
                    is_verified=True,
                    evidence_list=[
                        Evidence(
                            id="EV-403",
                            type=EvidenceType.PUBLICATION,
                            description="Published paper & benchmark repo on Ray + DeepSpeed multi-GPU optimization",
                            proof_snippet="Benchmarked distributed training pipelines using Ray and DeepSpeed across 8x H100 GPU nodes",
                            confidence_score=0.96
                        )
                    ]
                )
            ]
        )
    ]
