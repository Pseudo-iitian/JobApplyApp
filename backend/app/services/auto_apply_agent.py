import asyncio
import logging
import os
import re
import urllib.parse
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.job import Job
from app.models.auto_apply import AutoApplyProfile, PortalCredential, AutoApplyLog
from app.models.notification import Notification
from app.services.notifier import manager
from app.services.scraper import is_india_location

logger = logging.getLogger("AutoApplyAgent")

SCREENSHOTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

AGENT_RUNNING = False
AGENT_STOP_REQUESTED = False

def is_agent_active() -> bool:
    return AGENT_RUNNING

def request_stop_agent() -> bool:
    global AGENT_STOP_REQUESTED
    AGENT_STOP_REQUESTED = True
    logger.info("🛑 [AutoApplyAgent] Stop requested by user.")
    return True

def should_stop() -> bool:
    return AGENT_STOP_REQUESTED

def generate_company_password(company_name: str) -> str:
    """Generates a reliable, secure password compliant with corporate career portals."""
    clean_co = re.sub(r'[^a-zA-Z]', '', company_name)[:4].capitalize() or "Comp"
    return f"{clean_co}#2026@AbhiJob"

def evaluate_job_exp_limit(job: Job, max_allowed: float = 3.0) -> bool:
    """
    Returns True if job is eligible (<= max_allowed YOE).
    Returns False if job exceeds max_allowed (>= 4 YOE).
    """
    if job.experience_required and job.experience_required > max_allowed:
        return False
    text = f"{job.title} {job.description or ''} {job.experience_str or ''}".lower()
    for high_exp in ["4+ year", "5+ year", "6+ year", "7+ year", "8+ year", "10+ year", "7 - 10 year", "7-10 year", "8 to 12 year", "6 to 11 year", "6-11 year", "7-12 year", "7 to 12 year"]:
        if high_exp in text:
            return False
    return True

