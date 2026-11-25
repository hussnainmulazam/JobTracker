"""
Generator for templates/preview.html
Creates an interactive visual previewer for all 31 hiring email templates.
"""

import os
import json

TEMPLATES_DIR = os.path.dirname(os.path.abspath(__file__))
REGISTRY_PATH = os.path.join(TEMPLATES_DIR, "registry.json")

SAMPLE_DATA = {
    "candidate_name": "Hussnain Mulazam",
    "candidate_email": "hussnainmulazam@gmail.com",
    "job_title": "Senior Full-Stack Engineer",
    "company_name": "AIvonTech Global",
    "hr_name": "Sarah Connor",
    "company_email": "careers@aivontech.com",
    "company_website": "https://aivontech.com",
    "round_name": "Technical",
    "date": "Monday, November 23, 2026",
    "time": "02:00 PM",
    "timezone": "EST",
    "meeting_link": "https://meet.google.com/xyz-uvwx-rst",
    "feedback": "Strong algorithmic foundations and clear architectural intuition. Demonstrated excellent problem-solving during the live system design discussion.",
    "job_description": "Architecting resilient, distributed real-time recruitment infrastructure with Python, FastAPI, React, and PostgreSQL.",
    "round_description": "A 45-minute live technical discussion covering high-throughput system design, API contracts, database concurrency, and clean code principles.",
    "slot_1": "Tuesday, Nov 24, 2026 at 10:00 AM EST",
    "slot_2": "Wednesday, Nov 25, 2026 at 02:00 PM EST",
    "slot_3": "Thursday, Nov 26, 2026 at 04:30 PM EST",
    "reply_deadline": "Friday, November 20 at 5:00 PM EST",
    "offer_attachment_note": "Includes formal offer package with competitive base ($155,000/yr), 0.25% equity options, health & dental benefits, 401(k) matching, and $3,500 annual CPD stipend.",
    "brand_color": "#2563eb"
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Hiring Pipeline Email Template Inspector</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
  <style>
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: #0b1329;
      color: #e2e8f0;
      height: 100vh;
      overflow: hidden;
      display: flex;
    }

    /* Sidebar */
    .sidebar {
      width: 330px;
      background: #111c38;
      border-right: 1px solid #1e293b;
      display: flex;
      flex-direction: column;
      height: 100vh;
      flex-shrink: 0;
    }
    .sidebar-header {
      padding: 18px 20px 14px 20px;
      border-bottom: 1px solid #1e293b;
      background: #0d172e;
    }
    .sidebar-title {
      font-size: 15px;
      font-weight: 700;
      color: #f8fafc;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .badge-count {
      font-size: 11px;
      background: #2563eb;
      color: #ffffff;
      padding: 2px 7px;
      border-radius: 12px;
      font-weight: 600;
    }
    .sidebar-subtitle {
      font-size: 11px;
      color: #94a3b8;
      margin-top: 4px;
    }
    .search-box {
      padding: 10px 16px;
      border-bottom: 1px solid #1e293b;
      position: relative;
    }
    .search-input {
      width: 100%;
      background: #0d172e;
      border: 1px solid #334155;
      border-radius: 6px;
      padding: 8px 12px 8px 32px;
      color: #f8fafc;
      font-size: 12px;
      outline: none;
      transition: border-color 0.15s;
    }
    .search-input:focus {
      border-color: #3b82f6;
    }
    .search-icon {
      position: absolute;
      left: 26px;
      top: 18px;
      font-size: 13px;
      color: #64748b;
      pointer-events: none;
    }
    .template-list {
      flex: 1;
      overflow-y: auto;
      padding: 10px 8px 24px 8px;
    }
    .template-category {
      font-size: 10px;
      text-transform: uppercase;
      font-weight: 700;
      letter-spacing: 0.05em;
      color: #64748b;
      padding: 14px 10px 6px 10px;
    }
    .template-item {
      padding: 9px 12px;
      border-radius: 6px;
      cursor: pointer;
      margin-bottom: 3px;
      transition: all 0.15s;
      border: 1px solid transparent;
    }
    .template-item:hover {
      background: #1e293b;
    }
    .template-item.active {
      background: #1e3a8a;
      border-color: #3b82f6;
    }
    .template-item-name {
      font-size: 12px;
      font-weight: 600;
      color: #f1f5f9;
      display: block;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .template-item.active .template-item-name {
      color: #93c5fd;
    }
    .template-item-sub {
      font-size: 11px;
      color: #94a3b8;
      display: block;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      margin-top: 2px;
    }

    /* Main Area */
    .main-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
      background: #070d1e;
    }

    /* Top Controls Bar */
    .topbar {
      background: #0f172a;
      border-bottom: 1px solid #1e293b;
      padding: 12px 20px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .topbar-row-1 {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }
    .template-identity {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .template-badge {
      background: #1e293b;
      border: 1px solid #334155;
      padding: 3px 10px;
      border-radius: 4px;
      font-size: 12px;
      font-family: monospace;
      color: #38bdf8;
      font-weight: 600;
    }
    .template-subject-display {
      font-size: 14px;
      font-weight: 600;
      color: #f8fafc;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .controls-group {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .btn-toggle {
      background: #1e293b;
      border: 1px solid #334155;
      color: #94a3b8;
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 12px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s;
    }
    .btn-toggle:hover {
      background: #334155;
      color: #f8fafc;
    }
    .btn-toggle.active {
      background: #2563eb;
      border-color: #3b82f6;
      color: #ffffff;
      font-weight: 600;
    }

    /* Metadata Bar */
    .meta-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      font-size: 11px;
    }
    .meta-tags {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }
    .tag {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 8px;
      border-radius: 4px;
      font-weight: 500;
    }
    .tag-trigger {
      background: rgba(14, 165, 233, 0.15);
      color: #38bdf8;
      border: 1px solid rgba(14, 165, 233, 0.3);
    }
    .tag-step {
      background: rgba(34, 197, 94, 0.15);
      color: #4ade80;
      border: 1px solid rgba(34, 197, 94, 0.3);
    }
    .tag-preheader {
      color: #94a3b8;
      font-style: italic;
    }

    /* Stage / Viewport */
    .stage-container {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
      overflow-y: auto;
      background: #070d1e;
    }
    .viewport-card {
      background: #ffffff;
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5);
      border-radius: 8px;
      overflow: hidden;
      transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      height: 100%;
      border: none;
      display: flex;
      flex-direction: column;
    }
    .viewport-card.desktop {
      width: 650px;
    }
    .viewport-card.mobile {
      width: 375px;
      border-radius: 20px;
      border: 4px solid #334155;
    }
    .email-frame {
      width: 100%;
      height: 100%;
      border: none;
      background: #f1f5f9;
    }
    .text-view-card {
      width: 100%;
      max-width: 680px;
      height: 100%;
      background: #111c38;
      border: 1px solid #1e293b;
      border-radius: 8px;
      padding: 24px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 13px;
      line-height: 1.6;
      color: #e2e8f0;
      white-space: pre-wrap;
      overflow-y: auto;
      box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
    }

    /* Scrollbars */
    ::-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }
    ::-webkit-scrollbar-track {
      background: transparent;
    }
    ::-webkit-scrollbar-thumb {
      background: #334155;
      border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
      background: #475569;
    }
  </style>
