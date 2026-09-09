"""
Test suite for Evaluation 4: Recruiter Dashboard UI & Document Uploads.
Validates:
- DocumentParser in-memory byte extraction for resumes (PDF/TXT)
- Requisition conflict sample generation
- Dashboard data preparation and JSON export serialization
- Engine batch evaluation for Streamlit dashboard display
"""

import json
import pytest
from parsers.document_parser import DocumentParser
from core.llm_engine import ScreeningAgentEngine
from core.requirement_analyzer import RequirementAnalyzer
from data.sample_data import get_sample_requisition, get_sample_candidates
from app import get_conflict_requisition


def test_eval4_document_parser_bytes():
    """Verify that DocumentParser extracts text cleanly from in-memory bytes."""
    txt_content = b"Alex Chen\nStaff MLOps Lead\n6 years experience in Kubernetes and PyTorch."
    extracted = DocumentParser.extract_text_from_bytes(txt_content, "alex_chen.txt")
    assert "Alex Chen" in extracted
    assert "Kubernetes" in extracted

    # Test section extraction
    sections = DocumentParser.extract_sections(extracted)
    assert isinstance(sections, dict)
    assert "skills" in sections
    assert "experience" in sections


def test_eval4_conflict_requisition_generation():
    """Verify that the dashboard's conflict requisition correctly triggers conflict detection."""
    conflict_req = get_conflict_requisition()
    assert conflict_req.id == "REQ-CONFLICT-DEMO"
    assert conflict_req.max_salary == 7.5

    # Run conflict detection on it
    conflicts = RequirementAnalyzer.detect_requisition_conflicts(conflict_req)
    assert len(conflicts) >= 1
    # Check that experience vs junior level conflict was identified
    exp_conflict = next((c for c in conflicts if "Experience" in c.title or "Level" in c.title), None)
    assert exp_conflict is not None


def test_eval4_dashboard_report_and_export_serialization():
    """Verify that the full requisition analysis report can be serialized to JSON for UI export."""
    req = get_sample_requisition()
    candidates = get_sample_candidates()

    engine = ScreeningAgentEngine()
    report = engine.analyze_requisition_and_shortlist(req, candidates)

    assert len(report.shortlist) == len(candidates)
    assert report.requisition_id == req.id

    # Verify JSON export serialization (matching the app's export button)
    export_payload = {
        "job_title": req.title,
        "satisfaction_verdict": report.satisfaction_verdict,
        "candidates": [c.model_dump() for c in report.shortlist]
    }
    json_str = json.dumps(export_payload, indent=2)
    assert len(json_str) > 0
    assert "Alex Chen" in json_str


def test_eval4_candidate_segment_filters():
    """Verify candidate segmentation filters used in the UI sidebar."""
    req = get_sample_requisition()
    candidates = get_sample_candidates()

    engine = ScreeningAgentEngine()
    report = engine.analyze_requisition_and_shortlist(req, candidates)

    # Segment: Closest fit candidates
    closest_fits = [c for c in report.shortlist if c.required_criteria_met >= max(1, c.required_criteria_total - 1)]
    assert len(closest_fits) > 0

    # Top candidate should be Alex Chen
    assert report.shortlist[0].candidate_name == "Alex Chen"
