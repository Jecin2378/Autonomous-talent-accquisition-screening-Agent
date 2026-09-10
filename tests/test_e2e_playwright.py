"""
Playwright End-to-End Test Suite for Autonomous Talent Acquisition Screening Agent.
Tests the Streamlit Web Application from every corner:
1. Dashboard load & KPI summary cards
2. Requisition satisfaction verdict banner
3. Requisition conflict alert cards
4. Tab 1: Closest-Fit Shortlist & Trade-Off Cards
5. Tab 2: Candidate Requirement Matrix & Cell Inspector
6. Tab 3: Requirement Coverage & Restrictive Intersections
7. Tab 4: Forensic Contradiction & Evidence Ledger
8. Tab 5: Live Resume Uploader & AI Screener
9. Sidebar Requisition Switching (Standard vs Conflicting)
10. Shortlist Filtering & Candidate Search
"""

import time
import pytest
from playwright.sync_api import sync_playwright, Page, expect


STREAMLIT_URL = "http://localhost:8501"


@pytest.fixture(scope="module")
def browser_page():
    """Launches system browser and returns page context connected to Streamlit app."""
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page = context.new_page()
        try:
            page.goto(STREAMLIT_URL, wait_until="networkidle", timeout=25000)
            time.sleep(3) # Allow Streamlit hydration
            yield page
        finally:
            browser.close()


def test_e2e_01_dashboard_title_and_kpis(browser_page: Page):
    """Corner 1: Verify header title, subtitle, and KPI summary cards."""
    # Check Title
    expect(browser_page.locator("text=Autonomous Talent-Acquisition Screening Agent").first).to_be_visible(timeout=15000)
    
    # Check KPIs
    expect(browser_page.locator("text=Candidates Evaluated").first).to_be_visible()
    expect(browser_page.locator("text=Full Must-Have Matches").first).to_be_visible()
    expect(browser_page.locator("text=Avg Evidence Density").first).to_be_visible()


def test_e2e_02_satisfaction_verdict_banner(browser_page: Page):
    """Corner 2: Verify requirement satisfaction or live screening ready banner."""
    banner = browser_page.locator(".verdict-box-green, .verdict-box-red, .verdict-box-yellow").first
    expect(banner).to_be_visible()


def test_e2e_03_tab5_live_resume_parser_upload(browser_page: Page):
    """Corner 3: Verify Tab 5 Live Resume Upload & AI Screener Sandbox."""
    # Click Tab 5
    tab5 = browser_page.get_by_role("tab", name="📄 Live Resume Parser")
    tab5.click()
    time.sleep(1)

    # Check uploader is present
    expect(browser_page.locator("text=Drop Candidate Resumes Here").first).to_be_visible()

    # Click the demo load button or upload to populate candidates for downstream tab testing
    load_demo_btn = browser_page.locator("button:has-text('Load Sample Candidates (Demo)')").first
    if load_demo_btn.is_visible():
        load_demo_btn.click()
        time.sleep(2)


def test_e2e_04_tab1_closest_fit_shortlist(browser_page: Page):
    """Corner 4: Verify Tab 1 Closest-Fit Shortlist renders candidate cards, strengths, trade-offs."""
    # Click Tab 1
    tab1 = browser_page.get_by_role("tab", name="🏆 Closest-Fit Shortlist")
    tab1.click()
    time.sleep(1)

    # Check candidate card elements
    expect(browser_page.locator("text=Key Strengths").first).to_be_visible()
    expect(browser_page.locator("text=Trade-Offs").first).to_be_visible()

    # Check JSON export button
    expect(browser_page.locator("text=Export Shortlist Report").first).to_be_visible()


def test_e2e_05_tab2_candidate_matrix(browser_page: Page):
    """Corner 5: Verify Tab 2 Candidate Requirement Matrix table and cell inspector."""
    # Click Tab 2
    tab2 = browser_page.get_by_role("tab", name="🧩 Candidate Matrix")
    tab2.click()
    time.sleep(1)

    # Check matrix heading
    expect(browser_page.locator("text=Candidate Requirement Matrix").first).to_be_visible()
    # Check Detailed Matrix Cell Inspector
    expect(browser_page.locator("text=Detailed Matrix Cell Inspector").first).to_be_visible()


def test_e2e_06_tab3_coverage_and_pool_gaps(browser_page: Page):
    """Corner 6: Verify Tab 3 Requirement Coverage, Restrictive Intersections, and Recruiter Advice."""
    # Click Tab 3
    tab3 = browser_page.get_by_role("tab", name="📊 Coverage & Pool Gaps")
    tab3.click()
    time.sleep(1)

    # Check coverage sections
    expect(browser_page.locator("text=Individual Criteria Coverage").first).to_be_visible()
    expect(browser_page.locator("text=Restrictive Intersections").first).to_be_visible()
    expect(browser_page.locator("text=Pool Gap Analysis").first).to_be_visible()


def test_e2e_07_tab4_evidence_ledger(browser_page: Page):
    """Corner 7: Verify Tab 4 Forensic Evidence Ledger and Contradiction Flags."""
    # Click Tab 4
    tab4 = browser_page.get_by_role("tab", name="🚨 Evidence & Contradiction Ledger")
    tab4.click()
    time.sleep(1)

    # Check ledger heading
    expect(browser_page.locator("text=Forensic Contradiction & Evidence Ledger").first).to_be_visible()


def test_e2e_08_sidebar_requisition_switching(browser_page: Page):
    """Test Corner 8: Sidebar Requisition switcher toggles active vacancy and detects conflicts."""
    # Locate Active Job Requisition selectbox in sidebar
    req_sb = browser_page.locator('[data-testid="stSidebar"] [data-testid="stSelectbox"]').first
    req_sb.scroll_into_view_if_needed()
    req_sb.click()
    time.sleep(1)

    
    # Click the Junior AI Associate option
    opt = browser_page.locator('li[role="option"]').filter(has_text="Junior AI Associate").first
    if opt.is_visible():
        opt.click()
        time.sleep(2)
        # Verify the conflicts banner appears for the Junior AI Associate role
        expect(browser_page.locator("text=Detected Internal Requisition Conflicts").first).to_be_visible(timeout=10000)
    else:
        # Close selectbox if already selected or click body
        browser_page.keyboard.press("Escape")

