"""
Requirement Conflict & Trade-Off Shortlisting Engine.
Analyzes job requisitions for internal conflicts, evaluates candidate requirement coverage,
computes intersection restrictiveness, checks full requirement satisfaction,
and builds closest-fit trade-off shortlists.
"""

import re
import itertools
from typing import List, Dict, Any, Optional, Tuple, Set
from models.schemas import (
    JobRequisition, Requirement, RequirementType, SkillCategory,
    CandidateProfile, CandidateScore, RequirementStatus, ConstraintType,
    ConflictType, ConflictSeverity, RequirementConflict,
    RequirementCoverageItem, RequirementIntersectionItem,
    CandidateRequirementCell, CandidateMatrixRow, ShortlistCandidate,
    RequisitionAnalysisReport, EvaluationResult, ContradictionFlag
)
from core.skill_normalizer import SkillNormalizer
from core.tradeoff_analyzer import TradeoffAnalyzer


class RequirementAnalyzer:
    """
    Dedicated engine for Requirement Conflict Detection, Coverage Analysis,
    Candidate Requirement Matrix Generation, and Closest-Fit Shortlisting.
    """

    LOW_COVERAGE_THRESHOLD = 40.0
    HIGH_COVERAGE_THRESHOLD = 70.0

    @classmethod
    def detect_requisition_conflicts(
        cls,
        requisition: JobRequisition,
        candidates: Optional[List[CandidateProfile]] = None
    ) -> List[RequirementConflict]:
        """
        Identifies when requirements in a job requisition are individually valid
        but collectively difficult, conflicting, or overly restrictive.
        """
        conflicts: List[RequirementConflict] = []
        req_texts = [f"{r.title} {r.description}".lower() for r in requisition.requirements]
        all_req_text = " ".join(req_texts) + f" {requisition.title} {requisition.experience_level} {requisition.raw_description or ''}".lower()

        # 1. Experience vs Level Conflict (e.g. 5+ years experience + Junior role)
        max_min_years = max([r.min_years for r in requisition.requirements], default=0.0)
        # Check text mentions of 5+ years
        has_high_exp_claim = max_min_years >= 5.0 or bool(re.search(r'\b(5\+|5\s*years|6\+|7\+|8\+)\b', all_req_text))
        is_junior_level = (
            "junior" in requisition.title.lower() or
            "entry" in requisition.title.lower() or
            "junior" in requisition.experience_level.lower() or
            (requisition.target_role_level and "junior" in requisition.target_role_level.lower()) or
            "junior-level" in all_req_text or
            "entry-level" in all_req_text
        )

        if has_high_exp_claim and is_junior_level:
            conflicts.append(
                RequirementConflict(
                    conflict_type=ConflictType.EXPERIENCE_LEVEL_CONFLICT,
                    severity=ConflictSeverity.POTENTIAL_CONFLICT,
                    title="Experience & Level Contradiction",
                    conflicting_requirements=["5+ years software development", "Junior-level position"],
                    reason="A junior-level role normally targets candidates with lower experience (0-2 years), while the requisition requires at least 5 years."
                )
            )

        # 2. Compensation Constraint (e.g. Senior Experience >= 5 yrs + Salary <= 8 LPA)
        salary_limit = requisition.max_salary
        if salary_limit is None:
            # Check description or requirements for salary constraints
            salary_match = re.search(r'salary\s*<=\s*[₹$]?\s*(\d+(?:\.\d+)?)\s*(?:lpa|k)?', all_req_text)
            if salary_match:
                salary_limit = float(salary_match.group(1))

        if salary_limit is not None and has_high_exp_claim and salary_limit <= 8.5:
            conflicts.append(
                RequirementConflict(
                    conflict_type=ConflictType.COMPENSATION_CONSTRAINT,
                    severity=ConflictSeverity.HIGH_RESTRICTION,
                    title="Senior Tenure vs Below-Market Compensation Ceiling",
                    conflicting_requirements=["5+ years experience", f"Salary <= ₹{salary_limit:g} LPA"],
                    reason=f"Requiring 5+ years experience alongside a compensation cap of <= ₹{salary_limit:g} LPA creates severe candidate pool restriction."
                )
            )

        # 3. Rare Skill Combination Conflict
        skill_titles = [r.title for r in requisition.requirements if r.type == RequirementType.MUST_HAVE]
        if len(skill_titles) >= 4:
            has_deep_infra = any(s.lower() in all_req_text for s in ["kubernetes", "k8s", "distributed systems"])
            has_deep_ml = any(s.lower() in all_req_text for s in ["pytorch", "tensorflow", "deep learning", "ai/ml"])
            has_low_level = any(s.lower() in all_req_text for s in ["c++", "rust", "kernel"])
            if has_deep_infra and has_deep_ml and has_low_level:
                conflicts.append(
                    RequirementConflict(
                        conflict_type=ConflictType.SKILL_CONSTRAINT_CONFLICT,
                        severity=ConflictSeverity.HIGH_RESTRICTION,
                        title="Divergent Multi-Specialty Technology Stack",
                        conflicting_requirements=["Low-Level Systems", "Kubernetes / Infrastructure", "Deep Learning / ML"],
                        reason="Demanding high expertise across systems programming, container orchestration, and ML model engineering is rare in a single individual."
                    )
                )

        return conflicts

    @classmethod
    def evaluate_candidate_matrix(
        cls,
        requisition: JobRequisition,
        candidates: List[CandidateProfile],
        eval_results: Optional[List[EvaluationResult]] = None
    ) -> List[CandidateMatrixRow]:
        """
        Builds the Candidate Requirement Matrix mapping each candidate to each requirement
        using deterministic states: PASS, PARTIAL, FAIL, UNKNOWN, UNSUPPORTED, CONTRADICTORY.
        """
        if eval_results is None:
            eval_results = [TradeoffAnalyzer.evaluate_candidate(requisition, c) for c in candidates]

        eval_map = {res.candidate_id: res for res in eval_results}
        matrix_rows: List[CandidateMatrixRow] = []

        must_haves = [r for r in requisition.requirements if r.type == RequirementType.MUST_HAVE]
        preferreds = [r for r in requisition.requirements if r.type == RequirementType.PREFERRED]

        for cand in candidates:
            res = eval_map.get(cand.id)
            cells: Dict[str, RequirementStatus] = {}
            cell_details: List[CandidateRequirementCell] = []

            # Check contradictions from existing engine
            contradiction_skills = set()
            contradiction_dates = False
            if res:
                for contra in res.contradictions:
                    if contra.type.value in ["DATE_EXPERIENCE_CONTRADICTION", "SKILL_EXPERIENCE_CONTRADICTION"]:
                        contradiction_dates = True
                    contra_norm = SkillNormalizer.normalize(contra.claim)
                    contradiction_skills.add(contra_norm.lower())

            # Verified skills & claims
            verified_skills_norm = {SkillNormalizer.normalize(s).lower() for s in (res.verified_skills if res else [])}
            unverified_claims_norm = {SkillNormalizer.normalize(s).lower() for s in (res.unverified_claims if res else [])}

            for req in requisition.requirements:
                req_title = req.title
                status, reason = cls._evaluate_single_cell(
                    req=req,
                    candidate=cand,
                    res=res,
                    verified_skills=verified_skills_norm,
                    unverified_claims=unverified_claims_norm,
                    contradiction_skills=contradiction_skills,
                    contradiction_dates=contradiction_dates,
                    requisition=requisition
                )
                cells[req_title] = status
                cell_details.append(
                    CandidateRequirementCell(
                        requirement_id=req.id,
                        requirement_title=req_title,
                        status=status,
                        reason=reason,
                        is_must_have=(req.type == RequirementType.MUST_HAVE)
                    )
                )

            req_sat = sum(1 for r in must_haves if cells.get(r.title) == RequirementStatus.PASS)
            pref_sat = sum(1 for r in preferreds if cells.get(r.title) == RequirementStatus.PASS)
            all_req_pass = (req_sat == len(must_haves)) and (len(must_haves) > 0)

            matrix_rows.append(
                CandidateMatrixRow(
                    candidate_id=cand.id,
                    candidate_name=cand.full_name,
                    cells=cells,
                    cell_details=cell_details,
                    required_satisfied=req_sat,
                    required_total=len(must_haves),
                    preferred_satisfied=pref_sat,
                    preferred_total=len(preferreds),
                    satisfies_all_required=all_req_pass
                )
            )

        return matrix_rows

    @classmethod
    def _evaluate_single_cell(
        cls,
        req: Requirement,
        candidate: CandidateProfile,
        res: Optional[EvaluationResult],
        verified_skills: Set[str],
        unverified_claims: Set[str],
        contradiction_skills: Set[str],
        contradiction_dates: bool,
        requisition: JobRequisition
    ) -> Tuple[RequirementStatus, str]:
        """Evaluates one requirement for one candidate deterministically."""
        req_norm = SkillNormalizer.normalize(req.title).lower()
        text_lower = (candidate.raw_resume_text or "").lower()

        # 1. Numeric Minimum Experience Requirement
        is_exp_req = req.constraint_type == ConstraintType.NUMERIC_MIN or "year" in req.title.lower() or "experience" in req.title.lower() or req.min_years > 0
        if is_exp_req and req.category in [SkillCategory.OTHER, SkillCategory.DOMAIN]:
            target_years = req.min_years if req.min_years > 0 else (req.target_value or 5.0)
            if contradiction_dates:
                return RequirementStatus.CONTRADICTORY, f"Claimed experience contradicts verifiable timeline ({candidate.years_of_experience} yrs vs timeline)."
            if candidate.years_of_experience >= target_years:
                return RequirementStatus.PASS, f"Candidate has {candidate.years_of_experience} yrs (meets target of {target_years}+ yrs)."
            elif candidate.years_of_experience >= (target_years * 0.5):
                return RequirementStatus.PARTIAL, f"Candidate has {candidate.years_of_experience} yrs (below target of {target_years}+ yrs)."
            else:
                return RequirementStatus.FAIL, f"Candidate has {candidate.years_of_experience} yrs (far below {target_years}+ yrs)."

        # 2. Compensation / Salary Constraint
        is_salary_req = req.constraint_type == ConstraintType.NUMERIC_MAX or "salary" in req.title.lower() or "lpa" in req.title.lower()
        if is_salary_req:
            max_val = req.target_value or requisition.max_salary or 8.0
            if candidate.expected_salary is not None:
                if candidate.expected_salary <= max_val:
                    return RequirementStatus.PASS, f"Expected salary ₹{candidate.expected_salary} LPA is within ceiling ₹{max_val} LPA."
                else:
                    return RequirementStatus.FAIL, f"Expected salary ₹{candidate.expected_salary} LPA exceeds ceiling ₹{max_val} LPA."
            # Check metadata or resume text
            cand_sal = candidate.metadata.get("expected_salary") or candidate.metadata.get("salary")
            if cand_sal is not None:
                if float(cand_sal) <= max_val:
                    return RequirementStatus.PASS, f"Salary ₹{cand_sal} LPA <= ₹{max_val} LPA."
                else:
                    return RequirementStatus.FAIL, f"Salary ₹{cand_sal} LPA > ₹{max_val} LPA."
            return RequirementStatus.UNKNOWN, "No compensation data provided in candidate profile."

        # 3. Exact Level Requirement (e.g. Junior, Senior)
        if req.constraint_type == ConstraintType.EXACT_LEVEL or "level" in req.title.lower():
            target_lvl = str(req.target_value or requisition.experience_level or "Junior").lower()
            cand_lvl = str(candidate.current_level or candidate.current_role).lower()
            if target_lvl in cand_lvl:
                return RequirementStatus.PASS, f"Candidate role matches target level '{target_lvl}'."
            return RequirementStatus.PARTIAL, f"Candidate role is '{candidate.current_role}' (target '{target_lvl}')."

        # 4. Skill Presence & Strength Requirements (Default & Technical Criteria)
        # Check contradictions first
        is_contradicted = any(SkillNormalizer.are_equivalent(req_norm, cs) or req_norm in cs for cs in contradiction_skills)
        if is_contradicted:
            return RequirementStatus.CONTRADICTORY, f"Contradictory or conflicting claims detected for {req.title}."

        # Check if verified in existing screening result
        is_verified = any(SkillNormalizer.are_equivalent(req_norm, vs) or req_norm in vs for vs in verified_skills)
        if is_verified:
            return RequirementStatus.PASS, f"Verified with concrete evidence and project proof."

        # Check if claimed without verification (UNSUPPORTED)
        is_unverified_claim = any(SkillNormalizer.are_equivalent(req_norm, uc) or req_norm in uc for uc in unverified_claims)
        # Also check candidate claims list directly
        for clm in candidate.claims:
            if SkillNormalizer.are_equivalent(req_norm, SkillNormalizer.normalize(clm.skill_name).lower()):
                if clm.is_verified:
                    return RequirementStatus.PASS, f"Claim verified via {clm.verification_notes or 'proof snippets'}."
                else:
                    return RequirementStatus.UNSUPPORTED, f"Skill claimed but lacks supporting evidence or project tenure."

        if is_unverified_claim:
            return RequirementStatus.UNSUPPORTED, f"Claimed as keyword in resume summary without concrete proof snippets."

        # Check if mentioned in text without proof
        if req_norm in text_lower or req.title.lower() in text_lower:
            return RequirementStatus.UNSUPPORTED, f"Mentioned in resume text without verifiable project evidence."

        # Check if data is completely absent
        # If preferred, missing is treated as UNKNOWN or FAIL
        if req.type == RequirementType.PREFERRED:
            return RequirementStatus.UNKNOWN, f"No mention or evidence of preferred skill '{req.title}'."

        return RequirementStatus.FAIL, f"Requirement '{req.title}' is completely unfulfilled."

    @classmethod
    def calculate_coverage_and_intersections(
        cls,
        requisition: JobRequisition,
        matrix_rows: List[CandidateMatrixRow]
    ) -> Tuple[List[RequirementCoverageItem], List[RequirementIntersectionItem], str, bool]:
        """
        Calculates individual requirement coverage, restrictive intersections,
        and generates the explicit full-satisfaction verdict.
        """
        total_candidates = len(matrix_rows)
        coverage_items: List[RequirementCoverageItem] = []
        intersection_items: List[RequirementIntersectionItem] = []

        if total_candidates == 0:
            return [], [], "No candidate fully satisfies all required criteria. (0 candidates evaluated)", False

        must_haves = [r for r in requisition.requirements if r.type == RequirementType.MUST_HAVE]

        # 1. Individual Coverage
        for req in requisition.requirements:
            sat_count = sum(1 for row in matrix_rows if row.cells.get(req.title) == RequirementStatus.PASS)
            cov_pct = round((sat_count / total_candidates) * 100.0, 1)

            if cov_pct < cls.LOW_COVERAGE_THRESHOLD:
                status_str = "LOW_COVERAGE"
            elif cov_pct > cls.HIGH_COVERAGE_THRESHOLD:
                status_str = "HIGH_COVERAGE"
            else:
                status_str = "MODERATE_COVERAGE"

            coverage_items.append(
                RequirementCoverageItem(
                    requirement_id=req.id,
                    title=req.title,
                    is_required=(req.type == RequirementType.MUST_HAVE),
                    satisfied_count=sat_count,
                    total_candidates=total_candidates,
                    coverage_pct=cov_pct,
                    status=status_str
                )
            )

        # 2. Pairwise & Combined Intersections
        if len(must_haves) >= 2:
            for r1, r2 in itertools.combinations(must_haves[:4], 2):
                pair_sat = sum(
                    1 for row in matrix_rows
                    if row.cells.get(r1.title) == RequirementStatus.PASS and row.cells.get(r2.title) == RequirementStatus.PASS
                )
                pair_pct = round((pair_sat / total_candidates) * 100.0, 1)
                is_restr = pair_pct <= 25.0
                intersection_items.append(
                    RequirementIntersectionItem(
                        combination_name=f"{r1.title} AND {r2.title}",
                        requirements=[r1.title, r2.title],
                        satisfied_count=pair_sat,
                        total_candidates=total_candidates,
                        coverage_pct=pair_pct,
                        is_restrictive=is_restr,
                        notes="Highly restrictive pair" if is_restr else "Compatible pair"
                    )
                )

        # 3. All Required Criteria Full Intersection
        full_sat_count = sum(1 for row in matrix_rows if row.satisfies_all_required)
        full_pct = round((full_sat_count / total_candidates) * 100.0, 1)
        has_full_sat = (full_sat_count > 0)

        intersection_items.append(
            RequirementIntersectionItem(
                combination_name="All Required Criteria (Full Intersection)",
                requirements=[r.title for r in must_haves],
                satisfied_count=full_sat_count,
                total_candidates=total_candidates,
                coverage_pct=full_pct,
                is_restrictive=(full_sat_count == 0 or full_pct <= 20.0),
                notes="Zero candidates satisfy all criteria" if full_sat_count == 0 else "Satisfied by pool subset"
            )
        )

        # 4. Mandatory Requisition Satisfaction Verdict
        if has_full_sat:
            verdict = (
                f"FULL REQUIREMENT SATISFACTION: At least one candidate satisfies all required criteria. "
                f"({full_sat_count}/{total_candidates} candidates met 100% of Must-Have requirements)."
            )
        else:
            verdict = (
                "No candidate fully satisfies all required criteria.\n\n"
                "The applicant pool exhibits critical shortages across mandatory requirements. "
                "Recruiters should review the closest-fit shortlist and evaluate acceptable trade-offs."
            )

        return coverage_items, intersection_items, verdict, has_full_sat

    @classmethod
    def generate_closest_fit_shortlist(
        cls,
        requisition: JobRequisition,
        candidates: List[CandidateProfile],
        matrix_rows: List[CandidateMatrixRow],
        eval_results: Optional[List[EvaluationResult]] = None
    ) -> List[ShortlistCandidate]:
        """
        Ranks candidates by closest-fit multi-dimensional criteria when no candidate
        (or few candidates) fully satisfy the requisition.
        """
        if eval_results is None:
            eval_results = [TradeoffAnalyzer.evaluate_candidate(requisition, c) for c in candidates]

        eval_map = {res.candidate_id: res for res in eval_results}
        row_map = {r.candidate_id: r for r in matrix_rows}
        shortlist: List[ShortlistCandidate] = []

        for cand in candidates:
            res = eval_map.get(cand.id)
            row = row_map.get(cand.id)
            if not row or not res:
                continue

            strengths = []
            unmet_reqs = []
            partial_reqs = []
            unsupported_claims = []
            contradictions_list = [f"{c.type.value}: {c.assessment}" for c in res.contradictions]

            for cell in row.cell_details:
                if cell.status == RequirementStatus.PASS:
                    strengths.append(f"{cell.requirement_title} (Verified: {cell.reason})")
                elif cell.status == RequirementStatus.PARTIAL:
                    partial_reqs.append(f"{cell.requirement_title} ({cell.reason})")
                elif cell.status == RequirementStatus.UNSUPPORTED:
                    unsupported_claims.append(f"{cell.requirement_title} (Unverified claim)")
                elif cell.status in [RequirementStatus.FAIL, RequirementStatus.UNKNOWN]:
                    if cell.is_must_have:
                        unmet_reqs.append(f"{cell.requirement_title} ({cell.reason})")

            # Trade-off evaluation
            tradeoffs = []
            if unmet_reqs:
                tradeoffs.append(f"Missing mandatory requirement(s): {', '.join([u.split(' (')[0] for u in unmet_reqs])}.")
            if partial_reqs:
                tradeoffs.append(f"Partially satisfies: {', '.join([p.split(' (')[0] for p in partial_reqs])}.")
            if unsupported_claims:
                tradeoffs.append(f"Unsubstantiated claim(s): {', '.join([u.split(' (')[0] for u in unsupported_claims])}.")
            if contradictions_list:
                tradeoffs.append(f"Contradiction flag(s) present: {len(contradictions_list)} issue(s) detected.")

            # Evidence Confidence
            if len(res.contradictions) > 0:
                ev_confidence = "Reduced"
            elif res.score.evidence_density_score >= 85.0 and len(unsupported_claims) == 0:
                ev_confidence = "High"
            else:
                ev_confidence = "Moderate"

            # Overall human-readable assessment
            if row.satisfies_all_required:
                assessment = "Full Match: All mandatory requirements satisfied with verifiable evidence."
            elif row.required_satisfied >= max(1, row.required_total - 1) and not contradictions_list:
                assessment = "Strong Alternative: Closest-fit candidate satisfying major criteria with minor recoverable gaps."
            elif row.required_satisfied > 0:
                assessment = "Partial Fit: Meets selective criteria but presents significant trade-offs."
            else:
                assessment = "Unqualified / Low Fit: Fails majority of mandatory requirements."

            shortlist.append(
                ShortlistCandidate(
                    candidate_id=cand.id,
                    candidate_name=cand.full_name,
                    rank=1, # Updated after sorting
                    strengths=strengths if strengths else ["Baseline profile submission."],
                    unmet_requirements=unmet_reqs,
                    partial_requirements=partial_reqs,
                    contradictions=contradictions_list,
                    unsupported_claims=unsupported_claims,
                    tradeoffs=tradeoffs if tradeoffs else ["No significant trade-offs."],
                    evidence_confidence=ev_confidence,
                    required_criteria_met=row.required_satisfied,
                    required_criteria_total=row.required_total,
                    preferred_criteria_met=row.preferred_satisfied,
                    preferred_criteria_total=row.preferred_total,
                    overall_assessment=assessment,
                    secondary_score=res.score.overall_score,
                    project_verifications=res.project_verifications,
                    github_audit=res.github_audit
                )
            )

        # Multi-dimensional sorting (Required met desc, contradictions asc, secondary score desc)
        shortlist.sort(
            key=lambda c: (
                c.required_criteria_met,
                -len(c.contradictions),
                c.preferred_criteria_met,
                c.secondary_score or 0.0
            ),
            reverse=True
        )

        for rank_idx, cand in enumerate(shortlist, start=1):
            cand.rank = rank_idx

        return shortlist

    @classmethod
    def analyze_requisition_full(
        cls,
        requisition: JobRequisition,
        candidates: List[CandidateProfile]
    ) -> RequisitionAnalysisReport:
        """
        End-to-end analyzer:
        1. Detects Requisition Conflicts
        2. Evaluates Candidate Requirement Matrix
        3. Computes Coverage & Intersection Metrics
        4. Determines Full Requisition Satisfaction Verdict
        5. Generates Closest-Fit Shortlist
        """
        conflicts = cls.detect_requisition_conflicts(requisition, candidates)
        eval_results = [TradeoffAnalyzer.evaluate_candidate(requisition, c) for c in candidates]
        matrix_rows = cls.evaluate_candidate_matrix(requisition, candidates, eval_results)
        coverage_items, intersection_items, verdict, has_full_sat = cls.calculate_coverage_and_intersections(requisition, matrix_rows)
        shortlist = cls.generate_closest_fit_shortlist(requisition, candidates, matrix_rows, eval_results)

        # Summarize pool gaps
        unmet_titles = [c.title for c in coverage_items if c.is_required and c.satisfied_count == 0]
        if unmet_titles:
            pool_summary = f"Severe shortages in mandatory criteria: {', '.join(unmet_titles)} (0% pool coverage)."
        else:
            pool_summary = "All mandatory requirements have at least partial coverage across the applicant pool."

        return RequisitionAnalysisReport(
            requisition_id=requisition.id,
            requisition_title=requisition.title,
            conflicts_detected=conflicts,
            coverage_items=coverage_items,
            intersection_items=intersection_items,
            has_full_satisfaction=has_full_sat,
            satisfaction_verdict=verdict,
            pool_gaps_summary=pool_summary,
            matrix_rows=matrix_rows,
            shortlist=shortlist
        )
