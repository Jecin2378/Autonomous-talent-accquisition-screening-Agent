"""
Domain Requisitions Factory.
Provides structured, realistic job requisitions across modern engineering domains:
- Full Stack Development
- Backend Development
- Frontend Development
- Cloud Engineering
- DevOps Engineering
- AI & MLOps Platform Engineering
"""

from typing import Dict, List
from models.schemas import (
    JobRequisition, Requirement, RequirementType, SkillCategory,
    ConstraintType
)
from data.sample_data import get_sample_requisition


def get_fullstack_requisition() -> JobRequisition:
    """Returns realistic Full Stack Software Engineer requisition."""
    return JobRequisition(
        id="REQ-FULLSTACK-2026",
        title="Full Stack Software Engineer",
        department="Product Engineering",
        experience_level="Mid-to-Senior (3+ Years)",
        max_salary=24.0,
        salary_currency="LPA",
        requirements=[
            Requirement(
                id="FS-1",
                title="React / Modern Frontend",
                description="Frontend component architecture, state management, and responsive web applications",
                category=SkillCategory.FRAMEWORKS,
                type=RequirementType.MUST_HAVE,
                min_years=3.0,
                weight=1.5
            ),
            Requirement(
                id="FS-2",
                title="Node.js / Python Backend",
                description="Server-side API architecture, async request handling, and authentication",
                category=SkillCategory.LANGUAGES,
                type=RequirementType.MUST_HAVE,
                min_years=3.0,
                weight=1.5
            ),
            Requirement(
                id="FS-3",
                title="PostgreSQL / Relational Database",
                description="Database schema design, query optimization, and transaction management",
                category=SkillCategory.DATABASE,
                type=RequirementType.MUST_HAVE,
                min_years=2.0,
                weight=1.3
            ),
            Requirement(
                id="FS-4",
                title="TypeScript",
                description="Type-safe full-stack application development across client and server",
                category=SkillCategory.LANGUAGES,
                type=RequirementType.PREFERRED,
                min_years=2.0,
                weight=1.0
            ),
            Requirement(
                id="FS-5",
                title="Cloud & Docker Deployment",
                description="Containerizing full-stack web applications and deploying to cloud environments",
                category=SkillCategory.INFRASTRUCTURE,
                type=RequirementType.PREFERRED,
                min_years=1.0,
                weight=1.0
            )
        ],
        raw_description="Seeking a Full Stack Engineer to build high-performance user interfaces and scalable backend APIs."
    )


def get_backend_requisition() -> JobRequisition:
    """Returns realistic Backend Systems Engineer requisition."""
    return JobRequisition(
        id="REQ-BACKEND-2026",
        title="Senior Backend Systems Engineer",
        department="Platform Engineering",
        experience_level="Senior (4+ Years)",
        max_salary=28.0,
        salary_currency="LPA",
        requirements=[
            Requirement(
                id="BE-1",
                title="Python Programming",
                description="High-throughput asynchronous backend services, business logic, and API servers",
                category=SkillCategory.LANGUAGES,
                type=RequirementType.MUST_HAVE,
                min_years=4.0,
                weight=1.5
            ),
            Requirement(
                id="BE-2",
                title="PostgreSQL & Database Optimization",
                description="Relational database modeling, query tuning, indexing, and connection pooling",
                category=SkillCategory.DATABASE,
                type=RequirementType.MUST_HAVE,
                min_years=3.0,
                weight=1.5
            ),
            Requirement(
                id="BE-3",
                title="REST & Microservice Architecture",
                description="Scalable RESTful API contracts, service separation, and robust error handling",
                category=SkillCategory.FRAMEWORKS,
                type=RequirementType.MUST_HAVE,
                min_years=3.0,
                weight=1.4
            ),
            Requirement(
                id="BE-4",
                title="Redis / Caching & Queues",
                description="High-speed caching layers, distributed locking, and message queue processing",
                category=SkillCategory.DATABASE,
                type=RequirementType.PREFERRED,
                min_years=2.0,
                weight=1.1
            ),
            Requirement(
                id="BE-5",
                title="Distributed Systems & Kafka",
                description="Event-driven streaming architectures and asynchronous worker pipelines",
                category=SkillCategory.INFRASTRUCTURE,
                type=RequirementType.PREFERRED,
                min_years=2.0,
                weight=1.0
            )
        ],
        raw_description="Backend engineer needed to scale distributed microservices, transaction processing, and database architectures."
    )


