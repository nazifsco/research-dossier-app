"""
Research pipeline service.
Orchestrates the research scripts to generate dossiers.
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config import get_settings
from app.database import SessionLocal
from app.models.research import ResearchJob
from app.models.user import User
from app.services.email import send_report_ready_email

settings = get_settings()

# Path to execution scripts
# Navigate from: webapp/backend/app/services/research.py -> project root
_THIS_FILE = Path(__file__).resolve()
_PROJECT_ROOT = _THIS_FILE.parent.parent.parent.parent.parent  # Go up 5 levels to project root
SCRIPTS_PATH = _PROJECT_ROOT / "execution"
OUTPUT_BASE = _PROJECT_ROOT / ".tmp"

# Debug: print paths on module load
print(f"[Research Service] Scripts path: {SCRIPTS_PATH} (exists: {SCRIPTS_PATH.exists()})")
print(f"[Research Service] Output path: {OUTPUT_BASE} (exists: {OUTPUT_BASE.exists()})")


def run_script(script_name: str, **kwargs) -> dict:
    """Run an execution script and return its JSON output."""
    script_path = SCRIPTS_PATH / script_name

    if not script_path.exists():
        return {"success": False, "error": f"Script not found: {script_name}"}

    # Build command with arguments (keep underscores as scripts use them)
    cmd = [sys.executable, str(script_path)]
    for key, value in kwargs.items():
        if value is not None:
            cmd.extend([f"--{key}", str(value)])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=str(SCRIPTS_PATH.parent)
        )

        if result.returncode == 0:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"success": True, "output": result.stdout}
        else:
            return {"success": False, "error": result.stderr or "Script failed"}

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Script timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_research_pipeline(
    job_id: str,
    target: str,
    target_type: str,
    depth: str = "standard"
) -> None:
    """
    Run the full research pipeline for a job.
    Updates job status in database as it progresses.
    """
    db = SessionLocal()

    try:
        # Get job and mark as processing
        job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
        if not job:
            return

        job.status = "processing"
        job.started_at = datetime.utcnow()
        db.commit()

        # Create output directory
        safe_target = "".join(c for c in target if c.isalnum() or c in " -_").strip().replace(" ", "_")
        output_dir = OUTPUT_BASE / f"research_{safe_target}_{job_id[:8]}"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Phase 1: Web Search
        search_result = run_script(
            "search_web.py",
            query=target,
            num_results=20,
            output=str(output_dir / "01_search_results.json")
        )

        # Phase 1.5: Fetch top search result pages for detailed content
        pages_dir = output_dir / "03_pages"
        pages_dir.mkdir(exist_ok=True)

        search_file = output_dir / "01_search_results.json"
        if search_file.exists():
            try:
                with open(search_file, "r", encoding="utf-8") as f:
                    search_data = json.load(f)

                # Fetch top 8 pages (skip common low-value sites)
                skip_domains = ['youtube.com', 'twitter.com', 'facebook.com', 'instagram.com', 'linkedin.com/posts']
                fetched = 0
                for i, result in enumerate(search_data.get("results", [])):
                    if fetched >= 8:
                        break

                    url = result.get("url", "")
                    if not url or any(skip in url for skip in skip_domains):
                        continue

                    # Create safe filename
                    safe_name = f"page_{fetched+1:02d}"
                    page_result = run_script(
                        "fetch_webpage.py",
                        url=url,
                        output=str(pages_dir / f"{safe_name}.json"),
                        timeout=20
                    )
                    fetched += 1
            except Exception as e:
                print(f"[Research] Error fetching pages: {e}")

        # Phase 2: Fetch News
        news_result = run_script(
            "fetch_news.py",
            query=target,
            days=90,
            max_results=20,
            output=str(output_dir / "04_news.json")
        )

        # Phase 3: Wikipedia (if available)
        wiki_result = run_script(
            "fetch_wikipedia.py",
            query=target,
            entity_type=target_type,
            output=str(output_dir / "07_wikipedia.json")
        )

        # Phase 4: Financials (for companies)
        if target_type == "company":
            # Search for ticker by company name
            financials_result = run_script(
                "fetch_financials.py",
                company=target,  # Will search for ticker by company name
                output=str(output_dir / "05_financials.json")
            )

            # SEC Edgar for US public companies
            sec_result = run_script(
                "fetch_sec_edgar.py",
                company=target,
                output=str(output_dir / "08_sec_edgar.json")
            )

        # Phase 5: Social presence
        social_result = run_script(
            "fetch_social.py",
            target=target,
            output=str(output_dir / "06_social.json")
        )

        # Phase 6: Analyze collected data (basic analysis for metadata)
        analyze_result = run_script(
            "analyze_research.py",
            research_dir=str(output_dir),
            output=str(output_dir / "09_analysis.json")
        )

        # Phase 7: Generate dossier
        # Use LLM-powered generator if OpenAI API key is available
        if settings.openai_api_key:
            print(f"[Research] Using LLM-powered dossier generation")
            dossier_result = run_script(
                "generate_dossier_llm.py",
                research_dir=str(output_dir),
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                target=target,
                target_type=target_type
            )
        else:
            print(f"[Research] Using basic dossier generation (no OpenAI key)")
            dossier_result = run_script(
                "generate_dossier.py",
                research_dir=str(output_dir),
                format="markdown"
            )

        # Phase 8: Convert to styled HTML
        dossier_md_path = output_dir / "DOSSIER.md"
        report_html_path = output_dir / "REPORT.html"

        if dossier_md_path.exists():
            html_result = run_script(
                "md_to_styled_html.py",
                input=str(dossier_md_path),
                output=str(report_html_path)
            )

        # Check if report was generated
        if report_html_path.exists():
            job.status = "completed"
            job.report_path = str(report_html_path)
            job.report_url = f"/api/research/{job_id}/download"
        elif dossier_md_path.exists():
            # Fallback to markdown
            job.status = "completed"
            job.report_path = str(dossier_md_path)
            job.report_url = f"/api/research/{job_id}/download"
        else:
            job.status = "failed"
            job.error_message = "Failed to generate report"
            # Refund credits on failure
            user = db.query(User).filter(User.id == job.user_id).first()
            if user:
                user.credits += job.credits_used
                db.add(user)

        job.completed_at = datetime.utcnow()
        db.commit()

        # Send email notification when complete
        if job.status == "completed":
            user = db.query(User).filter(User.id == job.user_id).first()
            if user:
                try:
                    send_report_ready_email(job, user)
                except Exception as email_err:
                    print(f"Failed to send email notification: {email_err}")

    except Exception as e:
        # Mark job as failed and refund credits
        job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            # Refund credits
            user = db.query(User).filter(User.id == job.user_id).first()
            if user:
                user.credits += job.credits_used
                db.add(user)
            db.commit()

    finally:
        db.close()
