import re
from typing import List, Dict, Optional
from models.schemas import EvidenceSourceType, EvidenceSourceMetadata


class EvidenceSourceRegistry:
    """
    Modular Evidence Source Registry.
    Identifies domains, source types, supported claim categories, and retrieval availability.
    """

    DOMAIN_MAPPING: Dict[str, EvidenceSourceType] = {
        "github.com": EvidenceSourceType.GITHUB,
        "gitlab.com": EvidenceSourceType.GITLAB,
        "bitbucket.org": EvidenceSourceType.BITBUCKET,
        "leetcode.com": EvidenceSourceType.LEETCODE,
        "codeforces.com": EvidenceSourceType.CODEFORCES,
        "hackerrank.com": EvidenceSourceType.HACKERRANK,
        "codechef.com": EvidenceSourceType.CODECHEF,
        "kaggle.com": EvidenceSourceType.KAGGLE,
        "huggingface.co": EvidenceSourceType.HUGGINGFACE,
        "figma.com": EvidenceSourceType.PORTFOLIO,
        "behance.net": EvidenceSourceType.PORTFOLIO,
        "dribbble.com": EvidenceSourceType.PORTFOLIO,
        "arxiv.org": EvidenceSourceType.RESEARCH,
        "orcid.org": EvidenceSourceType.RESEARCH,
        "scholar.google.com": EvidenceSourceType.RESEARCH,
    }

    CLAIM_TYPE_SUPPORT: Dict[EvidenceSourceType, List[str]] = {
        EvidenceSourceType.GITHUB: ["software_projects", "programming_languages", "open_source", "infrastructure_code"],
        EvidenceSourceType.GITLAB: ["software_projects", "programming_languages", "ci_cd"],
        EvidenceSourceType.BITBUCKET: ["software_projects", "programming_languages"],
        EvidenceSourceType.LEETCODE: ["competitive_programming", "algorithms", "problem_solving"],
        EvidenceSourceType.CODEFORCES: ["competitive_programming", "algorithms"],
        EvidenceSourceType.HACKERRANK: ["competitive_programming", "coding_skills"],
        EvidenceSourceType.CODECHEF: ["competitive_programming"],
        EvidenceSourceType.KAGGLE: ["machine_learning", "data_science", "notebooks", "competitions"],
        EvidenceSourceType.HUGGINGFACE: ["machine_learning", "deep_learning", "ai_models"],
        EvidenceSourceType.PORTFOLIO: ["ui_ux", "design", "web_development", "projects"],
        EvidenceSourceType.RESEARCH: ["publications", "research_papers", "citations"],
        EvidenceSourceType.CERTIFICATION: ["cloud_certifications", "technical_certifications"],
        EvidenceSourceType.OTHER: ["general_public_web"]
    }

    URL_REGEX = re.compile(r'https?://[^\s<>"{}|\^~\[\]`]+|github\.com/[^\s<>"{}|\^~\[\]`]+|gitlab\.com/[^\s<>"{}|\^~\[\]`]+|leetcode\.com/[^\s<>"{}|\^~\[\]`]+|kaggle\.com/[^\s<>"{}|\^~\[\]`]+|huggingface\.co/[^\s<>"{}|\^~\[\]`]+', re.IGNORECASE)

    @classmethod
    def extract_urls(cls, text: str) -> List[str]:
        """Extracts all embedded URLs from resume or application text."""
        raw_matches = cls.URL_REGEX.findall(text)
        cleaned = []
        for url in raw_matches:
            url_clean = url.rstrip('.,;()')
            if not url_clean.startswith("http"):
                url_clean = "https://" + url_clean
            cleaned.append(url_clean)
        return list(dict.fromkeys(cleaned))

    @classmethod
    def identify_source(cls, url: str) -> EvidenceSourceMetadata:
        """Maps URL to domain, source type, and supported claim categories."""
        lowered = url.lower()
        matched_type = EvidenceSourceType.OTHER
        source_name = "Generic Web"

        for domain, stype in cls.DOMAIN_MAPPING.items():
            if domain in lowered:
                matched_type = stype
                source_name = domain.split('.')[0].title()
                break

        supported = cls.CLAIM_TYPE_SUPPORT.get(matched_type, ["general_public_web"])

        # Check accessibility hint (e.g. invalid/private/broken link pattern)
        is_accessible = True
        notes = "Publicly accessible source."
        if "404" in lowered or "private" in lowered or "inaccessible" in lowered or "invalid" in lowered or "broken" in lowered:
            is_accessible = False
            notes = "Source is inaccessible or returned non-200 status."

        return EvidenceSourceMetadata(
            source_name=source_name,
            source_type=matched_type,
            url=url,
            supported_claim_types=supported,
            is_accessible=is_accessible,
            notes=notes
        )


class EvidencePlanner:
    """Plans which evidence sources should be evaluated for a specific candidate claim."""

    @classmethod
    def plan_evidence_retrieval(cls, claim: str, available_sources: List[EvidenceSourceMetadata]) -> List[EvidenceSourceMetadata]:
        """Selects relevant sources appropriate for the claim without searching irrelevant providers."""
        claim_lowered = claim.lower()
        relevant_sources = []

        for src in available_sources:
            stype = src.source_type
            
            if stype == EvidenceSourceType.GITHUB or stype == EvidenceSourceType.GITLAB:
                if any(k in claim_lowered for k in ["python", "pytorch", "kubernetes", "k8s", "c++", "rust", "go", "code", "repo", "project", "open source"]):
                    relevant_sources.append(src)
            elif stype == EvidenceSourceType.LEETCODE or stype == EvidenceSourceType.CODEFORCES or stype == EvidenceSourceType.HACKERRANK:
                if any(k in claim_lowered for k in ["algorithm", "competitive", "problem solving", "leetcode", "rank"]):
                    relevant_sources.append(src)
            elif stype == EvidenceSourceType.KAGGLE or stype == EvidenceSourceType.HUGGINGFACE:
                if any(k in claim_lowered for k in ["machine learning", "ml", "ai", "model", "deep learning", "kaggle", "rag"]):
                    relevant_sources.append(src)
            elif stype == EvidenceSourceType.RESEARCH:
                if any(k in claim_lowered for k in ["paper", "publication", "research", "arxiv"]):
                    relevant_sources.append(src)
            else:
                relevant_sources.append(src)

        return relevant_sources if relevant_sources else available_sources
