"""
Supporting Templates (10 to 25) for Automated Hiring Pipeline.
"""

SUPPORTING_TEMPLATES = [
    {
        "id": "interview_reminder_24h",
        "subject": "Reminder: {{round_name}} Interview Tomorrow - {{job_title}} at {{company_name}}",
        "preheader": "Your {{round_name}} Interview is scheduled for tomorrow at {{time}} {{timezone}}.",
        "trigger_event": "24 hours prior to scheduled interview round.",
        "next_step": "Candidate verifies readiness and attends interview on schedule.",
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
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">Upcoming Interview Reminder</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Dear {{candidate_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">This is a friendly reminder that your <strong>{{round_name}} Interview</strong> for the <strong>{{job_title}}</strong> position at <strong>{{company_name}}</strong> takes place tomorrow.</p>
<table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation" class="box-bg" style="margin: 20px 0; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;">
  <tr>
    <td style="padding: 18px 20px;">
      <strong class="text-heading" style="display: block; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: {{brand_color}}; margin-bottom: 12px;">Meeting Schedule</strong>
      <table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation">
        <tr>
          <td style="padding: 5px 0; font-size: 13px; color: #64748b; font-weight: bold; width: 35%;">Stage:</td>
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
        Access Meeting Link &rarr;
      </a>
    </td>
  </tr>
</table>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 14px; line-height: 1.6; color: #475569;">Please plan to enter the meeting room 5 minutes before the start time. We look forward to speaking with you!</p>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">Best regards,<br><strong>{{hr_name}}</strong><br>{{company_name}} Recruiting Team</p>
""",
        "text_content": """Dear {{candidate_name}},

This is a friendly reminder that your {{round_name}} Interview for the {{job_title}} position at {{company_name}} takes place tomorrow.

MEETING SCHEDULE:
- Stage: {{round_name}} Interview
- Date: {{date}}
- Time: {{time}} ({{timezone}})
- Meeting Link: {{meeting_link}}

Please plan to enter the meeting room 5 minutes before the start time. We look forward to speaking with you!

Best regards,
{{hr_name}}
Talent Acquisition Team
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    },
    {
        "id": "interview_reminder_1h",
        "subject": "Starting in 1 Hour: {{round_name}} Interview for {{job_title}}",
        "preheader": "Your {{round_name}} Interview begins at {{time}} {{timezone}}. Meeting link enclosed.",
        "trigger_event": "1 hour prior to scheduled interview round.",
        "next_step": "Candidate joins video call room 5 minutes early.",
        "required_variables": [
            "candidate_name",
            "job_title",
            "company_name",
            "round_name",
            "time",
            "timezone",
            "meeting_link",
            "hr_name",
            "company_email",
            "company_website",
            "brand_color"
        ],
        "content_html": """
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">Starting in 1 Hour</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Dear {{candidate_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Your <strong>{{round_name}} Interview</strong> for the <strong>{{job_title}}</strong> role at <strong>{{company_name}}</strong> will begin in approximately one hour at <strong>{{time}} ({{timezone}})</strong>.</p>
<table border="0" cellpadding="0" cellspacing="0" role="presentation" style="margin: 24px 0 24px 0;">
  <tr>
    <td align="center" style="border-radius: 6px; background-color: {{brand_color}};">
      <a href="{{meeting_link}}" target="_blank" style="display: inline-block; padding: 14px 32px; font-family: Arial, Helvetica, sans-serif; font-size: 14px; font-weight: bold; color: #ffffff; text-decoration: none; border-radius: 6px; border: 1px solid {{brand_color}}; text-align: center; line-height: 1;">
        Join Video Call Now &rarr;
      </a>
    </td>
  </tr>
</table>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 14px; line-height: 1.6; color: #475569;">Please make sure your camera and microphone are tested, and join a few minutes early to ensure a prompt start.</p>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">See you shortly,<br><strong>{{hr_name}}</strong><br>{{company_name}} Recruiting Team</p>
""",
        "text_content": """Dear {{candidate_name}},

Your {{round_name}} Interview for the {{job_title}} role at {{company_name}} will begin in approximately one hour at {{time}} ({{timezone}}).

MEETING LINK: {{meeting_link}}

Please make sure your camera and microphone are tested, and join a few minutes early to ensure a prompt start.

See you shortly,
{{hr_name}}
Talent Acquisition Team
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    },
    {
        "id": "no_response_followup",
        "subject": "Following up: Next steps for {{job_title}} at {{company_name}}",
        "preheader": "Just checking in regarding your interview scheduling for {{job_title}}.",
        "trigger_event": "Candidate has not replied 48 hours after availability request.",
        "next_step": "Candidate replies with time slots before reply deadline.",
        "required_variables": [
            "candidate_name",
            "job_title",
            "company_name",
            "reply_deadline",
            "hr_name",
            "company_email",
            "company_website",
            "brand_color"
        ],
        "content_html": """
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">Following Up On Your Application</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Dear {{candidate_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">We are following up on our previous note regarding your application for the <strong>{{job_title}}</strong> position at <strong>{{company_name}}</strong>. We remain very eager to connect with you!</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Please reply directly to this email by <strong>{{reply_deadline}}</strong> with <strong>2 to 3 preferred dates and time slots</strong> (including your timezone) so we can lock in your interview on the team's calendar.</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 14px; line-height: 1.6; color: #64748b;">If you are no longer interested in exploring opportunities with us at this time, please let us know so we can update our records accordingly.</p>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">Warm regards,<br><strong>{{hr_name}}</strong><br>{{company_name}} Recruiting Team</p>
""",
        "text_content": """Dear {{candidate_name}},

We are following up on our previous note regarding your application for the {{job_title}} position at {{company_name}}. We remain very eager to connect with you!

Please reply directly to this email by {{reply_deadline}} with 2 to 3 preferred dates and time slots (including your timezone) so we can lock in your interview on the team's calendar.

If you are no longer interested in exploring opportunities with us at this time, please let us know so we can update our records accordingly.

Warm regards,
{{hr_name}}
Talent Acquisition Team
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    },
    {
        "id": "application_closed_no_response",
        "subject": "Application Closed: {{job_title}} at {{company_name}}",
        "preheader": "Notice regarding your application status for {{job_title}} at {{company_name}}.",
        "trigger_event": "Reply deadline elapsed without response from candidate.",
        "next_step": "Application archived; candidate can reapply in the future.",
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
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">Application Status: Closed</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Dear {{candidate_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">We are writing to inform you that because we have not received a response regarding interview scheduling for the <strong>{{job_title}}</strong> position at <strong>{{company_name}}</strong>, we have closed your application file for this opening.</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">We understand that timing and circumstances change. If you wish to be considered for future opportunities or if your schedule frees up down the road, please feel free to submit a new application through our careers portal.</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">We thank you for your initial interest in {{company_name}} and wish you the best in your career pursuits.</p>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">Sincerely,<br><strong>{{hr_name}}</strong><br>{{company_name}} Recruiting Team</p>
""",
        "text_content": """Dear {{candidate_name}},

We are writing to inform you that because we have not received a response regarding interview scheduling for the {{job_title}} position at {{company_name}}, we have closed your application file for this opening.

We understand that timing and circumstances change. If you wish to be considered for future opportunities or if your schedule frees up down the road, please feel free to submit a new application through our careers portal.

We thank you for your initial interest in {{company_name}} and wish you the best in your career pursuits.

Sincerely,
{{hr_name}}
Talent Acquisition Team
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    },
    {
        "id": "interview_rescheduled",
        "subject": "Rescheduled: {{round_name}} Interview for {{job_title}} - {{date}}",
        "preheader": "Your {{round_name}} Interview has been rescheduled to {{date}} at {{time}} {{timezone}}.",
        "trigger_event": "Interview rescheduled due to candidate or interviewer calendar adjustment.",
        "next_step": "Candidate and interviewer attend interview at updated date and time.",
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
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">Interview Rescheduled</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Dear {{candidate_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Your <strong>{{round_name}} Interview</strong> for the <strong>{{job_title}}</strong> position at <strong>{{company_name}}</strong> has been successfully rescheduled. Please review your updated time slot below:</p>
<table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation" class="box-bg" style="margin: 20px 0; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;">
  <tr>
    <td style="padding: 18px 20px;">
      <strong class="text-heading" style="display: block; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: {{brand_color}}; margin-bottom: 12px;">New Interview Details</strong>
      <table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation">
        <tr>
          <td style="padding: 5px 0; font-size: 13px; color: #64748b; font-weight: bold; width: 35%;">Interview Stage:</td>
          <td style="padding: 5px 0; font-size: 14px; color: #0f172a; font-weight: 600;">{{round_name}} Interview</td>
        </tr>
        <tr>
          <td style="padding: 5px 0; font-size: 13px; color: #64748b; font-weight: bold;">New Date:</td>
          <td style="padding: 5px 0; font-size: 14px; color: #0f172a; font-weight: 600;">{{date}}</td>
        </tr>
        <tr>
          <td style="padding: 5px 0; font-size: 13px; color: #64748b; font-weight: bold;">New Time:</td>
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
        Access Video Conference &rarr;
      </a>
    </td>
  </tr>
</table>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 14px; line-height: 1.6; color: #475569;">Your calendar invitation has been updated to reflect this new date and time. Please reach out if you have any questions.</p>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">Best regards,<br><strong>{{hr_name}}</strong><br>{{company_name}} Recruiting Team</p>
""",
        "text_content": """Dear {{candidate_name}},

Your {{round_name}} Interview for the {{job_title}} position at {{company_name}} has been successfully rescheduled. Please review your updated time slot below:

NEW INTERVIEW DETAILS:
- Stage: {{round_name}} Interview
- New Date: {{date}}
- New Time: {{time}} ({{timezone}})
- Meeting Link: {{meeting_link}}

Your calendar invitation has been updated to reflect this new date and time. Please reach out if you have any questions.

Best regards,
{{hr_name}}
Talent Acquisition Team
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    },
    {
        "id": "interview_cancelled_by_company",
        "subject": "Notice: Cancellation of {{round_name}} Interview for {{job_title}}",
        "preheader": "Important update regarding your scheduled {{round_name}} Interview on {{date}}.",
        "trigger_event": "Company cancels interview due to unforeseen internal conflict or emergency.",
        "next_step": "Recruiter follows up within 24 hours to re-coordinate interview timing.",
        "required_variables": [
            "candidate_name",
            "job_title",
            "company_name",
            "round_name",
            "date",
            "hr_name",
            "company_email",
            "company_website",
            "brand_color"
        ],
        "content_html": """
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">Interview Cancellation Notice</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Dear {{candidate_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">We sincerely apologize, but due to an unexpected scheduling conflict on our team, we need to cancel your upcoming <strong>{{round_name}} Interview</strong> for the <strong>{{job_title}}</strong> role originally scheduled on <strong>{{date}}</strong> at <strong>{{company_name}}</strong>.</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Please rest assured that your candidacy remains highly valued and in active consideration. We deeply respect your time and regret any inconvenience this sudden change may cause.</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Our recruiting coordinator will contact you within the next 24 hours with new interview options to reschedule this discussion at your earliest convenience.</p>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">With our sincere apologies,<br><strong>{{hr_name}}</strong><br>{{company_name}} Recruiting Team</p>
""",
        "text_content": """Dear {{candidate_name}},

We sincerely apologize, but due to an unexpected scheduling conflict on our team, we need to cancel your upcoming {{round_name}} Interview for the {{job_title}} role originally scheduled on {{date}} at {{company_name}}.

Please rest assured that your candidacy remains highly valued and in active consideration. We deeply respect your time and regret any inconvenience this sudden change may cause.

Our recruiting coordinator will contact you within the next 24 hours with new interview options to reschedule this discussion at your earliest convenience.

With our sincere apologies,
{{hr_name}}
Talent Acquisition Team
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    },
    {
        "id": "candidate_cancelled_confirmation",
        "subject": "Confirmation of Interview Cancellation: {{job_title}} at {{company_name}}",
        "preheader": "We have processed your interview cancellation for the {{round_name}} round.",
        "trigger_event": "Candidate requests interview cancellation.",
        "next_step": "Assess whether candidate requests reschedule or formal application withdrawal.",
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
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">Cancellation Confirmed</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Dear {{candidate_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">We have received your message and confirmed the cancellation of your <strong>{{round_name}} Interview</strong> for the <strong>{{job_title}}</strong> position at <strong>{{company_name}}</strong>.</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">If you would like to reschedule your interview for a different date and time, please reply directly to this email with your updated availability windows.</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Alternatively, if you wish to withdraw your application from consideration, simply let us know and we will archive your profile with gratitude for your time.</p>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">Best regards,<br><strong>{{hr_name}}</strong><br>{{company_name}} Recruiting Team</p>
""",
        "text_content": """Dear {{candidate_name}},

We have received your message and confirmed the cancellation of your {{round_name}} Interview for the {{job_title}} position at {{company_name}}.

If you would like to reschedule your interview for a different date and time, please reply directly to this email with your updated availability windows.

Alternatively, if you wish to withdraw your application from consideration, simply let us know and we will archive your profile with gratitude for your time.

Best regards,
{{hr_name}}
Talent Acquisition Team
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    },
    {
        "id": "candidate_no_show",
        "subject": "We missed you today: {{round_name}} Interview for {{job_title}}",
        "preheader": "We were unable to connect with you for your {{round_name}} Interview on {{date}}.",
        "trigger_event": "Candidate does not attend interview call after 15-minute grace period.",
        "next_step": "Candidate replies within 24 hours to explain absence or reschedule.",
        "required_variables": [
            "candidate_name",
            "job_title",
            "company_name",
            "round_name",
            "date",
            "reply_deadline",
            "hr_name",
            "company_email",
            "company_website",
            "brand_color"
        ],
        "content_html": """
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">We Missed You Today</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Dear {{candidate_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Our team was online and waiting for your scheduled <strong>{{round_name}} Interview</strong> for the <strong>{{job_title}}</strong> position on <strong>{{date}}</strong> at <strong>{{company_name}}</strong>, but were unable to connect with you.</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">We understand that unforeseen technical difficulties or personal emergencies can occur. If you are still interested in pursuing this opportunity, please reply to this email by <strong>{{reply_deadline}}</strong> with an update and your upcoming availability so we can determine whether rescheduling is feasible.</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 14px; line-height: 1.6; color: #64748b;">If we do not hear from you by the deadline, we will assume your circumstances have changed and will close your application file.</p>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">Best regards,<br><strong>{{hr_name}}</strong><br>{{company_name}} Recruiting Team</p>
""",
        "text_content": """Dear {{candidate_name}},

Our team was online and waiting for your scheduled {{round_name}} Interview for the {{job_title}} position on {{date}} at {{company_name}}, but were unable to connect with you.

We understand that unforeseen technical difficulties or personal emergencies can occur. If you are still interested in pursuing this opportunity, please reply to this email by {{reply_deadline}} with an update and your upcoming availability so we can determine whether rescheduling is feasible.

If we do not hear from you by the deadline, we will assume your circumstances have changed and will close your application file.

Best regards,
{{hr_name}}
Talent Acquisition Team
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    },
    {
        "id": "cv_unreadable_or_unsupported_format",
        "subject": "Action Required: Please resend your resume for {{job_title}}",
        "preheader": "We were unable to parse your resume attachment for the {{job_title}} position.",
        "trigger_event": "Automated CV extraction fails due to corrupted or unsupported file format.",
        "next_step": "Candidate resends resume in valid PDF or DOCX format.",
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
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">Action Required: Resume Re-upload</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Dear {{candidate_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Thank you for your application for the <strong>{{job_title}}</strong> position at <strong>{{company_name}}</strong>.</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">When reviewing your submission, our applicant tracking system was unable to read the attached resume file due to an unsupported format or file corruption.</p>
<table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation" style="margin: 20px 0; background-color: #fef2f2; border: 1px solid #fecaca; border-radius: 8px;">
  <tr>
    <td style="padding: 16px 20px;">
      <strong style="display: block; font-size: 13px; color: #991b1b; margin-bottom: 6px;">Supported File Types</strong>
      <p style="margin: 0; font-size: 14px; line-height: 1.5; color: #b91c1c;">
        Please reply directly to this email with your updated resume attached in standard <strong>PDF (.pdf)</strong> or <strong>Microsoft Word (.docx)</strong> format.
      </p>
    </td>
  </tr>
</table>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">As soon as we receive your updated file, our recruiting team will gladly proceed with evaluating your application.</p>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">Warm regards,<br><strong>{{hr_name}}</strong><br>{{company_name}} Recruiting Team</p>
""",
        "text_content": """Dear {{candidate_name}},

Thank you for your application for the {{job_title}} position at {{company_name}}.

When reviewing your submission, our applicant tracking system was unable to read the attached resume file due to an unsupported format or file corruption.

SUPPORTED FILE TYPES:
Please reply directly to this email with your updated resume attached in standard PDF (.pdf) or Microsoft Word (.docx) format.

As soon as we receive your updated file, our recruiting team will gladly proceed with evaluating your application.

Warm regards,
{{hr_name}}
Talent Acquisition Team
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    },
    {
        "id": "duplicate_application",
        "subject": "Notice Regarding Duplicate Application for {{job_title}} at {{company_name}}",
        "preheader": "We noticed multiple submissions for the {{job_title}} position.",
        "trigger_event": "Candidate submits duplicate application for the same role.",
        "next_step": "Active candidate profile remains in review pipeline.",
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
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">Duplicate Submission Notice</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Dear {{candidate_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">We noticed that you recently submitted an additional application for the <strong>{{job_title}}</strong> position at <strong>{{company_name}}</strong>.</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">We want to reassure you that your initial application is already active in our evaluation queue. We have merged any updated materials into your existing candidate profile so our team has complete visibility.</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">There is no further action required from your side at this stage. We will notify you directly as soon as our review is complete.</p>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">Warm regards,<br><strong>{{hr_name}}</strong><br>{{company_name}} Recruiting Team</p>
""",
        "text_content": """Dear {{candidate_name}},

We noticed that you recently submitted an additional application for the {{job_title}} position at {{company_name}}.

We want to reassure you that your initial application is already active in our evaluation queue. We have merged any updated materials into your existing candidate profile so our team has complete visibility.

There is no further action required from your side at this stage. We will notify you directly as soon as our review is complete.

Warm regards,
{{hr_name}}
Talent Acquisition Team
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    },
    {
        "id": "application_on_hold",
        "subject": "Application Status Update: {{job_title}} at {{company_name}}",
        "preheader": "Your profile for {{job_title}} has been added to our Talent Pool.",
        "trigger_event": "Role paused, requisition frozen, or candidate tagged for talent pool.",
        "next_step": "Candidate profile preserved in talent pool for future outreach.",
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
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">Application On Hold</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Dear {{candidate_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">We are writing to provide a transparent update regarding your application for the <strong>{{job_title}}</strong> position at <strong>{{company_name}}</strong>.</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Due to shifting organizational priorities, our hiring committee has placed this specific requisition on a temporary hold while we re-evaluate team timelines.</p>
<table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation" class="box-bg" style="margin: 20px 0; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;">
  <tr>
    <td style="padding: 16px 20px;">
      <strong class="text-heading" style="display: block; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: {{brand_color}}; margin-bottom: 4px;">Talent Pool Preservation</strong>
      <p class="text-body" style="margin: 0; font-size: 14px; line-height: 1.5; color: #334155;">
        Your qualifications and resume were highly rated by our team. We have added your profile to our priority Talent Pool, ensuring you are first in line for consideration once the search resumes.
      </p>
    </td>
  </tr>
</table>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Thank you for your patience and understanding. We will reach out promptly with any new developments.</p>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">Warm regards,<br><strong>{{hr_name}}</strong><br>{{company_name}} Recruiting Team</p>
""",
        "text_content": """Dear {{candidate_name}},

We are writing to provide a transparent update regarding your application for the {{job_title}} position at {{company_name}}.

Due to shifting organizational priorities, our hiring committee has placed this specific requisition on a temporary hold while we re-evaluate team timelines.

TALENT POOL PRESERVATION:
Your qualifications and resume were highly rated by our team. We have added your profile to our priority Talent Pool, ensuring you are first in line for consideration once the search resumes.

Thank you for your patience and understanding. We will reach out promptly with any new developments.

Warm regards,
{{hr_name}}
Talent Acquisition Team
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    },
    {
        "id": "documents_request",
        "subject": "Document Request: Pre-Offer Verification for {{job_title}}",
        "preheader": "Please provide required verification documents for your {{job_title}} application.",
        "trigger_event": "Candidate clears interview pipeline; pre-offer background verification initiated.",
        "next_step": "Candidate uploads or replies with required compliance documentation.",
        "required_variables": [
            "candidate_name",
            "job_title",
            "company_name",
            "reply_deadline",
            "hr_name",
            "company_email",
            "company_website",
            "brand_color"
        ],
        "content_html": """
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">Document Verification Request</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Dear {{candidate_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">As we prepare the final paperwork for your <strong>{{job_title}}</strong> application at <strong>{{company_name}}</strong>, we require a few standard verification documents to complete our pre-offer due diligence.</p>
<table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation" class="box-bg" style="margin: 20px 0; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;">
  <tr>
    <td style="padding: 18px 20px;">
      <strong class="text-heading" style="display: block; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: {{brand_color}}; margin-bottom: 10px;">Required Documents (Digital Copies)</strong>
      <ul style="margin: 0; padding-left: 20px; font-size: 14px; line-height: 1.6; color: #334155;">
        <li style="margin-bottom: 6px;">Government-issued photo identification (Passport or Driver's License)</li>
        <li style="margin-bottom: 6px;">Degree or highest education completion certificate</li>
        <li style="margin-bottom: 6px;">Two professional references (Name, Title, Organization, Email, and Phone)</li>
      </ul>
    </td>
  </tr>
</table>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Please reply directly to this email with secure PDF attachments by <strong>{{reply_deadline}}</strong>. All documentation is held in strict compliance with data privacy regulations.</p>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">Warm regards,<br><strong>{{hr_name}}</strong><br>{{company_name}} People Operations</p>
""",
        "text_content": """Dear {{candidate_name}},

As we prepare the final paperwork for your {{job_title}} application at {{company_name}}, we require a few standard verification documents to complete our pre-offer due diligence.

REQUIRED DOCUMENTS (Digital Copies):
1. Government-issued photo identification (Passport or Driver's License)
2. Degree or highest education completion certificate
3. Two professional references (Name, Title, Organization, Email, and Phone)

Please reply directly to this email with secure PDF attachments by {{reply_deadline}}. All documentation is held in strict compliance with data privacy regulations.

Warm regards,
{{hr_name}}
People Operations
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    },
    {
        "id": "offer_letter_cover",
        "subject": "Offer of Employment: {{job_title}} at {{company_name}}",
        "preheader": "We are thrilled to offer you the position of {{job_title}} at {{company_name}}!",
        "trigger_event": "HR manually dispatches official offer letter package.",
        "next_step": "Candidate reviews, signs, and returns offer letter before deadline.",
        "required_variables": [
            "candidate_name",
            "job_title",
            "company_name",
            "offer_attachment_note",
            "reply_deadline",
            "hr_name",
            "company_email",
            "company_website",
            "brand_color"
        ],
        "content_html": """
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">Formal Offer of Employment</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Dear {{candidate_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">We are delighted to extend a formal offer of employment for the position of <strong>{{job_title}}</strong> at <strong>{{company_name}}</strong>! Our leadership team was universally impressed by your talent and vision throughout the interview process.</p>
<table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation" class="box-bg" style="margin: 20px 0; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;">
  <tr>
    <td style="padding: 18px 20px;">
      <strong class="text-heading" style="display: block; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: {{brand_color}}; margin-bottom: 8px;">Offer Package Summary</strong>
      <p class="text-body" style="margin: 0; font-size: 14px; line-height: 1.6; color: #334155;">
        {{offer_attachment_note}}
      </p>
    </td>
  </tr>
</table>
<table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation" style="margin: 20px 0; background-color: #ecfdf5; border: 1px solid #6ee7b7; border-radius: 8px;">
  <tr>
    <td style="padding: 16px 20px;">
      <strong style="display: block; font-size: 13px; color: #065f46; margin-bottom: 6px;">Next Steps &amp; Acceptance</strong>
      <p style="margin: 0; font-size: 14px; line-height: 1.5; color: #047857;">
        Please review the attached formal agreement, sign electronically or manually, and return your completed document by <strong>{{reply_deadline}}</strong>.
      </p>
    </td>
  </tr>
</table>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">We are very excited about the contributions you will make to our mission and look forward to welcoming you to the team.</p>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">Warmest regards,<br><strong>{{hr_name}}</strong><br>{{company_name}} Leadership &amp; Talent Team</p>
""",
        "text_content": """Dear {{candidate_name}},

We are delighted to extend a formal offer of employment for the position of {{job_title}} at {{company_name}}! Our leadership team was universally impressed by your talent and vision throughout the interview process.

OFFER PACKAGE SUMMARY:
{{offer_attachment_note}}

NEXT STEPS & ACCEPTANCE:
Please review the attached formal agreement, sign electronically or manually, and return your completed document by {{reply_deadline}}.

We are very excited about the contributions you will make to our mission and look forward to welcoming you to the team.

Warmest regards,
{{hr_name}}
Leadership & Talent Team
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    },
    {
        "id": "offer_accepted_confirmation",
        "subject": "Welcome to the Team! Offer Acceptance Confirmed - {{company_name}}",
        "preheader": "We have received your signed offer letter for {{job_title}}. Welcome aboard!",
        "trigger_event": "Candidate signs and returns offer letter.",
        "next_step": "People Ops initiates pre-boarding and IT provisioning workflows.",
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
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">Welcome to the Team!</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Dear {{candidate_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">It is official! We have received your signed offer letter for the <strong>{{job_title}}</strong> position at <strong>{{company_name}}</strong>. Everyone on our team is ecstatic to have you join us.</p>
<table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation" class="box-bg" style="margin: 20px 0; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;">
  <tr>
    <td style="padding: 18px 20px;">
      <strong class="text-heading" style="display: block; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: {{brand_color}}; margin-bottom: 8px;">What Happens Next?</strong>
      <ul style="margin: 0; padding-left: 20px; font-size: 14px; line-height: 1.6; color: #334155;">
        <li style="margin-bottom: 6px;">Our People Operations team will set up your corporate email and systems access.</li>
        <li style="margin-bottom: 6px;">You will receive your pre-boarding welcome package and IT hardware shipping details.</li>
        <li style="margin-bottom: 6px;">A full Day 1 schedule will be shared prior to your start date.</li>
      </ul>
    </td>
  </tr>
</table>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">If you have any questions between now and your start date, please feel free to reach out. Welcome to {{company_name}}!</p>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">Warm regards,<br><strong>{{hr_name}}</strong><br>{{company_name}} People Team</p>
""",
        "text_content": """Dear {{candidate_name}},

It is official! We have received your signed offer letter for the {{job_title}} position at {{company_name}}. Everyone on our team is ecstatic to have you join us.

WHAT HAPPENS NEXT?
- Our People Operations team will set up your corporate email and systems access.
- You will receive your pre-boarding welcome package and IT hardware shipping details.
- A full Day 1 schedule will be shared prior to your start date.

If you have any questions between now and your start date, please feel free to reach out. Welcome to {{company_name}}!

Warm regards,
{{hr_name}}
People Team
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    },
    {
        "id": "offer_declined_acknowledgement",
        "subject": "Acknowledgement of Offer Decision: {{job_title}} at {{company_name}}",
        "preheader": "Thank you for your consideration regarding the {{job_title}} position.",
        "trigger_event": "Candidate declines employment offer.",
        "next_step": "Requisition reopened or next ranked candidate contacted.",
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
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">Offer Decision Acknowledgement</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Dear {{candidate_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Thank you for notifying us of your decision regarding our offer of employment for the <strong>{{job_title}}</strong> role at <strong>{{company_name}}</strong>.</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">While we are naturally disappointed that we will not have the opportunity to work together at this time, we completely respect your decision and wish you the absolute best with your next career chapter.</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">We would be honored to stay in touch for future possibilities should circumstances align down the road. Thank you once again for your professionalism throughout our hiring process.</p>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">Warm regards,<br><strong>{{hr_name}}</strong><br>{{company_name}} Talent Team</p>
""",
        "text_content": """Dear {{candidate_name}},

Thank you for notifying us of your decision regarding our offer of employment for the {{job_title}} role at {{company_name}}.

While we are naturally disappointed that we will not have the opportunity to work together at this time, we completely respect your decision and wish you the absolute best with your next career chapter.

We would be honored to stay in touch for future possibilities should circumstances align down the road. Thank you once again for your professionalism throughout our hiring process.

Warm regards,
{{hr_name}}
Talent Team
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    },
    {
        "id": "welcome_onboarding",
        "subject": "Welcome to {{company_name}}! Onboarding Information for {{job_title}}",
        "preheader": "Important onboarding instructions and Day 1 details for {{candidate_name}}.",
        "trigger_event": "3-5 days prior to new hire start date.",
        "next_step": "Candidate reviews Day 1 schedule and prepares for orientation.",
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
<h1 class="text-heading" style="margin: 0 0 16px 0; font-size: 20px; font-weight: bold; color: #0f172a; line-height: 1.3;">Day 1 Onboarding Roadmap</h1>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Dear {{candidate_name}},</p>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Your official start date at <strong>{{company_name}}</strong> as <strong>{{job_title}}</strong> is right around the corner! We are eager to welcome you to the team and have prepared your onboarding plan.</p>
<table border="0" cellpadding="0" cellspacing="0" width="100%" role="presentation" class="box-bg" style="margin: 20px 0; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;">
  <tr>
    <td style="padding: 18px 20px;">
      <strong class="text-heading" style="display: block; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: {{brand_color}}; margin-bottom: 10px;">Day 1 Schedule Highlights</strong>
      <ul style="margin: 0; padding-left: 20px; font-size: 14px; line-height: 1.6; color: #334155;">
        <li style="margin-bottom: 6px;"><strong>09:30 AM:</strong> Welcome Orientation &amp; Company Overview with HR</li>
        <li style="margin-bottom: 6px;"><strong>11:00 AM:</strong> IT Setup, Security Protocols, and System Verification</li>
        <li style="margin-bottom: 6px;"><strong>01:30 PM:</strong> Meet Your Manager &amp; Engineering Buddy</li>
        <li style="margin-bottom: 6px;"><strong>03:30 PM:</strong> Team Welcome Sync</li>
      </ul>
    </td>
  </tr>
</table>
<p class="text-body" style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">Please ensure you have your photo ID handy for identity verification. We are counting down the days and look forward to building great things together!</p>
<p class="text-body" style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #334155;">Warm regards,<br><strong>{{hr_name}}</strong><br>{{company_name}} People &amp; Culture</p>
""",
        "text_content": """Dear {{candidate_name}},

Your official start date at {{company_name}} as {{job_title}} is right around the corner! We are eager to welcome you to the team and have prepared your onboarding plan.

DAY 1 SCHEDULE HIGHLIGHTS:
- 09:30 AM: Welcome Orientation & Company Overview with HR
- 11:00 AM: IT Setup, Security Protocols, and System Verification
- 01:30 PM: Meet Your Manager & Engineering Buddy
- 03:30 PM: Team Welcome Sync

Please ensure you have your photo ID handy for identity verification. We are counting down the days and look forward to building great things together!

Warm regards,
{{hr_name}}
People & Culture
{{company_name}}
Email: {{company_email}}
Website: {{company_website}}
"""
    }
]

print(f"Loaded {len(SUPPORTING_TEMPLATES)} supporting templates.")
