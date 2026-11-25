/**
 * Auto-generated registry of all 31 candidate lifecycle and recruitment email templates.
 * Loaded from frontend/templates/ and synced with backend/templates/.
 */

export interface TemplateDefinition {
  id: string;
  name: string;
  category: "core" | "supporting" | "internal";
  subject: string;
  preheader?: string;
  body: string;
  required_variables: string[];
  trigger_event?: string;
}

export const ALL_RECRUITING_TEMPLATES: TemplateDefinition[] = [
  {
    "id": "cv_received",
    "name": "CV Received (Acknowledgement)",
    "category": "core",
    "subject": "Application Received: {{job_title}} at {{company_name}}",
    "preheader": "We have received your application for the {{job_title}} position at {{company_name}}.",
    "body": "Dear {{candidate_name}},\n\nThank you for your interest in joining {{company_name}}. We are pleased to confirm that we have received your resume and application materials for the {{job_title}} position.\n\nAPPLICATION SUMMARY:\n- Position: {{job_title}}\n- Organization: {{company_name}}\n- Current Status: Under Review\n\nOur talent acquisition team is actively evaluating your qualifications, achievements, and technical background against the specific objectives of this role.\n\nIf your profile meets our current requirements, we will reach out directly with instructions regarding the next phase of our interview process. Thank you again for your time, effort, and interest in our organization.\n\nWarm regards,\n{{hr_name}}\nTalent Acquisition Team\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "hr_name",
      "job_title"
    ],
    "trigger_event": "Candidate submits CV via Gmail or job application form."
  },
  {
    "id": "application_rejected",
    "name": "Application Rejected (Kind Notice)",
    "category": "core",
    "subject": "Update regarding your application for {{job_title}} at {{company_name}}",
    "preheader": "Thank you for your interest in the {{job_title}} position at {{company_name}}.",
    "body": "Dear {{candidate_name}},\n\nThank you for taking the time to apply for the {{job_title}} position at {{company_name}}. We sincerely appreciate your interest in our team and the opportunity to review your professional credentials.\n\nAfter careful evaluation of your application alongside a strong volume of candidates, we have decided not to advance your candidacy to the interview stage at this time. We are focusing our search on profiles with closer alignment to our immediate project stack and operational needs.\n\n--------------------------------------------------\nEVALUATION FEEDBACK:\n\"{{feedback}}\"\n--------------------------------------------------\n\nPlease know that our decision relates strictly to our current requisitions and is not a reflection of your overall abilities. We encourage you to monitor our careers page and apply for future openings that match your skill set.\n\nWe wish you every success with your continued career search.\n\nSincerely,\n{{hr_name}}\nTalent Acquisition Team\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "feedback",
      "hr_name",
      "job_title"
    ],
    "trigger_event": "HR reviews candidate CV scorecard and marks application as rejected."
  },
  {
    "id": "application_approved",
    "name": "Application Approved (Interview Invite)",
    "category": "core",
    "subject": "Congratulations! Next Steps for {{job_title}} at {{company_name}}",
    "preheader": "Your application for {{job_title}} has been approved. Please share your availability.",
    "body": "Dear {{candidate_name}},\n\nGreat news! We have thoroughly reviewed your background and resume, and we are delighted to invite you to the Initial Interview for the {{job_title}} position at {{company_name}}.\n\nThis introductory 30-minute conversation is designed to get to know you better, learn more about your technical and career journey, and discuss how your skills align with our current objectives.\n\nROLE OVERVIEW & KEY FOCUS:\n{{job_description}}\n\nACTION REQUIRED:\nPlease reply directly to this email by {{reply_deadline}} with 2 to 3 preferred time slots (including your timezone) across the next several business days during standard working hours.\n\nUpon receiving your reply, our recruiting team will confirm the date, time, and video meeting link. We look forward to speaking with you!\n\nWarm regards,\n{{hr_name}}\nTalent Acquisition Team\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "hr_name",
      "job_description",
      "job_title",
      "reply_deadline"
    ],
    "trigger_event": "HR approves candidate screening; candidate shortlisted for initial interview."
  },
  {
    "id": "interview_confirmed",
    "name": "Interview Confirmed",
    "category": "core",
    "subject": "Confirmed: {{round_name}} Interview for {{job_title}} - {{date}}",
    "preheader": "Your {{round_name}} Interview for {{job_title}} is scheduled for {{date}} at {{time}} {{timezone}}.",
    "body": "Dear {{candidate_name}},\n\nYour {{round_name}} Interview for the {{job_title}} position at {{company_name}} has been confirmed. Below are your meeting details:\n\nINTERVIEW DETAILS:\n- Interview Stage: {{round_name}} Interview\n- Date: {{date}}\n- Time: {{time}} ({{timezone}})\n- Meeting Link: {{meeting_link}}\n\nIMPORTANT INSTRUCTIONS:\n- Please join the video meeting 5 minutes early to test your audio, camera, and network connection.\n- Ensure you are in a quiet room with minimal background noise.\n- Reschedule Policy: If you need to reschedule, please notify us at least 24 hours in advance by replying directly to this email.\n\nBest regards,\n{{hr_name}}\nTalent Acquisition Team\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "date",
      "hr_name",
      "job_title",
      "meeting_link",
      "round_name",
      "time",
      "timezone"
    ],
    "trigger_event": "Recruiter schedules interview round in calendar."
  },
  {
    "id": "alternate_slots",
    "name": "Alternate Slots Offer",
    "category": "core",
    "subject": "Scheduling Your {{round_name}} Interview: Alternate Times for {{job_title}}",
    "preheader": "Please review alternate interview times for your {{round_name}} Interview.",
    "body": "Dear {{candidate_name}},\n\nThank you for sharing your availability for the {{round_name}} Interview for the {{job_title}} role at {{company_name}}.\n\nUnfortunately, our interviewing panel has preexisting scheduling conflicts during the specific windows you proposed. To ensure we keep your candidacy moving forward smoothly, we would like to offer the following alternate slots:\n\nALTERNATE SLOTS:\n1. {{slot_1}}\n2. {{slot_2}}\n3. {{slot_3}}\n\nPlease reply directly to this email by {{reply_deadline}} indicating which option works best for you. If none of these slots fit your schedule, please propose 2 to 3 alternative windows with your timezone.\n\nWarm regards,\n{{hr_name}}\nTalent Acquisition Team\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "hr_name",
      "job_title",
      "reply_deadline",
      "round_name",
      "slot_1",
      "slot_2",
      "slot_3"
    ],
    "trigger_event": "Candidate proposed slots conflict with interviewer calendar availability."
  },
  {
    "id": "next_round_availability",
    "name": "Next Round Availability Request",
    "category": "core",
    "subject": "You're Moving Forward! Availability for {{round_name}} Interview - {{company_name}}",
    "preheader": "Congratulations on passing your previous round! Next step: {{round_name}} Interview.",
    "body": "Dear {{candidate_name}},\n\nCongratulations! Our team thoroughly enjoyed speaking with you in your previous discussion, and we are excited to invite you to the next stage of our evaluation: the {{round_name}} Interview for the {{job_title}} role at {{company_name}}.\n\nROUND OVERVIEW: {{round_name}}\n{{round_description}}\n\nNEXT STEP:\nPlease reply directly to this email by {{reply_deadline}} with 2 to 3 available dates and times (including your timezone) across the upcoming week.\n\nOnce we receive your preferred times, we will coordinate with the interviewers and issue your calendar invite with video conference details.\n\nWarm regards,\n{{hr_name}}\nTalent Acquisition Team\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "hr_name",
      "job_title",
      "reply_deadline",
      "round_description",
      "round_name"
    ],
    "trigger_event": "Candidate passes previous interview round; advance to next round."
  },
  {
    "id": "interview_passed",
    "name": "Interview Passed (Congratulations)",
    "category": "core",
    "subject": "Great news regarding your {{round_name}} Interview for {{job_title}}",
    "preheader": "You have successfully passed the {{round_name}} Interview for {{job_title}} at {{company_name}}!",
    "body": "Dear {{candidate_name}},\n\nWe are pleased to inform you that you have successfully cleared the {{round_name}} Interview for the {{job_title}} position at {{company_name}}!\n\nThe interviewers were very impressed with your structured communication, professional depth, and domain knowledge throughout the conversation.\n\nSTATUS: Passed {{round_name}} - Advancing to Next Stage\n\nOur recruiting coordinator will be in touch within 24 to 48 hours with full preparation notes and scheduling instructions for your next session. Keep up the wonderful work!\n\nWarm regards,\n{{hr_name}}\nTalent Acquisition Team\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "hr_name",
      "job_title",
      "round_name"
    ],
    "trigger_event": "Interviewer/HR logs passing scorecard for Initial or Behavioral round."
  },
  {
    "id": "interview_rejected",
    "name": "Interview Rejected (Appreciative)",
    "category": "core",
    "subject": "Update on your interview for {{job_title}} at {{company_name}}",
    "preheader": "Thank you for taking the time to interview with us for the {{job_title}} position.",
    "body": "Dear {{candidate_name}},\n\nThank you very much for meeting with our team during the {{round_name}} Interview for the {{job_title}} role at {{company_name}}. We sincerely appreciate the time, preparation, and energy you invested in speaking with us.\n\nWhile our interviewing panel was impressed by many aspects of your background, we have made the difficult decision not to advance your candidacy to the next stage. We evaluated several exceptional candidates and chose to proceed with those whose specific experience more closely aligns with our immediate technical priorities.\n\n--------------------------------------------------\nEVALUATION FEEDBACK:\n\"{{feedback}}\"\n--------------------------------------------------\n\nWe would like to retain your resume in our talent network for future openings that match your skills. We wish you continued success in your professional endeavors and thank you again for considering {{company_name}}.\n\nWarm regards,\n{{hr_name}}\nTalent Acquisition Team\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "feedback",
      "hr_name",
      "job_title",
      "round_name"
    ],
    "trigger_event": "Candidate rejected following any interview round evaluation."
  },
  {
    "id": "all_rounds_cleared",
    "name": "All Rounds Cleared (Offer Prep)",
    "category": "core",
    "subject": "Congratulations! You have cleared all interview rounds for {{job_title}} at {{company_name}}",
    "preheader": "You have successfully completed all interview stages for {{job_title}} at {{company_name}}!",
    "body": "Dear {{candidate_name}},\n\nOn behalf of the entire hiring committee at {{company_name}}, we are thrilled to congratulate you on successfully clearing every stage of our interview process for the {{job_title}} position!\n\nAcross your Initial, Behavioral, and final Technical rounds, our team was universally impressed by your technical mastery, thoughtful problem-solving, and dedication to excellence.\n\nNEXT STEP: OFFER PACKAGE FINALIZATION\nOur talent acquisition leadership and hiring executive team are currently assembling your formal offer letter and onboarding roadmap.\n\nWe will reach out shortly to share your official offer letter and answer any questions you may have. Thank you once again for your remarkable commitment throughout this interview journey.\n\nWith warmest congratulations,\n{{hr_name}}\nLeadership & Talent Team\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "hr_name",
      "job_title"
    ],
    "trigger_event": "Candidate clears final technical round with positive recommendation."
  },
  {
    "id": "interview_reminder_24h",
    "name": "Interview Reminder (24h Before)",
    "category": "supporting",
    "subject": "Reminder: {{round_name}} Interview Tomorrow - {{job_title}} at {{company_name}}",
    "preheader": "Your {{round_name}} Interview is scheduled for tomorrow at {{time}} {{timezone}}.",
    "body": "Dear {{candidate_name}},\n\nThis is a friendly reminder that your {{round_name}} Interview for the {{job_title}} position at {{company_name}} takes place tomorrow.\n\nMEETING SCHEDULE:\n- Stage: {{round_name}} Interview\n- Date: {{date}}\n- Time: {{time}} ({{timezone}})\n- Meeting Link: {{meeting_link}}\n\nPlease plan to enter the meeting room 5 minutes before the start time. We look forward to speaking with you!\n\nBest regards,\n{{hr_name}}\nTalent Acquisition Team\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "date",
      "hr_name",
      "job_title",
      "meeting_link",
      "round_name",
      "time",
      "timezone"
    ],
    "trigger_event": "24 hours prior to scheduled interview round."
  },
  {
    "id": "interview_reminder_1h",
    "name": "Interview Reminder (1h Before)",
    "category": "supporting",
    "subject": "Starting in 1 Hour: {{round_name}} Interview for {{job_title}}",
    "preheader": "Your {{round_name}} Interview begins at {{time}} {{timezone}}. Meeting link enclosed.",
    "body": "Dear {{candidate_name}},\n\nYour {{round_name}} Interview for the {{job_title}} role at {{company_name}} will begin in approximately one hour at {{time}} ({{timezone}}).\n\nMEETING LINK: {{meeting_link}}\n\nPlease make sure your camera and microphone are tested, and join a few minutes early to ensure a prompt start.\n\nSee you shortly,\n{{hr_name}}\nTalent Acquisition Team\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "hr_name",
      "job_title",
      "meeting_link",
      "round_name",
      "time",
      "timezone"
    ],
    "trigger_event": "1 hour prior to scheduled interview round."
  },
  {
    "id": "no_response_followup",
    "name": "No-Response Follow-up Check-in",
    "category": "supporting",
    "subject": "Following up: Next steps for {{job_title}} at {{company_name}}",
    "preheader": "Just checking in regarding your interview scheduling for {{job_title}}.",
    "body": "Dear {{candidate_name}},\n\nWe are following up on our previous note regarding your application for the {{job_title}} position at {{company_name}}. We remain very eager to connect with you!\n\nPlease reply directly to this email by {{reply_deadline}} with 2 to 3 preferred dates and time slots (including your timezone) so we can lock in your interview on the team's calendar.\n\nIf you are no longer interested in exploring opportunities with us at this time, please let us know so we can update our records accordingly.\n\nWarm regards,\n{{hr_name}}\nTalent Acquisition Team\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "hr_name",
      "job_title",
      "reply_deadline"
    ],
    "trigger_event": "Candidate has not replied 48 hours after availability request."
  },
  {
    "id": "application_closed_no_response",
    "name": "Application Closed (No Response)",
    "category": "supporting",
    "subject": "Application Closed: {{job_title}} at {{company_name}}",
    "preheader": "Notice regarding your application status for {{job_title}} at {{company_name}}.",
    "body": "Dear {{candidate_name}},\n\nWe are writing to inform you that because we have not received a response regarding interview scheduling for the {{job_title}} position at {{company_name}}, we have closed your application file for this opening.\n\nWe understand that timing and circumstances change. If you wish to be considered for future opportunities or if your schedule frees up down the road, please feel free to submit a new application through our careers portal.\n\nWe thank you for your initial interest in {{company_name}} and wish you the best in your career pursuits.\n\nSincerely,\n{{hr_name}}\nTalent Acquisition Team\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "hr_name",
      "job_title"
    ],
    "trigger_event": "Reply deadline elapsed without response from candidate."
  },
  {
    "id": "interview_rescheduled",
    "name": "Interview Rescheduled",
    "category": "supporting",
    "subject": "Rescheduled: {{round_name}} Interview for {{job_title}} - {{date}}",
    "preheader": "Your {{round_name}} Interview has been rescheduled to {{date}} at {{time}} {{timezone}}.",
    "body": "Dear {{candidate_name}},\n\nYour {{round_name}} Interview for the {{job_title}} position at {{company_name}} has been successfully rescheduled. Please review your updated time slot below:\n\nNEW INTERVIEW DETAILS:\n- Stage: {{round_name}} Interview\n- New Date: {{date}}\n- New Time: {{time}} ({{timezone}})\n- Meeting Link: {{meeting_link}}\n\nYour calendar invitation has been updated to reflect this new date and time. Please reach out if you have any questions.\n\nBest regards,\n{{hr_name}}\nTalent Acquisition Team\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "date",
      "hr_name",
      "job_title",
      "meeting_link",
      "round_name",
      "time",
      "timezone"
    ],
    "trigger_event": "Interview rescheduled due to candidate or interviewer calendar adjustment."
  },
  {
    "id": "interview_cancelled_by_company",
    "name": "Interview Cancelled by Company",
    "category": "supporting",
    "subject": "Notice: Cancellation of {{round_name}} Interview for {{job_title}}",
    "preheader": "Important update regarding your scheduled {{round_name}} Interview on {{date}}.",
    "body": "Dear {{candidate_name}},\n\nWe sincerely apologize, but due to an unexpected scheduling conflict on our team, we need to cancel your upcoming {{round_name}} Interview for the {{job_title}} role originally scheduled on {{date}} at {{company_name}}.\n\nPlease rest assured that your candidacy remains highly valued and in active consideration. We deeply respect your time and regret any inconvenience this sudden change may cause.\n\nOur recruiting coordinator will contact you within the next 24 hours with new interview options to reschedule this discussion at your earliest convenience.\n\nWith our sincere apologies,\n{{hr_name}}\nTalent Acquisition Team\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "date",
      "hr_name",
      "job_title",
      "round_name"
    ],
    "trigger_event": "Company cancels interview due to unforeseen internal conflict or emergency."
  },
  {
    "id": "candidate_cancelled_confirmation",
    "name": "Candidate Cancelled Confirmation",
    "category": "supporting",
    "subject": "Confirmation of Interview Cancellation: {{job_title}} at {{company_name}}",
    "preheader": "We have processed your interview cancellation for the {{round_name}} round.",
    "body": "Dear {{candidate_name}},\n\nWe have received your message and confirmed the cancellation of your {{round_name}} Interview for the {{job_title}} position at {{company_name}}.\n\nIf you would like to reschedule your interview for a different date and time, please reply directly to this email with your updated availability windows.\n\nAlternatively, if you wish to withdraw your application from consideration, simply let us know and we will archive your profile with gratitude for your time.\n\nBest regards,\n{{hr_name}}\nTalent Acquisition Team\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "hr_name",
      "job_title",
      "round_name"
    ],
    "trigger_event": "Candidate requests interview cancellation."
  },
  {
    "id": "candidate_no_show",
    "name": "Candidate No-Show Follow-up",
    "category": "supporting",
    "subject": "We missed you today: {{round_name}} Interview for {{job_title}}",
    "preheader": "We were unable to connect with you for your {{round_name}} Interview on {{date}}.",
    "body": "Dear {{candidate_name}},\n\nOur team was online and waiting for your scheduled {{round_name}} Interview for the {{job_title}} position on {{date}} at {{company_name}}, but were unable to connect with you.\n\nWe understand that unforeseen technical difficulties or personal emergencies can occur. If you are still interested in pursuing this opportunity, please reply to this email by {{reply_deadline}} with an update and your upcoming availability so we can determine whether rescheduling is feasible.\n\nIf we do not hear from you by the deadline, we will assume your circumstances have changed and will close your application file.\n\nBest regards,\n{{hr_name}}\nTalent Acquisition Team\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "date",
      "hr_name",
      "job_title",
      "reply_deadline",
      "round_name"
    ],
    "trigger_event": "Candidate does not attend interview call after 15-minute grace period."
  },
  {
    "id": "cv_unreadable_or_unsupported_format",
    "name": "CV Unreadable / Format Request",
    "category": "supporting",
    "subject": "Action Required: Please resend your resume for {{job_title}}",
    "preheader": "We were unable to parse your resume attachment for the {{job_title}} position.",
    "body": "Dear {{candidate_name}},\n\nThank you for your application for the {{job_title}} position at {{company_name}}.\n\nWhen reviewing your submission, our applicant tracking system was unable to read the attached resume file due to an unsupported format or file corruption.\n\nSUPPORTED FILE TYPES:\nPlease reply directly to this email with your updated resume attached in standard PDF (.pdf) or Microsoft Word (.docx) format.\n\nAs soon as we receive your updated file, our recruiting team will gladly proceed with evaluating your application.\n\nWarm regards,\n{{hr_name}}\nTalent Acquisition Team\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "hr_name",
      "job_title"
    ],
    "trigger_event": "Automated CV extraction fails due to corrupted or unsupported file format."
  },
  {
    "id": "duplicate_application",
    "name": "Duplicate Application Notice",
    "category": "supporting",
    "subject": "Notice Regarding Duplicate Application for {{job_title}} at {{company_name}}",
    "preheader": "We noticed multiple submissions for the {{job_title}} position.",
    "body": "Dear {{candidate_name}},\n\nWe noticed that you recently submitted an additional application for the {{job_title}} position at {{company_name}}.\n\nWe want to reassure you that your initial application is already active in our evaluation queue. We have merged any updated materials into your existing candidate profile so our team has complete visibility.\n\nThere is no further action required from your side at this stage. We will notify you directly as soon as our review is complete.\n\nWarm regards,\n{{hr_name}}\nTalent Acquisition Team\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "hr_name",
      "job_title"
    ],
    "trigger_event": "Candidate submits duplicate application for the same role."
  },
  {
    "id": "application_on_hold",
    "name": "Application on Hold",
    "category": "supporting",
    "subject": "Application Status Update: {{job_title}} at {{company_name}}",
    "preheader": "Your profile for {{job_title}} has been added to our Talent Pool.",
    "body": "Dear {{candidate_name}},\n\nWe are writing to provide a transparent update regarding your application for the {{job_title}} position at {{company_name}}.\n\nDue to shifting organizational priorities, our hiring committee has placed this specific requisition on a temporary hold while we re-evaluate team timelines.\n\nTALENT POOL PRESERVATION:\nYour qualifications and resume were highly rated by our team. We have added your profile to our priority Talent Pool, ensuring you are first in line for consideration once the search resumes.\n\nThank you for your patience and understanding. We will reach out promptly with any new developments.\n\nWarm regards,\n{{hr_name}}\nTalent Acquisition Team\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "hr_name",
      "job_title"
    ],
    "trigger_event": "Role paused, requisition frozen, or candidate tagged for talent pool."
  },
  {
    "id": "documents_request",
    "name": "Documents & References Request",
    "category": "supporting",
    "subject": "Document Request: Pre-Offer Verification for {{job_title}}",
    "preheader": "Please provide required verification documents for your {{job_title}} application.",
    "body": "Dear {{candidate_name}},\n\nAs we prepare the final paperwork for your {{job_title}} application at {{company_name}}, we require a few standard verification documents to complete our pre-offer due diligence.\n\nREQUIRED DOCUMENTS (Digital Copies):\n1. Government-issued photo identification (Passport or Driver's License)\n2. Degree or highest education completion certificate\n3. Two professional references (Name, Title, Organization, Email, and Phone)\n\nPlease reply directly to this email with secure PDF attachments by {{reply_deadline}}. All documentation is held in strict compliance with data privacy regulations.\n\nWarm regards,\n{{hr_name}}\nPeople Operations\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "hr_name",
      "job_title",
      "reply_deadline"
    ],
    "trigger_event": "Candidate clears interview pipeline; pre-offer background verification initiated."
  },
  {
    "id": "offer_letter_cover",
    "name": "Offer Letter & Cover Email",
    "category": "supporting",
    "subject": "Offer of Employment: {{job_title}} at {{company_name}}",
    "preheader": "We are thrilled to offer you the position of {{job_title}} at {{company_name}}!",
    "body": "Dear {{candidate_name}},\n\nWe are delighted to extend a formal offer of employment for the position of {{job_title}} at {{company_name}}! Our leadership team was universally impressed by your talent and vision throughout the interview process.\n\nOFFER PACKAGE SUMMARY:\n{{offer_attachment_note}}\n\nNEXT STEPS & ACCEPTANCE:\nPlease review the attached formal agreement, sign electronically or manually, and return your completed document by {{reply_deadline}}.\n\nWe are very excited about the contributions you will make to our mission and look forward to welcoming you to the team.\n\nWarmest regards,\n{{hr_name}}\nLeadership & Talent Team\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "hr_name",
      "job_title",
      "offer_attachment_note",
      "reply_deadline"
    ],
    "trigger_event": "HR manually dispatches official offer letter package."
  },
  {
    "id": "offer_accepted_confirmation",
    "name": "Offer Accepted (Welcome Confirmation)",
    "category": "supporting",
    "subject": "Welcome to the Team! Offer Acceptance Confirmed - {{company_name}}",
    "preheader": "We have received your signed offer letter for {{job_title}}. Welcome aboard!",
    "body": "Dear {{candidate_name}},\n\nIt is official! We have received your signed offer letter for the {{job_title}} position at {{company_name}}. Everyone on our team is ecstatic to have you join us.\n\nWHAT HAPPENS NEXT?\n- Our People Operations team will set up your corporate email and systems access.\n- You will receive your pre-boarding welcome package and IT hardware shipping details.\n- A full Day 1 schedule will be shared prior to your start date.\n\nIf you have any questions between now and your start date, please feel free to reach out. Welcome to {{company_name}}!\n\nWarm regards,\n{{hr_name}}\nPeople Team\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "hr_name",
      "job_title"
    ],
    "trigger_event": "Candidate signs and returns offer letter."
  },
  {
    "id": "offer_declined_acknowledgement",
    "name": "Offer Declined Acknowledgement",
    "category": "supporting",
    "subject": "Acknowledgement of Offer Decision: {{job_title}} at {{company_name}}",
    "preheader": "Thank you for your consideration regarding the {{job_title}} position.",
    "body": "Dear {{candidate_name}},\n\nThank you for notifying us of your decision regarding our offer of employment for the {{job_title}} role at {{company_name}}.\n\nWhile we are naturally disappointed that we will not have the opportunity to work together at this time, we completely respect your decision and wish you the absolute best with your next career chapter.\n\nWe would be honored to stay in touch for future possibilities should circumstances align down the road. Thank you once again for your professionalism throughout our hiring process.\n\nWarm regards,\n{{hr_name}}\nTalent Team\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "hr_name",
      "job_title"
    ],
    "trigger_event": "Candidate declines employment offer."
  },
  {
    "id": "welcome_onboarding",
    "name": "Welcome & First Day Onboarding",
    "category": "supporting",
    "subject": "Welcome to {{company_name}}! Onboarding Information for {{job_title}}",
    "preheader": "Important onboarding instructions and Day 1 details for {{candidate_name}}.",
    "body": "Dear {{candidate_name}},\n\nYour official start date at {{company_name}} as {{job_title}} is right around the corner! We are eager to welcome you to the team and have prepared your onboarding plan.\n\nDAY 1 SCHEDULE HIGHLIGHTS:\n- 09:30 AM: Welcome Orientation & Company Overview with HR\n- 11:00 AM: IT Setup, Security Protocols, and System Verification\n- 01:30 PM: Meet Your Manager & Engineering Buddy\n- 03:30 PM: Team Welcome Sync\n\nPlease ensure you have your photo ID handy for identity verification. We are counting down the days and look forward to building great things together!\n\nWarm regards,\n{{hr_name}}\nPeople & Culture\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "hr_name",
      "job_title"
    ],
    "trigger_event": "3-5 days prior to new hire start date."
  },
  {
    "id": "hr_new_cv_scored",
    "name": "Internal: New CV Scored",
    "category": "internal",
    "subject": "[Action Required] New Candidate Scored: {{candidate_name}} for {{job_title}}",
    "preheader": "New candidate application parsed and scored for {{job_title}}. Ready for review.",
    "body": "Hello {{hr_name}},\n\nA new candidate application has been ingested and parsed for {{job_title}} at {{company_name}}. The candidate profile and deterministic scorecard are ready for your review.\n\nCANDIDATE OVERVIEW:\n- Candidate Name: {{candidate_name}}\n- Candidate Email: {{candidate_email}}\n- Target Position: {{job_title}}\n\nPlease log in to your recruiting dashboard to inspect the parsed resume, review matched skills and red flags, and make an Approve or Reject decision.\n\nAutomated Notification System\n{{company_name}} Talent Pipeline\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_email",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "hr_name",
      "job_title"
    ],
    "trigger_event": "New candidate CV parsed, contact extracted, and initial screening score computed."
  },
  {
    "id": "hr_candidate_replied_availability",
    "name": "Internal: Candidate Replied Availability",
    "category": "internal",
    "subject": "[Action Required] Availability Received: {{candidate_name}} for {{round_name}}",
    "preheader": "{{candidate_name}} has submitted availability for {{round_name}} Interview.",
    "body": "Hello {{hr_name}},\n\nCandidate {{candidate_name}} ({{candidate_email}}) has replied with their proposed availability for the {{round_name}} Interview for the {{job_title}} position at {{company_name}}.\n\nNEXT ACTION REQUIRED:\nOpen the Recruiting Inbox, review the candidate's proposed time slots against team calendars, and dispatch the interview confirmation.\n\nAutomated Notification System\n{{company_name}} Recruiting\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_email",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "hr_name",
      "job_title",
      "round_name"
    ],
    "trigger_event": "Candidate replies with time slots for interview scheduling."
  },
  {
    "id": "hr_interview_scheduled",
    "name": "Internal: Interview Scheduled",
    "category": "internal",
    "subject": "[Scheduled] {{round_name}} Interview: {{candidate_name}} for {{job_title}}",
    "preheader": "{{round_name}} interview scheduled for {{candidate_name}} on {{date}} at {{time}} {{timezone}}.",
    "body": "Hello Team,\n\nA new interview has been confirmed on the calendar for {{job_title}} at {{company_name}}. Please find the details below:\n\nSESSION DETAILS:\n- Candidate: {{candidate_name}} ({{candidate_email}})\n- Stage: {{round_name}} Interview\n- Date: {{date}}\n- Time: {{time}} ({{timezone}})\n- Meeting Link: {{meeting_link}}\n\nPlease review the candidate's resume and interview scorecard prior to the call. Please log your interview notes promptly following the discussion.\n\nRecruiting Coordination\n{{hr_name}}\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_email",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "date",
      "hr_name",
      "job_title",
      "meeting_link",
      "round_name",
      "time",
      "timezone"
    ],
    "trigger_event": "Interview calendar invitation generated and sent."
  },
  {
    "id": "hr_interviewer_reminder",
    "name": "Internal: Interviewer Reminder",
    "category": "internal",
    "subject": "[Reminder] Upcoming Interview Today: {{candidate_name}} ({{round_name}})",
    "preheader": "Reminder: You have an interview with {{candidate_name}} starting at {{time}} {{timezone}}.",
    "body": "Hello,\n\nYou have an upcoming {{round_name}} Interview with candidate {{candidate_name}} for the {{job_title}} position today at {{time}} ({{timezone}}) at {{company_name}}.\n\nMEETING LINK: {{meeting_link}}\n\nPlease log into the meeting room 2-3 minutes early to welcome the candidate. Following the conversation, please submit your feedback and evaluation score within 24 hours.\n\nBest regards,\n{{hr_name}}\nTalent Acquisition Team\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "hr_name",
      "job_title",
      "meeting_link",
      "round_name",
      "time",
      "timezone"
    ],
    "trigger_event": "2 hours prior to scheduled interview round."
  },
  {
    "id": "hr_pending_decision_reminder",
    "name": "Internal: Pending Decision Reminder",
    "category": "internal",
    "subject": "[Pending Decision] Action Needed for {{candidate_name}} - {{job_title}}",
    "preheader": "48 hours have elapsed without a decision logged for {{candidate_name}} ({{round_name}}).",
    "body": "Hello {{hr_name}},\n\nThis is an automated SLA reminder that candidate {{candidate_name}} for the {{job_title}} position at {{company_name}} has been awaiting an evaluation decision for over 48 hours following their {{round_name}} stage.\n\nCANDIDATE EXPERIENCE ALERT:\nTo maintain our target candidate experience SLA and prevent candidate drop-off, please log into the dashboard and record an Approve, Reject, or Hold decision today.\n\nTalent Operations Automation\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "hr_name",
      "job_title",
      "round_name"
    ],
    "trigger_event": "Candidate remains in pending state 48 hours after interview or scoring."
  },
  {
    "id": "hr_candidate_moved_to_offer_section",
    "name": "Internal: Candidate Moved to Offer",
    "category": "internal",
    "subject": "[Action Required] Prepare Offer Letter: {{candidate_name}} - {{job_title}}",
    "preheader": "{{candidate_name}} has passed all interview rounds. Ready for offer generation.",
    "body": "Hello {{hr_name}},\n\nExciting news! Candidate {{candidate_name}} has successfully cleared all interview rounds for the {{job_title}} position at {{company_name}}, including final technical review.\n\nACTION ITEMS:\n1. Draft formal offer letter and compensation schedule.\n2. Secure leadership approval on equity, bonus, and base salary.\n3. Dispatch offer letter cover template to candidate.\n\nTalent Operations Automation\n{{company_name}}\nEmail: {{company_email}}\nWebsite: {{company_website}}",
    "required_variables": [
      "brand_color",
      "candidate_name",
      "company_email",
      "company_name",
      "company_website",
      "hr_name",
      "job_title"
    ],
    "trigger_event": "Candidate clears final technical round and moves to offer stage."
  }
];

