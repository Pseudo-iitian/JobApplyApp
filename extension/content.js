// JobApplyApp - 1-Click AI Form Filler Content Script
// Specially tuned for Indian Tech Career Portals (Virtusa, Workday, Naukri, LinkedIn, Greenhouse, etc.)

(() => {
  // Prevent duplicate script injection
  if (window.__JOBAPPLY_INJECTED__) return;
  window.__JOBAPPLY_INJECTED__ = true;

  // Default candidate profile for Abhishek Verma (Rapipay Fintech Developer, 2+ YOE)
  let candidateProfile = {
    title: "Mr.",
    firstName: "Abhishek",
    lastName: "Verma",
    fullName: "Abhishek Verma",
    email: "abhishek.verma.6561@gmail.com",
    phoneCountryCode: "+91",
    countryCodeName: "India",
    phone: "6307801566", // Strictly 10 digits
    country: "India",
    state: "Uttar Pradesh",
    city: "Noida",
    zipCode: "201301",
    addressLine1: "Sector 62, Electronic City",
    addressLine2: "Noida, Uttar Pradesh",
    currentCompany: "Rapipay Fintech Private Limited",
    currentDesignation: "Backend Software Engineer",
    totalExperience: "2",
    totalExperienceYears: "2.2",
    currentCtc: "9.5 LPA",
    currentCtcNum: "950000",
    expectedCtc: "15 LPA",
    expectedCtcNum: "1500000",
    noticePeriod: "30 Days",
    noticePeriodServing: "Serving Notice Period",
    availableIn30Days: "Yes",
    workAuthIndia: "Yes",
    requireSponsorship: "No",
    gender: "Male",
    linkedin: "https://www.linkedin.com/in/abhishek-verma-backend",
    github: "https://github.com/AbhishekVerma-dev",
    skills: "Java 17, Spring Boot, Microservices, PostgreSQL, Apache Kafka, Redis, Docker, REST APIs, AWS",
    summary: "Backend Software Engineer with 2+ years experience building fintech platforms at Rapipay using Java 17, Spring Boot, Microservices, PostgreSQL, Kafka, and Redis."
  };

  // Attempt to sync latest profile from JobApplyApp local backend if available
  try {
    fetch("http://localhost:8000/api/auto-apply/profile")
      .then(res => res.json())
      .then(data => {
        if (data) {
          if (data.full_name) {
            candidateProfile.fullName = data.full_name;
            const parts = data.full_name.trim().split(/\s+/);
            candidateProfile.firstName = parts[0] || "Abhishek";
            candidateProfile.lastName = parts.slice(1).join(" ") || "Verma";
          }
          if (data.email) candidateProfile.email = data.email;
          if (data.phone) {
            // Strip any leading +91 or 91 so it stays strictly 10 digits
            const digits = data.phone.replace(/\D/g, "");
            candidateProfile.phone = digits.length > 10 ? digits.slice(-10) : digits;
          }
          if (data.current_company) candidateProfile.currentCompany = data.current_company;
          if (data.current_designation) candidateProfile.currentDesignation = data.current_designation;
          if (data.current_ctc) candidateProfile.currentCtc = data.current_ctc;
          if (data.expected_ctc) candidateProfile.expectedCtc = data.expected_ctc;
          if (data.notice_period) candidateProfile.noticePeriod = data.notice_period;
          if (data.linkedin_url) candidateProfile.linkedin = data.linkedin_url;
          if (data.github_url) candidateProfile.github = data.github_url;
        }
      })
      .catch(() => {
        // Fallback silently to embedded profile
      });
  } catch (e) {}

  // Helper to trigger real framework input/change events for React, Angular, Vue
  function setFieldValue(el, val) {
    if (!el || val === undefined || val === null) return false;
    try {
      el.focus();
      const proto = el instanceof HTMLTextAreaElement ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
      const nativeSetter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
      if (nativeSetter) {
        nativeSetter.call(el, String(val));
      } else {
        el.value = String(val);
      }
      el.dispatchEvent(new Event('input', { bubbles: true, composed: true }));
      el.dispatchEvent(new Event('change', { bubbles: true, composed: true }));
      el.dispatchEvent(new Event('blur', { bubbles: true, composed: true }));

      el.classList.add('jobapply-field-highlight');
      setTimeout(() => el.classList.remove('jobapply-field-highlight'), 3000);
      return true;
    } catch (err) {
      console.warn("Set field error:", err);
      return false;
    }
  }

  // Helper to select option in standard <select> elements
  function setSelectValue(selectEl, searchTerms) {
    if (!selectEl || !selectEl.options) return false;
    const terms = Array.isArray(searchTerms) ? searchTerms.map(t => String(t).toLowerCase().trim()) : [String(searchTerms).toLowerCase().trim()];
    
    // First try exact match
    for (let i = 0; i < selectEl.options.length; i++) {
      const opt = selectEl.options[i];
      const optText = (opt.text || "").toLowerCase().trim();
      const optVal = (opt.value || "").toLowerCase().trim();
      for (const term of terms) {
        if (optText === term || optVal === term) {
          selectEl.selectedIndex = i;
          selectEl.dispatchEvent(new Event('change', { bubbles: true }));
          selectEl.classList.add('jobapply-field-highlight');
          setTimeout(() => selectEl.classList.remove('jobapply-field-highlight'), 3000);
          return true;
        }
      }
    }

    // Then try partial match
    for (let i = 0; i < selectEl.options.length; i++) {
      const opt = selectEl.options[i];
      const optText = (opt.text || "").toLowerCase().trim();
      const optVal = (opt.value || "").toLowerCase().trim();
      for (const term of terms) {
        if ((optText.includes(term) || optVal.includes(term)) && optText !== "select" && optText !== "please select") {
          selectEl.selectedIndex = i;
          selectEl.dispatchEvent(new Event('change', { bubbles: true }));
          selectEl.classList.add('jobapply-field-highlight');
          setTimeout(() => selectEl.classList.remove('jobapply-field-highlight'), 3000);
          return true;
        }
      }
    }
    return false;
  }

  // Get field context (id, name, placeholder, label, container text)
  function getFieldContext(el) {
    const id = (el.id || "").toLowerCase();
    const name = (el.name || "").toLowerCase();
    const placeholder = (el.placeholder || "").toLowerCase();
    const aria = (el.getAttribute("aria-label") || "").toLowerCase();
    
    let labelText = "";
    if (el.id) {
      const lbl = document.querySelector(`label[for="${el.id}"]`);
      if (lbl) labelText = lbl.innerText.toLowerCase();
    }
    if (!labelText && el.closest('label')) {
      labelText = el.closest('label').innerText.toLowerCase();
    }
    
    // Also check closest parent container (e.g. .form-group, .field, etc)
    let containerText = "";
    const parent = el.closest('div, td, li, section');
    if (parent) {
      containerText = parent.innerText.slice(0, 100).toLowerCase();
    }

    return `${id} ${name} ${placeholder} ${aria} ${labelText} ${containerText}`;
  }

  // Main Form Autofill Execution
  function executeAutofill() {
    let filledCount = 0;
    const filledItems = [];

    // 1. SELECT DROPDOWNS (e.g. Title, Country Code, Country, State, Experience, Notice Period)
    const selects = document.querySelectorAll('select');
    selects.forEach(sel => {
      const ctx = getFieldContext(sel);

      // Title / Salutation (Mr / Ms)
      if (ctx.match(/\b(title|salutation|honorific)\b/)) {
        if (setSelectValue(sel, ["Mr.", "Mr", "Mister"])) {
          filledCount++;
          filledItems.push("Title (Mr.)");
        }
      }
      // Phone Country Code
      else if (ctx.match(/\b(country\s*code|dial\s*code|isd|phone.*code)\b/)) {
        if (setSelectValue(sel, ["+91", "91", "India (+91)", "India (91)", "India"])) {
          filledCount++;
          filledItems.push("Country Code (+91)");
        }
      }
      // Country
      else if (ctx.match(/\b(country|nation)\b/) && !ctx.includes("code")) {
        if (setSelectValue(sel, ["India", "IN", "IND"])) {
          filledCount++;
          filledItems.push("Country (India)");
        }
      }
      // State / Province
      else if (ctx.match(/\b(state|province|region)\b/)) {
        if (setSelectValue(sel, ["Uttar Pradesh", "UP", "Delhi", "Haryana", "Karnataka"])) {
          filledCount++;
          filledItems.push("State (Uttar Pradesh)");
        }
      }
      // Notice Period
      else if (ctx.match(/\b(notice\s*period|notice|availability)\b/)) {
        if (setSelectValue(sel, ["30 days", "1 month", "Serving notice period", "Serving notice", "Immediate", "< 30 days"])) {
          filledCount++;
          filledItems.push("Notice Period (30 Days)");
        }
      }
      // Experience
      else if (ctx.match(/\b(experience|yoe|exp)\b/)) {
        if (setSelectValue(sel, ["2 years", "2 - 3", "2+", "2", "1 - 3 years", "1-3"])) {
          filledCount++;
          filledItems.push("Experience (2 Yrs)");
        }
      }
      // Legal authorization
      else if (ctx.match(/\b(authorized|eligible|legally)\b/)) {
        if (setSelectValue(sel, ["Yes", "true"])) {
          filledCount++;
          filledItems.push("Work Authorization (Yes)");
        }
      }
      // Visa sponsorship
      else if (ctx.match(/\b(sponsorship|visa)\b/)) {
        if (setSelectValue(sel, ["No", "false"])) {
          filledCount++;
          filledItems.push("Sponsorship Required (No)");
        }
      }
      // Gender
      else if (ctx.match(/\b(gender|sex)\b/)) {
        if (setSelectValue(sel, ["Male", "M"])) {
          filledCount++;
          filledItems.push("Gender (Male)");
        }
      }
    });

    // 2. INPUT & TEXTAREA FIELDS
    const inputs = document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="checkbox"]):not([type="radio"]), textarea');
    inputs.forEach(inp => {
      const ctx = getFieldContext(inp);
      const isTextarea = inp instanceof HTMLTextAreaElement;

      // First Name
      if (ctx.match(/\b(first\s*name|fname|given\s*name)\b/) && !ctx.includes("last")) {
        if (setFieldValue(inp, candidateProfile.firstName)) {
          filledCount++;
          filledItems.push("First Name");
        }
      }
      // Last Name
      else if (ctx.match(/\b(last\s*name|lname|surname|family\s*name)\b/)) {
        if (setFieldValue(inp, candidateProfile.lastName)) {
          filledCount++;
          filledItems.push("Last Name");
        }
      }
      // Full Name (only if not distinct first/last name field)
      else if (ctx.match(/\b(full\s*name|candidate\s*name|applicant\s*name)\b/) || (ctx.match(/\bname\b/) && !ctx.includes("user") && !ctx.includes("company") && !ctx.includes("file"))) {
        if (setFieldValue(inp, candidateProfile.fullName)) {
          filledCount++;
          filledItems.push("Full Name");
        }
      }
      // Email
      else if (inp.type === "email" || ctx.match(/\b(email|e-mail)\b/)) {
        if (setFieldValue(inp, candidateProfile.email)) {
          filledCount++;
          filledItems.push("Email");
        }
      }
      // Phone Number (Strictly 10 digits without +91 prefix to prevent Virtusa length validation error!)
      else if (inp.type === "tel" || ctx.match(/\b(phone|mobile|contact\s*no|telephone|cell)\b/)) {
        if (!ctx.includes("code") && !ctx.includes("dial")) {
          if (setFieldValue(inp, candidateProfile.phone)) {
            filledCount++;
            filledItems.push("Phone (10 Digits)");
          }
        }
      }
      // City
      else if (ctx.match(/\b(city|town|district)\b/)) {
        if (setFieldValue(inp, candidateProfile.city)) {
          filledCount++;
          filledItems.push("City (Noida)");
        }
      }
      // State
      else if (ctx.match(/\b(state|province|region)\b/)) {
        if (setFieldValue(inp, candidateProfile.state)) {
          filledCount++;
          filledItems.push("State (UP)");
        }
      }
      // Zip / Postal Code
      else if (ctx.match(/\b(zip|postal|pincode|pin\s*code)\b/)) {
        if (setFieldValue(inp, candidateProfile.zipCode)) {
          filledCount++;
          filledItems.push("Zip Code (201301)");
        }
      }
      // Address Line 1
      else if (ctx.match(/\b(address\s*line\s*1|address1|street\s*1)\b/) || (ctx.match(/\baddress\b/) && !ctx.includes("email") && !ctx.includes("2"))) {
        if (setFieldValue(inp, candidateProfile.addressLine1)) {
          filledCount++;
          filledItems.push("Address Line 1");
        }
      }
      // Address Line 2
      else if (ctx.match(/\b(address\s*line\s*2|address2|street\s*2|apartment|suite)\b/)) {
        if (setFieldValue(inp, candidateProfile.addressLine2)) {
          filledCount++;
          filledItems.push("Address Line 2");
        }
      }
      // Current Company / Employer
      else if (ctx.match(/\b(current\s*company|present\s*company|employer|current\s*organization)\b/)) {
        if (setFieldValue(inp, candidateProfile.currentCompany)) {
          filledCount++;
          filledItems.push("Current Company (Rapipay)");
        }
      }
      // Designation / Title
      else if (ctx.match(/\b(designation|current\s*title|current\s*role|job\s*title)\b/)) {
        if (setFieldValue(inp, candidateProfile.currentDesignation)) {
          filledCount++;
          filledItems.push("Designation");
        }
      }
      // Total Experience (in Years)
      else if (ctx.match(/\b(total\s*exp|experience\s*in\s*years|overall\s*exp|years\s*of\s*exp|yoe)\b/)) {
        if (setFieldValue(inp, candidateProfile.totalExperience)) {
          filledCount++;
          filledItems.push("Experience (2 Yrs)");
        }
      }
      // Current CTC
      else if (ctx.match(/\b(current\s*ctc|current\s*salary|current\s*compensation|present\s*ctc)\b/)) {
        const val = inp.type === "number" ? candidateProfile.currentCtcNum : candidateProfile.currentCtc;
        if (setFieldValue(inp, val)) {
          filledCount++;
          filledItems.push("Current CTC (9.5 LPA)");
        }
      }
      // Expected CTC
      else if (ctx.match(/\b(expected\s*ctc|expected\s*salary|expected\s*compensation)\b/)) {
        const val = inp.type === "number" ? candidateProfile.expectedCtcNum : candidateProfile.expectedCtc;
        if (setFieldValue(inp, val)) {
          filledCount++;
          filledItems.push("Expected CTC (15 LPA)");
        }
      }
      // Notice Period
      else if (ctx.match(/\b(notice\s*period|notice\s*time)\b/)) {
        const val = inp.type === "number" ? "30" : candidateProfile.noticePeriod;
        if (setFieldValue(inp, val)) {
          filledCount++;
          filledItems.push("Notice Period (30 Days)");
        }
      }
      // LinkedIn URL
      else if (ctx.match(/\b(linkedin|linked\s*in)\b/)) {
        if (setFieldValue(inp, candidateProfile.linkedin)) {
          filledCount++;
          filledItems.push("LinkedIn URL");
        }
      }
      // GitHub URL
      else if (ctx.match(/\b(github|git)\b/)) {
        if (setFieldValue(inp, candidateProfile.github)) {
          filledCount++;
          filledItems.push("GitHub URL");
        }
      }
      // Cover Letter / Summary / Pitch
      else if (isTextarea || ctx.match(/\b(cover\s*letter|pitch|summary|about\s*yourself|message)\b/)) {
        if (setFieldValue(inp, candidateProfile.summary)) {
          filledCount++;
          filledItems.push("Cover Letter / Pitch");
        }
      }
    });

    // 3. RADIO BUTTONS & CHECKBOXES
    const radios = document.querySelectorAll('input[type="radio"], input[type="checkbox"]');
    radios.forEach(rb => {
      const ctx = getFieldContext(rb);
      if (rb.type === "radio") {
        const val = (rb.value || "").toLowerCase();
        // Legally authorized to work -> YES
        if (ctx.match(/\b(authorized|legally|eligible\s*to\s*work)\b/) && (val === "yes" || val === "true" || ctx.includes("yes"))) {
          if (!rb.checked) {
            rb.click();
            filledCount++;
          }
        }
        // Require visa sponsorship -> NO
        else if (ctx.match(/\b(sponsorship|visa)\b/) && (val === "no" || val === "false" || ctx.includes("no"))) {
          if (!rb.checked) {
            rb.click();
            filledCount++;
          }
        }
      } else if (rb.type === "checkbox") {
        // Privacy / Terms / Declaration
        if (ctx.match(/\b(terms|privacy|agree|declare|declaration|acknowledg)\b/) && !rb.checked) {
          rb.click();
          filledCount++;
        }
      }
    });

    // Show Feedback Toast
    showToast(filledCount, filledItems);
  }

  // Visual Toast Message on Page
  function showToast(count, items) {
    let oldToast = document.getElementById('jobapply-autofill-toast');
    if (oldToast) oldToast.remove();

    const toast = document.createElement('div');
    toast.id = 'jobapply-autofill-toast';
    
    if (count > 0) {
      const summaryList = items.slice(0, 5).join(", ");
      const extra = items.length > 5 ? ` +${items.length - 5} more` : "";
      toast.innerHTML = `
        <div style="font-size: 24px; line-height: 1;">⚡</div>
        <div style="flex: 1;">
          <div style="font-weight: 700; font-size: 14px; color: #38bdf8;">
            ✨ ${count} Fields Autofilled for Abhishek Verma!
          </div>
          <div style="font-size: 12px; color: #cbd5e1; margin-top: 4px; line-height: 1.4;">
            Filled: ${summaryList}${extra}.
          </div>
        </div>
        <button id="jobapply-toast-close" style="background: none; border: none; color: #94a3b8; font-size: 16px; cursor: pointer; padding: 2px;">✕</button>
      `;
    } else {
      toast.innerHTML = `
        <div style="font-size: 22px; line-height: 1;">ℹ️</div>
        <div style="flex: 1;">
          <div style="font-weight: 700; font-size: 13px; color: #f59e0b;">
            Form Fields Scanned
          </div>
          <div style="font-size: 12px; color: #cbd5e1; margin-top: 2px;">
            No empty supported fields found on this active tab or step.
          </div>
        </div>
        <button id="jobapply-toast-close" style="background: none; border: none; color: #94a3b8; font-size: 16px; cursor: pointer;">✕</button>
      `;
    }

    document.body.appendChild(toast);

    const closeBtn = document.getElementById('jobapply-toast-close');
    if (closeBtn) closeBtn.onclick = () => toast.remove();

    setTimeout(() => {
      if (toast && toast.parentNode) {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.4s ease';
        setTimeout(() => toast.remove(), 400);
      }
    }, 5000);
  }

  // Create and inject the floating round button ("gol sa side me icon")
  function injectFloatingActionIcon() {
    if (document.getElementById('jobapply-autofill-fab-container')) return;

    const container = document.createElement('div');
    container.id = 'jobapply-autofill-fab-container';

    container.innerHTML = `
      <div id="jobapply-autofill-tooltip">
        ✨ Autofill (Top) | 📥 1-Click Save to Kanban (Bottom)
      </div>
      <button id="jobapply-autofill-fab" title="1-Click Autofill Abhishek's Profile">
        <svg viewBox="0 0 24 24">
          <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
          <circle cx="12" cy="12" r="3" fill="#38bdf8"/>
        </svg>
      </button>
      <button id="jobapply-save-job-fab" title="📥 1-Click Save this Opening/Career Page to JobApplyApp DISCOVERED" style="width: 44px; height: 44px; border-radius: 50%; background: #10b981; border: 2px solid #ffffff; box-shadow: 0 6px 16px rgba(16, 185, 129, 0.45); display: flex; align-items: center; justify-content: center; cursor: pointer; color: white; margin-top: 8px; transition: transform 0.2s ease; outline: none;">
        <span style="font-size: 20px;">📥</span>
      </button>
    `;

    const target = document.body || document.documentElement;
    if (!target) {
      setTimeout(injectFloatingActionIcon, 100);
      return;
    }

    target.appendChild(container);
    console.log("⚡ [JobApplyApp] 1-Click Autofill & Save Floating Icons injected successfully!");

    const fab = document.getElementById('jobapply-autofill-fab');
    if (fab) {
      fab.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();

        fab.style.transform = 'scale(0.9) rotate(45deg)';
        setTimeout(() => {
          fab.style.transform = '';
          executeAutofill();
        }, 150);
      });
    }

    const saveFab = document.getElementById('jobapply-save-job-fab');
    if (saveFab) {
      saveFab.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        saveCurrentPageToJobApply();
      });
    }

    // Draggable functionality so user can drag it up or down to avoid blocking forms
    let isDragging = false;
    let startY = 0;
    let startTop = 0;

    fab?.addEventListener('mousedown', (e) => {
      if (e.button !== 0) return;
      isDragging = false;
      startY = e.clientY;
      const rect = container.getBoundingClientRect();
      startTop = rect.top;

      const onMouseMove = (moveEvent) => {
        const dy = moveEvent.clientY - startY;
        if (Math.abs(dy) > 5) {
          isDragging = true;
          container.style.top = `${startTop + dy}px`;
          container.style.transform = 'none';
        }
      };

      const onMouseUp = () => {
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
      };

      document.addEventListener('mousemove', onMouseMove);
      document.addEventListener('mouseup', onMouseUp);
    });
  }

  function saveCurrentPageToJobApply() {
    const pageTitle = (document.title || "Career Opening").trim();
    const url = window.location.href;
    const hostname = window.location.hostname.replace('www.', '');
    const bodyText = (document.body ? document.body.innerText : "").slice(0, 3500);

    // Extract HR email if present on page
    const emails = bodyText.match(/([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)/g);
    let hrEmail = null;
    if (emails) {
      const valid = emails.filter(em => !['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'].some(ext => em.toLowerCase().endsWith('.' + ext)));
      if (valid.length > 0) hrEmail = valid[0];
    }

    let compName = hostname.split('.')[0];
    compName = compName.charAt(0).toUpperCase() + compName.slice(1);

    showToastMessage(`⏳ Sending "${compName}" opening to DISCOVERED...`);

    fetch("http://localhost:8000/api/jobs/discovered-post", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: pageTitle.slice(0, 100),
        company: compName,
        location: "Noida / Bangalore / India",
        experience_str: "1 - 2 Years Exp",
        description: bodyText,
        post_url: url,
        apply_link: url,
        hr_email: hrEmail,
        google_form_url: null,
        source: "Universal Web / Career Portal"
      })
    })
    .then(async res => {
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Server rejected job");
      }
      return data;
    })
    .then(saved => {
      showToastMessage(`🎉 Saved "${compName}: ${pageTitle.slice(0, 30)}" to DISCOVERED!`);
    })
    .catch(err => {
      showToastMessage(`❌ Save failed: ${err.message || err}`);
    });
  }

  // Inject when DOM is ready and keep alive across SPA step transitions
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectFloatingActionIcon);
  } else {
    injectFloatingActionIcon();
  }

  // Periodic check to ensure floating icon stays visible if SPA re-renders the body
  setInterval(() => {
    if (!document.getElementById('jobapply-autofill-fab-container')) {
      injectFloatingActionIcon();
    }
  }, 1500);

  // Listen for extension popup or shortcut messages
  if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.onMessage) {
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      if (request.action === "TRIGGER_AUTOFILL") {
        executeAutofill();
        sendResponse({ status: "success" });
      } else if (request.action === "START_LINKEDIN_HUNTER") {
        startLinkedInAutoScroll();
        sendResponse({ status: "hunting_started" });
      } else if (request.action === "STOP_LINKEDIN_HUNTER") {
        stopLinkedInAutoScroll();
        sendResponse({ status: "hunting_stopped" });
      } else if (request.action === "SWITCH_LINKEDIN_STREAM") {
        switchToStream(request.streamIndex !== undefined ? request.streamIndex : 0);
        sendResponse({ status: "stream_switched" });
      }
    });
  }

  // ==============================================================================
  // LINKEDIN LIVE MULTI-STREAM AUTO-HUNTER AGENT
  // Dedicated to cycling LinkedIn Search Posts for:
  // 1. "Java Backend Developer"
  // 2. "Java Developer"
  // 3. "Software Engineer" (Java)
  // Sorted by "date_posted" (latest first, max 2-3 days old only!).
  // Filters candidate qualifications: 2 YOE (specifically 1 to 3 and 2 to 5 years).
  // Extracts: Canonical Post URL, External Apply / Portal link, Recruiter HR Email.
  // Sends verified jobs straight to JobApplyApp Kanban DISCOVERED!
  // ==============================================================================
  const LINKEDIN_STREAMS = [
    {
      id: "java-backend",
      label: "Java Backend Dev",
      tabLabel: "☕ Java Backend",
      query: "Java Backend Developer",
      url: "https://www.linkedin.com/search/results/content/?keywords=Java%20Backend%20Developer&sortBy=%22date_posted%22"
    },
    {
      id: "java-dev",
      label: "Java Developer",
      tabLabel: "⚡ Java Dev",
      query: "Java Developer",
      url: "https://www.linkedin.com/search/results/content/?keywords=Java%20Developer&sortBy=%22date_posted%22"
    },
    {
      id: "software-engineer",
      label: "Software Engineer",
      tabLabel: "💻 Software Eng",
      query: "Software Engineer Java",
      url: "https://www.linkedin.com/search/results/content/?keywords=Software%20Engineer%20Java&sortBy=%22date_posted%22"
    }
  ];

  function detectStreamFromUrl() {
    const href = window.location.href.toLowerCase();
    if (href.includes("java%20backend") || href.includes("java+backend") || href.includes("backend%20developer")) {
      return 0;
    } else if (href.includes("software%20engineer") || href.includes("software+engineer")) {
      return 2;
    } else if (href.includes("java%20developer") || href.includes("java+developer") || href.includes("keywords=java")) {
      return 1;
    }
    return 0;
  }

  let linkedInHunterActive = false;
  let linkedInScrollTimer = null;
  let currentStreamIndex = detectStreamFromUrl();
  let autoRotateStreams = true;
  let discoveredCount = 0;
  let scrollCount = 0;
  let totalCheckedCount = 0;

  // Restore session state across LinkedIn SPA navigation or page refresh
  try {
    const sActive = sessionStorage.getItem('jobapply_hunter_active');
    if (sActive === 'true') linkedInHunterActive = true;
    const sIdx = sessionStorage.getItem('jobapply_stream_idx');
    if (sIdx !== null) currentStreamIndex = parseInt(sIdx, 10) || 0;
    const sRotate = sessionStorage.getItem('jobapply_auto_rotate');
    if (sRotate !== null) autoRotateStreams = (sRotate === 'true');
    const sDisc = sessionStorage.getItem('jobapply_discovered_count');
    if (sDisc !== null) discoveredCount = parseInt(sDisc, 10) || 0;
    const sCheck = sessionStorage.getItem('jobapply_checked_count');
    if (sCheck !== null) totalCheckedCount = parseInt(sCheck, 10) || 0;
  } catch(e) {}

  function isLinkedInDomain() {
    return window.location.hostname.includes("linkedin.com");
  }

  function switchToStream(index) {
    if (index < 0 || index >= LINKEDIN_STREAMS.length) index = 0;
    currentStreamIndex = index;
    try {
      sessionStorage.setItem('jobapply_stream_idx', String(currentStreamIndex));
      sessionStorage.setItem('jobapply_hunter_active', 'true');
      sessionStorage.setItem('jobapply_auto_rotate', autoRotateStreams ? 'true' : 'false');
      sessionStorage.setItem('jobapply_discovered_count', String(discoveredCount));
      sessionStorage.setItem('jobapply_checked_count', String(totalCheckedCount));
    } catch(e) {}
    showToastMessage(`🚀 Navigating to stream: ${LINKEDIN_STREAMS[index].label}...`);
    window.location.href = LINKEDIN_STREAMS[index].url;
  }

  function rotateToNextStream() {
    const nextIndex = (currentStreamIndex + 1) % LINKEDIN_STREAMS.length;
    showToastMessage(`🔄 Auto-cycling to next stream: ${LINKEDIN_STREAMS[nextIndex].label}...`);
    switchToStream(nextIndex);
  }

  function performHunterScroll(amount = 700) {
    // 1. Window scroll
    try { window.scrollBy(0, amount); } catch(e) {}

    // 2. documentElement & scrollingElement
    try {
      if (document.scrollingElement) {
        document.scrollingElement.scrollTop += amount;
      }
      if (document.documentElement) {
        document.documentElement.scrollTop += amount;
      }
      if (document.body) {
        document.body.scrollTop += amount;
      }
    } catch(e) {}

    // 3. Scrollable internal containers on LinkedIn
    try {
      const candidates = document.querySelectorAll(
        '.scaffold-layout__main, main, .authentication-outlet, div.scaffold-finite-scroll, div[tabindex="-1"]'
      );
      candidates.forEach(el => {
        if (el.scrollHeight > el.clientHeight) {
          el.scrollTop += amount;
        }
      });
    } catch(e) {}

    // 4. Auto-click LinkedIn's floating "New posts" pill if it appears
    try {
      const newPills = document.querySelectorAll(
        '.feed-new-update-pill, button.feed-new-update-pill__btn, button[aria-label*="new update"], button[aria-label*="new post"]'
      );
      newPills.forEach(p => {
        try { p.click(); } catch(e) {}
      });
    } catch(e) {}
  }

  function refreshLinkedInFeed() {
    showToastMessage("🔄 Refreshing LinkedIn stream for latest posts...");
    const statusMsg = document.getElementById('jobapply-hunter-status-msg');
    if (statusMsg) statusMsg.innerHTML = "🔄 <span style='color:#38bdf8'>Reloading fresh posts...</span>";

    // Try clicking floating "New posts" button first
    const pill = document.querySelector('.feed-new-update-pill, button.feed-new-update-pill__btn, button[aria-label*="new update"], button[aria-label*="new post"]');
    if (pill) {
      pill.click();
      return;
    }

    // Scroll back to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
    if (document.scrollingElement) document.scrollingElement.scrollTop = 0;

    // Trigger stream reload
    setTimeout(() => {
      window.location.reload();
    }, 600);
  }

  function injectLinkedInHunterBar() {
    if (!isLinkedInDomain()) return;
    if (document.getElementById('jobapply-linkedin-hunter-bar')) return;

    const currentStream = LINKEDIN_STREAMS[currentStreamIndex] || LINKEDIN_STREAMS[0];

    const bar = document.createElement('div');
    bar.id = 'jobapply-linkedin-hunter-bar';
    bar.innerHTML = `
      <div class="jobapply-hunter-header">
        <div class="jobapply-hunter-title">
          <span>⚡ LinkedIn Java Hunter</span>
        </div>
        <span id="jobapply-hunter-badge" style="font-size: 10px; background: rgba(56, 189, 248, 0.2); color: #38bdf8; padding: 2px 6px; border-radius: 4px; font-weight: 700;">
          Abhishek (2 YOE)
        </span>
      </div>

      <!-- 3 Search Streams Tabs -->
      <div class="jobapply-hunter-stream-tabs" style="display:flex; gap:4px; margin-bottom:8px;">
        <button id="jobapply-tab-0" class="jobapply-stream-tab ${currentStreamIndex === 0 ? 'jobapply-stream-tab-active' : ''}" style="flex:1; font-size:10px; padding:5px 2px; border-radius:6px; cursor:pointer; font-weight:700; border:1px solid #334155; background:${currentStreamIndex === 0 ? '#0284c7' : '#1e293b'}; color:${currentStreamIndex === 0 ? '#fff' : '#94a3b8'};">
          ☕ Java Backend
        </button>
        <button id="jobapply-tab-1" class="jobapply-stream-tab ${currentStreamIndex === 1 ? 'jobapply-stream-tab-active' : ''}" style="flex:1; font-size:10px; padding:5px 2px; border-radius:6px; cursor:pointer; font-weight:700; border:1px solid #334155; background:${currentStreamIndex === 1 ? '#0284c7' : '#1e293b'}; color:${currentStreamIndex === 1 ? '#fff' : '#94a3b8'};">
          ⚡ Java Dev
        </button>
        <button id="jobapply-tab-2" class="jobapply-stream-tab ${currentStreamIndex === 2 ? 'jobapply-stream-tab-active' : ''}" style="flex:1; font-size:10px; padding:5px 2px; border-radius:6px; cursor:pointer; font-weight:700; border:1px solid #334155; background:${currentStreamIndex === 2 ? '#0284c7' : '#1e293b'}; color:${currentStreamIndex === 2 ? '#fff' : '#94a3b8'};">
          💻 Software Eng
        </button>
      </div>

      <div class="jobapply-hunter-stats">
        <div>Stream: <strong id="jobapply-current-stream-name" style="color:#38bdf8">${currentStream.label}</strong> (Posts / Latest)</div>
        <div style="margin-top: 3px; font-size: 11px;">
          Checked: <strong id="jobapply-checked-count">${totalCheckedCount}</strong> | Saved: <strong id="jobapply-post-count" style="color: #10b981;">${discoveredCount}</strong> to Kanban
        </div>
        <div id="jobapply-hunter-status-msg" style="color: #94a3b8; font-size: 11px; margin-top: 3px; font-weight: 500;">
          ${linkedInHunterActive ? "🟢 <span style='color:#10b981'>Active: Scrolling & Scanning...</span>" : "⏸ Idle - Click Start to Auto-Hunt"}
        </div>
      </div>

      <!-- Auto-Rotate Toggle -->
      <div style="display:flex; align-items:center; justify-content:space-between; margin-top:6px; margin-bottom:8px; font-size:11px; color:#cbd5e1; background:#1e293b; padding:4px 8px; border-radius:6px; border:1px solid #334155;">
        <label for="jobapply-rotate-toggle" style="cursor:pointer; display:flex; align-items:center; gap:5px; font-weight:600;">
          <input type="checkbox" id="jobapply-rotate-toggle" ${autoRotateStreams ? 'checked' : ''} style="cursor:pointer;" />
          <span>🔁 Cycle 3 Streams & Refresh</span>
        </label>
        <span style="font-size:10px; color:#38bdf8;">Max 2-3 Days</span>
      </div>

      <div class="jobapply-hunter-actions" style="display:flex; flex-direction:column; gap:6px;">
        <button id="jobapply-btn-autoscroll" class="jobapply-hunter-btn ${linkedInHunterActive ? 'jobapply-hunter-btn-active' : ''}" style="background: ${linkedInHunterActive ? '#10b981' : '#0284c7'}; color:#fff; font-weight:700; cursor:pointer;">
          ${linkedInHunterActive ? "⏸ Pause Auto-Hunter" : "▶ Start Auto-Hunter (Continuous)"}
        </button>
        <div style="display:flex; gap:6px;">
          <button id="jobapply-btn-scan-now" class="jobapply-hunter-btn" style="background: #334155; flex:1; cursor:pointer;">
            ⚡ Scan Now
          </button>
          <button id="jobapply-btn-refresh-feed" class="jobapply-hunter-btn" style="background: #1e293b; color:#38bdf8; border:1px solid #0284c7; flex:1; cursor:pointer;">
            🔄 Refresh / Next
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(bar);

    // Event listeners
    document.getElementById('jobapply-tab-0')?.addEventListener('click', (e) => {
      e.preventDefault();
      switchToStream(0);
    });
    document.getElementById('jobapply-tab-1')?.addEventListener('click', (e) => {
      e.preventDefault();
      switchToStream(1);
    });
    document.getElementById('jobapply-tab-2')?.addEventListener('click', (e) => {
      e.preventDefault();
      switchToStream(2);
    });

    document.getElementById('jobapply-rotate-toggle')?.addEventListener('change', (e) => {
      autoRotateStreams = e.target.checked;
      try {
        sessionStorage.setItem('jobapply_auto_rotate', autoRotateStreams ? 'true' : 'false');
      } catch(err) {}
      showToastMessage(autoRotateStreams ? "🔁 Auto-stream rotation enabled." : "⏸ Fixed stream mode enabled.");
    });

    document.getElementById('jobapply-btn-autoscroll')?.addEventListener('click', (e) => {
      e.preventDefault();
      toggleLinkedInAutoScroll();
    });

    document.getElementById('jobapply-btn-scan-now')?.addEventListener('click', (e) => {
      e.preventDefault();
      scanLinkedInPosts();
      showToastMessage(`⚡ Scanned visible posts! Checked: ${totalCheckedCount}, Saved: ${discoveredCount}`);
    });

    document.getElementById('jobapply-btn-refresh-feed')?.addEventListener('click', (e) => {
      e.preventDefault();
      if (autoRotateStreams) {
        rotateToNextStream();
      } else {
        refreshLinkedInFeed();
      }
    });
  }

  function toggleLinkedInAutoScroll() {
    if (linkedInHunterActive) {
      stopLinkedInAutoScroll();
    } else {
      startLinkedInAutoScroll();
    }
  }

  function startLinkedInAutoScroll() {
    linkedInHunterActive = true;
    scrollCount = 0;
    try {
      sessionStorage.setItem('jobapply_hunter_active', 'true');
    } catch(e) {}

    const btn = document.getElementById('jobapply-btn-autoscroll');
    if (btn) {
      btn.innerText = "⏸ Pause Auto-Hunter";
      btn.style.background = "#10b981";
      btn.classList.add('jobapply-hunter-btn-active');
    }
    const statusMsg = document.getElementById('jobapply-hunter-status-msg');
    const streamName = (LINKEDIN_STREAMS[currentStreamIndex] || LINKEDIN_STREAMS[0]).label;
    if (statusMsg) statusMsg.innerHTML = `🟢 <span style='color:#10b981'>Active: Hunting [${streamName}]...</span>`;

    showToastMessage(`🚀 LinkedIn Auto-Hunter Started for ${streamName}!`);

    // Immediate first scan & scroll
    scanLinkedInPosts();
    performHunterScroll(500);

    // Continuous visible scrolling every 1.6 seconds
    if (linkedInScrollTimer) clearInterval(linkedInScrollTimer);
    linkedInScrollTimer = setInterval(() => {
      if (!linkedInHunterActive) return;

      scrollCount++;
      performHunterScroll(650);
      scanLinkedInPosts();

      const statusEl = document.getElementById('jobapply-hunter-status-msg');
      if (statusEl) {
        statusEl.innerHTML = `🟢 Scrolling (#${scrollCount}) | Checked: ${totalCheckedCount} | Saved: <strong style="color:#10b981">${discoveredCount}</strong>`;
      }

      // After 28 scrolls (approx 45 seconds of deep feed scanning):
      // Either advance to the next stream (cycling all 3 search queries) or refresh current feed!
      if (scrollCount >= 28) {
        scrollCount = 0;
        if (autoRotateStreams) {
          rotateToNextStream();
        } else {
          refreshLinkedInFeed();
        }
      }
    }, 1600);
  }

  function stopLinkedInAutoScroll() {
    linkedInHunterActive = false;
    try {
      sessionStorage.setItem('jobapply_hunter_active', 'false');
    } catch(e) {}

    if (linkedInScrollTimer) {
      clearInterval(linkedInScrollTimer);
      linkedInScrollTimer = null;
    }
    const btn = document.getElementById('jobapply-btn-autoscroll');
    if (btn) {
      btn.innerText = "▶ Start Auto-Hunter (Continuous)";
      btn.style.background = "#0284c7";
      btn.classList.remove('jobapply-hunter-btn-active');
    }
    const statusMsg = document.getElementById('jobapply-hunter-status-msg');
    if (statusMsg) statusMsg.innerHTML = "⏸ <span style='color:#94a3b8'>Paused. Click Start to resume.</span>";

    showToastMessage("⏸ Auto-Hunter Paused.");
  }

  function scanLinkedInPosts() {
    if (!isLinkedInDomain()) return;

    // Expand truncated "...see more" buttons so full text is parsed
    const seeMoreBtns = document.querySelectorAll(
      '.feed-shared-inline-show-more-text button, button[aria-label*="see more"], .see-more'
    );
    seeMoreBtns.forEach(btn => {
      try { btn.click(); } catch (e) {}
    });

    // Find all feed post cards & job cards (handles feed/foryou, feed, and search streams)
    const postCards = document.querySelectorAll(
      'div.feed-shared-update-v2, div[data-urn*="activity"], div[data-id*="activity"], div[data-view-name*="feed-full-update"], div[data-view-name*="feed-update"], div.occludable-update, div.job-card-container, li.jobs-search-results__list-item'
    );

    postCards.forEach(card => {
      if (card.dataset.jobapplyScanned === "true") return;
      card.dataset.jobapplyScanned = "true";
      totalCheckedCount++;
      try {
        sessionStorage.setItem('jobapply_checked_count', String(totalCheckedCount));
      } catch(e) {}

      const checkedEl = document.getElementById('jobapply-checked-count');
      if (checkedEl) checkedEl.innerText = String(totalCheckedCount);

      const rawText = card.innerText || "";
      const text = rawText.toLowerCase();
      if (!text) return;

      // 1. Check for Java / Spring Boot / Backend / Software Engineering cues
      const hasRelevantRole = (
        text.includes("java") ||
        text.includes("spring") ||
        text.includes("springboot") ||
        text.includes("backend") ||
        text.includes("back-end") ||
        text.includes("back end") ||
        text.includes("software engineering") ||
        text.includes("software engineer") ||
        text.includes("software developer") ||
        text.includes("microservice") ||
        text.includes("micro-service") ||
        text.includes("sde") ||
        text.includes("sde 1") ||
        text.includes("sde-1") ||
        text.includes("sde 2") ||
        text.includes("sde-2") ||
        text.includes("api") ||
        text.includes("apis") ||
        text.includes("rest api")
      );
      if (!hasRelevantRole) return;

      // Filter out pure frontend roles that have no backend/java relevance
      if ((text.includes("frontend developer") || text.includes("front-end developer") || text.includes("react developer") || text.includes("angular developer")) && !text.includes("java") && !text.includes("backend")) {
        return;
      }

      // 2. Check for hiring / referral cues
      const hasHiring = (
        text.includes("#hiring") ||
        text.includes("hiring") ||
        text.includes("we are hiring") ||
        text.includes("looking for") ||
        text.includes("immediate opening") ||
        text.includes("immediate requirement") ||
        text.includes("urgent requirement") ||
        text.includes("job opening") ||
        text.includes("opening for") ||
        text.includes("referral") ||
        text.includes("share resume") ||
        text.includes("drop cv") ||
        text.includes("drop resume") ||
        text.includes("send cv") ||
        text.includes("send resume") ||
        text.includes("reach out") ||
        text.includes("apply") ||
        text.includes("dm me")
      );
      if (!hasHiring && !card.classList.contains('job-card-container')) return;

      // 3. Strict 2 YOE experience check (Candidate: Abhishek Verma, 2 YOE)
      // User requirement: Matches posts for Java Developer with 2 years of experience,
      // specifically 1 to 3 years OR 2 to 5 years (and 2 YOE variants: 1-2, 2-4, 2-3, 0-2, 2+, 1+, 2 yrs).
      const isSeniorLeadership = (
        text.includes("principal") ||
        text.includes("architect") ||
        text.includes("tech lead") ||
        text.includes("team lead") ||
        text.includes("vp ") ||
        text.includes("vice president") ||
        text.includes("engineering manager") ||
        text.includes("staff engineer") ||
        text.includes("lead java") ||
        text.includes("lead backend") ||
        text.includes("sr. java") ||
        text.includes("senior java") ||
        text.includes("director of engineering") ||
        text.includes("head of engineering")
      );
      if (isSeniorLeadership) return;

      // Find role experience ranges (e.g. 1-3 years, 2-5 years, 2-4 years, 1-2 years)
      const rangeRegex = /(\d+(?:\.\d+)?)\s*(?:-|to|–)\s*(\d+(?:\.\d+)?)\s*(?:\+)?\s*(?:years?|yrs?|yoe)(?!\s*ago)/gi;
      let rangeMatch;
      let eligibleRange = null;
      let seniorRangeRequired = false;

      while ((rangeMatch = rangeRegex.exec(text)) !== null) {
        const low = parseFloat(rangeMatch[1]);
        const high = parseFloat(rangeMatch[2]);
        // Ignore company age (e.g. 10-15 years in business, 15+ years of excellence)
        if (low >= 8.0) continue;

        // 2 YOE meets ranges where minimum required is <= 2.5 (e.g. 1-3, 2-5, 2-4, 1-2, 2-3, 0-2, 1-4)
        if (low <= 2.5 && high >= 1.0) {
          if (!eligibleRange) eligibleRange = `${Math.round(low)} - ${Math.round(high)} Years Exp`;
        } else if (low > 3.0) {
          seniorRangeRequired = true;
        }
      }
      if (seniorRangeRequired && !eligibleRange) return;

      // Find single-number experience cues if no range found yet
      let eligibleSingle = null;
      let seniorSingleRequired = false;

      // X+ years
      const plusRegex = /(\d+(?:\.\d+)?)\s*\+\s*(?:years?|yrs?|yoe)/gi;
      let plusMatch;
      while ((plusMatch = plusRegex.exec(text)) !== null) {
        const val = parseFloat(plusMatch[1]);
        if (val >= 8.0) continue; // Skip company age
        if (val <= 2.5) {
          if (!eligibleSingle) eligibleSingle = `${Math.round(val)}+ Years Exp`;
        } else if (val > 3.0) {
          seniorSingleRequired = true;
        }
      }

      // Minimum X years
      const minRegex = /(?:minimum|at\s+least|min\.?)\s*(?:of\s+)?(\d+(?:\.\d+)?)\s*(?:years?|yrs?|yoe)/gi;
      let minMatch;
      while ((minMatch = minRegex.exec(text)) !== null) {
        const val = parseFloat(minMatch[1]);
        if (val >= 8.0) continue;
        if (val <= 2.5) {
          if (!eligibleSingle) eligibleSingle = `${Math.round(val)}+ Years Exp`;
        } else if (val > 3.0) {
          seniorSingleRequired = true;
        }
      }

      // Standalone 'X years of experience'
      const exactRegex = /(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s*(?:of)?\s*(?:\w+\s+){0,3}(?:experience|exp)/gi;
      let exactMatch;
      while ((exactMatch = exactRegex.exec(text)) !== null) {
        const val = parseFloat(exactMatch[1]);
        if (val >= 8.0) continue;
        if (val <= 2.5) {
          if (!eligibleSingle) eligibleSingle = `${Math.round(val)} Years Exp`;
        } else if (val > 3.0) {
          seniorSingleRequired = true;
        }
      }

      if (seniorSingleRequired && !eligibleRange && !eligibleSingle) return;

      // 3b. STRICT 2-3 DAYS RECENCY FILTER (Latest first, max 2-3 days old only!)
      const timeElem = card.querySelector(
        '.update-components-actor__sub-description, ' +
        '.update-components-actor__sub-description-link, ' +
        '.feed-shared-actor__sub-description, ' +
        '.update-components-actor__meta-link, ' +
        'time, ' +
        '.feed-shared-actor__sub-description-link, ' +
        '.update-components-actor__supplementary-actor-info, ' +
        'span.visually-hidden'
      );
      const timeRaw = timeElem ? timeElem.innerText.toLowerCase().trim() : '';
      let postDateStr = "Today";

      if (timeRaw) {
        const isOlderThan3Days = (
          /\b(?:[4-9]d|[1-9]\d+d|[1-9]\d*w|[1-9]\d*mo|[1-9]\d*yr|month|year|week)\b/i.test(timeRaw) ||
          timeRaw.includes('4d') || timeRaw.includes('5d') || timeRaw.includes('6d') || timeRaw.includes('7d') ||
          timeRaw.includes('week') || timeRaw.includes('month') || timeRaw.includes('year') ||
          timeRaw.includes('4 days') || timeRaw.includes('5 days') || timeRaw.includes('6 days') || timeRaw.includes('7 days')
        );
        if (isOlderThan3Days) {
          return; // Skip stale post (> 3 days old)
        }

        if (timeRaw.includes('1d') || timeRaw.includes('1 day')) postDateStr = "1 day ago";
        else if (timeRaw.includes('2d') || timeRaw.includes('2 days')) postDateStr = "2 days ago";
        else if (timeRaw.includes('3d') || timeRaw.includes('3 days')) postDateStr = "3 days ago";
        else if (timeRaw.includes('h') || timeRaw.includes('m') || timeRaw.includes('now') || timeRaw.includes('today')) postDateStr = "Today";
        else postDateStr = "Recent";
      }

      const expStr = eligibleRange || eligibleSingle || "2 Years Exp";

      // 4. Extract Post Details
      const authorElem = card.querySelector('.update-components-actor__name, .feed-shared-actor__name, .update-components-actor__title, .job-card-container__primary-description');
      const headlineElem = card.querySelector('.update-components-actor__description, .feed-shared-actor__description, .update-components-actor__sub-description');
      const authorName = authorElem ? authorElem.innerText.trim() : "LinkedIn Recruiter";
      const authorHeadline = headlineElem ? headlineElem.innerText.trim() : "Tech Network";

      // 4b. Detect Real Company Name & Role Title from Post Body
      let postTitle = `Java / Backend Developer (${expStr}) - ${authorName}`;
      let postCompany = authorHeadline ? `${authorName} (${authorHeadline.slice(0, 35)})` : authorName;

      const mHiring1 = rawText.match(/([A-Za-z0-9\.\s]+?)\s+is\s+Hiring\s*[\|\-:\–]\s*([^\n\r]+)/i);
      if (mHiring1 && mHiring1[1].trim().length < 40 && mHiring1[2].trim().length < 80) {
        postCompany = mHiring1[1].trim();
        postTitle = mHiring1[2].trim();
      } else {
        const mHiring2 = rawText.match(/Hiring\s*:\s*([^\n\r@]+?)\s*[@|at]\s*([A-Za-z0-9\.\s]+)/i);
        if (mHiring2 && mHiring2[2].trim().length < 40) {
          postTitle = mHiring2[1].trim();
          postCompany = mHiring2[2].trim();
        }
      }

      // 4c. Canonical LinkedIn Post URL Extraction
      let postUrl = "";

      // 1. Direct URN attributes
      const urnSource = card.hasAttribute('data-urn') ? card.getAttribute('data-urn') : (card.getAttribute('data-id') || card.getAttribute('data-chameleon-urn'));
      if (urnSource) {
        const m = urnSource.match(/urn:li:(?:activity|ugcPost|share):(\d+)/);
        if (m) {
          postUrl = `https://www.linkedin.com/feed/update/urn:li:activity:${m[1]}/`;
        }
      }

      // 2. Child with data-urn or data-id
      if (!postUrl) {
        const childUrn = card.querySelector('[data-urn*="activity"], [data-id*="activity"]');
        if (childUrn) {
          const raw = childUrn.getAttribute('data-urn') || childUrn.getAttribute('data-id') || '';
          const m = raw.match(/urn:li:(?:activity|ugcPost|share):(\d+)/);
          if (m) {
            postUrl = `https://www.linkedin.com/feed/update/urn:li:activity:${m[1]}/`;
          }
        }
      }

      // 3. Timestamp anchor link
      if (!postUrl) {
        const timestampAnchor = card.querySelector(
          'a.update-components-actor__sub-description-link, ' +
          'a.update-components-actor__meta-link, ' +
          'a.feed-shared-actor__sub-description-link, ' +
          'a[href*="/feed/update/urn:li:activity:"], ' +
          'a[href*="/feed/update/urn:li:share:"], ' +
          'a[href*="linkedin.com/posts/"], ' +
          'a[href*="/posts/"]'
        );
        if (timestampAnchor && timestampAnchor.href) {
          postUrl = timestampAnchor.href.split('?')[0].replace(/\/+$/, '') + '/';
        }
      }

      // 4. Any anchor inside card matching /feed/update/ or /posts/
      if (!postUrl) {
        const postAnchor = card.querySelector('a[href*="/feed/update/"], a[href*="/posts/"], a.job-card-list__title, a[href*="/jobs/view/"]');
        if (postAnchor && postAnchor.href) {
          postUrl = postAnchor.href.split('?')[0].replace(/\/+$/, '') + '/';
        }
      }

      // 5. Raw outerHTML match for activity ID
      if (!postUrl) {
        const mHtml = (card.outerHTML || '').match(/urn:li:activity:(\d{18,20})/);
        if (mHtml) {
          postUrl = `https://www.linkedin.com/feed/update/urn:li:activity:${mHtml[1]}/`;
        }
      }

      // 6. Current page permalink fallback
      if (!postUrl && (window.location.href.includes('/feed/update/') || window.location.href.includes('/posts/'))) {
        postUrl = window.location.href.split('?')[0].replace(/\/+$/, '') + '/';
      }

      if (!postUrl) return;

      // 4d. Apply Link Extraction (Extracts lnkd.in, career sites, forms)
      let detectedApplyLink = null;
      let formUrl = null;

      // Scan DOM anchor tags in description container
      const textContainers = card.querySelectorAll(
        '.feed-shared-update-v2__description, .update-components-text, .feed-shared-inline-show-more-text, .feed-shared-text'
      );
      const searchElements = textContainers.length > 0 ? textContainers : [card];

      for (const container of searchElements) {
        const anchors = container.querySelectorAll('a[href]');
        for (const a of anchors) {
          const h = (a.href || '').trim();
          if (!h.startsWith('http')) continue;
          if (h.includes('/feed/hashtag/') || h.includes('/in/') || h.includes('/company/') || h.includes('/search/')) continue;
          if (h.includes('/feed/update/') || h.includes('/posts/')) continue;

          // Detected external career application link!
          if (h.includes('lnkd.in') || !h.includes('linkedin.com')) {
            detectedApplyLink = h;
            break;
          }
        }
        if (detectedApplyLink) break;
      }

      // Regex search inside raw text for lnkd.in
      if (!detectedApplyLink) {
        const lnkdMatch = rawText.match(/(https?:\/\/lnkd\.in\/[a-zA-Z0-9_\-]+)/i);
        if (lnkdMatch) {
          detectedApplyLink = lnkdMatch[1];
        }
      }

      // Google Form / Form URL
      const formMatch = rawText.match(/(https?:\/\/(?:forms\.gle|docs\.google\.com\/forms|forms\.office\.com|bit\.ly)[^\s\)]+)/i);
      if (formMatch) {
        formUrl = formMatch[1];
        if (!detectedApplyLink) detectedApplyLink = formMatch[1];
      }

      // Contextual apply link
      if (!detectedApplyLink) {
        const applyContextMatch = rawText.match(/(?:apply|link|careers?|portal|opening)[\s\:\-\–\(\[]*\(?(https?:\/\/[^\s\)\>\]]+)/i);
        if (applyContextMatch) {
          const cand = applyContextMatch[1];
          if (!cand.includes('/in/') && !cand.includes('/hashtag/')) {
            detectedApplyLink = cand;
          }
        }
      }

      const applyLink = detectedApplyLink || postUrl;

      // Extract HR Email
      let hrEmail = null;
      const emailMatch = rawText.match(/([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)/);
      if (emailMatch) {
        const found = emailMatch[1];
        if (!['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'].some(ext => found.toLowerCase().endsWith('.' + ext))) {
          hrEmail = found;
        }
      }

      // Highlight post on LinkedIn visually
      card.classList.add('jobapply-discovered-post');
      if (!card.querySelector('.jobapply-post-badge')) {
        const badge = document.createElement('div');
        badge.className = 'jobapply-post-badge';
        badge.innerHTML = `
          <div style="display:flex; align-items:center; justify-content:space-between; width:100%; gap:8px;">
            <span style="font-weight:700; color:#38bdf8; display:flex; align-items:center; gap:6px;">
              🎯 JobApplyApp: Discovered 2 YOE Opening (${postCompany})!
            </span>
            <div style="display:flex; align-items:center; gap:6px;">
              ${detectedApplyLink ? `<a href="${detectedApplyLink}" target="_blank" style="background:#0284c7; color:#fff; text-decoration:none; padding:3px 8px; border-radius:4px; font-size:10px; font-weight:700;">🔗 Direct Apply Link</a>` : ''}
              <button class="jobapply-copy-link-btn" style="background:#0f172a; border:1px solid #38bdf8; color:#38bdf8; padding:3px 8px; border-radius:4px; font-size:10px; cursor:pointer; font-weight:600;">
                📋 Copy Post Link
              </button>
            </div>
          </div>
        `;
        card.insertBefore(badge, card.firstChild);

        badge.querySelector('.jobapply-copy-link-btn')?.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          navigator.clipboard.writeText(postUrl);
          showToastMessage(`📋 Copied Post Link to clipboard: ${postUrl}`);
        });
      }

      // Send verified post to backend Kanban DISCOVERED column!
      fetch("http://localhost:8000/api/jobs/discovered-post", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: postTitle,
          company: postCompany,
          location: "India / Remote",
          experience_str: expStr,
          description: rawText.slice(0, 3500),
          post_url: postUrl,
          apply_link: applyLink,
          hr_email: hrEmail,
          google_form_url: formUrl,
          source: `LinkedIn Post (${LINKEDIN_STREAMS[currentStreamIndex]?.label || "Hiring"})`,
          posted_date_str: postDateStr
        })
      })
      .then(res => res.json())
      .then(savedJob => {
        discoveredCount++;
        try {
          sessionStorage.setItem('jobapply_discovered_count', String(discoveredCount));
        } catch(e) {}
        const counterEl = document.getElementById('jobapply-post-count');
        if (counterEl) counterEl.innerText = String(discoveredCount);
        showToastMessage(`✨ Verified Post Saved: ${postCompany} - ${postTitle}! Added to DISCOVERED.`);
      })
      .catch(err => {
        console.warn("Discovered post sync notice:", err);
      });
    });
  }

  function showToastMessage(msg) {
    let t = document.getElementById('jobapply-live-toast');
    if (t) t.remove();

    t = document.createElement('div');
    t.id = 'jobapply-live-toast';
    t.style.position = 'fixed';
    t.style.bottom = '20px';
    t.style.left = '20px';
    t.style.background = '#0f172a';
    t.style.border = '1px solid #0284c7';
    t.style.color = '#ffffff';
    t.style.padding = '12px 18px';
    t.style.borderRadius = '12px';
    t.style.zIndex = '2147483647';
    t.style.boxShadow = '0 10px 25px rgba(0,0,0,0.5)';
    t.style.fontSize = '12px';
    t.style.fontWeight = '600';
    t.style.display = 'flex';
    t.style.alignItems = 'center';
    t.style.gap = '8px';
    t.innerHTML = `<span>🎯</span><span>${msg}</span>`;

    document.body.appendChild(t);
    setTimeout(() => { if (t) t.remove(); }, 4000);
  }

  // Inject LinkedIn Hunter when on LinkedIn and auto-resume if active
  if (isLinkedInDomain()) {
    function initLinkedInHunter() {
      injectLinkedInHunterBar();
      // Auto-resume continuous hunting across page reloads/nav if previously active
      try {
        if (sessionStorage.getItem('jobapply_hunter_active') === 'true') {
          setTimeout(() => {
            if (!linkedInHunterActive) startLinkedInAutoScroll();
          }, 1200);
        }
      } catch(e) {}
    }

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', initLinkedInHunter);
    } else {
      initLinkedInHunter();
    }

    // Periodically re-check bar & scan loaded posts across LinkedIn SPA navigation
    setInterval(() => {
      if (!document.getElementById('jobapply-linkedin-hunter-bar')) {
        injectLinkedInHunterBar();
      }
      scanLinkedInPosts();
    }, 2500);
  }

})();

