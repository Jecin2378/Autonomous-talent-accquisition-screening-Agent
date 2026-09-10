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
from core.domain_requisitions import (
    get_available_domains, get_requisition_by_domain, get_conflict_requisition
)


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
    st.markdown("### 🎯 Preferred Domain & Role")
    st.caption("Select domain role to screen candidates with dedicated skill sets:")
    domain_options = get_available_domains()
    domain_choice = st.selectbox(
        "Recruiter Preferred Role",
        options=domain_options,
        index=0
    )
    active_req = get_requisition_by_domain(domain_choice)

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

    st.markdown("---")
    st.markdown("### 🗂️ Candidate Pool")
    pool_count = len(st.session_state.get("candidate_pool", []))
    st.markdown(f"**Live Resumes in Pool**: `{pool_count}`")
    if st.button("🗑️ Clear Active Pool", key="btn_clear_sidebar"):
        st.session_state.candidate_pool = []
        st.session_state.uploaded_candidates = {}
        st.session_state.processed_files = set()
        st.rerun()
    if st.button("🧪 Load Sample Candidates (Demo)", key="btn_load_demo_sidebar"):
        demo_cands = get_sample_candidates()
        if "uploaded_candidates" not in st.session_state:
            st.session_state.uploaded_candidates = {}
        for c in demo_cands:
            st.session_state.uploaded_candidates[f"demo_{c.id}"] = c
        st.session_state.candidate_pool = list(st.session_state.uploaded_candidates.values())
        st.rerun()

# Initialize Engine with Groq AI
engine = ScreeningAgentEngine(api_key=groq_api_key, base_url=groq_base_url, model=groq_model)

# Initialize Session State
if "candidate_pool" not in st.session_state:
    st.session_state.candidate_pool = []
if "uploaded_candidates" not in st.session_state:
    st.session_state.uploaded_candidates = {}
if "processed_files" not in st.session_state:
    st.session_state.processed_files = set()

# Automatically sync resumes from Live Resume Parser
raw_uploaded = st.session_state.get("resume_uploader")
if raw_uploaded:
    current_keys = set()
    new_resumes = []
    for up_file in raw_uploaded:
        f_bytes = up_file.getvalue()
        f_key = f"{up_file.name}_{len(f_bytes)}"
        current_keys.add(f_key)
        if f_key not in st.session_state.uploaded_candidates:
            new_resumes.append((up_file, f_bytes, f_key))

    for up_file, f_bytes, f_key in new_resumes:
        raw_text = DocumentParser.extract_text_from_bytes(f_bytes, up_file.name)
        name_hint = up_file.name.rsplit(".", 1)[0].replace("_", " ").title()
        new_profile = engine.groq_client.extract_candidate_profile(
            raw_text=raw_text,
            candidate_name=name_hint,
            requisition=active_req
        )
        st.session_state.uploaded_candidates[f_key] = new_profile
        st.session_state.processed_files.add(f_key)

    # Prune any uploaded files that user removed in the uploader widget
    for k in list(st.session_state.uploaded_candidates.keys()):
        if not k.startswith("demo_") and k not in current_keys:
            del st.session_state.uploaded_candidates[k]
            st.session_state.processed_files.discard(k)

    st.session_state.candidate_pool = list(st.session_state.uploaded_candidates.values())
