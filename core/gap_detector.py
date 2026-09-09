from typing import List
from models.schemas import JobRequisition, EvaluationResult, PoolGapReport, RequirementType
from core.skill_normalizer import SkillNormalizer


class PoolGapDetector:
    """Scans the applicant pool to identify systemic skill shortages across candidates."""

    @classmethod
    def analyze_pool_gaps(cls, requisition: JobRequisition, results: List[EvaluationResult]) -> PoolGapReport:
        total_candidates = len(results)
        if total_candidates == 0:
            return PoolGapReport(
                job_id=requisition.id,
                job_title=requisition.title,
                total_candidates_evaluated=0,
                unmet_must_haves=[],
                unmet_preferred=[],
                gap_analysis_summary="No candidates available for pool gap evaluation.",
                recruiter_actionable_recommendations=["Upload candidate resumes to analyze applicant pool gaps."]
            )

        # Track how many candidates satisfy each requirement
        must_have_counts = {r.title: 0 for r in requisition.requirements if r.type == RequirementType.MUST_HAVE}
        preferred_counts = {r.title: 0 for r in requisition.requirements if r.type == RequirementType.PREFERRED}

        for eval_res in results:
            for req_title in must_have_counts.keys():
                if req_title not in eval_res.missing_must_haves:
                    must_have_counts[req_title] += 1

            for req_title in preferred_counts.keys():
                if req_title not in eval_res.missing_preferred:
                    preferred_counts[req_title] += 1

        unmet_must_haves = [req for req, count in must_have_counts.items() if count == 0]
        unmet_preferred = [req for req, count in preferred_counts.items() if count == 0]

        low_coverage_must_haves = [req for req, count in must_have_counts.items() if 0 < count <= max(1, total_candidates * 0.25)]

        recommendations = []
        if unmet_must_haves:
            recommendations.append(
                f"CRITICAL GAP: 0% of applicant pool satisfies mandatory requirement: '{', '.join(unmet_must_haves)}'. "
                f"Consider revising requisition constraints or launching outbound headhunting."
            )

        if low_coverage_must_haves:
            recommendations.append(
                f"LOW COVERAGE: Only {low_coverage_must_haves[0]} is met by <= 25% of candidates. Risk of bottleneck."
            )

        if unmet_preferred:
            recommendations.append(
                f"NICE-TO-HAVE SHORTAGE: None of the current candidates have verified experience in '{', '.join(unmet_preferred)}'."
            )

        if not recommendations:
            recommendations.append("HEALTHY CANDIDATE POOL: At least one top candidate satisfies every required and preferred criterion.")

        summary = (
            f"Evaluated {total_candidates} candidate(s) for '{requisition.title}'. "
            f"Found {len(unmet_must_haves)} unfulfilled mandatory criteria and {len(unmet_preferred)} unfulfilled preferred criteria."
        )

        return PoolGapReport(
            job_id=requisition.id,
            job_title=requisition.title,
            total_candidates_evaluated=total_candidates,
            unmet_must_haves=unmet_must_haves,
            unmet_preferred=unmet_preferred,
            gap_analysis_summary=summary,
            recruiter_actionable_recommendations=recommendations
        )
