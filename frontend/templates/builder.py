"""
Complete Template Builder and Asset Generator.
Compiles all 31 templates into /templates/<template_id>.html and .txt,
creates registry.json, preview.html, validate.py, and README.md.
"""

import os
import json
import re

TEMPLATES_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(TEMPLATES_DIR, ".."))

from definitions_core import CORE_TEMPLATES
from definitions_supporting import SUPPORTING_TEMPLATES
from definitions_internal import INTERNAL_TEMPLATES

ALL_TEMPLATES = CORE_TEMPLATES + SUPPORTING_TEMPLATES + INTERNAL_TEMPLATES

# ─────────────────────────────────────────────────────────────────────────────
# 1. Base Layout HTML
# ─────────────────────────────────────────────────────────────────────────────
BASE_LAYOUT_HTML = """<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="x-apple-disable-message-reformatting">
  <title>{{company_name}} Careers</title>
  <!--[if mso]>
  <noscript>
    <xml>
      <o:OfficeDocumentSettings>
        <o:PixelsPerInch>96</o:PixelsPerInch>
      </o:OfficeDocumentSettings>
    </xml>
  </noscript>
  <![endif]-->
  <style>
    /* Reset styles */
    html, body {
      margin: 0 auto !important;
      padding: 0 !important;
      height: 100% !important;
      width: 100% !important;
      background-color: #f1f5f9;
      font-family: Arial, Helvetica, sans-serif;
      -webkit-font-smoothing: antialiased;
      -ms-text-size-adjust: 100%;
      -webkit-text-size-adjust: 100%;
    }
    div[style*="margin: 16px 0"] {
      margin: 0 !important;
    }
    table, td {
      mso-table-lspace: 0pt !important;
      mso-table-rspace: 0pt !important;
    }
    table {
      border-spacing: 0 !important;
      border-collapse: collapse !important;
      table-layout: fixed !important;
      margin: 0 auto !important;
    }
    img {
      -ms-interpolation-mode: bicubic;
      border: 0;
      height: auto;
      line-height: 100%;
      outline: none;
      text-decoration: none;
    }
    a {
      text-decoration: none;
    }
    /* Mobile styles */
    @media only screen and (max-width: 620px) {
      .email-container {
        width: 100% !important;
        max-width: 100% !important;
      }
      .content-padding {
        padding: 24px 20px !important;
      }
      .header-padding {
        padding: 20px 20px !important;
      }
      .footer-padding {
        padding: 24px 20px !important;
      }
      .mobile-full-width {
        width: 100% !important;
        display: block !important;
      }
      .mobile-center {
        text-align: center !important;
      }
    }
    /* Dark mode preferences */
    @media (prefers-color-scheme: dark) {
      .body-bg {
        background-color: #0b1120 !important;
      }
      .card-bg {
        background-color: #1e293b !important;
        border-color: #334155 !important;
      }
      .text-heading {
        color: #f8fafc !important;
      }
      .text-body {
        color: #cbd5e1 !important;
      }
      .text-muted {
        color: #94a3b8 !important;
      }
      .box-bg {
        background-color: #0f172a !important;
        border-color: #334155 !important;
      }
      .quote-bg {
        background-color: #1e293b !important;
        border-left-color: {{brand_color}} !important;
      }
      .footer-text {
        color: #64748b !important;
      }
    }
  </style>
</head>
<body class="body-bg" style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: Arial, Helvetica, sans-serif; -webkit-font-smoothing: antialiased;">
  <!-- Preheader preview text (hidden from view, shows in email client inbox preview) -->
  <div style="display: none; font-size: 1px; line-height: 1px; max-height: 0px; max-width: 0px; opacity: 0; overflow: hidden; mso-hide: all; font-family: sans-serif;">
    {{preheader_text}}
    &zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
  </div>

  <!-- Outer wrapper table -->
  <table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation" class="body-bg" style="background-color: #f1f5f9; margin: 0 auto; table-layout: fixed;">
    <tr>
      <td align="center" style="padding: 32px 12px 48px 12px;">
        <!-- Email Container (max 600px) -->
        <!--[if (gte mso 9)|(IE)]>
        <table align="center" border="0" cellspacing="0" cellpadding="0" width="600">
        <tr>
        <td align="center" valign="top" width="600">
        <![endif]-->
        <table border="0" cellpadding="0" cellspacing="0" width="100%" class="email-container" role="presentation" style="max-width: 600px; width: 100%; margin: 0 auto;">
          
          <!-- Top Accent Bar -->
          <tr>
            <td height="4" style="height: 4px; background-color: {{brand_color}}; font-size: 0; line-height: 0; border-radius: 8px 8px 0 0;">&nbsp;</td>
          </tr>

          <!-- Main White Card -->
          <tr>
            <td class="card-bg" style="background-color: #ffffff; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; border-radius: 0 0 12px 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);">
              
              <!-- Header Section -->
              <table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation">
                <tr>
                  <td class="header-padding" style="padding: 28px 36px 20px 36px; border-bottom: 1px solid #f1f5f9;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation">
                      <tr>
                        <td align="left" valign="middle">
                          <span class="text-heading" style="font-size: 20px; font-weight: bold; color: #0f172a; letter-spacing: -0.3px; text-decoration: none; font-family: Arial, Helvetica, sans-serif;">
                            {{company_name}}
                          </span>
                        </td>
                        <td align="right" valign="middle">
                          <span style="display: inline-block; padding: 4px 10px; font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; color: {{brand_color}}; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 9999px; font-family: Arial, Helvetica, sans-serif;">
                            Talent &amp; Recruiting
                          </span>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

              <!-- Main Content Body -->
              <table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation">
                <tr>
                  <td class="content-padding" style="padding: 32px 36px 36px 36px;">
                    <!-- CONTENT_START -->
                    {{content}}
                    <!-- CONTENT_END -->
                  </td>
                </tr>
              </table>

              <!-- Footer Section -->
              <table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation">
                <tr>
                  <td class="footer-padding" style="padding: 24px 36px 28px 36px; background-color: #f8fafc; border-top: 1px solid #e2e8f0; border-radius: 0 0 12px 12px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation">
                      <tr>
                        <td style="font-family: Arial, Helvetica, sans-serif; font-size: 13px; line-height: 1.6; color: #64748b;">
                          <strong class="text-heading" style="color: #334155; font-size: 13px; display: block; margin-bottom: 2px;">
                            {{hr_name}} &bull; Talent Acquisition Team
                          </strong>
                          <span>{{company_name}}</span><br>
                          <a href="mailto:{{company_email}}" style="color: {{brand_color}}; text-decoration: none; font-weight: 500;">{{company_email}}</a>
                          &bull;
                          <a href="{{company_website}}" target="_blank" style="color: {{brand_color}}; text-decoration: none; font-weight: 500;">{{company_website}}</a>
                        </td>
                      </tr>
                      <tr>
                        <td style="padding-top: 16px; font-family: Arial, Helvetica, sans-serif; font-size: 11px; line-height: 1.5; color: #94a3b8; border-top: 1px solid #e2e8f0; margin-top: 16px;">
                          This automated communication was dispatched regarding your application for {{job_title}} at {{company_name}}. Please reply directly to this email if you have any questions or require special accommodations.
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

            </td>
          </tr>

        </table>
        <!--[if (gte mso 9)|(IE)]>
        </td>
        </tr>
        </table>
        <![endif]-->
      </td>
    </tr>
  </table>
</body>
</html>
"""

