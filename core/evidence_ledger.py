from typing import List, Dict, Any
from models.schemas import (
    CandidateProfile, EvidenceLedgerEntry, EvidenceState,
    IdentityLinkStatus, IdentityLinkage, EvidenceSourceMetadata
)
from core.evidence_registry import EvidenceSourceRegistry, EvidencePlanner
from core.evidence_collectors import EvidenceCollector
from core.identity_linker import IdentityLinker
from core.skill_normalizer import SkillNormalizer


class EvidenceLedgerBuilder:
    """
    Central Evidence Ledger Generator.
    Extracts embedded URLs, maps sources, collects public evidence, checks identity linkage,
    and produces traceable Evidence Ledger entries for candidate claims.
    """

    @classmethod
    def build_ledger(cls, candidate: CandidateProfile) -> List[EvidenceLedgerEntry]:
        ledger_entries: List[EvidenceLedgerEntry] = []

        # 1. Extract embedded URLs from resume & profile links
        extracted_urls = EvidenceSourceRegistry.extract_urls(candidate.raw_resume_text)
        all_urls = list(set(extracted_urls + candidate.repository_links))

        # 2. Identify Sources
        source_metas: List[EvidenceSourceMetadata] = [
            EvidenceSourceRegistry.identify_source(u) for u in all_urls
        ]

        # Process each candidate claim
        for claim in candidate.claims:
            claim_name = SkillNormalizer.normalize(claim.skill_name)
            
            # Plan sources
            planned_sources = EvidencePlanner.plan_evidence_retrieval(claim_name, source_metas)
            
            collected_sources_info = []
            has_supported_evidence = False
            has_unaccessible = False
            unclear_identity = False
            has_contradiction = False
            
            # Collect evidence from internal resume
            resume_evidence = [e for e in claim.evidence_list if e.confidence_score >= 0.70]
            if resume_evidence:
                collected_sources_info.append({
                    "source": "resume",
                    "text": resume_evidence[0].proof_snippet
                })
                has_supported_evidence = True

            # Collect evidence from planned external sources
            linkage_result = IdentityLinkage(status=IdentityLinkStatus.STRONG, reasons=["Resume internal"], confidence_score=1.0)

            for src_meta in planned_sources:
                if not src_meta.is_accessible:
                    has_unaccessible = True
                    collected_sources_info.append({
                        "source": src_meta.source_name,
                        "text": f"URL {src_meta.url} returned status unavailable"
                    })
                    continue

                # Check identity linkage
                linkage = IdentityLinker.evaluate_linkage(candidate, src_meta)
                linkage_result = linkage

                if linkage.status == IdentityLinkStatus.UNCLEAR:
                    unclear_identity = True
                    collected_sources_info.append({
                        "source": src_meta.source_name,
                        "text": f"Unverified: URL {src_meta.url} could not be confidently linked to candidate name"
                    })
                    continue

                # Collect public evidence
                ev_data = EvidenceCollector.collect(src_meta, candidate.raw_resume_text)
                for snippet in ev_data.get("evidence_snippets", []):
                    collected_sources_info.append({
                        "source": src_meta.source_name.lower(),
                        "text": snippet
                    })
                    has_supported_evidence = True

            # Determine Evidence State
            if not claim.is_verified and not has_supported_evidence:
                if has_unaccessible or unclear_identity:
                    state = EvidenceState.UNVERIFIED
                    reasoning = "External source is inaccessible or unlinked; claim marked unverified without candidate penalty."
                else:
                    state = EvidenceState.CONTRADICTORY_UNSUPPORTED
                    reasoning = "Claim lacks supporting professional or project evidence in candidate application."
            elif unclear_identity and not resume_evidence:
                state = EvidenceState.UNVERIFIED
                reasoning = "External evidence identity linkage is unclear."
            else:
                state = EvidenceState.SUPPORTED
                reasoning = f"Claim supported by {len(collected_sources_info)} verified evidence item(s)."

            ledger_entries.append(
                EvidenceLedgerEntry(
                    claim=claim_name,
                    sources=collected_sources_info if collected_sources_info else [{"source": "resume", "text": "Claim listed in skills summary"}],
                    assessment=state,
                    confidence="high" if state == EvidenceState.SUPPORTED else "reduced",
                    identity_linkage=linkage_result,
                    reasoning=reasoning
                )
            )

        return ledger_entries
