"""
Core Templates (1 to 9) for Automated Hiring Pipeline.
"""

CORE_TEMPLATES = [
    {
        "id": "cv_received",
        "subject": "Application Received: {{job_title}} at {{company_name}}",
        "preheader": "We have received your application for the {{job_title}} position at {{company_name}}.",
        "trigger_event": "Candidate submits CV via Gmail or job application form.",
        "next_step": "AI parses and scores candidate CV; HR reviews candidate scorecard.",
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
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">Application Received</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Dear {{candidate_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Thank you for your interest in joining <strong>{{company_name}}</strong>. We are pleased to confirm that we have received your resume and application materials for the <strong>{{job_title}}</strong> position.</p>
<table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation" class="box-bg" style="margin: 20px 0; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;">
  <tr>
    <td style="padding: 16px 20px;">
      <table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation">
        <tr>
          <td style="padding: 4px 0; font-size: 13px; color: #64748b; font-weight: bold; width: 35%;">Position:</td>
          <td style="padding: 4px 0; font-size: 14px; color: #0f172a; font-weight: 600;">{{job_title}}</td>
        </tr>
        <tr>
          <td style="padding: 4px 0; font-size: 13px; color: #64748b; font-weight: bold;">Organization:</td>
          <td style="padding: 4px 0; font-size: 14px; color: #0f172a; font-weight: 600;">{{company_name}}</td>
        </tr>
        <tr>
          <td style="padding: 4px 0; font-size: 13px; color: #64748b; font-weight: bold;">Current Status:</td>
          <td style="padding: 4px 0; font-size: 14px; color: {{brand_color}}; font-weight: 600;">Under Review</td>
        </tr>
      </table>
    </td>
  </tr>
</table>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Our talent acquisition team is actively evaluating your qualifications, achievements, and technical background against the specific objectives of this role.</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">If your profile meets our current requirements, we will reach out directly with instructions regarding the next phase of our interview process. Thank you again for your time, effort, and interest in our organization.</p>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">Warm regards,<br><strong>{{hr_name}}</strong><br>{{company_name}} Recruiting Team</p>
""",
        "text_content": """Dear {{candidate_name}},

Thank you for your interest in joining {{company_name}}. We are pleased to confirm that we have received your resume and application materials for the {{job_title}} position.

APPLICATION SUMMARY:
- Position: {{job_title}}
- Organization: {{company_name}}
- Current Status: Under Review

Our talent acquisition team is actively evaluating your qualifications, achievements, and technical background against the specific objectives of this role.

If your profile meets our current requirements, we will reach out directly with instructions regarding the next phase of our interview process. Thank you again for your time, effort, and interest in our organization.

Warm regards,
{{hr_name}}
Talent Acquisition Team
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    },
    {
        "id": "application_rejected",
        "subject": "Update regarding your application for {{job_title}} at {{company_name}}",
        "preheader": "Thank you for your interest in the {{job_title}} position at {{company_name}}.",
        "trigger_event": "HR reviews candidate CV scorecard and marks application as rejected.",
        "next_step": "Candidate profile archived; candidate eligible for future openings.",
        "required_variables": [
            "candidate_name",
            "job_title",
            "company_name",
            "feedback",
            "hr_name",
            "company_email",
            "company_website",
            "brand_color"
        ],
        "content_html": """
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">Application Status Update</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Dear {{candidate_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Thank you for taking the time to apply for the <strong>{{job_title}}</strong> position at <strong>{{company_name}}</strong>. We sincerely appreciate your interest in our team and the opportunity to review your professional credentials.</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">After careful evaluation of your application alongside a strong volume of candidates, we have decided not to advance your candidacy to the interview stage at this time. We are focusing our search on profiles with closer alignment to our immediate project stack and operational needs.</p>
<table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation" class="quote-bg" style="margin: 24px 0; background-color: #f8fafc; border-left: 4px solid {{brand_color}}; border-radius: 0 8px 8px 0;">
  <tr>
    <td style="padding: 16px 20px;">
      <span style="display: block; font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; color: #64748b; margin-bottom: 6px;">Evaluation Feedback</span>
      <p class="text-body" style="margin: 0; font-size: 14px; line-height: 1.6; color: #334155; font-style: italic;">
        "{{feedback}}"
      </p>
    </td>
  </tr>
</table>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Please know that our decision relates strictly to our current requisitions and is not a reflection of your overall abilities. We encourage you to monitor our careers page and apply for future openings that match your skill set.</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">We wish you every success with your continued career search.</p>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">Sincerely,<br><strong>{{hr_name}}</strong><br>{{company_name}} Recruiting Team</p>
""",
        "text_content": """Dear {{candidate_name}},

Thank you for taking the time to apply for the {{job_title}} position at {{company_name}}. We sincerely appreciate your interest in our team and the opportunity to review your professional credentials.

After careful evaluation of your application alongside a strong volume of candidates, we have decided not to advance your candidacy to the interview stage at this time. We are focusing our search on profiles with closer alignment to our immediate project stack and operational needs.

--------------------------------------------------
EVALUATION FEEDBACK:
"{{feedback}}"
--------------------------------------------------

Please know that our decision relates strictly to our current requisitions and is not a reflection of your overall abilities. We encourage you to monitor our careers page and apply for future openings that match your skill set.

We wish you every success with your continued career search.

Sincerely,
{{hr_name}}
Talent Acquisition Team
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    },
    {
        "id": "application_approved",
        "subject": "Congratulations! Next Steps for {{job_title}} at {{company_name}}",
        "preheader": "Your application for {{job_title}} has been approved. Please share your availability.",
        "trigger_event": "HR approves candidate screening; candidate shortlisted for initial interview.",
        "next_step": "Candidate replies with 2-3 availability time slots for Initial Interview.",
        "required_variables": [
            "candidate_name",
            "job_title",
            "company_name",
            "job_description",
            "reply_deadline",
            "hr_name",
            "company_email",
            "company_website",
            "brand_color"
        ],
        "content_html": """
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">Application Shortlisted</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Dear {{candidate_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Great news! We have thoroughly reviewed your background and resume, and we are delighted to invite you to the <strong>Initial Interview</strong> for the <strong>{{job_title}}</strong> position at <strong>{{company_name}}</strong>.</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">This introductory 30-minute conversation is designed to get to know you better, learn more about your technical and career journey, and discuss how your skills align with our current objectives.</p>
<table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation" class="box-bg" style="margin: 20px 0; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;">
  <tr>
    <td style="padding: 18px 20px;">
      <strong class="text-heading" style="display: block; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: {{brand_color}}; margin-bottom: 8px;">Role Overview & Key Focus</strong>
      <p class="text-body" style="margin: 0; font-size: 14px; line-height: 1.6; color: #334155;">
        {{job_description}}
      </p>
    </td>
  </tr>
</table>
<table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation" style="margin: 20px 0; background-color: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 8px;">
  <tr>
    <td style="padding: 16px 20px;">
      <strong style="display: block; font-size: 13px; color: #065f46; margin-bottom: 6px;">Action Required: Submit Your Availability</strong>
      <p style="margin: 0; font-size: 14px; line-height: 1.5; color: #047857;">
        Please reply directly to this email by <strong>{{reply_deadline}}</strong> with <strong>2 to 3 preferred time slots</strong> (including your timezone) across the next several business days.
      </p>
    </td>
  </tr>
</table>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Upon receiving your reply, our recruiting team will confirm the date, time, and video meeting link. We look forward to speaking with you!</p>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">Warm regards,<br><strong>{{hr_name}}</strong><br>{{company_name}} Recruiting Team</p>
""",
        "text_content": """Dear {{candidate_name}},

Great news! We have thoroughly reviewed your background and resume, and we are delighted to invite you to the Initial Interview for the {{job_title}} position at {{company_name}}.

This introductory 30-minute conversation is designed to get to know you better, learn more about your technical and career journey, and discuss how your skills align with our current objectives.

ROLE OVERVIEW & KEY FOCUS:
{{job_description}}

ACTION REQUIRED:
Please reply directly to this email by {{reply_deadline}} with 2 to 3 preferred time slots (including your timezone) across the next several business days during standard working hours.

Upon receiving your reply, our recruiting team will confirm the date, time, and video meeting link. We look forward to speaking with you!

Warm regards,
{{hr_name}}
Talent Acquisition Team
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    },
    {
        "id": "interview_confirmed",
        "subject": "Confirmed: {{round_name}} Interview for {{job_title}} - {{date}}",
        "preheader": "Your {{round_name}} Interview for {{job_title}} is scheduled for {{date}} at {{time}} {{timezone}}.",
        "trigger_event": "Recruiter schedules interview round in calendar.",
        "next_step": "Candidate and interviewer join video meeting at confirmed time.",
        "required_variables": [
            "candidate_name",
            "job_title",
            "company_name",
            "round_name",
            "date",
            "time",
            "timezone",
            "meeting_link",
            "hr_name",
            "company_email",
            "company_website",
            "brand_color"
        ],
        "content_html": """
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">Interview Confirmed</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Dear {{candidate_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Your <strong>{{round_name}} Interview</strong> for the <strong>{{job_title}}</strong> position at <strong>{{company_name}}</strong> has been confirmed. Below are your meeting details:</p>
<table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation" class="box-bg" style="margin: 20px 0; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;">
  <tr>
    <td style="padding: 18px 20px;">
      <strong class="text-heading" style="display: block; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: {{brand_color}}; margin-bottom: 12px;">Interview Details</strong>
      <table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation">
        <tr>
          <td style="padding: 5px 0; font-size: 13px; color: #64748b; font-weight: bold; width: 35%;">Interview Stage:</td>
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
<table border="0" cellpadding="0" cellspacing="0" role="presentation" style="margin: 28px 0 24px 0;">
  <tr>
    <td align="center" style="border-radius: 6px; background-color: {{brand_color}};">
      <a href="{{meeting_link}}" target="_blank" style="display: inline-block; padding: 14px 28px; font-family: Arial, Helvetica, sans-serif; font-size: 14px; font-weight: bold; color: #ffffff; text-decoration: none; border-radius: 6px; border: 1px solid {{brand_color}}; text-align: center; line-height: 1;">
        Join Video Meeting &rarr;
      </a>
    </td>
  </tr>
</table>
<p class="text-body" style="margin: 0 0 12px 0; font-size: 14px; line-height: 1.6; color: #475569;"><strong>Important Instructions:</strong></p>
<ul style="margin: 0 0 16px 0; padding-left: 20px; color: #475569; font-size: 14px; line-height: 1.6;">
  <li style="margin-bottom: 6px;">Please join the video conference link <strong>5 minutes early</strong> to verify your audio and video connections.</li>
  <li style="margin-bottom: 6px;">Ensure you are in a quiet environment with a reliable internet connection.</li>
  <li style="margin-bottom: 6px;">If you need to reschedule, please provide at least <strong>24 hours advance notice</strong> by replying directly to this email so we can coordinate with our interviewing team.</li>
</ul>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">Best regards,<br><strong>{{hr_name}}</strong><br>{{company_name}} Recruiting Team</p>
""",
        "text_content": """Dear {{candidate_name}},

Your {{round_name}} Interview for the {{job_title}} position at {{company_name}} has been confirmed. Below are your meeting details:

INTERVIEW DETAILS:
- Interview Stage: {{round_name}} Interview
- Date: {{date}}
- Time: {{time}} ({{timezone}})
- Meeting Link: {{meeting_link}}

IMPORTANT INSTRUCTIONS:
- Please join the video meeting 5 minutes early to test your audio, camera, and network connection.
- Ensure you are in a quiet room with minimal background noise.
- Reschedule Policy: If you need to reschedule, please notify us at least 24 hours in advance by replying directly to this email.

Best regards,
{{hr_name}}
Talent Acquisition Team
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    },
    {
        "id": "alternate_slots",
        "subject": "Scheduling Your {{round_name}} Interview: Alternate Times for {{job_title}}",
        "preheader": "Please review alternate interview times for your {{round_name}} Interview.",
        "trigger_event": "Candidate proposed slots conflict with interviewer calendar availability.",
        "next_step": "Candidate picks one alternate slot or suggests new times by reply deadline.",
        "required_variables": [
            "candidate_name",
            "job_title",
            "company_name",
            "round_name",
            "slot_1",
            "slot_2",
            "slot_3",
            "reply_deadline",
            "hr_name",
            "company_email",
            "company_website",
            "brand_color"
        ],
        "content_html": """
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">Alternate Interview Times</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Dear {{candidate_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Thank you for sharing your availability for the <strong>{{round_name}} Interview</strong> for the <strong>{{job_title}}</strong> role at <strong>{{company_name}}</strong>.</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Unfortunately, our interviewing panel has preexisting scheduling conflicts during the specific windows you proposed. To ensure we keep your candidacy moving forward smoothly, we would like to offer the following alternate slots:</p>
<table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation" class="box-bg" style="margin: 20px 0; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;">
  <tr>
    <td style="padding: 18px 20px;">
      <strong class="text-heading" style="display: block; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: {{brand_color}}; margin-bottom: 12px;">Available Options (Choose One)</strong>
      <table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation">
        <tr>
          <td style="padding: 8px 12px; margin-bottom: 6px; background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 14px; font-weight: 600; color: #0f172a;">
            &bull; Option A: {{slot_1}}
          </td>
        </tr>
        <tr><td height="8" style="font-size: 0; line-height: 0;">&nbsp;</td></tr>
        <tr>
          <td style="padding: 8px 12px; margin-bottom: 6px; background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 14px; font-weight: 600; color: #0f172a;">
            &bull; Option B: {{slot_2}}
          </td>
        </tr>
        <tr><td height="8" style="font-size: 0; line-height: 0;">&nbsp;</td></tr>
        <tr>
          <td style="padding: 8px 12px; background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 14px; font-weight: 600; color: #0f172a;">
            &bull; Option C: {{slot_3}}
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Please reply directly to this email by <strong>{{reply_deadline}}</strong> indicating which of the above slots works best for you. If none of these options suit your schedule, please feel free to provide 2 to 3 new time windows.</p>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">Warm regards,<br><strong>{{hr_name}}</strong><br>{{company_name}} Recruiting Team</p>
""",
        "text_content": """Dear {{candidate_name}},

Thank you for sharing your availability for the {{round_name}} Interview for the {{job_title}} role at {{company_name}}.

Unfortunately, our interviewing panel has preexisting scheduling conflicts during the specific windows you proposed. To ensure we keep your candidacy moving forward smoothly, we would like to offer the following alternate slots:

ALTERNATE SLOTS:
1. {{slot_1}}
2. {{slot_2}}
3. {{slot_3}}

Please reply directly to this email by {{reply_deadline}} indicating which option works best for you. If none of these slots fit your schedule, please propose 2 to 3 alternative windows with your timezone.

Warm regards,
{{hr_name}}
Talent Acquisition Team
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    },
    {
        "id": "next_round_availability",
        "subject": "You're Moving Forward! Availability for {{round_name}} Interview - {{company_name}}",
        "preheader": "Congratulations on passing your previous round! Next step: {{round_name}} Interview.",
        "trigger_event": "Candidate passes previous interview round; advance to next round.",
        "next_step": "Candidate replies with availability slots for the next round.",
        "required_variables": [
            "candidate_name",
            "job_title",
            "company_name",
            "round_name",
            "round_description",
            "reply_deadline",
            "hr_name",
            "company_email",
            "company_website",
            "brand_color"
        ],
        "content_html": """
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">Advancing to Next Round</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Dear {{candidate_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Congratulations! Our team thoroughly enjoyed speaking with you in your previous discussion, and we are excited to invite you to the next stage of our evaluation: the <strong>{{round_name}} Interview</strong> for the <strong>{{job_title}}</strong> role at <strong>{{company_name}}</strong>.</p>
<table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation" class="box-bg" style="margin: 20px 0; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;">
  <tr>
    <td style="padding: 18px 20px;">
      <strong class="text-heading" style="display: block; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: {{brand_color}}; margin-bottom: 8px;">Round Overview: {{round_name}}</strong>
      <p class="text-body" style="margin: 0; font-size: 14px; line-height: 1.6; color: #334155;">
        {{round_description}}
      </p>
    </td>
  </tr>
</table>
<table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation" style="margin: 20px 0; background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px;">
  <tr>
    <td style="padding: 16px 20px;">
      <strong style="display: block; font-size: 13px; color: #166534; margin-bottom: 6px;">Next Step: Provide Your Availability</strong>
      <p style="margin: 0; font-size: 14px; line-height: 1.5; color: #15803d;">
        Please reply directly to this note by <strong>{{reply_deadline}}</strong> with <strong>2 to 3 available dates and times</strong> (including your timezone) across the upcoming week.
      </p>
    </td>
  </tr>
</table>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Once we receive your preferred times, we will coordinate with the interviewers and issue your calendar invite with video conference details.</p>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">Warm regards,<br><strong>{{hr_name}}</strong><br>{{company_name}} Recruiting Team</p>
""",
        "text_content": """Dear {{candidate_name}},

Congratulations! Our team thoroughly enjoyed speaking with you in your previous discussion, and we are excited to invite you to the next stage of our evaluation: the {{round_name}} Interview for the {{job_title}} role at {{company_name}}.

ROUND OVERVIEW: {{round_name}}
{{round_description}}

NEXT STEP:
Please reply directly to this email by {{reply_deadline}} with 2 to 3 available dates and times (including your timezone) across the upcoming week.

Once we receive your preferred times, we will coordinate with the interviewers and issue your calendar invite with video conference details.

Warm regards,
{{hr_name}}
Talent Acquisition Team
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    },
    {
        "id": "interview_passed",
        "subject": "Great news regarding your {{round_name}} Interview for {{job_title}}",
        "preheader": "You have successfully passed the {{round_name}} Interview for {{job_title}} at {{company_name}}!",
        "trigger_event": "Interviewer/HR logs passing scorecard for Initial or Behavioral round.",
        "next_step": "Recruiter sends next_round_availability with specific round expectations.",
        "required_variables": [
            "candidate_name",
            "job_title",
            "company_name",
            "round_name",
            "hr_name",
            "company_email",
            "company_website",
            "brand_color"
        ],
        "content_html": """
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">Interview Stage Cleared</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Dear {{candidate_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">We are pleased to inform you that you have successfully cleared the <strong>{{round_name}} Interview</strong> for the <strong>{{job_title}}</strong> position at <strong>{{company_name}}</strong>!</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">The interviewers were very impressed with your structured communication, professional depth, and domain knowledge throughout the conversation.</p>
<table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation" class="box-bg" style="margin: 20px 0; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;">
  <tr>
    <td style="padding: 16px 20px;">
      <span style="display: block; font-size: 12px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; color: {{brand_color}}; margin-bottom: 4px;">Status</span>
      <p class="text-body" style="margin: 0; font-size: 14px; font-weight: 600; color: #0f172a;">
        Passed {{round_name}} &bull; Advancing to Next Evaluation Stage
      </p>
    </td>
  </tr>
</table>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Our recruiting coordinator will be in touch within 24 to 48 hours with full preparation notes and scheduling instructions for your next session. Keep up the wonderful work!</p>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">Warm regards,<br><strong>{{hr_name}}</strong><br>{{company_name}} Recruiting Team</p>
""",
        "text_content": """Dear {{candidate_name}},

We are pleased to inform you that you have successfully cleared the {{round_name}} Interview for the {{job_title}} position at {{company_name}}!

The interviewers were very impressed with your structured communication, professional depth, and domain knowledge throughout the conversation.

STATUS: Passed {{round_name}} - Advancing to Next Stage

Our recruiting coordinator will be in touch within 24 to 48 hours with full preparation notes and scheduling instructions for your next session. Keep up the wonderful work!

Warm regards,
{{hr_name}}
Talent Acquisition Team
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    },
    {
        "id": "interview_rejected",
        "subject": "Update on your interview for {{job_title}} at {{company_name}}",
        "preheader": "Thank you for taking the time to interview with us for the {{job_title}} position.",
        "trigger_event": "Candidate rejected following any interview round evaluation.",
        "next_step": "Candidate file closed; feedback recorded in pipeline archive.",
        "required_variables": [
            "candidate_name",
            "job_title",
            "company_name",
            "round_name",
            "feedback",
            "hr_name",
            "company_email",
            "company_website",
            "brand_color"
        ],
        "content_html": """
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">Interview Evaluation Update</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Dear {{candidate_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Thank you very much for meeting with our team during the <strong>{{round_name}} Interview</strong> for the <strong>{{job_title}}</strong> role at <strong>{{company_name}}</strong>. We sincerely appreciate the time, preparation, and energy you invested in speaking with us.</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">While our interviewing panel was impressed by many aspects of your background, we have made the difficult decision not to advance your candidacy to the next stage. We evaluated several exceptional candidates and chose to proceed with those whose specific experience more closely aligns with our immediate technical priorities.</p>
<table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation" class="quote-bg" style="margin: 24px 0; background-color: #f8fafc; border-left: 4px solid {{brand_color}}; border-radius: 0 8px 8px 0;">
  <tr>
    <td style="padding: 16px 20px;">
      <span style="display: block; font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; color: #64748b; margin-bottom: 6px;">Evaluation Feedback</span>
      <p class="text-body" style="margin: 0; font-size: 14px; line-height: 1.6; color: #334155; font-style: italic;">
        "{{feedback}}"
      </p>
    </td>
  </tr>
</table>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">We would like to retain your resume in our talent network for future openings that match your skills. We wish you continued success in your professional endeavors and thank you again for considering {{company_name}}.</p>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">Warm regards,<br><strong>{{hr_name}}</strong><br>{{company_name}} Recruiting Team</p>
""",
        "text_content": """Dear {{candidate_name}},

Thank you very much for meeting with our team during the {{round_name}} Interview for the {{job_title}} role at {{company_name}}. We sincerely appreciate the time, preparation, and energy you invested in speaking with us.

While our interviewing panel was impressed by many aspects of your background, we have made the difficult decision not to advance your candidacy to the next stage. We evaluated several exceptional candidates and chose to proceed with those whose specific experience more closely aligns with our immediate technical priorities.

--------------------------------------------------
EVALUATION FEEDBACK:
"{{feedback}}"
--------------------------------------------------

We would like to retain your resume in our talent network for future openings that match your skills. We wish you continued success in your professional endeavors and thank you again for considering {{company_name}}.

Warm regards,
{{hr_name}}
Talent Acquisition Team
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    },
    {
        "id": "all_rounds_cleared",
        "subject": "Congratulations! You have cleared all interview rounds for {{job_title}} at {{company_name}}",
        "preheader": "You have successfully completed all interview stages for {{job_title}} at {{company_name}}!",
        "trigger_event": "Candidate clears final technical round with positive recommendation.",
        "next_step": "HR prepares offer letter and schedules offer review call.",
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
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">Congratulations! All Rounds Cleared</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Dear {{candidate_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">On behalf of the entire hiring committee at <strong>{{company_name}}</strong>, we are thrilled to congratulate you on successfully clearing every stage of our interview process for the <strong>{{job_title}}</strong> position!</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Across your Initial, Behavioral, and final Technical rounds, our team was universally impressed by your technical mastery, thoughtful problem-solving, and dedication to excellence.</p>
<table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation" style="margin: 20px 0; background-color: #ecfdf5; border: 1px solid #6ee7b7; border-radius: 8px;">
  <tr>
    <td style="padding: 18px 20px;">
      <strong style="display: block; font-size: 13px; color: #065f46; margin-bottom: 6px;">Next Step: Offer Package Finalization</strong>
      <p style="margin: 0; font-size: 14px; line-height: 1.5; color: #047857;">
        Our talent acquisition leadership and hiring executive team are currently assembling your formal offer letter and onboarding roadmap.
      </p>
    </td>
  </tr>
</table>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">We will reach out shortly to share your official offer letter and answer any questions you may have. Thank you once again for your remarkable commitment throughout this interview journey.</p>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">With warmest congratulations,<br><strong>{{hr_name}}</strong><br>{{company_name}} Leadership &amp; Talent Team</p>
""",
        "text_content": """Dear {{candidate_name}},

On behalf of the entire hiring committee at {{company_name}}, we are thrilled to congratulate you on successfully clearing every stage of our interview process for the {{job_title}} position!

Across your Initial, Behavioral, and final Technical rounds, our team was universally impressed by your technical mastery, thoughtful problem-solving, and dedication to excellence.

NEXT STEP: OFFER PACKAGE FINALIZATION
Our talent acquisition leadership and hiring executive team are currently assembling your formal offer letter and onboarding roadmap.

We will reach out shortly to share your official offer letter and answer any questions you may have. Thank you once again for your remarkable commitment throughout this interview journey.

With warmest congratulations,
{{hr_name}}
Leadership & Talent Team
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    }
]

print(f"Loaded {len(CORE_TEMPLATES)} core templates.")