elif not any(k.startswith("demo_") for k in st.session_state.uploaded_candidates.keys()):
    st.session_state.candidate_pool = []
    st.session_state.uploaded_candidates = {}
    st.session_state.processed_files = set()

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
    avg_evidence = round(sum(r.score.evidence_density_score for r in eval_results) / max(len(eval_results), 1), 1) if eval_results else 0.0
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Avg Evidence Density</div>
        <div class="kpi-num">{avg_evidence}%</div>
    </div>
    """, unsafe_allow_html=True)

# Requisition Satisfaction Alert Banner
st.markdown("<br>", unsafe_allow_html=True)
if len(candidates) == 0:
    st.markdown("""
    <div class="verdict-box-yellow" style="background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.4); border-radius: 12px; padding: 16px 20px;">
        <h4 style="margin:0; color:#60a5fa;">📄 Live Screening Ready — No Resumes Uploaded</h4>
        <p style="margin:4px 0 0 0; color:#cbd5e1;">Upload candidate resumes (PDF or TXT) in the <strong>Live Resume Parser</strong> tab below to automatically generate the Closest-Fit Shortlist, Candidate Matrix, Coverage & Pool Gaps, and Forensic Evidence Ledger.</p>
    </div>
    """, unsafe_allow_html=True)
elif report.has_full_satisfaction:
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

    if not candidates:
        st.markdown("""
        <div style="background: rgba(30, 41, 59, 0.6); border: 1px dashed rgba(148, 163, 184, 0.3); border-radius: 12px; padding: 36px 24px; text-align: center; margin: 20px 0;">
            <div style="font-size: 40px; margin-bottom: 12px;">🏆</div>
            <h3 style="margin:0 0 8px 0; color:#f8fafc;">No Candidates in Shortlist Yet</h3>
            <p style="color:#94a3b8; max-width: 600px; margin: 0 auto 16px auto;">
                Upload candidate resumes via the <strong>Live Resume Parser</strong> tab to instantly rank candidates, analyze trade-offs, and inspect verified evidence snippets.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
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

                # 1. Project-to-Skill Verification (Internal Resume Audit)
                if cand.project_verifications:
                    backed_cnt = sum(1 for p in cand.project_verifications if p.is_project_backed)
                    with st.expander(f"🛠️ Project-to-Skill Verification ({backed_cnt}/{len(cand.project_verifications)} Skills Backed by Projects)", expanded=False):
                        pv_rows = []
                        for pv in cand.project_verifications:
                            pv_rows.append({
                                "Skill": pv.skill_name,
                                "Project Verification": "✅ PROJECT-BACKED" if pv.is_project_backed else "⚠️ KEYWORD ONLY",
                                "Associated Project": pv.project_title,
                                "Measurable Impact": pv.metric_impact or "—",
                                "Resume Evidence Snippet": pv.proof_snippet
                            })
                        st.dataframe(pd.DataFrame(pv_rows), use_container_width=True)

                # 2. GitHub Project & Code Verification (External Repo Audit)
                if cand.github_audit and cand.github_audit.github_url:
                    with st.expander(f"🐙 GitHub Project & Code Audit (@{cand.github_audit.username})", expanded=False):
                        st.markdown(f"**Audit Status**: {cand.github_audit.audit_verdict}")
                        st.markdown(f"- **GitHub URL**: [{cand.github_audit.github_url}]({cand.github_audit.github_url})")
                        if cand.github_audit.skills_substantiated:
                            st.markdown(f"- **Skills Corroborated by GitHub Projects**: `{', '.join(cand.github_audit.skills_substantiated)}`")
                        if cand.github_audit.skills_unsubstantiated:
                            st.caption(f"Uncorroborated on GitHub: {', '.join(cand.github_audit.skills_unsubstantiated[:6])}")
                        
                        if cand.github_audit.repos:
                            st.markdown("##### 📦 Audited Repositories:")
                            for r in cand.github_audit.repos:
                                match_tag = f" — *Matches skills: {', '.join(r.matched_skills)}*" if r.matched_skills else ""
                                st.markdown(f"- 📁 **[{r.repo_name}]({r.repo_url})** (`{r.primary_language or 'Code'}`){match_tag}")
                                if r.description:
                                    st.caption(f"> {r.description}")

                # 3. Expandable Evidence Drawer
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

    if not candidates:
        st.markdown("""
        <div style="background: rgba(30, 41, 59, 0.6); border: 1px dashed rgba(148, 163, 184, 0.3); border-radius: 12px; padding: 36px 24px; text-align: center; margin: 20px 0;">
            <div style="font-size: 40px; margin-bottom: 12px;">🧩</div>
            <h3 style="margin:0 0 8px 0; color:#f8fafc;">Candidate Matrix Empty</h3>
            <p style="color:#94a3b8; max-width: 600px; margin: 0 auto;">
                Drop resumes into the <strong>Live Resume Parser</strong> tab to generate requirement-by-requirement deterministic evaluations (PASS, PARTIAL, FAIL, UNSUPPORTED).
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
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
    
    if not candidates:
        st.markdown("""
        <div style="background: rgba(30, 41, 59, 0.6); border: 1px dashed rgba(148, 163, 184, 0.3); border-radius: 12px; padding: 36px 24px; text-align: center; margin: 20px 0;">
            <div style="font-size: 40px; margin-bottom: 12px;">📊</div>
            <h3 style="margin:0 0 8px 0; color:#f8fafc;">Pool Coverage & Gaps Empty</h3>
            <p style="color:#94a3b8; max-width: 600px; margin: 0 auto;">
                Upload candidate resumes via the <strong>Live Resume Parser</strong> tab to calculate requirement coverage, restrictive intersections, and pool gap recommendations.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
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

    if not candidates:
        st.markdown("""
        <div style="background: rgba(30, 41, 59, 0.6); border: 1px dashed rgba(148, 163, 184, 0.3); border-radius: 12px; padding: 36px 24px; text-align: center; margin: 20px 0;">
            <div style="font-size: 40px; margin-bottom: 12px;">🚨</div>
            <h3 style="margin:0 0 8px 0; color:#f8fafc;">Evidence & Contradiction Ledger Empty</h3>
            <p style="color:#94a3b8; max-width: 600px; margin: 0 auto;">
                Upload candidate resumes via the <strong>Live Resume Parser</strong> tab to audit claims against external evidence repositories and detect timeline/skill contradictions.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
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

    c_stat1, c_stat2 = st.columns([3, 1])
    with c_stat1:
        if candidates:
            st.success(f"🟢 **Active Screening Pool**: `{len(candidates)} candidate(s) loaded` — Synchronized with all dashboard tabs.")
        else:
            st.info("ℹ️ **Active Screening Pool**: `0 candidates loaded` — Drop resumes below to start screening.")
    with c_stat2:
        if st.button("🗑️ Clear All Resumes", key="btn_clear_tab_pool"):
            st.session_state.candidate_pool = []
            st.session_state.uploaded_candidates = {}
            st.session_state.processed_files = set()
            st.rerun()

    uploaded_files = st.file_uploader(
        "Drop Candidate Resumes Here (PDF or TXT)",
        type=["pdf", "txt"],
        accept_multiple_files=True,
        key="resume_uploader"
    )

    if candidates:
        st.markdown("---")
        st.markdown("### 👥 Parsed Candidates in Active Screening Pool")
        for cand in candidates:
            c_res = next((r for r in eval_results if r.candidate_id == cand.id), None)
            with st.container():
                st.markdown(f"#### 👤 {cand.full_name} (`{cand.current_role}`) - *{cand.years_of_experience} yrs exp*")
                if c_res:
                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                    with col_m1:
                        st.metric("Overall Score", f"{c_res.score.overall_score}/100")
                    with col_m2:
                        st.metric("Evidence Density", f"{c_res.score.evidence_density_score}%")
                    with col_m3:
                        st.metric("Requirement Match", f"{c_res.score.requirement_match_score}%")
                    with col_m4:
                        st.metric("Spam Penalty", f"-{c_res.score.keyword_spam_penalty} pts")

                    st.markdown(f"**Verdict**: *{c_res.tradeoff.summary_verdict}*")
                
                # 1. Project-to-Skill Verification & GitHub Badges
                if c_res:
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        if c_res.project_verifications:
                            pb_cnt = sum(1 for p in c_res.project_verifications if p.is_project_backed)
                            p_cls = "badge-pass" if pb_cnt == len(c_res.project_verifications) else ("badge-unsupported" if pb_cnt > 0 else "badge-fail")
                            st.markdown(f"**🛠️ Project Verification**: <span class='badge {p_cls}'>{pb_cnt}/{len(c_res.project_verifications)} Skills Project-Backed</span>", unsafe_allow_html=True)
                    with col_b2:
                        if c_res.github_audit and c_res.github_audit.github_url:
                            gh_cls = "badge-pass" if c_res.github_audit.is_verified else "badge-unsupported"
                            st.markdown(f"**🐙 GitHub Repo Audit**: <span class='badge {gh_cls}'>{'✅ Verified Code' if c_res.github_audit.is_verified else '⚠️ Unsubstantiated'}</span> `@{c_res.github_audit.username}`", unsafe_allow_html=True)
                        else:
                            st.markdown("**🐙 GitHub Repo Audit**: <span class='badge badge-fail'>No GitHub URL Found</span>", unsafe_allow_html=True)

                # 2. Show AI Extracted Claims
                with st.expander(f"🔍 View AI-Extracted Claims & Proof Snippets ({len(cand.claims)} skills)", expanded=False):
                    if cand.claims:
                        for clm in cand.claims:
                            status_icon = "✅" if clm.is_verified else "⚠️"
                            badge_cls = "badge-pass" if clm.is_verified else "badge-unsupported"
                            st.markdown(f"**{status_icon} {clm.skill_name}** ({clm.claimed_years} yrs) - <span class='badge {badge_cls}'>{'Verified Proof' if clm.is_verified else 'Unverified Keyword'}</span>", unsafe_allow_html=True)
                            for ev in clm.evidence_list:
                                st.markdown(f"> *[{ev.type.value}]* `{ev.proof_snippet}`")
                    else:
                        st.caption("No claims extracted.")

                # 3. Show Project-to-Skill Verification Matrix
                if c_res and c_res.project_verifications:
                    with st.expander(f"🛠️ Project-to-Skill Verification Breakdown ({sum(1 for p in c_res.project_verifications if p.is_project_backed)}/{len(c_res.project_verifications)} Project-Backed)", expanded=False):
                        pv_rows = []
                        for pv in c_res.project_verifications:
                            pv_rows.append({
                                "Skill": pv.skill_name,
                                "Project-Backed?": "✅ YES" if pv.is_project_backed else "⚠️ KEYWORD ONLY",
                                "Project Context": pv.project_title,
                                "Metric / Deliverable": pv.metric_impact or "—",
                                "Evidence Snippet": pv.proof_snippet
                            })
                        st.dataframe(pd.DataFrame(pv_rows), use_container_width=True)

                # 4. Show GitHub Repo Audit
                if c_res and c_res.github_audit and c_res.github_audit.github_url:
                    with st.expander(f"🐙 GitHub Project & Code Audit Details (@{c_res.github_audit.username})", expanded=False):
                        st.markdown(f"**Status**: {c_res.github_audit.audit_verdict}")
                        st.markdown(f"**URL**: [{c_res.github_audit.github_url}]({c_res.github_audit.github_url})")
                        if c_res.github_audit.skills_substantiated:
                            st.markdown(f"- **Corroborated Skills**: `{', '.join(c_res.github_audit.skills_substantiated)}`")
                        if c_res.github_audit.repos:
                            st.markdown("##### 📦 Audited Repositories:")
                            for r in c_res.github_audit.repos:
                                match_tag = f" — *Matches skills: {', '.join(r.matched_skills)}*" if r.matched_skills else ""
                                st.markdown(f"- 📁 **[{r.repo_name}]({r.repo_url})** (`{r.primary_language or 'Code'}`){match_tag}")
                                if r.description:
                                    st.caption(f"> {r.description}")

                # Action button to remove candidate individually
                col_btn1, _ = st.columns([2, 5])
                with col_btn1:
                    if st.button(f"❌ Remove {cand.full_name}", key=f"del_{cand.id}"):
                        st.session_state.candidate_pool = [c for c in st.session_state.candidate_pool if c.id != cand.id]
                        for k, v in list(st.session_state.uploaded_candidates.items()):
                            if v.id == cand.id:
                                del st.session_state.uploaded_candidates[k]
                                st.session_state.processed_files.discard(k)
                        st.rerun()

                st.divider()

