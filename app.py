"""
Streamlit Web Dashboard for Autonomous Talent Acquisition Screening Agent.
Features:
- Candidate Evaluation & Evidence Verification
- Requisition Conflict & Trade-Off Analysis
- Candidate Requirement Matrix
- Pool Coverage & Restrictive Intersection Metrics
- Full Satisfaction Checker & Closest-Fit Shortlist
"""

import streamlit as st
import pandas as pd
from models.schemas import (
    JobRequisition, CandidateProfile, RequirementStatus, RequirementType,
    ConflictSeverity, EvidenceType
)
from core.llm_engine import ScreeningAgentEngine
from core.requirement_analyzer import RequirementAnalyzer
from data.sample_data import get_sample_requisition, get_sample_candidates


st.set_page_config(
    page_title="AI Talent Screening & Requisition Conflict Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Glassmorphic Styling
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc;
    }
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        backdrop-filter: blur(10px);
    }
    .badge-pass { background-color: #065f46; color: #34d399; padding: 4px 8px; border-radius: 6px; font-weight: bold; }
    .badge-fail { background-color: #7f1d1d; color: #f87171; padding: 4px 8px; border-radius: 6px; font-weight: bold; }
    .badge-unsupported { background-color: #78350f; color: #fbbf24; padding: 4px 8px; border-radius: 6px; font-weight: bold; }
    .badge-contradictory { background-color: #831843; color: #f472b6; padding: 4px 8px; border-radius: 6px; font-weight: bold; }
    .badge-unknown { background-color: #374151; color: #9ca3af; padding: 4px 8px; border-radius: 6px; font-weight: bold; }
    .badge-partial { background-color: #1e3a8a; color: #60a5fa; padding: 4px 8px; border-radius: 6px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# App Header
st.title("🤖 Autonomous Talent-Acquisition Screening Agent")
st.caption("Evidence-Grounded Screening, Requisition Conflict Detection & Closest-Fit Trade-Off Shortlisting")

# Sidebar - Settings & Data Loading
with st.sidebar:
    st.header("⚙️ Configuration")
    st.info("Demonstrating offline evidence verification & multi-dimensional screening.")
    sample_req = get_sample_requisition()
    sample_candidates = get_sample_candidates()
    
    st.subheader("Job Requisition")
    st.write(f"**Title**: {sample_req.title}")
    st.write(f"**Department**: {sample_req.department}")
    st.write(f"**Level**: {sample_req.experience_level}")
    st.write(f"**Must-Haves**: {len([r for r in sample_req.requirements if r.type == RequirementType.MUST_HAVE])}")
    st.write(f"**Preferred**: {len([r for r in sample_req.requirements if r.type == RequirementType.PREFERRED])}")

# Engine Execution
engine = ScreeningAgentEngine()
report = engine.analyze_requisition_and_shortlist(sample_req, sample_candidates)
results = engine.evaluate_batch(sample_req, sample_candidates)

# Section 1: Executive Overview & Requisition Satisfaction
st.markdown("---")
st.header("📋 Requisition Analysis & Satisfaction Status")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Candidates Evaluated", len(sample_candidates))
with col2:
    st.metric("Conflicts Detected", len(report.conflicts_detected))
with col3:
    full_sat_count = sum(1 for m in report.matrix_rows if m.satisfies_all_required)
    st.metric("Full Must-Have Matches", f"{full_sat_count}/{len(sample_candidates)}")
with col4:
    st.metric("Applicant Pool Health", "Shortage Identified" if not report.has_full_satisfaction else "Fully Satisfied")

# Satisfaction Verdict Alert Box
if report.has_full_satisfaction:
    st.success(f"✅ {report.satisfaction_verdict}")
else:
    st.error(f"⚠️ **{report.satisfaction_verdict.split('.')[0]}.**\n\n{report.satisfaction_verdict}")

# Section 2: Requisition Conflicts (Surprise Challenge Core)
st.markdown("---")
st.subheader("⚠️ Detected Requisition Conflicts")
if report.conflicts_detected:
    for conflict in report.conflicts_detected:
        with st.expander(f"🚨 {conflict.severity.value}: {conflict.title}", expanded=True):
            st.markdown(f"**Conflicting Criteria**: {', '.join(conflict.conflicting_requirements)}")
            st.markdown(f"**Evidence-Based Reason**: {conflict.reason}")
else:
    st.info("No internal requisition conflicts detected for this requisition.")

# Section 3: Requirement Coverage & Restrictive Intersections
st.markdown("---")
st.subheader("📊 Requirement Coverage & Intersection Analysis")

tab1, tab2 = st.tabs(["Individual Criteria Coverage", "Intersection & Combination Analysis"])

with tab1:
    cov_data = []
    for c in report.coverage_items:
        cov_data.append({
            "Requirement": c.title,
            "Type": "MUST HAVE" if c.is_required else "PREFERRED",
            "Candidates Meeting": f"{c.satisfied_count} / {c.total_candidates}",
            "Coverage %": f"{c.coverage_pct}%",
            "Status": c.status
        })
    st.dataframe(pd.DataFrame(cov_data), use_container_width=True)

with tab2:
    inter_data = []
    for item in report.intersection_items:
        inter_data.append({
            "Combination": item.combination_name,
            "Candidates Meeting": f"{item.satisfied_count} / {item.total_candidates}",
            "Coverage %": f"{item.coverage_pct}%",
            "Restrictive": "YES" if item.is_restrictive else "NO",
            "Notes": item.notes
        })
    st.dataframe(pd.DataFrame(inter_data), use_container_width=True)

# Section 4: Candidate Requirement Matrix
st.markdown("---")
st.subheader("🧩 Candidate Requirement Matrix")
st.caption("Deterministic evaluation states: PASS, PARTIAL, FAIL, UNKNOWN, UNSUPPORTED, CONTRADICTORY")

matrix_display = []
for row in report.matrix_rows:
    row_dict = {
        "Candidate": row.candidate_name,
        "Must-Haves Met": f"{row.required_satisfied}/{row.required_total}",
        "Preferred Met": f"{row.preferred_satisfied}/{row.preferred_total}",
        "Full Match": "✅ YES" if row.satisfies_all_required else "❌ NO"
    }
    for cell in row.cell_details:
        row_dict[cell.requirement_title] = cell.status.value
    matrix_display.append(row_dict)

st.dataframe(pd.DataFrame(matrix_display), use_container_width=True)

# Section 5: Closest-Fit Shortlist & Trade-Off Analysis
st.markdown("---")
st.header("🏆 Closest-Fit Candidate Shortlist & Trade-Offs")
st.caption("Candidates ranked by satisfied required criteria, trade-off severity, and evidence confidence (scores are secondary).")

for cand in report.shortlist:
    with st.container():
        st.markdown(f"### #{cand.rank} {cand.candidate_name}")
        st.markdown(f"**Assessment**: *{cand.overall_assessment}* | **Evidence Confidence**: **{cand.evidence_confidence}** | **Secondary Match Score**: {cand.secondary_score}/100")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 💪 Key Strengths & Verified Criteria")
            for s in cand.strengths:
                st.markdown(f"- {s}")
            if cand.preferred_criteria_met > 0:
                st.markdown(f"- *Meets {cand.preferred_criteria_met}/{cand.preferred_criteria_total} preferred criteria.*")
        
        with c2:
            st.markdown("#### ⚖️ Trade-Offs & Unmet Criteria")
            for t in cand.tradeoffs:
                st.markdown(f"- {t}")
            for u in cand.unmet_requirements:
                st.markdown(f"- ❌ **Unmet**: {u}")
            for contra in cand.contradictions:
                st.markdown(f"- 🚨 **Contradiction**: {contra}")
            for unsup in cand.unsupported_claims:
                st.markdown(f"- ⚠️ **Unsupported**: {unsup}")
        
        st.divider()
