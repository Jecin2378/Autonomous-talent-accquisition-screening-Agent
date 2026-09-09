import re
from typing import List, Tuple
from models.schemas import CandidateProfile, Claim, Evidence, EvidenceType
from core.skill_normalizer import SkillNormalizer


class EvidenceVerifier:
    """Evaluates candidate claims against concrete evidence to flag keyword spamming."""

    METRIC_PATTERN = re.compile(r'(\d+%\s*|\d+x\s*|\$\d+|\d+\s*nodes|\d+\s*ms|\d+\s*k|\d+\s*m|\d+\s*users|\d+\s*requests)', re.IGNORECASE)

    @classmethod
    def verify_candidate_profile(cls, candidate: CandidateProfile) -> Tuple[CandidateProfile, float, float]:
        """
        Verifies all claims in candidate profile.
        Returns: (Updated Profile, Evidence Density Score (0-100), Keyword Spam Penalty (0-50))
        """
        total_claims = len(candidate.claims)
        if total_claims == 0:
            # Generate claims automatically from raw resume text
            candidate.claims = cls._extract_claims_from_text(candidate.raw_resume_text)
            total_claims = len(candidate.claims)

        verified_count = 0
        total_evidence_weight = 0.0
        unsubstantiated_count = 0

        for claim in candidate.claims:
            norm_skill = SkillNormalizer.normalize(claim.skill_name)
            claim.skill_name = norm_skill

            # Check resume text for evidence if list is empty
            if not claim.evidence_list:
                claim.evidence_list = cls._find_evidence_in_text(norm_skill, candidate.raw_resume_text, candidate.repository_links)

            # Evaluate evidence quality
            valid_evidence = [e for e in claim.evidence_list if e.type != EvidenceType.UNSUBSTANTIATED_KEYWORD]
            
            if valid_evidence:
                claim.is_verified = True
                verified_count += 1
                best_confidence = max(e.confidence_score for e in valid_evidence)
                total_evidence_weight += best_confidence
                claim.verification_notes = f"Verified with {len(valid_evidence)} evidence proof snippet(s)."
            else:
                claim.is_verified = False
                unsubstantiated_count += 1
                claim.verification_notes = "ALERT: Claim listed as keyword without supporting project tenure or quantifiable evidence."
                if not claim.evidence_list:
                    claim.evidence_list.append(
                        Evidence(
                            id=f"UNSUB-{norm_skill}",
                            type=EvidenceType.UNSUBSTANTIATED_KEYWORD,
                            description="Unverified keyword claim",
                            proof_snippet=f"Skill '{norm_skill}' mentioned in summary without work history proof",
                            confidence_score=0.10
                        )
                    )

        evidence_density = (total_evidence_weight / max(total_claims, 1)) * 100.0
        spam_ratio = unsubstantiated_count / max(total_claims, 1)
        keyword_spam_penalty = spam_ratio * 40.0

        return candidate, round(evidence_density, 1), round(keyword_spam_penalty, 1)

    @classmethod
    def _extract_claims_from_text(cls, text: str) -> List[Claim]:
        skills = SkillNormalizer.extract_canonical_skills(text)
        claims = []
        for s in skills:
            claims.append(Claim(skill_name=s, claimed_years=1.0))
        return claims

    @classmethod
    def _find_evidence_in_text(cls, skill: str, text: str, repo_links: List[str]) -> List[Evidence]:
        evidence_items = []
        lines = text.split("\n")

        for idx, line in enumerate(lines):
            lowered = line.lower()
            # Match using SkillNormalizer.are_equivalent
            if SkillNormalizer.are_equivalent(skill, line) or skill.lower() in lowered:
                has_metric = bool(cls.METRIC_PATTERN.search(line))
                
                if has_metric:
                    evidence_items.append(
                        Evidence(
                            id=f"EV-METRIC-{idx}",
                            type=EvidenceType.METRIC_IMPACT,
                            description=f"Quantifiable impact snippet for {skill}",
                            proof_snippet=line.strip(),
                            confidence_score=0.95
                        )
                    )
                else:
                    evidence_items.append(
                        Evidence(
                            id=f"EV-TENURE-{idx}",
                            type=EvidenceType.TENURE_WORK_HISTORY,
                            description=f"Work history implementation for {skill}",
                            proof_snippet=line.strip(),
                            confidence_score=0.85
                        )
                    )

        for repo in repo_links:
            if SkillNormalizer.are_equivalent(skill, repo) or skill.lower() in repo.lower():
                evidence_items.append(
                    Evidence(
                        id=f"EV-REPO-{len(evidence_items)}",
                        type=EvidenceType.GITHUB_REPO,
                        description=f"Open-source repository evidence for {skill}",
                        proof_snippet=repo,
                        confidence_score=0.90
                    )
                )

        return evidence_items
