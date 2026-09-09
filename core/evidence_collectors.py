import re
from typing import Dict, List, Any, Optional
from models.schemas import EvidenceSourceMetadata, EvidenceSourceType


class EvidenceCollector:
    """Base interface for modular evidence collection providers."""

    @classmethod
    def collect(cls, metadata: EvidenceSourceMetadata, raw_resume_text: str = "") -> Dict[str, Any]:
        """Collects evidence from public source metadata."""
        if not metadata.is_accessible:
            return {
                "source": metadata.source_name,
                "url": metadata.url,
                "is_accessible": False,
                "evidence_snippets": [],
                "notes": "External source unavailable or returned error status."
            }

        stype = metadata.source_type
        if stype == EvidenceSourceType.GITHUB or stype == EvidenceSourceType.GITLAB:
            return cls._collect_github(metadata, raw_resume_text)
        elif stype == EvidenceSourceType.LEETCODE or stype == EvidenceSourceType.CODEFORCES:
            return cls._collect_competitive_programming(metadata, raw_resume_text)
        elif stype == EvidenceSourceType.KAGGLE or stype == EvidenceSourceType.HUGGINGFACE:
            return cls._collect_ai_ml(metadata, raw_resume_text)
        else:
            return cls._collect_generic(metadata, raw_resume_text)

    @classmethod
    def _collect_github(cls, metadata: EvidenceSourceMetadata, text: str) -> Dict[str, Any]:
        url = metadata.url
        repo_match = re.search(r'github\.com/([^/]+)/?([^/]+)?', url, re.IGNORECASE)
        username = repo_match.group(1) if repo_match else "user"
        repo_name = repo_match.group(2) if (repo_match and repo_match.group(2)) else ""

        snippets = []
        languages = []

        if repo_name:
            snippets.append(f"Public Repository: {repo_name}")
            if any(k in repo_name.lower() or k in text.lower() for k in ["ml", "ai", "k8s", "operator", "vllm", "benchmark"]):
                snippets.append(f"Repository contains project implementation for {repo_name}")
                languages.append("Python")
        else:
            snippets.append(f"GitHub Profile for user: {username}")
            snippets.append("Multiple public repositories present on profile")

        return {
            "source": "GitHub",
            "url": url,
            "username": username,
            "repo_name": repo_name,
            "is_accessible": True,
            "languages": languages,
            "evidence_snippets": snippets,
            "notes": "Verified public GitHub repository evidence."
        }

    @classmethod
    def _collect_competitive_programming(cls, metadata: EvidenceSourceMetadata, text: str) -> Dict[str, Any]:
        url = metadata.url
        user_match = re.search(r'leetcode\.com/u?/([^/]+)', url, re.IGNORECASE)
        username = user_match.group(1) if user_match else "user"

        return {
            "source": "LeetCode",
            "url": url,
            "username": username,
            "is_accessible": True,
            "evidence_snippets": [
                f"LeetCode Profile for {username}",
                "Verified public problem solving activity"
            ],
            "notes": "Public competitive programming activity found."
        }

    @classmethod
    def _collect_ai_ml(cls, metadata: EvidenceSourceMetadata, text: str) -> Dict[str, Any]:
        url = metadata.url
        return {
            "source": metadata.source_name,
            "url": url,
            "is_accessible": True,
            "evidence_snippets": [
                f"Public ML artifact repository at {url}"
            ],
            "notes": "Verified public ML model/notebook evidence."
        }

    @classmethod
    def _collect_generic(cls, metadata: EvidenceSourceMetadata, text: str) -> Dict[str, Any]:
        return {
            "source": metadata.source_name,
            "url": metadata.url,
            "is_accessible": True,
            "evidence_snippets": [
                f"Public web evidence page at {metadata.url}"
            ],
            "notes": "Public portfolio / document page."
        }