def get_frontend_requisition() -> JobRequisition:
    """Returns realistic Frontend Engineer requisition."""
    return JobRequisition(
        id="REQ-FRONTEND-2026",
        title="Senior Frontend Engineer",
        department="User Experience Engineering",
        experience_level="Senior (4+ Years)",
        max_salary=25.0,
        salary_currency="LPA",
        requirements=[
            Requirement(
                id="FE-1",
                title="React / UI Frameworks",
                description="Advanced React development, custom hooks, virtualized rendering, and component lifecycle",
                category=SkillCategory.FRAMEWORKS,
                type=RequirementType.MUST_HAVE,
                min_years=4.0,
                weight=1.5
            ),
            Requirement(
                id="FE-2",
                title="TypeScript / Modern JavaScript",
                description="Strict TypeScript typing, modern ES6+ features, and modular code architecture",
                category=SkillCategory.LANGUAGES,
                type=RequirementType.MUST_HAVE,
                min_years=3.0,
                weight=1.5
            ),
            Requirement(
                id="FE-3",
                title="State Management & Client Architecture",
                description="Complex application state, caching with React Query/Redux, and optimistic UI updates",
                category=SkillCategory.FRAMEWORKS,
                type=RequirementType.MUST_HAVE,
                min_years=3.0,
                weight=1.3
            ),
            Requirement(
                id="FE-4",
                title="CSS / Tailwind & Responsive Layouts",
                description="Pixel-perfect responsive design systems, cross-browser compatibility, and CSS architecture",
                category=SkillCategory.FRAMEWORKS,
                type=RequirementType.PREFERRED,
                min_years=2.0,
                weight=1.0
            ),
            Requirement(
                id="FE-5",
                title="Web Performance & Core Web Vitals",
                description="Lighthouse score optimization, code splitting, bundle reduction, and client-side profiling",
                category=SkillCategory.OTHER,
                type=RequirementType.PREFERRED,
                min_years=1.0,
                weight=1.0
            )
        ],
        raw_description="Senior frontend engineer to lead client architecture, UI component systems, and web application performance."
    )


def get_cloud_requisition() -> JobRequisition:
    """Returns realistic Cloud Infrastructure Architect requisition."""
    return JobRequisition(
        id="REQ-CLOUD-2026",
        title="Cloud Infrastructure Engineer",
        department="Cloud Platform Architecture",
        experience_level="Senior (4+ Years)",
        max_salary=30.0,
        salary_currency="LPA",
        requirements=[
            Requirement(
                id="CL-1",
                title="AWS Cloud Architecture",
                description="Production AWS architecture including VPC networking, IAM security, EC2, S3, and RDS",
                category=SkillCategory.INFRASTRUCTURE,
                type=RequirementType.MUST_HAVE,
                min_years=4.0,
                weight=1.5
            ),
            Requirement(
                id="CL-2",
                title="Terraform / Infrastructure as Code",
                description="Writing and maintaining declarative IaC modules for multi-account, multi-region deployments",
                category=SkillCategory.INFRASTRUCTURE,
                type=RequirementType.MUST_HAVE,
                min_years=3.0,
                weight=1.5
            ),
            Requirement(
                id="CL-3",
                title="Cloud Security & IAM Governance",
                description="Least-privilege IAM policies, KMS encryption, security groups, and audit logging",
                category=SkillCategory.INFRASTRUCTURE,
                type=RequirementType.MUST_HAVE,
                min_years=3.0,
                weight=1.3
            ),
            Requirement(
                id="CL-4",
                title="Docker & Container Services",
                description="Containerizing microservices and operating container workloads via AWS ECS or EKS",
                category=SkillCategory.INFRASTRUCTURE,
                type=RequirementType.PREFERRED,
                min_years=2.0,
                weight=1.1
            ),
            Requirement(
                id="CL-5",
                title="Serverless & Event-Driven Cloud",
                description="Designing serverless workflows using AWS Lambda, API Gateway, and SQS/SNS",
                category=SkillCategory.INFRASTRUCTURE,
                type=RequirementType.PREFERRED,
                min_years=1.0,
                weight=1.0
            )
        ],
        raw_description="Cloud engineer needed to design secure, highly available, cost-effective infrastructure on AWS using Terraform."
    )