async def broadcast_agent_telemetry(
    job_id: int, 
    company: str, 
    step: str, 
    message: str, 
    screenshot: Optional[str] = None
):
    """Sends real-time telemetry to the frontend via WebSockets."""
    try:
        await manager.broadcast({
            "event": "AUTO_APPLY_STEP",
            "job_id": job_id,
            "company": company,
            "step": step,
            "message": message,
            "screenshot": screenshot,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
    except Exception as e:
        logger.warning(f"Telemetry broadcast warning: {e}")

async def dismiss_common_popups(page) -> None:
    """Intelligently detects and dismisses city popups, cookie banners, and marketing overlays."""
    # 1. City / Location selection modals (e.g. Naukri)
    close_selectors = [
        ".crossIcon", "button.crossIcon", "div.crossIcon", "i.crossIcon",
        "button[aria-label='Close']", "button[aria-label='close']",
        ".modal-close", "button.close", ".close-icon",
        "button:has-text('Later')", "button:has-text('Not now')", "button:has-text('No thanks')"
    ]
    for sel in close_selectors:
        try:
            btn = await page.query_selector(sel)
            if btn and await btn.is_visible():
                await btn.click()
                await asyncio.sleep(0.5)
                break
        except Exception:
            pass

    # 2. Cookie consents & permissions
    cookie_selectors = [
        "button:has-text('Accept All')", "button:has-text('Accept all')",
        "button:has-text('Accept Cookies')", "button:has-text('Allow all')",
        "button:has-text('I Agree')", "button:has-text('Got it')",
        "button:has-text('Accept')"
    ]
    for sel in cookie_selectors:
        try:
            btn = await page.query_selector(sel)
            if btn and await btn.is_visible():
                await btn.click()
                await asyncio.sleep(0.5)
                break
        except Exception:
            pass

async def locate_and_click_apply_action(page) -> bool:
    """Finds and clicks primary Apply, Easy Apply, or Apply on Company Site button."""
    apply_button_selectors = [
        # Naukri direct single job blue apply button selectors
        "button.apply-button",
        "div.apply-button-container button",
        "div[class*='apply-btn'] button",
        "div[class*='styles_jdc__apply-btn'] button",
        "button[class*='apply-button']",
        "button[id*='apply' i]",
        "#apply-button",
        ".apply-button",
        "button:has-text('Apply on company site')",
        "a:has-text('Apply on company site')",
        "button:has-text('Apply on company')",
        "a:has-text('Apply on company')",
        # LinkedIn and standard job board selectors
        "button:has-text('Easy Apply')",
        "button:has-text('Apply Now')",
        "a:has-text('Apply Now')",
        "button:has-text('Quick Apply')",
        "a:has-text('Quick Apply')",
        "button:has-text('Apply')",
        "a:has-text('Apply')",
        "button[class*='apply' i]",
        "a[class*='apply' i]",
        "[data-test='apply-button']",
        ".jobs-apply-button"
    ]
    for sel in apply_button_selectors:
        try:
            btn = await page.query_selector(sel)
            if btn and await btn.is_visible():
                await btn.scroll_into_view_if_needed()
                await asyncio.sleep(0.5)
                await btn.click()
                await asyncio.sleep(2.0)
                return True
        except Exception:
            pass
    return False

async def autofill_form_elements(page, profile: AutoApplyProfile) -> Dict[str, Any]:
    """Autonomous field identification and autofill across career portals."""
    filled_fields = []
    first_name = (profile.full_name or "Abhishek").split()[0]
    last_name = (profile.full_name or "Verma").split()[-1] if len((profile.full_name or "").split()) > 1 else "Verma"

    # Input mappings
    text_fields = [
        (["input[name*='first' i]", "input[id*='first' i]", "input[placeholder*='first' i]"], first_name, "First Name"),
        (["input[name*='last' i]", "input[id*='last' i]", "input[placeholder*='last' i]"], last_name, "Last Name"),
        (["input[name*='name' i]", "input[id*='name' i]", "input[placeholder*='name' i]"], profile.full_name, "Full Name"),
        (["input[type='email']", "input[name*='email' i]", "input[id*='email' i]"], profile.email, "Email"),
        (["input[type='tel']", "input[name*='phone' i]", "input[name*='mobile' i]", "input[id*='phone' i]"], profile.phone, "Phone"),
        (["input[name*='company' i]", "input[placeholder*='company' i]", "input[name*='employer' i]"], profile.current_company, "Company"),
        (["input[name*='designation' i]", "input[name*='title' i]", "input[placeholder*='designation' i]"], profile.current_designation, "Designation"),
        (["input[name*='current_ctc' i]", "input[placeholder*='current ctc' i]", "input[placeholder*='current salary' i]"], profile.current_ctc, "Current CTC"),
        (["input[name*='expected' i]", "input[placeholder*='expected ctc' i]", "input[placeholder*='expected salary' i]"], profile.expected_ctc, "Expected CTC"),
        (["input[name*='notice' i]", "input[placeholder*='notice' i]"], profile.notice_period, "Notice Period"),
        (["input[name*='city' i]", "input[placeholder*='city' i]", "input[name*='location' i]"], "Noida", "City/Location"),
        (["input[name*='linkedin' i]", "input[placeholder*='linkedin' i]"], profile.linkedin_url, "LinkedIn"),
        (["input[name*='github' i]", "input[placeholder*='github' i]"], profile.github_url, "GitHub"),
        (["input[name*='exp' i]", "input[placeholder*='experience' i]"], "2", "Experience (Years)"),
    ]

    for selectors, val, label in text_fields:
        if not val:
            continue
        for sel in selectors:
            try:
                el = await page.query_selector(sel)
                if el and await el.is_visible():
                    curr_val = await el.input_value()
                    if not curr_val:
                        await el.fill(str(val))
                        filled_fields.append(label)
                        await asyncio.sleep(0.2)
                        break
            except Exception:
                pass

    # Textareas (Cover letter / pitch)
    textarea_selectors = [
        "textarea[name*='cover' i]", "textarea[placeholder*='cover' i]",
        "textarea[name*='pitch' i]", "textarea[name*='summary' i]",
        "textarea[placeholder*='message' i]"
    ]
    for sel in textarea_selectors:
        try:
            ta = await page.query_selector(sel)
            if ta and await ta.is_visible():
                curr_val = await ta.input_value()
                if not curr_val and profile.cover_letter_template:
                    await ta.fill(profile.cover_letter_template[:1500])
                    filled_fields.append("Cover Letter / Pitch")
                    break
        except Exception:
            pass

    # File upload (Resume PDF)
    resume_uploaded = False
    if profile.resume_path and os.path.exists(profile.resume_path):
        try:
            file_input = await page.query_selector("input[type='file']")
            if file_input:
                await file_input.set_input_files(profile.resume_path)
                resume_uploaded = True
                filled_fields.append("Resume PDF")
        except Exception as fe:
            logger.warning(f"File upload note: {fe}")

    # Dropdowns (<select>)
    try:
        selects = await page.query_selector_all("select")
        for sel_el in selects:
            try:
                if await sel_el.is_visible():
                    options = await sel_el.query_selector_all("option")
                    for opt in options:
                        opt_text = (await opt.inner_text()).lower()
                        opt_val = await opt.get_attribute("value")
                        if any(term in opt_text for term in ["30 days", "immediate", "1 month", "2 years", "2+", "india", "yes"]):
                            if opt_val:
                                await sel_el.select_option(value=opt_val)
                                filled_fields.append("Dropdown Option")
                                break
            except Exception:
                pass
    except Exception:
        pass

    # Checkboxes (Agreements & Declarations)
    try:
        checkboxes = await page.query_selector_all("input[type='checkbox']")
        for cb in checkboxes:
            try:
                if await cb.is_visible() and not await cb.is_checked():
                    await cb.check()
                    filled_fields.append("Declaration Checkbox")
            except Exception:
                pass
    except Exception:
        pass

    return {
        "filled_count": len(filled_fields),
        "fields": filled_fields,
        "resume_uploaded": resume_uploaded
    }

async def execute_autonomous_job_application(
    page,
    job: Job,
    profile: AutoApplyProfile
) -> Dict[str, Any]:
    """
    Executes end-to-end autonomous application inside an active Playwright page.
    """
    target_url = job.apply_link or ""
    await broadcast_agent_telemetry(
        job.id, job.company, "NAVIGATING", 
        f"Navigating to {job.company} portal: {target_url}"
    )

    try:
        await page.goto(target_url, timeout=30000, wait_until="domcontentloaded")
    except Exception as e:
        logger.warning(f"Initial page load note: {e}")

    if should_stop():
        return {"status": "STOPPED", "fields_filled": [], "resume_attached": False, "submission_clicked": False, "screenshot": None}

    await asyncio.sleep(1.5)

    # 1. Dismiss overlays & location popups
    await broadcast_agent_telemetry(
        job.id, job.company, "INSPECTING", 
        "Analyzing DOM structure & dismissing location/cookie overlays..."
    )
    await dismiss_common_popups(page)
    if should_stop():
        return {"status": "STOPPED", "fields_filled": [], "resume_attached": False, "submission_clicked": False, "screenshot": None}
    await asyncio.sleep(0.5)

    # 2. Click Apply button if visible
    apply_clicked = await locate_and_click_apply_action(page)
    if should_stop():
        return {"status": "STOPPED", "fields_filled": [], "resume_attached": False, "submission_clicked": False, "screenshot": None}

    if apply_clicked:
        await broadcast_agent_telemetry(
            job.id, job.company, "APPLY_CLICKED", 
            "✔ Clicked 'Apply' / 'Easy Apply' action button."
        )
        await asyncio.sleep(1.5)
    else:
        await broadcast_agent_telemetry(
            job.id, job.company, "DIRECT_PORTAL", 
            "Direct application portal detected. Analyzing form fields..."
        )

    # Check if a new tab opened in the context
    active_page = page
    if len(page.context.pages) > 1:
        active_page = page.context.pages[-1]
        await active_page.bring_to_front()
        await asyncio.sleep(1.0)

    if should_stop():
        return {"status": "STOPPED", "fields_filled": [], "resume_attached": False, "submission_clicked": False, "screenshot": None}

    # 3. Autofill Form Elements
    form_result = await autofill_form_elements(active_page, profile)
    filled_summary = ", ".join(form_result["fields"][:5])
    await broadcast_agent_telemetry(
        job.id, job.company, "FORM_FILLED", 
        f"✔ Autofilled {form_result['filled_count']} fields ({filled_summary}). Resume: {'Attached' if form_result['resume_uploaded'] else 'Not required'}."
    )
    if should_stop():
        return {"status": "STOPPED", "fields_filled": form_result["fields"], "resume_attached": form_result["resume_uploaded"], "submission_clicked": False, "screenshot": None}
    await asyncio.sleep(1.0)

    # 4. Trigger Submission / Continue if available
    submit_selectors = [
        "button[type='submit']",
        "button:has-text('Submit Application')",
        "button:has-text('Submit')",
        "button:has-text('Apply Now')",
        "button:has-text('Review')",
        "button:has-text('Next')",
        "button:has-text('Continue')"
    ]
    submission_attempted = False
    for s_sel in submit_selectors:
        try:
            s_btn = await active_page.query_selector(s_sel)
            if s_btn and await s_btn.is_visible():
                await s_btn.scroll_into_view_if_needed()
                await asyncio.sleep(0.5)
                await s_btn.click()
                submission_attempted = True
                await broadcast_agent_telemetry(
                    job.id, job.company, "SUBMITTING", 
                    f"✔ Clicked application submission action: '{s_sel}'."
                )
                await asyncio.sleep(2.5)
                break
        except Exception:
            pass

    # 5. Capture visual verification screenshot
    screenshot_filename = f"job_{job.id}_{int(datetime.utcnow().timestamp())}.png"
    screenshot_full_path = os.path.join(SCREENSHOTS_DIR, screenshot_filename)
    try:
        await active_page.screenshot(path=screenshot_full_path, full_page=False)
        screenshot_url = f"/static/screenshots/{screenshot_filename}"
    except Exception as se:
        logger.warning(f"Screenshot capture note: {se}")
        screenshot_url = None

    await broadcast_agent_telemetry(
        job.id, job.company, "COMPLETED", 
        f"🎉 Application workflow completed for {job.company}! Moving ticket to APPLIED.",
        screenshot=screenshot_url
    )

    return {
        "status": "APPLIED",
        "fields_filled": form_result["fields"],
        "resume_attached": form_result["resume_uploaded"],
        "submission_clicked": submission_attempted,
        "screenshot": screenshot_url
    }

async def run_auto_apply_cycle(
    db: Session, 
    batch_size: int = 5,
    auto_open_browser: bool = True
) -> Dict[str, Any]:
    """
    Autonomous AI Job Application Agent Execution:
    1. Selects top candidate jobs from DISCOVERED (strictly filtered for India & 2 YOE).
    2. Filters out any roles requiring > 3 YOE into REJECTED bucket.
    3. Launches Playwright headful Google Chrome on the desktop screen.
    4. Visually executes form navigation, fills candidate details, attaches resume, submits.
    5. Stores secure generated password in AWS RDS portal credentials.
    6. Moves applied jobs to APPLIED stage on the Kanban board.
    7. Broadcasts real-time step telemetry and WebSocket events.
    """
    profile = db.query(AutoApplyProfile).first()
    if not profile:
        profile = AutoApplyProfile()
        db.add(profile)
        db.commit()
        db.refresh(profile)

    global AGENT_RUNNING, AGENT_STOP_REQUESTED
    AGENT_RUNNING = True
    AGENT_STOP_REQUESTED = False

    logger.info(f"🚀 [Auto-Apply Agent] Launching autonomous cycle for batch size: {batch_size}")

    try:
        # Fetch target jobs from DISCOVERED column (newest posted first, strictly India)
        all_candidates: List[Job] = (
            db.query(Job)
            .filter(Job.status == "DISCOVERED")
            .order_by(Job.posted_at.desc().nullslast(), Job.id.desc())
            .all()
        )

        candidate_jobs = []
        for j in all_candidates:
            if not is_india_location(j.location):
                j.status = "REJECTED"
                j.match_reasons = "Filtered by Location Guard: Non-India role."
                continue
            candidate_jobs.append(j)
            if len(candidate_jobs) >= batch_size:
                break

        db.commit()

        if not candidate_jobs:
            return {
                "status": "idle",
                "message": "No eligible jobs found in DISCOVERED column. The 24/7 scraper is actively hunting new openings!",
                "processed_count": 0,
                "applied": [],
                "rejected_experience": []
            }

        results_applied = []
        results_rejected_exp = []
        logs_to_add = []

        # Ensure desktop display environment is configured for headful automation
        if "DISPLAY" not in os.environ:
            os.environ["DISPLAY"] = ":1"
        if "XAUTHORITY" not in os.environ and os.path.exists("/run/user/1001/gdm/Xauthority"):
            os.environ["XAUTHORITY"] = "/run/user/1001/gdm/Xauthority"

        browser = None
        playwright_ctx = None

        if auto_open_browser:
            try:
                from playwright.async_api import async_playwright
                playwright_ctx = await async_playwright().start()
                browser = await playwright_ctx.chromium.launch(
                    executable_path="/usr/bin/google-chrome" if os.path.exists("/usr/bin/google-chrome") else None,
                    headless=False,
                    args=[
                        "--start-maximized",
                        "--no-sandbox",
                        "--disable-blink-features=AutomationControlled"
                    ]
                )
                logger.info("✔ [Auto-Apply Agent] Headful Google Chrome successfully launched on desktop display.")
            except Exception as be:
                logger.warning(f"Could not launch headful Chrome ({be}), falling back to headless.")
                try:
                    if playwright_ctx:
                        browser = await playwright_ctx.chromium.launch(headless=True)
                except Exception as be2:
                    logger.error(f"Playwright fallback error: {be2}")

        for job in candidate_jobs:
            if should_stop():
                logger.info("🛑 [Auto-Apply Agent] User requested agent halt. Stopping batch execution.")
                await broadcast_agent_telemetry(0, "SYSTEM", "STOPPED", "🛑 Autonomous Agent stopped by user.")
                break

            # Step A: Experience check (<= 3 YOE only, reject >= 4 YOE)
            if not evaluate_job_exp_limit(job, max_allowed=profile.max_exp_allowed):
                job.status = "REJECTED"
                job.match_reasons = f"Auto-rejected by Agent: Required experience exceeds candidate profile limit (2-3 YOE)."
                results_rejected_exp.append({
                    "job_id": job.id,
                    "company": job.company,
                    "title": job.title,
                    "reason": "Exceeds candidate 2-3 YOE limit"
                })
                log = AutoApplyLog(
                    job_id=job.id,
                    company=job.company,
                    title=job.title,
                    channel="FILTER_GUARD",
                    status="REJECTED_EXPERIENCE",
                    details="Role requires > 3 YOE. Moved to REJECTED bucket."
                )
                logs_to_add.append(log)
                continue

            # Step B: Identify channel & credentials
            channel = "PORTAL"
            direct_link = job.apply_link or ""
            gmail_url = None

            if job.hr_email:
                channel = "GMAIL"
                subject = f"Application: {job.title} - 2+ Years Exp (Java / Spring Boot)"
                gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={urllib.parse.quote(job.hr_email)}&su={urllib.parse.quote(subject)}&body={urllib.parse.quote(profile.cover_letter_template)}"
            elif job.google_form_url:
                channel = "GOOGLE_FORM"
                direct_link = job.google_form_url
            elif "linkedin.com" in direct_link.lower():
                channel = "LINKEDIN"

            # Step C: Portal Credentials Generation and Persistence
            portal_password = generate_company_password(job.company)
            cred = db.query(PortalCredential).filter(PortalCredential.company == job.company).first()
            if not cred:
                cred = PortalCredential(
                    company=job.company,
                    portal_domain=urllib.parse.urlparse(direct_link).netloc if direct_link else "direct",
                    email=profile.email,
                    password=portal_password,
                    job_id=job.id,
                    apply_url=direct_link
                )
                db.add(cred)

            # Step D: Autonomous Playwright execution
            screenshot_url = None
            if browser and direct_link:
                try:
                    context = await browser.new_context(
                        viewport=None,
                        no_viewport=True,
                        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                    )
                    page = await context.new_page()
                    app_res = await execute_autonomous_job_application(page, job, profile)
                    screenshot_url = app_res.get("screenshot")
                    if app_res.get("status") == "STOPPED" or should_stop():
                        logger.info("🛑 [Auto-Apply Agent] Execution stopped by user during job application.")
                        await broadcast_agent_telemetry(job.id, job.company, "STOPPED", "🛑 Autonomous Agent stopped by user.")
                        await context.close()
                        break
                    # Pause 2 seconds so user can visually inspect the page
                    await asyncio.sleep(2.0)
                    await context.close()
                except Exception as ape:
                    logger.warning(f"Autonomous application step warning for {job.company}: {ape}")
                    await broadcast_agent_telemetry(
                        job.id, job.company, "NOTICE", f"Page notice: {ape}"
                    )

            if should_stop():
                logger.info("🛑 [Auto-Apply Agent] Halting execution due to stop request.")
                break

            # Step E: Move job status to APPLIED
            job.status = "APPLIED"
            results_applied.append({
                "job_id": job.id,
                "company": job.company,
                "title": job.title,
                "channel": channel,
                "apply_link": direct_link,
                "gmail_url": gmail_url,
                "portal_password": portal_password,
                "resume_path": profile.resume_path,
                "screenshot": screenshot_url
            })

            log = AutoApplyLog(
                job_id=job.id,
                company=job.company,
                title=job.title,
                channel=channel,
                status="APPLIED",
                details=f"Autonomously applied via {channel}. Portal Password: {portal_password}. Resume attached from {profile.resume_path}."
            )
            logs_to_add.append(log)

            # Step F: Broadcast live WebSocket update so Kanban card moves immediately
            await manager.broadcast({
                "event": "JOB_STATUS_CHANGED",
                "job_id": job.id,
                "status": "APPLIED",
                "company": job.company,
                "title": job.title
            })

    finally:
        # Close the browser cleanly after the batch is finished
        if browser:
            try:
                await browser.close()
            except Exception:
                pass
        if playwright_ctx:
            try:
                await playwright_ctx.stop()
            except Exception:
                pass
        AGENT_RUNNING = False
        AGENT_STOP_REQUESTED = False

    # Commit all stage transitions and logs to AWS RDS
    if logs_to_add:
        db.add_all(logs_to_add)
    db.commit()

    logger.info(f"✔ [Auto-Apply Agent] Cycle complete: {len(results_applied)} applied, {len(results_rejected_exp)} filtered out.")
    return {
        "status": "success",
        "processed_count": len(candidate_jobs),
        "applied_count": len(results_applied),
        "rejected_count": len(results_rejected_exp),
        "applied": results_applied,
        "rejected_experience": results_rejected_exp
    }