export function normalizeCandidateName(rawName?: string): { fullName: string; firstName: string } {
  if (!rawName || !rawName.trim()) {
    return { fullName: "Candidate", firstName: "there" };
  }
  const cleaned = rawName.trim().replace(/\s+/g, " ");
  const words = cleaned.split(" ").map((w) => {
    if (w.toUpperCase() === w || w.toLowerCase() === w) {
      return w.charAt(0).toUpperCase() + w.slice(1).toLowerCase();
    }
    return w;
  });
  const fullName = words.join(" ");
  const firstName = words[0] || "there";
  return { fullName, firstName };
}

export function fillTemplate(
  text: string,
  context: {
    candidate_name?: string;
    job_title?: string;
    company_name?: string;
    hr_name?: string;
    company_email?: string;
    company_website?: string;
    schedule_link?: string;
    booking_link?: string;
    meet_link?: string;
    date?: string;
    time?: string;
    timezone?: string;
    [key: string]: any;
  }
): string {
  if (!text) return "";

  const { fullName, firstName } = normalizeCandidateName(context.candidate_name);
  const company = (context.company_name || "AivonTech").trim();
  const hr = (context.hr_name || "Talent Acquisition Team").trim();
  const hrDeduplicated = hr.toLowerCase() === company.toLowerCase() ? company : hr;

  const ctx: Record<string, string> = {
    candidate_name: firstName,
    candidate_full_name: fullName,
    job_title: context.job_title || "Open Position",
    role: context.job_title || "Open Position",
    company_name: company,
    company: company,
    hr_name: hrDeduplicated,
    company_email: context.company_email || "recruiting@" + company.toLowerCase().replace(/[^a-z0-9]/g, "") + ".com",
    company_website: context.company_website || "https://" + company.toLowerCase().replace(/[^a-z0-9]/g, "") + ".com",
    schedule_link: context.schedule_link || context.booking_link || "https://hrhiringloop.vercel.app",
    booking_link: context.booking_link || context.schedule_link || "https://hrhiringloop.vercel.app",
    meeting_link: context.meet_link || "https://meet.google.com",
    date: context.date || "Upcoming",
    time: context.time || "TBD",
    timezone: context.timezone || "UTC",
    round_name: context.round_name || "Interview",
    feedback: context.feedback || "your qualifications and experience",
    reply_deadline: context.reply_deadline || "48 hours",
    slot_1: context.slot_1 || "Tomorrow at 10:00 AM",
    slot_2: context.slot_2 || "Tomorrow at 2:00 PM",
    slot_3: context.slot_3 || "Day after tomorrow at 11:00 AM",
    offer_attachment_note: context.offer_attachment_note || "Please review the attached formal offer letter.",
    brand_color: context.brand_color || "#2563EB",
  };

  let result = text;
  for (const [key, val] of Object.entries(ctx)) {
    result = result.replace(new RegExp(`\\{\\{${key}\\}\\}`, "g"), val);
    result = result.replace(new RegExp(`\\{${key}\\}`, "g"), val);
  }

  // Also replace any Dear {{candidate_name}} or Hi {{candidate_name}} with friendly greeting
  result = result.replace(/^Dear there,/m, "Hi there,");

  return result;
}