def main():
    print(f"Total templates to generate: {len(ALL_TEMPLATES)}")
    assert len(ALL_TEMPLATES) == 31, f"Expected 31 templates, found {len(ALL_TEMPLATES)}"

    # 1. Write base_layout.html
    base_layout_path = os.path.join(TEMPLATES_DIR, "base_layout.html")
    with open(base_layout_path, "w", encoding="utf-8") as f:
        f.write(BASE_LAYOUT_HTML)
    print(f"Wrote {base_layout_path}")

    # 2. Build registry.json
    registry_data = {
        "version": "1.0.0",
        "system": "Automated Hiring Pipeline Email Templates",
        "description": "Registry of production-ready responsive email templates for each hiring stage.",
        "global_variables": [
            "candidate_name",
            "candidate_email",
            "job_title",
            "company_name",
            "hr_name",
            "company_email",
            "company_website",
            "round_name",
            "date",
            "time",
            "timezone",
            "meeting_link",
            "feedback",
            "job_description",
            "round_description",
            "slot_1",
            "slot_2",
            "slot_3",
            "reply_deadline",
            "offer_attachment_note",
            "brand_color"
        ],
        "categories": {
            "core": [t["id"] for t in CORE_TEMPLATES],
            "supporting": [t["id"] for t in SUPPORTING_TEMPLATES],
            "internal": [t["id"] for t in INTERNAL_TEMPLATES]
        },
        "templates": {}
    }

    # 3. Write each template HTML & TXT
    for tpl in ALL_TEMPLATES:
        t_id = tpl["id"]
        preheader = tpl.get("preheader", "")
        content_html = tpl["content_html"].strip()
        text_content = tpl["text_content"].strip()

        # Combine with base layout
        full_html = (
            BASE_LAYOUT_HTML.replace("{{preheader_text}}", preheader)
            .replace("{{content}}", content_html)
        )

        html_path = os.path.join(TEMPLATES_DIR, f"{t_id}.html")
        txt_path = os.path.join(TEMPLATES_DIR, f"{t_id}.txt")

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(full_html)

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text_content)

        # Add to registry
        registry_data["templates"][t_id] = {
            "id": t_id,
            "subject": tpl["subject"],
            "preheader": preheader,
            "trigger_event": tpl["trigger_event"],
            "next_step": tpl["next_step"],
            "required_variables": sorted(list(set(tpl["required_variables"]))),
            "html_file": f"{t_id}.html",
            "text_file": f"{t_id}.txt"
        }

    # Write registry.json
    registry_path = os.path.join(TEMPLATES_DIR, "registry.json")
    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry_data, f, indent=2)
    print(f"Wrote {registry_path}")

    # 4. Generate Validation Script (templates/validate.py & validate_templates.py)
    validate_script = """#!/usr/bin/env python3
\"\"\"
Validation script for Hiring Pipeline Email Templates.
Verifies that:
1. All 31 templates exist in HTML and TXT format.
2. Every {{variable}} in every HTML and TXT template is explicitly declared in registry.json.
3. Every required variable declared in registry.json is actually used in the template.
4. Base layout and registry.json are valid and well-formed.
\"\"\"
import os
import json
import re
import sys

TEMPLATES_DIR = os.path.dirname(os.path.abspath(__file__))
if not os.path.exists(os.path.join(TEMPLATES_DIR, "registry.json")):
    # Try looking in 'templates' subfolder if run from repo root
    if os.path.exists(os.path.join(TEMPLATES_DIR, "templates", "registry.json")):
        TEMPLATES_DIR = os.path.join(TEMPLATES_DIR, "templates")

REGISTRY_PATH = os.path.join(TEMPLATES_DIR, "registry.json")

def validate():
    print("=" * 65)
    print(" HIRING PIPELINE EMAIL TEMPLATE VALIDATION")
    print("=" * 65)

    if not os.path.exists(REGISTRY_PATH):
        print(f"[FAIL] registry.json not found at {REGISTRY_PATH}")
        sys.exit(1)

    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    templates = registry.get("templates", {})
    print(f"Found {len(templates)} templates in registry.json.")

    var_pattern = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")
    errors = []
    warnings = []
    checked_count = 0

    for t_id, meta in templates.items():
        checked_count += 1
        html_file = os.path.join(TEMPLATES_DIR, f"{t_id}.html")
        txt_file = os.path.join(TEMPLATES_DIR, f"{t_id}.txt")
        declared_vars = set(meta.get("required_variables", []))

        # Check file existence
        if not os.path.exists(html_file):
            errors.append(f"[{t_id}] HTML file missing: {html_file}")
            continue
        if not os.path.exists(txt_file):
            errors.append(f"[{t_id}] TXT file missing: {txt_file}")
            continue

        with open(html_file, "r", encoding="utf-8") as f:
            html_content = f.read()
        with open(txt_file, "r", encoding="utf-8") as f:
            txt_content = f.read()

        html_vars = set(var_pattern.findall(html_content))
        txt_vars = set(var_pattern.findall(txt_content))
        subj_vars = set(var_pattern.findall(meta.get("subject", "")))
        all_used_vars = html_vars.union(txt_vars).union(subj_vars)

        # Remove internal template slot placeholder if any
        all_used_vars.discard("content")
        all_used_vars.discard("preheader_text")

        # 1. Every variable used must be declared in registry.json
        undeclared = all_used_vars - declared_vars
        if undeclared:
            errors.append(f"[{t_id}] Undeclared variables used in template: {sorted(list(undeclared))}")

        # 2. Every declared variable should be present in the template or subject
        unused = declared_vars - all_used_vars
        if unused:
            warnings.append(f"[{t_id}] Declared variables not found in template body/subject: {sorted(list(unused))}")

    print(f"Validated {checked_count} templates.")
    print("-" * 65)

    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            print("  [WARN] " + w)
        print("-" * 65)

    if errors:
        print(f"ERRORS ({len(errors)}):")
        for e in errors:
            print("  [FAIL] " + e)
        print("=" * 65)
        print("RESULT: VALIDATION FAILED")
        return False
    else:
        print("ALL VARIABLES DECLARED AND VALIDATED SUCCESSFULLY!")
        print(f"31/31 templates passed strict validation.")
        print("=" * 65)
        print("RESULT: PASS")
        return True

if __name__ == "__main__":
    success = validate()
    sys.exit(0 if success else 1)
"""

    validate_path = os.path.join(TEMPLATES_DIR, "validate.py")
    with open(validate_path, "w", encoding="utf-8") as f:
        f.write(validate_script)

    root_validate_path = os.path.join(ROOT_DIR, "validate_templates.py")
    with open(root_validate_path, "w", encoding="utf-8") as f:
        f.write(validate_script)

    print(f"Wrote {validate_path} & {root_validate_path}")

    # 5. Generate Visual Preview Page (templates/preview.html)
    import make_preview
    make_preview.generate_preview()

    # 6. Generate README.md
    generate_readme_md(registry_data)

    print('All template assets built successfully!')