</head>
<body>

  <!-- Left Sidebar -->
  <aside class="sidebar">
    <div class="sidebar-header">
      <div class="sidebar-title">
        <i class="bi bi-envelope-paper-heart-fill" style="color: #3b82f6;"></i>
        <span>Template Inspector</span>
        <span class="badge-count" id="totalCountBadge">31</span>
      </div>
      <div class="sidebar-subtitle">Hiring Pipeline Dual-Format Engine</div>
    </div>

    <div class="search-box">
      <i class="bi bi-search search-icon"></i>
      <input type="text" id="searchInput" class="search-input" placeholder="Filter templates (e.g. interview, reject)..." oninput="filterTemplates()">
    </div>

    <div class="template-list" id="templateList">
      <!-- Items generated dynamically -->
    </div>
  </aside>

  <!-- Main Work Area -->
  <main class="main-content">
    <!-- Topbar -->
    <header class="topbar">
      <div class="topbar-row-1">
        <div class="template-identity">
          <span class="template-badge" id="templateIdBadge">cv_received</span>
          <span class="template-subject-display" id="templateSubjectDisplay">Subject line loading...</span>
        </div>

        <div class="controls-group">
          <!-- Viewport toggles -->
          <button id="btnDesktop" class="btn-toggle active" onclick="setDevice('desktop')" title="Desktop View (650px)">
            <i class="bi bi-display"></i> Desktop
          </button>
          <button id="btnMobile" class="btn-toggle" onclick="setDevice('mobile')" title="Mobile View (375px)">
            <i class="bi bi-phone"></i> Mobile
          </button>

          <div style="width: 1px; height: 20px; background: #334155; margin: 0 4px;"></div>

          <!-- Format toggles -->
          <button id="btnHtml" class="btn-toggle active" onclick="setMode('html')" title="Rendered HTML View">
            <i class="bi bi-filetype-html"></i> HTML
          </button>
          <button id="btnText" class="btn-toggle" onclick="setMode('text')" title="Plain-Text View">
            <i class="bi bi-file-text"></i> Plain Text
          </button>
        </div>
      </div>

      <div class="meta-bar">
        <div class="meta-tags">
          <span class="tag tag-trigger" id="triggerTag"><i class="bi bi-lightning-charge-fill"></i> Trigger: cv_received_via_gmail</span>
          <span class="tag tag-step" id="stepTag"><i class="bi bi-arrow-right-circle-fill"></i> Next: resume_parsing_and_scoring</span>
        </div>
        <div class="tag-preheader" id="preheaderTag">Preview: ...</div>
      </div>
    </header>

    <!-- Stage -->
    <section class="stage-container">
      <div id="htmlCard" class="viewport-card desktop">
        <iframe id="emailFrame" class="email-frame" sandbox="allow-same-origin"></iframe>
      </div>
      <div id="textCard" class="text-view-card" style="display: none;"></div>
    </section>
  </main>

  <script>
    const REGISTRY = __REGISTRY_DATA__;
    const TEMPLATES = __TEMPLATES_DATA__;
    const SAMPLE_DATA = __SAMPLE_DATA__;

    let currentId = "cv_received";
    let currentMode = "html";
    let currentDevice = "desktop";

    function substitute(str) {
      if (!str) return "";
      return str.replace(/\{\{([a-zA-Z0-9_]+)\}\}/g, function(match, key) {
        return SAMPLE_DATA[key] !== undefined ? SAMPLE_DATA[key] : match;
      });
    }

    function init() {
      renderSidebar();
      selectTemplate(currentId);
    }

    function renderSidebar() {
      const list = document.getElementById("templateList");
      list.innerHTML = "";

      const categories = [
        { key: "core", title: "1. Core Pipeline (1-9)" },
        { key: "supporting", title: "2. Supporting Pipeline (10-25)" },
        { key: "internal", title: "3. Internal HR & Interviewer (26-31)" }
      ];

      categories.forEach(cat => {
        const header = document.createElement("div");
        header.className = "template-category";
        header.innerText = cat.title;
        list.appendChild(header);

        const ids = REGISTRY.categories[cat.key] || [];
        ids.forEach(id => {
          const meta = REGISTRY.templates[id];
          if (!meta) return;

          const item = document.createElement("div");
          item.className = "template-item" + (id === currentId ? " active" : "");
          item.id = "item-" + id;
          item.onclick = () => selectTemplate(id);

          item.innerHTML = `
            <span class="template-item-name">${id}</span>
            <span class="template-item-sub">${meta.subject}</span>
          `;
          list.appendChild(item);
        });
      });
    }

    function filterTemplates() {
      const q = document.getElementById("searchInput").value.toLowerCase();
      document.querySelectorAll(".template-item").forEach(el => {
        const text = el.innerText.toLowerCase();
        el.style.display = text.includes(q) ? "block" : "none";
      });
    }

    function selectTemplate(id) {
      currentId = id;
      document.querySelectorAll(".template-item").forEach(el => el.classList.remove("active"));
      const activeEl = document.getElementById("item-" + id);
      if (activeEl) activeEl.classList.add("active");

      const tpl = TEMPLATES[id];
      if (!tpl) return;

      document.getElementById("templateIdBadge").innerText = id;
      document.getElementById("templateSubjectDisplay").innerText = substitute(tpl.subject);
      document.getElementById("triggerTag").innerHTML = '<i class="bi bi-lightning-charge-fill"></i> Trigger: ' + tpl.trigger_event;
      document.getElementById("stepTag").innerHTML = '<i class="bi bi-arrow-right-circle-fill"></i> Next: ' + tpl.next_step;
      document.getElementById("preheaderTag").innerText = 'Preview: ' + substitute(tpl.preheader);

      renderView();
    }

    function renderView() {
      const tpl = TEMPLATES[currentId];
      if (!tpl) return;

      if (currentMode === "html") {
        document.getElementById("htmlCard").style.display = "flex";
        document.getElementById("textCard").style.display = "none";
        const frame = document.getElementById("emailFrame");
        frame.srcdoc = substitute(tpl.html);
      } else {
        document.getElementById("htmlCard").style.display = "none";
        document.getElementById("textCard").style.display = "block";
        document.getElementById("textCard").innerText = substitute(tpl.text);
      }
    }

    function setMode(mode) {
      currentMode = mode;
      document.getElementById("btnHtml").classList.toggle("active", mode === "html");
      document.getElementById("btnText").classList.toggle("active", mode === "text");
      renderView();
    }

    function setDevice(device) {
      currentDevice = device;
      document.getElementById("btnDesktop").classList.toggle("active", device === "desktop");
      document.getElementById("btnMobile").classList.toggle("active", device === "mobile");

      const card = document.getElementById("htmlCard");
      card.className = "viewport-card " + device;
    }

    window.onload = init;
  </script>
