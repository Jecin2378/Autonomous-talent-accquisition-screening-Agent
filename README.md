# 🤖 Autonomous Talent Acquisition Screening Agent

An **AI-powered talent screening agent** that evaluates candidates based on **evidence, not just resume keywords**.

## 🎯 Problem

Traditional resume screening can:

* Reward unsupported skill claims.
* Miss equivalent skills written using different terminology.
* Hide important trade-offs behind a single score.
* Fail to identify requirements that no candidate satisfies.

## 💡 Our Solution

Our agent:

1. Extracts **required and preferred** criteria from a job requisition.
2. Extracts candidate **skills and claims**.
3. Cross-checks claims against **evidence in the application**.
4. Recognizes **equivalent skills and terminology**.
5. Compares candidates using **multiple dimensions and trade-offs**.
6. Identifies **unmet requirements across the applicant pool**.

## 🧠 Agent Flow

```text
Job Requisition
       ↓
Requirement Analysis
       ↓
Candidate Claims
       ↓
Evidence Verification
       ↓
Skill Normalization
       ↓
Candidate Evaluation
       ↓
Trade-off Analysis
       ↓
Pool Gap Detection
       ↓
Explainable Shortlist
```

## 🛠️ Tech Stack

* **Python**
* **LLM**
* **Pydantic**
* **PDF/Text Processing**
* **Streamlit**
* **JSON / SQLite**

## 🔐 Core Principles

* **Evidence > Keywords**
* No fabricated evidence
* Equivalent terminology is recognized
* Decisions remain explainable
* Multi-dimensional candidate comparison

## 🚀 Goal

Build a transparent and autonomous screening agent that helps recruiters make **evidence-backed hiring decisions**.

> **Don't just match the resume. Verify the claim.**