def get_devops_requisition() -> JobRequisition:
    """Returns realistic Senior DevOps & Site Reliability requisition."""
    return JobRequisition(
        id="REQ-DEVOPS-2026",
        title="Senior DevOps & SRE Engineer",
        department="DevOps & Infrastructure",
        experience_level="Senior (4+ Years)",
        max_salary=28.0,
        salary_currency="LPA",
        requirements=[
            Requirement(
                id="DO-1",
                title="CI/CD Pipeline Automation",
                description="Building enterprise CI/CD pipelines with automated testing, staging gates, and security scans",
                category=SkillCategory.INFRASTRUCTURE,
                type=RequirementType.MUST_HAVE,
                min_years=4.0,
                weight=1.5
            ),
            Requirement(
                id="DO-2",
                title="Kubernetes / Cluster Administration",
                description="Managing production Kubernetes clusters, Helm package deployments, and rolling zero-downtime upgrades",
                category=SkillCategory.INFRASTRUCTURE,
                type=RequirementType.MUST_HAVE,
                min_years=3.0,
                weight=1.5
            ),
            Requirement(
                id="DO-3",
                title="Linux & Systems Automation",
                description="Linux system administration, network diagnostics, and scripting in Bash or Python",
                category=SkillCategory.INFRASTRUCTURE,
                type=RequirementType.MUST_HAVE,
                min_years=3.0,
                weight=1.4
            ),
            Requirement(
                id="DO-4",
                title="Prometheus & Grafana Observability",
                description="Setting up cluster metrics collection, custom alerting, dashboards, and log aggregation",
                category=SkillCategory.INFRASTRUCTURE,
                type=RequirementType.PREFERRED,
                min_years=2.0,
                weight=1.1
            ),
            Requirement(
                id="DO-5",
                title="Terraform / IaC",
                description="Automating cloud infrastructure provisioning for dev, staging, and production clusters",
                category=SkillCategory.INFRASTRUCTURE,
                type=RequirementType.PREFERRED,
                min_years=2.0,
                weight=1.0
            )
        ],
        raw_description="DevOps engineer to lead Kubernetes deployment automation, continuous delivery pipelines, and 99.99% system availability."
    )


def get_conflict_requisition() -> JobRequisition:
    """Returns sample requisition containing realistic requirement conflicts."""
    return JobRequisition(
        id="REQ-CONFLICT-DEMO",
        title="Junior AI Platform Associate (With Conflicts)",
        department="AI Infrastructure",
        experience_level="Junior-Level",
        max_salary=7.5,
        salary_currency="LPA",
        requirements=[
            Requirement(
                id="RC-1",
                title="Software Experience",
                description="5+ years software development experience required",
                category=SkillCategory.OTHER,
                min_years=5.0,
                type=RequirementType.MUST_HAVE,
                constraint_type=ConstraintType.NUMERIC_MIN
            ),
            Requirement(
                id="RC-2",
                title="Kubernetes",
                description="Production K8s cluster administration",
                category=SkillCategory.INFRASTRUCTURE,
                min_years=3.0,
                type=RequirementType.MUST_HAVE
            ),
            Requirement(
                id="RC-3",
                title="Python Programming",
                description="Python async services",
                category=SkillCategory.LANGUAGES,
                min_years=3.0,
                type=RequirementType.MUST_HAVE
            ),
            Requirement(
                id="RC-4",
                title="Salary Alignment",
                description="Salary ceiling <= 7.5 LPA",
                category=SkillCategory.OTHER,
                type=RequirementType.MUST_HAVE,
                constraint_type=ConstraintType.NUMERIC_MAX,
                target_value=7.5
            ),
            Requirement(
                id="RC-5",
                title="AWS",
                description="AWS infrastructure preferred",
                category=SkillCategory.INFRASTRUCTURE,
                type=RequirementType.PREFERRED
            )
        ],
        raw_description="Junior-level position seeking talent with 5+ years experience and K8s expertise under ₹7.5 LPA."
    )


DOMAIN_REQUISITIONS_MAP: Dict[str, JobRequisition] = {
    "🌐 Full Stack Development": get_fullstack_requisition(),
    "⚙️ Backend Development": get_backend_requisition(),
    "🎨 Frontend Development": get_frontend_requisition(),
    "☁️ Cloud Engineering": get_cloud_requisition(),
    "🚀 DevOps Engineering": get_devops_requisition(),
    "🤖 Senior AI Platform & MLOps (Standard)": get_sample_requisition(),
    "⚠️ Junior AI Associate (Requisition Conflict Demo)": get_conflict_requisition()
}


def get_available_domains() -> List[str]:
    """Returns ordered list of available recruiter domains."""
    return list(DOMAIN_REQUISITIONS_MAP.keys())


def get_requisition_by_domain(domain_name: str) -> JobRequisition:
    """Retrieves job requisition corresponding to selected domain key."""
    if domain_name in DOMAIN_REQUISITIONS_MAP:
        return DOMAIN_REQUISITIONS_MAP[domain_name]
    for k, v in DOMAIN_REQUISITIONS_MAP.items():
        if domain_name.lower() in k.lower():
            return v
    return get_backend_requisition()