</body>
</html>
"""

def generate_preview():
    if not os.path.exists(REGISTRY_PATH):
        print(f"Error: registry.json not found at {REGISTRY_PATH}")
        return False

    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    templates_payload = {}
    for t_id, meta in registry.get("templates", {}).items():
        html_file = os.path.join(TEMPLATES_DIR, f"{t_id}.html")
        txt_file = os.path.join(TEMPLATES_DIR, f"{t_id}.txt")

        html_raw = ""
        if os.path.exists(html_file):
            with open(html_file, "r", encoding="utf-8") as f:
                html_raw = f.read()

        txt_raw = ""
        if os.path.exists(txt_file):
            with open(txt_file, "r", encoding="utf-8") as f:
                txt_raw = f.read()

        templates_payload[t_id] = {
            "id": t_id,
            "subject": meta.get("subject", ""),
            "preheader": meta.get("preheader", ""),
            "trigger_event": meta.get("trigger_event", ""),
            "next_step": meta.get("next_step", ""),
            "required_variables": meta.get("required_variables", []),
            "html": html_raw,
            "text": txt_raw
        }

    page = (
        HTML_TEMPLATE.replace("__REGISTRY_DATA__", json.dumps(registry))
        .replace("__TEMPLATES_DATA__", json.dumps(templates_payload))
        .replace("__SAMPLE_DATA__", json.dumps(SAMPLE_DATA))
    )

    preview_path = os.path.join(TEMPLATES_DIR, "preview.html")
    with open(preview_path, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"Wrote visual preview page: {preview_path}")
    return True

if __name__ == "__main__":
    generate_preview()
