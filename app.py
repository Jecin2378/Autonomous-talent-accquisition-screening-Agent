"""
Streamlit Web Dashboard for Autonomous Talent Acquisition Screening Agent.
Evaluation 4: Recruiter Dashboard with Glassmorphism Interface.
"""

import json
import os
import streamlit as st
import pandas as pd
from typing import List

from models.schemas import (
    JobRequisition, Requirement, CandidateProfile, RequirementType,
    SkillCategory, ConstraintType, RequirementStatus, ConflictSeverity
)
from core.llm_engine import ScreeningAgentEngine
from core.requirement_analyzer import RequirementAnalyzer
from core.evidence_ledger import EvidenceLedgerBuilder
from parsers.document_parser import DocumentParser
from data.sample_data import get_sample_requisition, get_sample_candidates


# Page Config
st.set_page_config(
    page_title="Autonomous Talent Screening Agent | Recruiter Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load External Stylesheet
css_path = os.path.join(os.path.dirname(__file__), "static", "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Custom Helper Functions
def get_conflict_requisition() -> JobRequisition:
    """Returns sample requisition containing realistic requirement conflicts."""
    return JobRequisition(
        id="REQ-CONFLICT-DEMO",
        title="Junior AI Platform Associate",
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


# Sidebar Configuration
with st.sidebar:
    st.markdown("## ⚙️ Control Panel")
    st.caption("Configure screening rules, active job requisition, and data sources.")
    
    st.markdown("### 🤖 Groq AI Engine")
    groq_api_key = st.text_input(
        "Groq API Key",
        value=os.getenv("GROQ_API_KEY", ""),
        type="password",
        placeholder="Enter your gsk_... key"
    )
    groq_base_url = st.text_input("Groq Base URL", value=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"))
    groq_model = st.selectbox(
        "ChatGPT OSS Model",
        options=["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"],
        index=0
    )
    if groq_api_key:
        st.success(f"🟢 Connected: `{groq_model}`")
    else:
        st.info("ℹ️ Running in Offline Mode (Enter key to enable AI extraction)")

    st.markdown("---")
    req_choice = st.selectbox(
        "Active Job Requisition",
        options=[
            "Senior AI Platform & MLOps Engineer (Standard)",
            "Junior AI Associate (With Internal Conflicts)"
        ],
        index=0
    )

    if req_choice.startswith("Senior"):
        active_req = get_sample_requisition()
    else:
        active_req = get_conflict_requisition()

    st.markdown("### 📋 Requisition Summary")
    st.markdown(f"**Title**: `{active_req.title}`")
    st.markdown(f"**Department**: `{active_req.department}`")
    st.markdown(f"**Level**: `{active_req.experience_level}`")
    if active_req.max_salary:
        st.markdown(f"**Salary Cap**: `₹{active_req.max_salary} {active_req.salary_currency}`")

    must_haves = [r for r in active_req.requirements if r.type == RequirementType.MUST_HAVE]
    preferreds = [r for r in active_req.requirements if r.type == RequirementType.PREFERRED]
    st.markdown(f"**Must-Haves**: `{len(must_haves)}` | **Preferred**: `{len(preferreds)}`")

    st.markdown("---")
    st.markdown("### 🔍 Filter Shortlist")
    search_query = st.text_input("Search Candidate Name / Skill", "")
    filter_mode = st.radio("Segment Filter", ["All Candidates", "Closest Fit Candidates", "Has Contradictions", "Spam Penalized"], index=0)

# Initialize Engine with Groq AI
engine = ScreeningAgentEngine(api_key=groq_api_key, base_url=groq_base_url, model=groq_model)

# Initialize or Retrieve Candidates in Session
if "candidate_pool" not in st.session_state:
    st.session_state.candidate_pool = get_sample_candidates()

candidates: List[CandidateProfile] = st.session_state.candidate_pool

# Run Full Requisition Conflict & Shortlist Analysis
report = engine.analyze_requisition_and_shortlist(active_req, candidates)
eval_results = engine.evaluate_batch(active_req, candidates)

# Header Section
st.markdown('<div class="hero-title">🤖 Autonomous Talent-Acquisition Screening Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">Evidence-First Verification • Requisition Conflict Detection • Closest-Fit Trade-Off Shortlisting</div>', unsafe_allow_html=True)

# Top KPI Summary Cards
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
with kpi_col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Candidates Evaluated</div>
        <div class="kpi-num">{len(candidates)}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col2:
    full_sat_count = sum(1 for m in report.matrix_rows if m.satisfies_all_required)
    color_class = "badge-pass" if full_sat_count > 0 else "badge-fail"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Full Must-Have Matches</div>
        <div class="kpi-num">{full_sat_count} <span class="badge {color_class}">{full_sat_count}/{len(candidates)}</span></div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col3:
    conflict_count = len(report.conflicts_detected)
    badge_color = "badge-contradictory" if conflict_count > 0 else "badge-pass"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Requisition Conflicts</div>
        <div class="kpi-num">{conflict_count} <span class="badge {badge_color}">{'Detected' if conflict_count > 0 else 'Clean'}</span></div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col4:
    avg_evidence = round(sum(r.score.evidence_density_score for r in eval_results) / max(len(eval_results), 1), 1)
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Avg Evidence Density</div>
        <div class="kpi-num">{avg_evidence}%</div>
    </div>
    """, unsafe_allow_html=True)

# Requisition Satisfaction Alert Banner
st.markdown("<br>", unsafe_allow_html=True)
if report.has_full_satisfaction:
    st.markdown(f"""
    <div class="verdict-box-green">
        <h4 style="margin:0; color:#34d399;">✅ Full Requirement Satisfaction Achieved</h4>
        <p style="margin:4px 0 0 0; color:#e2e8f0;">{report.satisfaction_verdict}</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="verdict-box-red">
        <h4 style="margin:0; color:#fb7185;">⚠️ No candidate fully satisfies all required criteria.</h4>
        <p style="margin:4px 0 0 0; color:#e2e8f0;">{report.satisfaction_verdict.replace('No candidate fully satisfies all required criteria.', '').strip()}</p>
    </div>
    """, unsafe_allow_html=True)

# Requisition Conflicts Alert Section
if report.conflicts_detected:
    with st.expander("🚨 View Detected Internal Requisition Conflicts", expanded=True):
        for conf in report.conflicts_detected:
            st.markdown(f"**{conf.severity.value}**: `{conf.title}`")
            st.markdown(f"- **Conflicting Elements**: {', '.join(conf.conflicting_requirements)}")
            st.markdown(f"- **Evidence-Based Rationale**: *{conf.reason}*")
            st.divider()

# Main Interactive Tabs
tab_shortlist, tab_matrix, tab_coverage, tab_ledger, tab_upload = st.tabs([
    "🏆 Closest-Fit Shortlist",
    "🧩 Candidate Matrix",
    "📊 Coverage & Pool Gaps",
    "🚨 Evidence & Contradiction Ledger",
    "📄 Live Resume Parser"
])

# -------------------------------------------------------------
# TAB 1: CLOSEST-FIT SHORTLIST & TRADE-OFFS
# -------------------------------------------------------------
with tab_shortlist:
    st.markdown("### 🏆 Candidate Shortlist & Trade-Off Analysis")
    st.caption("Candidates evaluated along multiple dimensions: required criteria met, trade-off severity, and evidence confidence.")

    # Filter shortlist
    filtered_shortlist = report.shortlist
    if search_query:
        filtered_shortlist = [c for c in filtered_shortlist if search_query.lower() in c.candidate_name.lower()]
    
    if filter_mode == "Closest Fit Candidates":
        filtered_shortlist = [c for c in filtered_shortlist if c.required_criteria_met >= max(1, c.required_criteria_total - 1)]
    elif filter_mode == "Has Contradictions":
        filtered_shortlist = [c for c in filtered_shortlist if len(c.contradictions) > 0]
    elif filter_mode == "Spam Penalized":
        filtered_shortlist = [c for c in filtered_shortlist if len(c.unsupported_claims) > 0]

    for cand in filtered_shortlist:
        with st.container():
            col_head, col_score = st.columns([3, 1])
            with col_head:
                st.markdown(f"#### #{cand.rank} {cand.candidate_name}")
                st.markdown(f"**Assessment**: *{cand.overall_assessment}*")
            with col_score:
                conf_badge = "badge-pass" if cand.evidence_confidence == "High" else ("badge-unsupported" if cand.evidence_confidence == "Moderate" else "badge-contradictory")
                st.markdown(f'<span class="badge {conf_badge}">Confidence: {cand.evidence_confidence}</span> <span class="score-pill">Score: {cand.secondary_score}/100</span>', unsafe_allow_html=True)
                st.markdown(f"**Required**: `{cand.required_criteria_met}/{cand.required_criteria_total}` | **Preferred**: `{cand.preferred_criteria_met}/{cand.preferred_criteria_total}`")

            # Two Column Strengths vs Trade-Offs
            col_str, col_trd = st.columns(2)
            with col_str:
                st.markdown("**💪 Key Strengths & Verified Criteria**")
                for s in cand.strengths:
                    st.markdown(f"- ✅ {s}")
                if not cand.strengths:
                    st.markdown("- *No verified strengths recorded.*")

            with col_trd:
                st.markdown("**⚖️ Trade-Offs & Gaps**")
                for t in cand.tradeoffs:
                    st.markdown(f"- ⚠️ {t}")
                for u in cand.unmet_requirements:
                    st.markdown(f"- ❌ **Unmet**: {u}")
                for contra in cand.contradictions:
                    st.markdown(f"- 🚨 **Contradiction**: {contra}")
                for unsup in cand.unsupported_claims:
                    st.markdown(f"- ⚠️ **Unverified Claim**: {unsup}")

            # Expandable Evidence Drawer
            with st.expander(f"🔍 Inspect Evidence & Proof Snippets for {cand.candidate_name}"):
                c_prof = next((cp for cp in candidates if cp.id == cand.candidate_id), None)
                if c_prof and c_prof.claims:
                    for clm in c_prof.claims:
                        v_icon = "✅" if clm.is_verified else "⚠️"
                        st.markdown(f"**{v_icon} {clm.skill_name}** ({clm.claimed_years} yrs claimed)")
                        if clm.verification_notes:
                            st.caption(clm.verification_notes)
                        for ev in clm.evidence_list:
                            st.markdown(f"> *[{ev.type.value}]* {ev.proof_snippet} `(confidence: {ev.confidence_score})`")
                elif c_prof:
                    st.text(c_prof.raw_resume_text[:400] + "...")

            st.divider()

    # Download Shortlist Report
    shortlist_export = {
        "job_title": active_req.title,
        "satisfaction_verdict": report.satisfaction_verdict,
        "candidates": [c.model_dump() for c in report.shortlist]
    }
    st.download_button(
        label="📥 Export Shortlist Report (JSON)",
        data=json.dumps(shortlist_export, indent=2),
        file_name=f"shortlist_{active_req.id.lower()}.json",
        mime="application/json"
    )

# -------------------------------------------------------------
# TAB 2: CANDIDATE REQUIREMENT MATRIX
# -------------------------------------------------------------
with tab_matrix:
    st.markdown("### 🧩 Candidate Requirement Matrix")
    st.caption("Deterministic evaluation states: PASS, PARTIAL, FAIL, UNKNOWN, UNSUPPORTED, CONTRADICTORY.")

    matrix_rows_data = []
    for row in report.matrix_rows:
        r_dict = {
            "Candidate": row.candidate_name,
            "Must-Haves": f"{row.required_satisfied}/{row.required_total}",
            "Preferred": f"{row.preferred_satisfied}/{row.preferred_total}",
            "Full Match": "✅ YES" if row.satisfies_all_required else "❌ NO"
        }
        for cell in row.cell_details:
            r_dict[cell.requirement_title] = cell.status.value
        matrix_rows_data.append(r_dict)

    df_matrix = pd.DataFrame(matrix_rows_data)
    st.dataframe(df_matrix, use_container_width=True)

    # Detailed Cell Inspector
    st.markdown("#### 🔬 Detailed Matrix Cell Inspector")
    sel_cand = st.selectbox("Select Candidate to Inspect", options=[r.candidate_name for r in report.matrix_rows])
    sel_row = next((r for r in report.matrix_rows if r.candidate_name == sel_cand), None)
    if sel_row:
        cell_table = []
        for cell in sel_row.cell_details:
            cell_table.append({
                "Requirement": cell.requirement_title,
                "Type": "MUST HAVE" if cell.is_must_have else "PREFERRED",
                "Evaluation State": cell.status.value,
                "Deterministic Reason / Proof": cell.reason
            })
        st.dataframe(pd.DataFrame(cell_table), use_container_width=True)

# -------------------------------------------------------------
# TAB 3: COVERAGE & POOL GAPS
# -------------------------------------------------------------
with tab_coverage:
    st.markdown("### 📊 Requirement Coverage & Pool Restrictiveness")
    
    c1_cov, c2_cov = st.columns([1, 1])
    with c1_cov:
        st.markdown("#### Individual Criteria Coverage")
        cov_table = []
        for item in report.coverage_items:
            cov_table.append({
                "Requirement": item.title,
                "Required": "YES" if item.is_required else "NO",
                "Candidates Meeting": f"{item.satisfied_count} / {item.total_candidates}",
                "Coverage": f"{item.coverage_pct}%",
                "Status": item.status
            })
        st.dataframe(pd.DataFrame(cov_table), use_container_width=True)

    with c2_cov:
        st.markdown("#### Restrictive Intersections (Combined Criteria)")
        inter_table = []
        for item in report.intersection_items:
            inter_table.append({
                "Requirement Intersection": item.combination_name,
                "Coverage": f"{item.satisfied_count}/{item.total_candidates} ({item.coverage_pct}%)",
                "Restrictive": "YES" if item.is_restrictive else "NO",
                "Notes": item.notes
            })
        st.dataframe(pd.DataFrame(inter_table), use_container_width=True)

    # Pool Gap Report & Recommendations
    st.markdown("---")
    st.markdown("#### 📋 Pool Gap Analysis & Recruiter Actionable Advice")
    pool_report = engine.generate_pool_report(active_req, eval_results)
    st.info(f"**Gap Summary**: {pool_report.gap_analysis_summary}")
    for rec in pool_report.recruiter_actionable_recommendations:
        st.markdown(f"- 💡 **Recommendation**: {rec}")

# -------------------------------------------------------------
# TAB 4: EVIDENCE & CONTRADICTION LEDGER
# -------------------------------------------------------------
with tab_ledger:
    st.markdown("### 🚨 Forensic Contradiction & Evidence Ledger")
    st.caption("Traceable verification mapping candidate claims to public evidence repositories and identity linkage.")

    for cand_prof in candidates:
        with st.expander(f"Candidate: {cand_prof.full_name} ({cand_prof.current_role})", expanded=False):
            ledger = EvidenceLedgerBuilder.build_ledger(cand_prof)
            res = next((r for r in eval_results if r.candidate_id == cand_prof.id), None)
            
            # Contradictions
            if res and res.contradictions:
                st.markdown("##### 🚨 Contradiction & Unsupported Flags")
                for c in res.contradictions:
                    st.error(f"**{c.flag}** ({c.type.value})\n- **Claim**: {c.claim}\n- **Assessment**: {c.assessment}")
            else:
                st.success("Zero contradiction flags detected for this candidate.")

            # Evidence Ledger
            st.markdown("##### 📑 Traceable Evidence Ledger Entries")
            ledger_table = []
            for entry in ledger:
                ledger_table.append({
                    "Claim": entry.claim,
                    "Assessment State": entry.assessment.value,
                    "Confidence": entry.confidence,
                    "Identity Status": entry.identity_linkage.status.value,
                    "Sources Linked": len(entry.sources),
                    "Reasoning": entry.reasoning
                })
            st.dataframe(pd.DataFrame(ledger_table), use_container_width=True)

# -------------------------------------------------------------
# TAB 5: LIVE RESUME PARSER & UPLOAD SANDBOX
# -------------------------------------------------------------
with tab_upload:
    st.markdown("### 📄 Live Resume Upload & AI-Powered Screener")
    st.caption("Upload raw PDF or TXT resumes. Groq AI (`openai/gpt-oss-120b`) extracts skills, evidence snippets, metrics, and timeline proof.")

    uploaded_files = st.file_uploader(
        "Drop Candidate Resumes Here (PDF or TXT)",
        type=["pdf", "txt"],
        accept_multiple_files=True
    )

    if uploaded_files:
        st.info(f"Processing {len(uploaded_files)} candidate resume(s) with Groq AI...")
        for up_file in uploaded_files:
            file_bytes = up_file.read()
            
            with st.spinner(f"Extracting claims & evidence for `{up_file.name}` via Groq AI..."):
                new_cand = engine.groq_client.extract_candidate_profile(
                    raw_text=DocumentParser.extract_text_from_bytes(file_bytes, up_file.name),
                    candidate_name=up_file.name.rsplit(".", 1)[0].replace("_", " ").title()
                )
                new_res = engine.evaluate_single_candidate(active_req, new_cand)
            
            with st.container():
                st.markdown(f"#### 👤 {new_cand.full_name} (`{new_cand.current_role}`) - *{new_cand.years_of_experience} yrs exp*")
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                with col_m1:
                    st.metric("Overall Score", f"{new_res.score.overall_score}/100")
                with col_m2:
                    st.metric("Evidence Density", f"{new_res.score.evidence_density_score}%")
                with col_m3:
                    st.metric("Requirement Match", f"{new_res.score.requirement_match_score}%")
                with col_m4:
                    st.metric("Spam Penalty", f"-{new_res.score.keyword_spam_penalty} pts")

                st.markdown(f"**Verdict**: *{new_res.tradeoff.summary_verdict}*")
                
                # Show AI Extracted Claims
                with st.expander("🔍 View AI-Extracted Claims & Proof Snippets", expanded=True):
                    if new_cand.claims:
                        for clm in new_cand.claims:
                            status_icon = "✅" if clm.is_verified else "⚠️"
                            badge_cls = "badge-pass" if clm.is_verified else "badge-unsupported"
                            st.markdown(f"**{status_icon} {clm.skill_name}** ({clm.claimed_years} yrs) - <span class='badge {badge_cls}'>{'Verified Proof' if clm.is_verified else 'Unverified Keyword'}</span>", unsafe_allow_html=True)
                            for ev in clm.evidence_list:
                                st.markdown(f"> *[{ev.type.value}]* `{ev.proof_snippet}`")
                    else:
                        st.caption("No claims extracted.")

                # Action button to add candidate into the active pool
                if st.button(f"➕ Add {new_cand.full_name} to Active Candidate Pool", key=f"btn_{new_cand.id}"):
                    if not any(c.id == new_cand.id for c in st.session_state.candidate_pool):
                        st.session_state.candidate_pool.append(new_cand)
                        st.success(f"Added {new_cand.full_name} to candidate pool! Re-evaluating dashboard...")
                        st.rerun()

                st.divider()
