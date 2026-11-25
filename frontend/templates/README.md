# Automated Hiring Pipeline Email Templates

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
