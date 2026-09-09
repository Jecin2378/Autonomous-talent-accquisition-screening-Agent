from typing import List
from models.schemas import (
    JobRequisition, CandidateProfile, RequirementType,
    EvaluationResult, CandidateScore, CandidateTradeoff
)
from core.skill_normalizer import SkillNormalizer
from core.evidence_verifier import EvidenceVerifier
from core.contradiction_detector import ContradictionDetector
from core.evidence_ledger import EvidenceLedgerBuilder


class TradeoffAnalyzer:
    """Evaluates candidate fit, multi-dimensional trade-offs, and explainable scorecards."""

    @classmethod
    def evaluate_candidate(cls, requisition: JobRequisition, candidate: CandidateProfile) -> EvaluationResult:
        """Runs full evidence verification, contradiction detection, evidence ledgering, and trade-off scoring."""

        # 1. Evidence Verification & Keyword Spam Check
        verified_candidate, evidence_density, spam_penalty = EvidenceVerifier.verify_candidate_profile(candidate)

        # 2. Contradiction & Unsupported Claim Detection
        contradictions = ContradictionDetector.analyze_candidate(verified_candidate)

        # 3. Build Central Evidence Ledger
        evidence_ledger = EvidenceLedgerBuilder.build_ledger(verified_candidate)

        # 4. Extract Candidate Verified & Unverified Skills
        verified_skills = set()
        unverified_skills = set()

        for claim in verified_candidate.claims:
            norm = SkillNormalizer.normalize(claim.skill_name)
            if claim.is_verified:
                verified_skills.add(norm)
            else:
                unverified_skills.add(norm)

        # 5. Requisition Matching
        must_haves = [r for r in requisition.requirements if r.type == RequirementType.MUST_HAVE]
        preferreds = [r for r in requisition.requirements if r.type == RequirementType.PREFERRED]

        missing_must_haves = []
        satisfied_must_haves = []

        for req in must_haves:
            req_norm = SkillNormalizer.normalize(req.title)
            is_matched = any(SkillNormalizer.are_equivalent(req_norm, s) for s in verified_skills)
            if is_matched:
                satisfied_must_haves.append(req.title)
            else:
                missing_must_haves.append(req.title)

        missing_preferred = []
        satisfied_preferred = []

        for req in preferreds:
            req_norm = SkillNormalizer.normalize(req.title)
            is_matched = any(SkillNormalizer.are_equivalent(req_norm, s) for s in verified_skills)
            if is_matched:
                satisfied_preferred.append(req.title)
            else:
                missing_preferred.append(req.title)

        # 6. Score Calculation
        must_have_match_pct = (len(satisfied_must_haves) / max(len(must_haves), 1)) * 100.0
        preferred_match_pct = (len(satisfied_preferred) / max(len(preferreds), 1)) * 100.0 if preferreds else 100.0
        
        requirement_match_score = (must_have_match_pct * 0.75) + (preferred_match_pct * 0.25)
        tenure_score = min(candidate.years_of_experience / 5.0, 1.0) * 100.0
        contradiction_penalty = len(contradictions) * 10.0

        raw_overall = (requirement_match_score * 0.50) + (evidence_density * 0.35) + (tenure_score * 0.15)
        final_overall = max(0.0, min(100.0, raw_overall - spam_penalty - contradiction_penalty))

        score_obj = CandidateScore(
            overall_score=round(final_overall, 1),
            evidence_density_score=round(evidence_density, 1),
            requirement_match_score=round(requirement_match_score, 1),
            skill_depth_score=round(tenure_score, 1),
            keyword_spam_penalty=round(spam_penalty, 1)
        )

        # 7. Trade-off Analysis & Contradiction Rationale
        strengths = []
        trade_off_risks = []

        if must_have_match_pct == 100.0:
            strengths.append("Satisfies 100% of mandatory role requirements with verified proof.")
        else:
            trade_off_risks.append(f"Missing {len(missing_must_haves)} mandatory requirement(s): {', '.join(missing_must_haves)}.")

        if evidence_density >= 85.0:
            strengths.append(f"High evidence density ({evidence_density}%): backed by metrics, tenure, or repo code.")
        elif evidence_density < 50.0:
            trade_off_risks.append(f"Low evidence density ({evidence_density}%): multiple unsubstantiated keyword claims detected.")

        if candidate.years_of_experience < 3.0 and final_overall > 70.0:
            strengths.append("High Potential / Junior candidate with strong project execution density.")
            trade_off_risks.append("Shorter overall professional tenure (under 3 years).")

        if spam_penalty > 15.0:
            trade_off_risks.append(f"Penalized (-{spam_penalty} pts) due to unverified keyword padding.")

        for c in contradictions:
            trade_off_risks.append(f"⚠️ {c.type}: {c.assessment}")

        summary_verdict = (
            f"{candidate.full_name} scores {final_overall}/100. "
            f"Satisfies {len(satisfied_must_haves)}/{len(must_haves)} Must-Haves. "
            f"{len(contradictions)} contradiction flag(s) detected. "
            f"{len(evidence_ledger)} Evidence Ledger entry(ies) recorded."
        )

        tradeoff_obj = CandidateTradeoff(
            candidate_id=candidate.id,
            candidate_name=candidate.full_name,
            key_strengths=strengths if strengths else ["Basic profile eligibility."],
            trade_off_risks=trade_off_risks if trade_off_risks else ["No significant trade-off risks identified."],
            summary_verdict=summary_verdict
        )

        contradiction_text = ""
        if contradictions:
            contradiction_text = "\n### 🚨 Contradiction & Unsupported Claim Flags:\n"
            for idx, c in enumerate(contradictions, 1):
                ev_str = "; ".join(f"[{e.source}] {e.text}" for e in c.evidence)
                contradiction_text += f"{idx}. **{c.flag}** ({c.type})\n   - **Claim**: {c.claim}\n   - **Evidence**: {ev_str}\n   - **Assessment**: {c.assessment}\n"

        explainable_rationale = (
            f"### Evaluation Rationale for {candidate.full_name}\n"
            f"- **Overall Match**: {final_overall}/100 | **Evidence Density**: {evidence_density}%\n"
            f"- **Verified Core Skills**: {', '.join(verified_skills) if verified_skills else 'None'}\n"
            f"- **Unverified Claims**: {', '.join(unverified_skills) if unverified_skills else 'None'}\n"
            f"{contradiction_text}\n"
            f"- **Trade-off Summary**: {summary_verdict}\n"
        )

        return EvaluationResult(
            candidate_id=candidate.id,
            candidate_name=candidate.full_name,
            score=score_obj,
            verified_skills=list(verified_skills),
            missing_must_haves=missing_must_haves,
            missing_preferred=missing_preferred,
            unverified_claims=list(unverified_skills),
            contradictions=contradictions,
            evidence_ledger=evidence_ledger,
            tradeoff=tradeoff_obj,
            explainable_rationale=explainable_rationale
        )
