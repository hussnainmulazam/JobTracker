"""
Internal (HR / Interviewer) Templates (26 to 31) for Automated Hiring Pipeline.
"""

INTERNAL_TEMPLATES = [
    {
        "id": "hr_new_cv_scored",
        "subject": "[Action Required] New Candidate Scored: {{candidate_name}} for {{job_title}}",
        "preheader": "New candidate application parsed and scored for {{job_title}}. Ready for review.",
        "trigger_event": "New candidate CV parsed, contact extracted, and initial screening score computed.",
        "next_step": "HR reviews candidate profile and scorecard to Approve or Reject.",
        "required_variables": [
            "candidate_name",
            "candidate_email",
            "job_title",
            "company_name",
            "hr_name",
            "company_email",
            "company_website",
            "brand_color"
        ],
        "content_html": """
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">[Action Required] New Candidate Profile Scored</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Hello {{hr_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">A new candidate application has been ingested and parsed for <strong>{{job_title}}</strong> at <strong>{{company_name}}</strong>. The candidate profile and deterministic scorecard are ready for your review.</p>
<table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation" class="box-bg" style="margin: 20px 0; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;">
  <tr>
    <td style="padding: 18px 20px;">
      <strong class="text-heading" style="display: block; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: {{brand_color}}; margin-bottom: 12px;">Candidate Overview</strong>
      <table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation">
        <tr>
          <td style="padding: 5px 0; font-size: 13px; color: #64748b; font-weight: bold; width: 35%;">Candidate Name:</td>
          <td style="padding: 5px 0; font-size: 14px; color: #0f172a; font-weight: 600;">{{candidate_name}}</td>
        </tr>
        <tr>
          <td style="padding: 5px 0; font-size: 13px; color: #64748b; font-weight: bold;">Candidate Email:</td>
          <td style="padding: 5px 0; font-size: 14px; color: #0f172a; font-weight: 600;">{{candidate_email}}</td>
        </tr>
        <tr>
          <td style="padding: 5px 0; font-size: 13px; color: #64748b; font-weight: bold;">Target Position:</td>
          <td style="padding: 5px 0; font-size: 14px; color: #0f172a; font-weight: 600;">{{job_title}}</td>
        </tr>
      </table>
    </td>
  </tr>
</table>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 14px; line-height: 1.6; color: #475569;">Please log in to your recruiting dashboard to inspect the parsed resume, review matched skills and red flags, and make an Approve or Reject decision.</p>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">Automated Notification System<br>{{company_name}} Talent Pipeline</p>
""",
        "text_content": """Hello {{hr_name}},

A new candidate application has been ingested and parsed for {{job_title}} at {{company_name}}. The candidate profile and deterministic scorecard are ready for your review.

CANDIDATE OVERVIEW:
- Candidate Name: {{candidate_name}}
- Candidate Email: {{candidate_email}}
- Target Position: {{job_title}}

Please log in to your recruiting dashboard to inspect the parsed resume, review matched skills and red flags, and make an Approve or Reject decision.

Automated Notification System
{{company_name}} Talent Pipeline
Email: {{company_email}}
Website: {{company_website}}
"""
    },
    {
        "id": "hr_candidate_replied_availability",
        "subject": "[Action Required] Availability Received: {{candidate_name}} for {{round_name}}",
        "preheader": "{{candidate_name}} has submitted availability for {{round_name}} Interview.",
        "trigger_event": "Candidate replies with time slots for interview scheduling.",
        "next_step": "Recruiter selects best time, schedules calendar event, and confirms with candidate.",
        "required_variables": [
            "candidate_name",
            "candidate_email",
            "job_title",
            "round_name",
            "company_name",
            "hr_name",
            "company_email",
            "company_website",
            "brand_color"
        ],
        "content_html": """
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">Candidate Availability Received</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Hello {{hr_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Candidate <strong>{{candidate_name}}</strong> ({{candidate_email}}) has replied with their proposed availability for the <strong>{{round_name}} Interview</strong> for the <strong>{{job_title}}</strong> position at <strong>{{company_name}}</strong>.</p>
<table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation" class="box-bg" style="margin: 20px 0; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;">
  <tr>
    <td style="padding: 16px 20px;">
      <strong class="text-heading" style="display: block; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: {{brand_color}}; margin-bottom: 8px;">Next Action Required</strong>
      <p class="text-body" style="margin: 0; font-size: 14px; line-height: 1.5; color: #334155;">
        Open the Recruiting Inbox, review the candidate's proposed time slots against team calendars, and dispatch the interview confirmation.
      </p>
    </td>
  </tr>
</table>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">Automated Notification System<br>{{company_name}} Recruiting</p>
""",
        "text_content": """Hello {{hr_name}},

Candidate {{candidate_name}} ({{candidate_email}}) has replied with their proposed availability for the {{round_name}} Interview for the {{job_title}} position at {{company_name}}.

NEXT ACTION REQUIRED:
Open the Recruiting Inbox, review the candidate's proposed time slots against team calendars, and dispatch the interview confirmation.

Automated Notification System
{{company_name}} Recruiting
Email: {{company_email}}
Website: {{company_website}}
"""
    },
    {
        "id": "hr_interview_scheduled",
        "subject": "[Scheduled] {{round_name}} Interview: {{candidate_name}} for {{job_title}}",
        "preheader": "{{round_name}} interview scheduled for {{candidate_name}} on {{date}} at {{time}} {{timezone}}.",
        "trigger_event": "Interview calendar invitation generated and sent.",
        "next_step": "Interviewer prepares evaluation notes and joins session at scheduled time.",
        "required_variables": [
            "candidate_name",
            "candidate_email",
            "job_title",
            "round_name",
            "date",
            "time",
            "timezone",
            "meeting_link",
            "company_name",
            "hr_name",
            "company_email",
            "company_website",
            "brand_color"
        ],
        "content_html": """
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">Interview Scheduled Notice</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Hello Team,</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">A new interview has been confirmed on the calendar for <strong>{{job_title}}</strong> at <strong>{{company_name}}</strong>. Please find the details below:</p>
<table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation" class="box-bg" style="margin: 20px 0; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;">
  <tr>
    <td style="padding: 18px 20px;">
      <strong class="text-heading" style="display: block; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: {{brand_color}}; margin-bottom: 12px;">Session Details</strong>
      <table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation">
        <tr>
          <td style="padding: 5px 0; font-size: 13px; color: #64748b; font-weight: bold; width: 35%;">Candidate:</td>
          <td style="padding: 5px 0; font-size: 14px; color: #0f172a; font-weight: 600;">{{candidate_name}} ({{candidate_email}})</td>
        </tr>
        <tr>
          <td style="padding: 5px 0; font-size: 13px; color: #64748b; font-weight: bold;">Stage:</td>
          <td style="padding: 5px 0; font-size: 14px; color: #0f172a; font-weight: 600;">{{round_name}} Interview</td>
        </tr>
        <tr>
          <td style="padding: 5px 0; font-size: 13px; color: #64748b; font-weight: bold;">Date:</td>
          <td style="padding: 5px 0; font-size: 14px; color: #0f172a; font-weight: 600;">{{date}}</td>
        </tr>
        <tr>
          <td style="padding: 5px 0; font-size: 13px; color: #64748b; font-weight: bold;">Time:</td>
          <td style="padding: 5px 0; font-size: 14px; color: #0f172a; font-weight: 600;">{{time}} ({{timezone}})</td>
        </tr>
      </table>
    </td>
  </tr>
</table>
<table border="0" cellpadding="0" cellspacing="0" role="presentation" style="margin: 24px 0;">
  <tr>
    <td align="center" style="border-radius: 6px; background-color: {{brand_color}};">
      <a href="{{meeting_link}}" target="_blank" style="display: inline-block; padding: 12px 24px; font-family: Arial, Helvetica, sans-serif; font-size: 14px; font-weight: bold; color: #ffffff; text-decoration: none; border-radius: 6px; border: 1px solid {{brand_color}}; text-align: center; line-height: 1;">
        Access Interview Video Room &rarr;
      </a>
    </td>
  </tr>
</table>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 14px; line-height: 1.6; color: #475569;">Please review the candidate's resume and interview scorecard prior to the call. Please log your interview notes promptly following the discussion.</p>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">Recruiting Coordination<br>{{hr_name}} &bull; {{company_name}}</p>
""",
        "text_content": """Hello Team,

A new interview has been confirmed on the calendar for {{job_title}} at {{company_name}}. Please find the details below:

SESSION DETAILS:
- Candidate: {{candidate_name}} ({{candidate_email}})
- Stage: {{round_name}} Interview
- Date: {{date}}
- Time: {{time}} ({{timezone}})
- Meeting Link: {{meeting_link}}

Please review the candidate's resume and interview scorecard prior to the call. Please log your interview notes promptly following the discussion.

Recruiting Coordination
{{hr_name}}
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    },
    {
        "id": "hr_interviewer_reminder",
        "subject": "[Reminder] Upcoming Interview Today: {{candidate_name}} ({{round_name}})",
        "preheader": "Reminder: You have an interview with {{candidate_name}} starting at {{time}} {{timezone}}.",
        "trigger_event": "2 hours prior to scheduled interview round.",
        "next_step": "Interviewer conducts interview and fills scorecard.",
        "required_variables": [
            "candidate_name",
            "job_title",
            "round_name",
            "time",
            "timezone",
            "meeting_link",
            "company_name",
            "hr_name",
            "company_email",
            "company_website",
            "brand_color"
        ],
        "content_html": """
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">Upcoming Interview Reminder</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Hello,</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">You have an upcoming <strong>{{round_name}} Interview</strong> with candidate <strong>{{candidate_name}}</strong> for the <strong>{{job_title}}</strong> position today at <strong>{{time}} ({{timezone}})</strong> at <strong>{{company_name}}</strong>.</p>
<table border="0" cellpadding="0" cellspacing="0" role="presentation" style="margin: 20px 0;">
  <tr>
    <td align="center" style="border-radius: 6px; background-color: {{brand_color}};">
      <a href="{{meeting_link}}" target="_blank" style="display: inline-block; padding: 12px 24px; font-family: Arial, Helvetica, sans-serif; font-size: 14px; font-weight: bold; color: #ffffff; text-decoration: none; border-radius: 6px; border: 1px solid {{brand_color}}; text-align: center; line-height: 1;">
        Open Meeting Link &rarr;
      </a>
    </td>
  </tr>
</table>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 14px; line-height: 1.6; color: #475569;">Please log into the meeting room 2-3 minutes early to welcome the candidate. Following the conversation, please submit your feedback and evaluation score within 24 hours.</p>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">Best regards,<br>{{hr_name}} &bull; {{company_name}} Talent Team</p>
""",
        "text_content": """Hello,

You have an upcoming {{round_name}} Interview with candidate {{candidate_name}} for the {{job_title}} position today at {{time}} ({{timezone}}) at {{company_name}}.

MEETING LINK: {{meeting_link}}

Please log into the meeting room 2-3 minutes early to welcome the candidate. Following the conversation, please submit your feedback and evaluation score within 24 hours.

Best regards,
{{hr_name}}
Talent Acquisition Team
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    },
    {
        "id": "hr_pending_decision_reminder",
        "subject": "[Pending Decision] Action Needed for {{candidate_name}} - {{job_title}}",
        "preheader": "48 hours have elapsed without a decision logged for {{candidate_name}} ({{round_name}}).",
        "trigger_event": "Candidate remains in pending state 48 hours after interview or scoring.",
        "next_step": "HR or hiring manager reviews scorecard and logs an Approve or Reject decision.",
        "required_variables": [
            "candidate_name",
            "job_title",
            "round_name",
            "company_name",
            "hr_name",
            "company_email",
            "company_website",
            "brand_color"
        ],
        "content_html": """
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">[Action Required] Pending Candidate Decision</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Hello {{hr_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">This is an automated SLA reminder that candidate <strong>{{candidate_name}}</strong> for the <strong>{{job_title}}</strong> position at <strong>{{company_name}}</strong> has been awaiting an evaluation decision for over <strong>48 hours</strong> following their <strong>{{round_name}}</strong> stage.</p>
<table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation" class="box-bg" style="margin: 20px 0; background-color: #fffbeb; border: 1px solid #fde68a; border-radius: 8px;">
  <tr>
    <td style="padding: 16px 20px;">
      <strong style="display: block; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: #b45309; margin-bottom: 4px;">Candidate Experience Alert</strong>
      <p style="margin: 0; font-size: 14px; line-height: 1.5; color: #92400e;">
        To maintain our target candidate experience SLA and prevent candidate drop-off, please log into the dashboard and record an Approve, Reject, or Hold decision today.
      </p>
    </td>
  </tr>
</table>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">Talent Operations Automation<br>{{company_name}}</p>
""",
        "text_content": """Hello {{hr_name}},

This is an automated SLA reminder that candidate {{candidate_name}} for the {{job_title}} position at {{company_name}} has been awaiting an evaluation decision for over 48 hours following their {{round_name}} stage.

CANDIDATE EXPERIENCE ALERT:
To maintain our target candidate experience SLA and prevent candidate drop-off, please log into the dashboard and record an Approve, Reject, or Hold decision today.

Talent Operations Automation
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    },
    {
        "id": "hr_candidate_moved_to_offer_section",
        "subject": "[Action Required] Prepare Offer Letter: {{candidate_name}} - {{job_title}}",
        "preheader": "{{candidate_name}} has passed all interview rounds. Ready for offer generation.",
        "trigger_event": "Candidate clears final technical round and moves to offer stage.",
        "next_step": "HR and executive leadership draft compensation terms and generate offer document.",
        "required_variables": [
            "candidate_name",
            "job_title",
            "company_name",
            "hr_name",
            "company_email",
            "company_website",
            "brand_color"
        ],
        "content_html": """
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">[Action Required] Prepare Offer Letter</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Hello {{hr_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Exciting news! Candidate <strong>{{candidate_name}}</strong> has successfully cleared all interview rounds for the <strong>{{job_title}}</strong> position at <strong>{{company_name}}</strong>, including final technical review.</p>
<table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation" class="box-bg" style="margin: 20px 0; background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px;">
  <tr>
    <td style="padding: 18px 20px;">
      <strong style="display: block; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: #166534; margin-bottom: 8px;">Action Items:</strong>
      <ul style="margin: 0; padding-left: 20px; font-size: 14px; line-height: 1.6; color: #15803d;">
        <li style="margin-bottom: 6px;">Draft formal offer letter and compensation schedule.</li>
        <li style="margin-bottom: 6px;">Secure leadership approval on equity, bonus, and base salary.</li>
        <li style="margin-bottom: 6px;">Dispatch offer letter cover template to candidate.</li>
      </ul>
    </td>
  </tr>
</table>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">Talent Operations Automation<br>{{company_name}}</p>
""",
        "text_content": """Hello {{hr_name}},

Exciting news! Candidate {{candidate_name}} has successfully cleared all interview rounds for the {{job_title}} position at {{company_name}}, including final technical review.

ACTION ITEMS:
1. Draft formal offer letter and compensation schedule.
2. Secure leadership approval on equity, bonus, and base salary.
3. Dispatch offer letter cover template to candidate.

Talent Operations Automation
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    }
]

print(f"Loaded {len(INTERNAL_TEMPLATES)} internal templates.")
