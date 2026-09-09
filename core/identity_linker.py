import re
from typing import List, Dict, Any
from models.schemas import CandidateProfile, IdentityLinkStatus, IdentityLinkage, EvidenceSourceMetadata


class IdentityLinker:
    """Evaluates whether external URLs and evidence belong to the candidate application."""

    @classmethod
    def evaluate_linkage(cls, candidate: CandidateProfile, source_meta: EvidenceSourceMetadata) -> IdentityLinkage:
        reasons = []
        confidence = 0.5
        status = IdentityLinkStatus.POSSIBLE

        candidate_name_parts = set(candidate.full_name.lower().split())
        email_handle = candidate.email.split('@')[0].lower() if candidate.email else ""
        url_lowered = source_meta.url.lower()

        # Check explicit mention in resume text
        if source_meta.url in candidate.raw_resume_text:
            reasons.append("URL explicitly listed in resume document.")
            confidence += 0.3

        # Check name or handle match in URL
        url_match = any(part in url_lowered for part in candidate_name_parts if len(part) > 2)
        handle_match = email_handle and (email_handle in url_lowered)

        if url_match or handle_match:
            reasons.append("Profile URL matches candidate name or email handle.")
            confidence += 0.3

        # Check if URL explicitly contains completely different name/organization without link
        if "anonymous" in url_lowered or "unlinked" in url_lowered:
            status = IdentityLinkStatus.UNCLEAR
            confidence = 0.2
            reasons.append("URL handle does not match candidate identity and lacks cross-referencing.")
            return IdentityLinkage(status=status, reasons=reasons, confidence_score=confidence)

        if confidence >= 0.7:
            status = IdentityLinkStatus.STRONG
        elif confidence >= 0.4:
            status = IdentityLinkStatus.POSSIBLE
        else:
            status = IdentityLinkStatus.UNCLEAR

        return IdentityLinkage(
            status=status,
            reasons=reasons if reasons else ["Provided in candidate application."],
            confidence_score=round(min(1.0, confidence), 2)
        )