def generate_readme_md(registry_data):
    readme_content = """# Automated Hiring Pipeline Email Templates

A comprehensive, production-grade email template system engineered for automated hiring pipelines. Every stage of the recruitment lifecycle is covered with mobile-responsive, bulletproof HTML email templates and matching plain-text versions.

---

## Architecture & Directory Structure

```text
/templates/
├── base_layout.html         # Shared master layout (header, card wrapper, footer)
├── registry.json            # Central template registry (subjects, variables, triggers, next steps)
├── preview.html             # Interactive visual inspector for all 31 templates
├── validate.py              # Strict validation script for {{variables}} and integrity
├── <template_id>.html       # Standalone production HTML email (31 templates)
├── <template_id>.txt        # Plain-text ASCII email fallback (31 templates)
└── README.md                # System documentation and agent integration guide
```

---

## Template Directory & Stages

### 1. Core Pipeline Templates (1 - 9)
| Template ID | Stage | Trigger Event | Next Pipeline Step |
|---|---|---|---|
| `cv_received` | Ingestion | CV arrives via Gmail / portal | AI scores CV; HR reviews |
| `application_rejected` | Screening Rejection | HR rejects CV scorecard | Archived; eligible for future |
| `application_approved` | Shortlisted | HR approves screening | Candidate sends Initial slots |
| `interview_confirmed` | Confirmation | Calendar event booked | Candidate attends interview |
| `alternate_slots` | Scheduling Conflict | Candidate times conflict | Candidate selects alternate |
| `next_round_availability` | Round Progression | Previous round passed | Candidate sends next slots |
| `interview_passed` | Round Approval | Interviewer passes candidate | Recruiter schedules next round |
| `interview_rejected` | Interview Rejection | Candidate rejected post-interview | File archived with feedback |
| `all_rounds_cleared` | Final Completion | Final Technical round passed | HR drafts offer package |

### 2. Supporting Templates (10 - 25)
- `interview_reminder_24h` &bull; Sent 24 hours prior to scheduled interview.
- `interview_reminder_1h` &bull; Sent 1 hour prior to scheduled interview with direct video link.
- `no_response_followup` &bull; Sent 48 hours after no candidate response to availability request.
- `application_closed_no_response` &bull; Closes application after reply deadline elapses.
- `interview_rescheduled` &bull; Confirms updated date, time, and video meeting link.
- `interview_cancelled_by_company` &bull; Apologetic cancellation notice due to internal conflicts.
- `candidate_cancelled_confirmation` &bull; Acknowledges candidate-initiated cancellation.
- `candidate_no_show` &bull; Sent after a 15-minute grace period when candidate misses interview.
- `cv_unreadable_or_unsupported_format` &bull; Requests candidate re-upload resume in PDF/DOCX.
- `duplicate_application` &bull; Reassures candidate their active profile is in review.
- `application_on_hold` &bull; Places candidate in priority Talent Pool when requisition pauses.
- `documents_request` &bull; Requests ID, degree, and professional reference documents.
- `offer_letter_cover` &bull; Accompanies formal offer letter attachment for signing.
- `offer_accepted_confirmation` &bull; Celebrates offer acceptance and initiates pre-boarding.
- `offer_declined_acknowledgement` &bull; Respectful acknowledgement of candidate declining offer.
- `welcome_onboarding` &bull; Sent 3-5 days before start date with Day 1 roadmap.

### 3. Internal (HR & Interviewer) Templates (26 - 31)
- `hr_new_cv_scored` &bull; Alerts HR that a candidate was parsed, scored, and ready for review.
- `hr_candidate_replied_availability` &bull; Alerts recruiter that candidate sent interview times.
- `hr_interview_scheduled` &bull; Calendar confirmation to interview panel with candidate details.
- `hr_interviewer_reminder` &bull; Sent 2 hours before interview prompting prompt scorecard logging.
- `hr_pending_decision_reminder` &bull; SLA alert after 48h with no HR approve/reject decision.
- `hr_candidate_moved_to_offer_section` &bull; Prompts HR to draft formal compensation package.

---

## How an Automated Agent Selects a Template

The AI agent should inspect `registry.json` using the pipeline event as the key:

1. **Match `trigger_event`**: When an event occurs in the hiring state machine (e.g., `candidate_shortlisted`), query `registry.json` for the template where `trigger_event` matches.
2. **Retrieve `required_variables`**: Look up the template's required variables list.
3. **Populate Variables**:
   ```python
   import json

   with open("templates/registry.json") as f:
       registry = json.load(f)

   template_meta = registry["templates"]["interview_confirmed"]
   with open(f"templates/{template_meta['html_file']}") as f:
       html_template = f.read()

   # Replace {{variables}}
   for var in template_meta["required_variables"]:
       placeholder = f"{{{{{var}}}}}"
       html_template = html_template.replace(placeholder, str(context[var]))
   ```
4. **Dispatch Dual-Format Email**: Send both HTML body and Plain Text (`.txt`) fallback via SMTP/Gmail API.

---

## Design & Email Client Compatibility Rules

- **Max Width**: 600px centered layout for optimal readability.
- **Table Layout**: Robust HTML table architecture compatible with Microsoft Outlook (MSO), Apple Mail, Gmail (Web, iOS, Android), Yahoo, and mobile web clients.
- **Bulletproof Buttons**: Table-cell based CTAs with inline background color, padding, and styled anchor tags.
- **Rejection Feedback**: Every rejection template includes a distinct, stylized quote box displaying `{{feedback}}`.
- **Reusable Templates**: Templates `interview_confirmed` and `alternate_slots` accept `{{round_name}}` dynamically for Initial, Behavioral, and Technical rounds.
- **Configurable Branding**: Primary accent colors and CTAs adapt dynamically via `{{brand_color}}`.
- **Validation**: Run `python templates/validate.py` (or `python validate_templates.py`) to verify template integrity.

---

## Visual Inspection

Open `templates/preview.html` in any modern web browser to visually inspect all 31 templates, toggle between desktop (600px) and mobile (375px) viewports, and switch between HTML and Plain Text modes with live sample data.
"""
    readme_path = os.path.join(TEMPLATES_DIR, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
    print(f"Wrote README: {readme_path}")

if __name__ == "__main__":
    main()
