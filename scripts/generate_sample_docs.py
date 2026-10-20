import fitz  # PyMuPDF
from pathlib import Path

def create_sample_pdf(file_path: Path, title: str, pages_content: list):
    doc = fitz.open()
    for page_num, text in enumerate(pages_content, 1):
        page = doc.new_page(width=595, height=842)  # A4 size
        # Header
        page.insert_text(
            (50, 45),
            f"ENTERPRISE INTERNAL DOCUMENT - {title.upper()}",
            fontsize=9,
            color=(0.4, 0.4, 0.4)
        )
        # Title
        page.insert_text(
            (50, 80),
            f"{title} (Page {page_num})",
            fontsize=16,
            color=(0.1, 0.2, 0.5)
        )
        # Body text wrapped
        rect = fitz.Rect(50, 110, 545, 780)
        page.insert_textbox(rect, text, fontsize=11, lineheight=1.4)
        # Footer
        page.insert_text(
            (50, 800),
            f"Classification: Enterprise Confidential  |  Page {page_num} of {len(pages_content)}",
            fontsize=8,
            color=(0.5, 0.5, 0.5)
        )
    file_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(file_path))
    doc.close()
    print(f"Generated PDF: {file_path}")

def generate_all():
    base_dir = Path(__file__).resolve().parent.parent / "sample_docs"

    # 1. Employee Handbook (Public / General)
    handbook_pages = [
        """1.0 Annual Leave & Paid Time Off (PTO) Policy
All regular full-time employees are entitled to 24 paid vacation days per calendar year, accrued monthly at a rate of 2.0 days per month. In addition, employees receive 10 designated statutory holidays and 8 emergency sick leave days. Unused vacation days up to a maximum of 5 days may be rolled over into the subsequent calendar year, but must be utilized prior to March 31st.

2.0 Flexible & Remote Work Framework
The enterprise operates on a structured hybrid model. Team members may work remotely up to two (2) days per standard working week, coordinated with their immediate department lead. Core collaboration hours across all time zones are 10:00 AM to 3:00 PM local time. High-speed home internet stipend of $75 per month is reimbursed automatically upon expense submission.""",

        """3.0 Professional Learning & Development Stipend
Every full-time team member has access to an annual $2,500 Learning and Development budget. Eligible expenses include industry certifications (AWS, GCP, CISA, PMP), technical books, conference attendance, and academic coursework. Reimbursement requests require prior manager sign-off via the HR portal.

4.0 Code of Conduct and Anti-Harassment
The organization maintains a zero-tolerance policy regarding harassment, discrimination, or retaliatory actions. All internal concerns may be escalated confidentially through the Integrity Helpline or submitted directly to People Operations without fear of adverse consequences."""
    ]
    create_sample_pdf(base_dir / "Employee_Handbook_General_Policy.pdf", "Employee Handbook & Corporate Policies", handbook_pages)

    # 2. Engineering Architecture (Internal / Engineering)
    engineering_pages = [
        """1.0 Cloud Infrastructure Overview & Microservices Architecture
The production platform is hosted on AWS with an active-active multi-region topology spanning us-east-1 (N. Virginia) and eu-central-1 (Frankfurt). All microservices are containerized via Docker and orchestrated with Amazon EKS (Elastic Kubernetes Service). Each microservice maintains dedicated ingress controllers, Envoy service mesh proxies, and isolated IAM roles.

2.0 High-Throughput Caching Tier
Data caching utilizes an Amazon ElastiCache Redis cluster version 7.1 with 16 distributed shards. Cluster settings enforce a maxmemory allocation of 32 GB per node with allkeys-lru eviction policy. Target cache hit ratios must maintain above 94.5% to protect underlying Aurora PostgreSQL database read replicas.""",

        """3.0 Canary Deployments & CI/CD Pipeline
Continuous delivery is driven via GitHub Actions and ArgoCD. Every pull request passes automated unit tests, SonarQube static security analysis, and container vulnerability scanning with Trivy. Production rollouts employ progressive canary deployments:
- Stage 1: 5% traffic routing for 15 minutes with automated error rate monitoring.
- Stage 2: 25% traffic routing for 30 minutes.
- Stage 3: 100% full cutover if p99 latency remains under 120ms and HTTP 5xx errors are below 0.01%.

4.0 Disaster Recovery & Recovery Point Objectives
Automated cross-region database snapshots execute every 4 hours. The Recovery Point Objective (RPO) is strictly designated at 15 minutes, while the Recovery Time Objective (RTO) is guaranteed at 45 minutes for full regional failover."""
    ]
    create_sample_pdf(base_dir / "Engineering_Cloud_Infrastructure.pdf", "Engineering Cloud Architecture & Infrastructure", engineering_pages)

    # 3. Q3 Confidential Financial Audit (Confidential / Finance)
    finance_pages = [
        """1.0 Executive Financial Summary - Q3 Performance
For the third quarter (Q3), consolidated enterprise gross revenue reached $48,250,000, representing an 18.4% year-over-year increase compared to Q3 of the prior fiscal year ($40,750,000). Total Annual Recurring Revenue (ARR) closed at $192,800,000. 

2.0 Profitability Margins & EBITDA
Adjusted EBITDA for the quarter was $12,740,000, yielding a strong EBITDA margin of 26.4%. Net dollar retention (NDR) across Tier-1 enterprise accounts reached 118.2%, driven primarily by expansion in AI analytics and security add-ons. Operating expenses (OpEx) were managed at $24,100,000, coming in 3.2% under forecast due to infrastructure optimizations.""",

        """3.0 Confidential Escrow & Project Falcon Acquisition Reserve
As approved by the Board of Directors, a dedicated reserve of $14,000,000 has been deposited into an interest-bearing escrow account with JPMorgan Chase. This capital is allocated specifically for the impending acquisition of Project Falcon (cloud security telemetry startup). Closing date is scheduled for December 15th, subject to regulatory clearance.

4.0 Free Cash Flow and Capital Expenditure
Free Cash Flow (FCF) for Q3 was $9,850,000, representing a 20.4% conversion rate from revenue. CapEx investments totaled $2,890,000, directed toward custom GPU server clusters for internal model inference."""
    ]
    create_sample_pdf(base_dir / "Q3_Confidential_Financial_Audit.pdf", "Q3 Confidential Financial Audit & Board Report", finance_pages)

    # 4. HR Executive Compensation (Restricted / HR / Exec)
    hr_pages = [
        """1.0 Restricted Executive Compensation Structure
This document contains classified compensation data accessible only to C-Level Executives and People Operations Leadership. The 2026 Executive Incentive Pool totals $12,500,000 in equity refresh grants and retention bonuses.

2.0 C-Suite Base Compensation & Equity Targets
- Chief Executive Officer (CEO): Base salary $650,000, Target Annual Bonus 100% ($650,000), Equity Pool Allocation 35%.
- Chief Technology Officer (CTO): Base salary $420,000, Target Annual Bonus 75% ($315,000), Equity Pool Allocation 22%.
- Chief People Officer (CPO): Base salary $380,000, Target Annual Bonus 60% ($228,000), Equity Pool Allocation 15%.
- Chief Financial Officer (CFO): Base salary $410,000, Target Annual Bonus 75% ($307,500), Equity Pool Allocation 20%.""",

        """3.0 Executive Retention & Severance Guarantees
In the event of a change-of-control transaction, a double-trigger acceleration clause applies to all unvested restricted stock units (RSUs) for executive committee members. Severance guarantees include eighteen (18) months of base salary continuation and full COBRA health benefit coverage for twenty-four (24) months.

4.0 Performance Multipliers for 2026
Bonus payouts are tied directly to three corporate scorecards:
1. Enterprise ARR growth exceeding $210M (40% weight).
2. Customer retention exceeding 95% (30% weight).
3. Operating cash flow margin reaching 28% (30% weight)."""
    ]
    create_sample_pdf(base_dir / "HR_Executive_Compensation_2026.pdf", "Executive Compensation & Incentive Program 2026", hr_pages)

if __name__ == "__main__":
    generate_all()
