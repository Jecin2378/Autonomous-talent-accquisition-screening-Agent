import re
from typing import List, Dict, Any, Optional, Tuple
from models.schemas import (
    CandidateProfile, ContradictionResult, ContradictionType,
    ContradictionFlag, EvidenceReference, Claim
)
from core.skill_normalizer import SkillNormalizer


class ContradictionDetector:
    """
    Component for detecting contradictions and unsupported claims across
    candidate resumes, cover notes, job titles, and experience timelines.
    """

    YEAR_CLAIM_PATTERN = re.compile(r'(\d+|\b[a-zA-Z]+\b)\s*\+?\s*years?\s+(?:of\s+)?([a-zA-Z0-9\+\#\.\s]+?)(?:\s+experience|\s+working|\,|\.|\n|$)', re.IGNORECASE)
    EXPERT_CLAIM_PATTERN = re.compile(r'(expert|master|guru|lead|advanced\s+specialist)\s+(?:in|with)?\s+([a-zA-Z0-9\+\#\.\s]+)', re.IGNORECASE)
    DATE_RANGE_PATTERN = re.compile(r'\(?\s*(\b20\d{2}\b)\s*(?:[\-\–\s]|to)+\s*(\b20\d{2}\b|present|current)\s*\)?', re.IGNORECASE)
    TITLE_PATTERN = re.compile(r'(senior|lead|principal|staff|head|chief)\s+(software|engineer|developer|architect|manager)', re.IGNORECASE)
    BASIC_TASK_PATTERN = re.compile(r'(completed\s+basic|assigned\s+tasks\s+under\s+supervision|assisted\s+senior|junior\s+support|entry\s+level\s+tasks)', re.IGNORECASE)

    WORD_TO_NUM = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
    }

    @classmethod
    def analyze_candidate(cls, candidate: CandidateProfile, current_year: int = 2026) -> List[ContradictionResult]:
        """Runs comprehensive contradiction analysis on candidate application."""
        contradictions: List[ContradictionResult] = []

        # 1. Date & Experience Duration Validation
        cls._check_date_timeline_contradictions(candidate, current_year, contradictions)

        # 2. Cross-Document (Resume vs Cover Note) Validation
        cls._check_resume_vs_cover_note(candidate, contradictions)

        # 3. Expertise vs Evidence Validation (e.g. Expert claim vs Coursework evidence)
        cls._check_expertise_vs_evidence(candidate, contradictions)

        # 4. Job Title vs Responsibilities Mismatch
        cls._check_title_vs_responsibilities(candidate, contradictions)

        # 5. Unsupported Claims Check (Absence of evidence flagged without fabricating contradiction)
        cls._check_unsupported_claims(candidate, contradictions)

        return contradictions

    @classmethod
    def _check_date_timeline_contradictions(cls, candidate: CandidateProfile, current_year: int, contradictions: List[ContradictionResult]):
        """Detects contradictions between claimed years of experience and date timelines."""
        text = candidate.raw_resume_text or ""
        lines = text.split("\n")

        prof_timeline_ranges = []
        timeline_evidence = []

        for line in lines:
            matches = cls.DATE_RANGE_PATTERN.findall(line)
            for m in matches:
                start_yr = int(m[0])
                end_str = m[1].lower()
                end_yr = current_year if ("present" in end_str or "current" in end_str) else int(end_str)
                duration = max(0.5, end_yr - start_yr)
                
                is_education = any(k in line.lower() for k in ["b.tech", "b.s.", "education", "degree", "university", "school"])
                
                if not is_education:
                    prof_timeline_ranges.append((start_yr, end_yr, duration))
                    src = "experience"
                else:
                    src = "education"

                timeline_evidence.append(EvidenceReference(
                    source=src,
                    text=line.strip()
                ))

        max_prof_tenure = sum(dur for _, _, dur in prof_timeline_ranges) if prof_timeline_ranges else candidate.years_of_experience

        # Check explicit claims in text or candidate.claims
        year_claims = cls.YEAR_CLAIM_PATTERN.findall(text)
        for claim_match in year_claims:
            num_str = claim_match[0].lower()
            skill_claimed = claim_match[1].strip()
            
            claimed_years = 0.0
            if num_str.isdigit():
                claimed_years = float(num_str)
            elif num_str in cls.WORD_TO_NUM:
                claimed_years = float(cls.WORD_TO_NUM[num_str])

            if claimed_years > 0:
                if max_prof_tenure >= 0 and claimed_years > max_prof_tenure + 0.5:
                    claim_text = f"{int(claimed_years) if claimed_years.is_integer() else claimed_years} years of {skill_claimed} experience"
                    
                    contradictions.append(
                        ContradictionResult(
                            candidate_id=candidate.id,
                            flag=ContradictionFlag.CONTRADICTORY_UNSUPPORTED.value,
                            type=ContradictionType.DATE_EXPERIENCE_CONTRADICTION,
                            claim=claim_text,
                            evidence=timeline_evidence if timeline_evidence else [
                                EvidenceReference(source="experience", text=f"Listed professional timeline duration: {max_prof_tenure} year(s)")
                            ],
                            assessment=f"The claimed {int(claimed_years) if claimed_years.is_integer() else claimed_years} years of {skill_claimed} experience is not supported by the available professional/project timeline.",
                            confidence="reduced"
                        )
                    )

    @classmethod
    def _check_resume_vs_cover_note(cls, candidate: CandidateProfile, contradictions: List[ContradictionResult]):
        """Compares claims in resume against cover note to find direct conflicts."""
        if not candidate.cover_note:
            return

        resume_text = candidate.raw_resume_text or ""
        cover_text = candidate.cover_note or ""

        resume_matches = cls.YEAR_CLAIM_PATTERN.findall(resume_text)
        cover_matches = cls.YEAR_CLAIM_PATTERN.findall(cover_text)

        for r_num, r_domain in resume_matches:
            r_val = float(r_num) if r_num.isdigit() else float(cls.WORD_TO_NUM.get(r_num.lower(), 0))
            if r_val == 0:
                continue

            for c_num, c_domain in cover_matches:
                c_val = float(c_num) if c_num.isdigit() else float(cls.WORD_TO_NUM.get(c_num.lower(), 0))
                if c_val == 0:
                    continue

                if SkillNormalizer.are_equivalent(r_domain, c_domain):
                    if abs(r_val - c_val) >= 2.0:
                        r_snippet = f"{int(r_val)} years of {r_domain} experience"
                        c_snippet = f"{int(c_val)} years of {c_domain} experience"

                        contradictions.append(
                            ContradictionResult(
                                candidate_id=candidate.id,
                                flag=ContradictionFlag.CONTRADICTORY_UNSUPPORTED.value,
                                type=ContradictionType.RESUME_COVER_NOTE_CONTRADICTION,
                                claim=f"Experience duration conflict: Resume ({int(r_val)} yrs) vs Cover Note ({int(c_val)} yrs)",
                                evidence=[
                                    EvidenceReference(source="resume", text=r_snippet),
                                    EvidenceReference(source="cover_note", text=c_snippet)
                                ],
                                assessment=f"Inconsistency detected between resume ({int(r_val)} years) and cover note ({int(c_val)} years) regarding {r_domain} experience.",
                                confidence="reduced"
                            )
                        )

    @classmethod
    def _check_expertise_vs_evidence(cls, candidate: CandidateProfile, contradictions: List[ContradictionResult]):
        """Detects 'Expert' claims supported only by basic course or tutorial evidence."""
        text = candidate.raw_resume_text or ""
        lines = text.split("\n")

        for line in lines:
            expert_matches = cls.EXPERT_CLAIM_PATTERN.findall(line)
            for lvl, skill_raw in expert_matches:
                skill_norm = SkillNormalizer.normalize(skill_raw)
                
                course_evidence = []
                prod_evidence = []

                for ev_line in lines:
                    if SkillNormalizer.are_equivalent(skill_norm, ev_line) or skill_raw.lower() in ev_line.lower():
                        if re.search(r'(completed|course|tutorial|bootcamp|certificate|online\s+class|introduced\s+to)', ev_line, re.IGNORECASE):
                            course_evidence.append(ev_line.strip())
                        elif re.search(r'(built|architected|deployed|managed|lead|scaled|\d+%\s*|\d+\s*users)', ev_line, re.IGNORECASE) and ev_line.strip() != line.strip():
                            prod_evidence.append(ev_line.strip())

                if course_evidence and not prod_evidence:
                    contradictions.append(
                        ContradictionResult(
                            candidate_id=candidate.id,
                            flag=ContradictionFlag.UNSUPPORTED_CLAIM.value,
                            type=ContradictionType.EXPERTISE_EVIDENCE_CONTRADICTION,
                            claim=line.strip(),
                            evidence=[
                                EvidenceReference(source="resume", text=course_evidence[0])
                            ],
                            assessment=f"The claim '{line.strip()}' is insufficiently supported as only coursework evidence was found in the application.",
                            confidence="reduced"
                        )
                    )

    @classmethod
    def _check_title_vs_responsibilities(cls, candidate: CandidateProfile, contradictions: List[ContradictionResult]):
        """Detects mismatch between Senior job title and basic/supervised responsibilities."""
        text = candidate.raw_resume_text or ""
        lines = text.split("\n")

        current_title = ""
        for line in lines:
            if cls.TITLE_PATTERN.search(line) and len(line.strip()) < 60:
                current_title = line.strip()
            elif current_title and cls.BASIC_TASK_PATTERN.search(line):
                contradictions.append(
                    ContradictionResult(
                        candidate_id=candidate.id,
                        flag=ContradictionFlag.CONTRADICTORY_UNSUPPORTED.value,
                        type=ContradictionType.TITLE_RESPONSIBILITY_MISMATCH,
                        claim=f"Title: {current_title}",
                        evidence=[
                            EvidenceReference(source="experience", text=current_title),
                            EvidenceReference(source="experience", text=line.strip())
                        ],
                        assessment=f"Possible mismatch between title '{current_title}' and described responsibilities ('{line.strip()}').",
                        confidence="reduced"
                    )
                )

    @classmethod
    def _check_unsupported_claims(cls, candidate: CandidateProfile, contradictions: List[ContradictionResult]):
        """Identifies claims that lack supporting evidence without inventing contradictions."""
        for claim in candidate.claims:
            norm_skill = SkillNormalizer.normalize(claim.skill_name)
            if not claim.is_verified and not claim.evidence_list:
                already_flagged = any(norm_skill.lower() in c.claim.lower() for c in contradictions)
                if not already_flagged:
                    contradictions.append(
                        ContradictionResult(
                            candidate_id=candidate.id,
                            flag=ContradictionFlag.UNSUPPORTED_CLAIM.value,
                            type=ContradictionType.SKILL_EXPERIENCE_CONTRADICTION,
                            claim=f"Claim: {norm_skill}",
                            evidence=[
                                EvidenceReference(source="skills_summary", text=f"Listed '{norm_skill}' in skills section")
                            ],
                            assessment=f"Claim '{norm_skill}' is insufficiently supported by available professional/project evidence.",
                            confidence="reduced"
                        )
                    )
