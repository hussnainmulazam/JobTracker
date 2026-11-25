"""
scheduling_service.py
~~~~~~~~~~~~~~~~~~~~~
Core service for recruiter availability, public candidate scheduling links,
Google Calendar FreeBusy integration, Google Meet link generation,
double-booking protection, rescheduling, cancellation, and automated reminders.
"""
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

import httpx
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, or_, select

from app.core.config import settings
from app.models.candidate import Candidate, CandidateStage
from app.models.google_account import GoogleAccount
from app.models.interview import (
    AvailabilitySchedule,
    Interview,
    InterviewStatus,
    SchedulingLink,
    SchedulingLinkStatus,
)
from app.models.job_opening import JobOpening, JobOpeningStatus
from app.models.message import Message, MessageDirection, MessageStatus, MessageType
from app.models.onboarding import OnboardingSetup
from app.models.user import User
from app.schemas.scheduling import (
    AvailabilityScheduleCreateOrUpdate,
    AvailabilityScheduleRead,
    AvailabilityWeekPreviewResponse,
    CalendarBookedInterview,
    CalendarBusyEvent,
    CalendarFreeSlot,
    InterviewRead,
    InterviewResultResponse,
    OfferDraftResponse,
    OfferSendRequest,
    PublicSchedulePageInfo,
    PublicSlotsResponse,
    ReminderProcessResult,
    SchedulingLinkRead,
    TimeSlot,
    WorkingBlock,
)
from app.services.audit_log_service import audit_log_service
from app.services.calendar_cache import calendar_cache
from app.services.google_service import GoogleService
from app.services.template_service import fill_template_variables, get_default_templates, render_user_template
from app.core.events import agent_events
from app.schemas.google import GoogleSendEmailRequest

logger = logging.getLogger(__name__)

GOOGLE_CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensures datetime object is timezone-aware in UTC to prevent offset-naive comparison errors."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class SchedulingService:
    # ── 1. Availability Management ───────────────────────────────────────────

    def get_or_create_availability(
        self, session: Session, user_id: uuid.UUID
    ) -> AvailabilitySchedule:
        """
        Fetches the recruiter's availability schedule, or creates default:
        Mon-Fri 09:00-17:00 in Asia/Karachi with 30m slots and 10m buffer.
        """
        schedule = session.exec(
            select(AvailabilitySchedule).where(AvailabilitySchedule.user_id == user_id)
        ).first()

        if not schedule:
            default_weekly = {
                "mon": [{"start": "09:00", "end": "17:00"}],
                "tue": [{"start": "09:00", "end": "17:00"}],
                "wed": [{"start": "09:00", "end": "17:00"}],
                "thu": [{"start": "09:00", "end": "17:00"}],
                "fri": [{"start": "09:00", "end": "17:00"}],
                "sat": [],
                "sun": [],
            }
            schedule = AvailabilitySchedule(
                user_id=user_id,
                timezone="Asia/Karachi",
                slot_duration_minutes=30,
                buffer_minutes=10,
                weekly_hours=default_weekly,
                is_active=True,
            )
            session.add(schedule)
            session.commit()
            session.refresh(schedule)

        return schedule

    def update_availability(
        self,
        session: Session,
        user_id: uuid.UUID,
        payload: AvailabilityScheduleCreateOrUpdate,
    ) -> AvailabilitySchedule:
        """Create or update recruiter's weekly working availability schedule."""
        schedule = session.exec(
            select(AvailabilitySchedule).where(AvailabilitySchedule.user_id == user_id)
        ).first()

        # Format weekly_hours to standard dict of lists
        weekly_dict: Dict[str, List[Dict[str, str]]] = {}
        for day, blocks in payload.weekly_hours.items():
            weekly_dict[day.lower()] = [
                {"start": b.start, "end": b.end} if isinstance(b, WorkingBlock) else b
                for b in blocks
            ]

        if not schedule:
            schedule = AvailabilitySchedule(
                user_id=user_id,
                timezone=payload.timezone or "Asia/Karachi",
                slot_duration_minutes=payload.slot_duration_minutes or 30,
                buffer_minutes=payload.buffer_minutes or 10,
                weekly_hours=weekly_dict,
                blocked_dates=payload.blocked_dates or [],
                is_active=payload.is_active,
            )
            session.add(schedule)
        else:
            schedule.timezone = payload.timezone or schedule.timezone
            schedule.slot_duration_minutes = payload.slot_duration_minutes or schedule.slot_duration_minutes
            schedule.buffer_minutes = payload.buffer_minutes if payload.buffer_minutes is not None else schedule.buffer_minutes
            schedule.weekly_hours = weekly_dict
            if payload.blocked_dates is not None:
                schedule.blocked_dates = payload.blocked_dates
            schedule.is_active = payload.is_active
            schedule.updated_at = datetime.now(timezone.utc)
            session.add(schedule)

        session.commit()
        session.refresh(schedule)
        from app.services.cache_service import cache_service
        cache_service.delete_prefix(f"calendar:events:{user_id}")
        cache_service.delete(f"calendar:availability:{user_id}")
        cache_service.delete_prefix("calendar:slots:")
        return schedule

    # ── 2. Scheduling Links ───────────────────────────────────────────────────

    def get_round_duration(
        self,
        session: Session,
        user_id: uuid.UUID,
        round_type: str,
    ) -> int:
        """
        Returns slot duration in minutes for a given interview round:
        - initial: default 30 min
        - behavioral: default 45 min
        - final: default 60 min
        Respects custom configured round durations in OnboardingSetup if available.
        """
        round_type_normalized = (round_type or "initial").lower().strip()
        default_durations = {
            "initial": 30,
            "behavioral": 45,
            "final": 60,
        }
        try:
            onboarding = session.exec(
                select(OnboardingSetup).where(OnboardingSetup.user_id == user_id)
            ).first()
            if onboarding and onboarding.interview_rounds:
                for round_item in onboarding.interview_rounds:
                    name = str(round_item.get("round_name", "")).lower()
                    dur = round_item.get("duration_minutes")
                    if dur and isinstance(dur, (int, float)) and dur > 0:
                        if round_type_normalized in name or (round_type_normalized == "behavioral" and "technical" in name):
                            return int(dur)
        except Exception as exc:
            logger.warning("Could not lookup custom round duration: %s", exc)

        return default_durations.get(round_type_normalized, 30)

    def create_scheduling_link(
        self,
        session: Session,
        user_id: uuid.UUID,
        candidate_id: uuid.UUID,
        round_type: str = "initial",
        slot_duration_minutes: Optional[int] = None,
        validity_days: int = 7,
    ) -> SchedulingLinkRead:
        """
        Generates a tokenized public booking link for a candidate.
        Token is unique and expires in validity_days (default 7 days).
        Duration defaults to the round's duration (initial 30m, behavioral 45m, final 60m).
        """
        candidate = session.exec(
            select(Candidate).where(
                Candidate.id == candidate_id,
                Candidate.user_id == user_id,
            )
        ).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found.")

        opening = session.exec(
            select(JobOpening).where(JobOpening.id == candidate.opening_id)
        ).first()
        if not opening:
            raise HTTPException(status_code=404, detail="Job opening not found.")

        effective_duration = slot_duration_minutes or self.get_round_duration(session, user_id, round_type)
        token = secrets.token_urlsafe(24)
        expires_at = datetime.now(timezone.utc) + timedelta(days=validity_days)

        link = SchedulingLink(
            token=token,
            user_id=user_id,
            candidate_id=candidate.id,
            opening_id=opening.id,
            round_type=round_type,
            slot_duration_minutes=effective_duration,
            status=SchedulingLinkStatus.active,
            expires_at=expires_at,
        )
        session.add(link)
        session.commit()
        session.refresh(link)

        return SchedulingLinkRead(
            id=link.id,
            token=link.token,
            user_id=link.user_id,
            candidate_id=link.candidate_id,
            candidate_name=candidate.name,
            candidate_email=candidate.email,
            opening_id=link.opening_id,
            opening_title=opening.title,
            round_type=link.round_type or "initial",
            slot_duration_minutes=link.slot_duration_minutes,
            status=link.status.value if hasattr(link.status, "value") else str(link.status),
            expires_at=ensure_utc(link.expires_at),
            public_url=f"/schedule/{link.token}",
            created_at=ensure_utc(link.created_at),
        )

    def get_public_link_info(
        self, session: Session, token: str
    ) -> PublicSchedulePageInfo:
        """
        Returns info for candidate on public scheduling page (/schedule/{token}).
        Handles token expiry and already booked states.
        """
        link = session.exec(
            select(SchedulingLink).where(SchedulingLink.token == token)
        ).first()
        if not link:
            raise HTTPException(status_code=404, detail="Scheduling link not found or invalid.")

        now_utc = datetime.now(timezone.utc)
        current_status = link.status.value if hasattr(link.status, "value") else str(link.status)
        link_expires_at = ensure_utc(link.expires_at) or now_utc

        # Handle token expiry
        if current_status == "active" and link_expires_at < now_utc:
            link.status = SchedulingLinkStatus.expired
            session.add(link)
            session.commit()
            session.refresh(link)
            current_status = "expired"

        candidate = session.exec(select(Candidate).where(Candidate.id == link.candidate_id)).first()
        opening = session.exec(select(JobOpening).where(JobOpening.id == link.opening_id)).first()
        recruiter = session.exec(select(User).where(User.id == link.user_id)).first()

        existing_interview_read: Optional[InterviewRead] = None
        if current_status == "booked":
            interview = session.exec(
                select(Interview).where(
                    Interview.scheduling_link_id == link.id,
                    Interview.status != InterviewStatus.cancelled,
                )
            ).first()
            if interview:
                existing_interview_read = self._to_interview_read(interview, candidate, opening)

        # Look up default timezone from HR availability schedule
        avail = session.exec(
            select(AvailabilitySchedule).where(AvailabilitySchedule.user_id == link.user_id)
        ).first()
        default_tz = avail.timezone if avail else "Asia/Karachi"

        return PublicSchedulePageInfo(
            token=link.token,
            status=current_status,
            expires_at=ensure_utc(link.expires_at),
            candidate_name=candidate.name if candidate else "Candidate",
            candidate_email=candidate.email if candidate else "",
            candidate_phone=candidate.phone if candidate else None,
            opening_title=opening.title if opening else "Position",
            round_type=getattr(link, "round_type", "initial") or "initial",
            slot_duration_minutes=link.slot_duration_minutes,
            default_timezone=default_tz,
            interviewer_email=recruiter.email if recruiter else "recruiter@company.com",
            existing_interview=existing_interview_read,
        )

    # ── 3. Google Calendar FreeBusy & Conference Integration ──────────────────

    async def get_google_calendar_busy_ranges(
        self,
        session: Session,
        user_id: uuid.UUID,
        time_min_utc: datetime,
        time_max_utc: datetime,
    ) -> List[Tuple[datetime, datetime]]:
        """
        Calls Google Calendar FreeBusy API to fetch recruiter's external commitments.
        Returns list of (busy_start_utc, busy_end_utc).
        """
        account = session.exec(
            select(GoogleAccount).where(GoogleAccount.user_id == user_id)
        ).first()

        if not account:
            return []

        google_service = GoogleService(session)
        try:
            access_token = google_service.get_valid_access_token(account)
            if not access_token or access_token.startswith("simulated_"):
                return []

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
            body = {
                "timeMin": time_min_utc.isoformat(),
                "timeMax": time_max_utc.isoformat(),
                "timeZone": "UTC",
                "items": [{"id": "primary"}],
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    f"{GOOGLE_CALENDAR_API_BASE}/freeBusy",
                    json=body,
                    headers=headers,
                )
                if not res.is_success:
                    logger.warning("Google Calendar FreeBusy API error: %s %s", res.status_code, res.text)
                    return []

                data = res.json()
                busy_items = data.get("calendars", {}).get("primary", {}).get("busy", [])
                ranges: List[Tuple[datetime, datetime]] = []
                for item in busy_items:
                    b_start = datetime.fromisoformat(item["start"].replace("Z", "+00:00"))
                    b_end = datetime.fromisoformat(item["end"].replace("Z", "+00:00"))
                    ranges.append((b_start, b_end))
                return ranges
        except Exception as exc:
            logger.warning("Failed to query Google Calendar freeBusy: %s", exc)
            return []

    async def create_google_calendar_event(
        self,
        session: Session,
        user_id: uuid.UUID,
        summary: str,
        description: str,
        start_time_utc: datetime,
        end_time_utc: datetime,
        candidate_email: str,
        recruiter_email: str,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Creates a Google Calendar event with conferenceData (Google Meet) and invites both emails.
        Returns (google_calendar_event_id, meet_link).
        """
        account = session.exec(
            select(GoogleAccount).where(GoogleAccount.user_id == user_id)
        ).first()

        request_id = f"meet-{uuid.uuid4().hex[:12]}"
        simulated_meet = f"https://meet.google.com/{secrets.token_hex(3)}-{secrets.token_hex(4)}-{secrets.token_hex(3)}"
        simulated_event_id = f"cal_evt_{uuid.uuid4().hex[:16]}"

        if not account:
            return simulated_event_id, simulated_meet

        google_service = GoogleService(session)
        try:
            access_token = google_service.get_valid_access_token(account)
            if not access_token or access_token.startswith("simulated_"):
                return simulated_event_id, simulated_meet

            effective_recruiter = account.email or recruiter_email
            attendees = [{"email": effective_recruiter, "responseStatus": "accepted"}]
            if candidate_email and candidate_email.lower() != effective_recruiter.lower():
                attendees.append({"email": candidate_email})
            if recruiter_email and recruiter_email.lower() != effective_recruiter.lower():
                attendees.append({"email": recruiter_email, "responseStatus": "accepted"})

            event_body = {
                "summary": summary,
                "description": description,
                "start": {"dateTime": start_time_utc.isoformat()},
                "end": {"dateTime": end_time_utc.isoformat()},
                "attendees": attendees,
                "conferenceData": {
                    "createRequest": {
                        "requestId": request_id,
                        "conferenceSolutionKey": {"type": "hangoutsMeet"},
                    }
                },
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "email", "minutes": 24 * 60},
                        {"method": "popup", "minutes": 15},
                    ],
                },
            }

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
            url = f"{GOOGLE_CALENDAR_API_BASE}/calendars/primary/events?conferenceDataVersion=1"

            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=event_body, headers=headers)
                if not resp.is_success:
                    logger.error("Failed to create Google Calendar event: %s", resp.text)
                    return simulated_event_id, simulated_meet

                data = resp.json()
                event_id = data.get("id", simulated_event_id)
                meet_link = (
                    data.get("hangoutLink")
                    or data.get("conferenceData", {}).get("entryPoints", [{}])[0].get("uri")
                    or simulated_meet
                )
                return event_id, meet_link
        except Exception as exc:
            logger.warning("Error calling Google Calendar API: %s. Using simulated Meet link.", exc)
            return simulated_event_id, simulated_meet

    async def update_google_calendar_event_time(
        self,
        session: Session,
        user_id: uuid.UUID,
        event_id: str,
        start_time_utc: datetime,
        end_time_utc: datetime,
    ) -> bool:
        """Updates event time on Google Calendar when rescheduled."""
        account = session.exec(select(GoogleAccount).where(GoogleAccount.user_id == user_id)).first()
        if not account or not event_id or event_id.startswith("cal_evt_"):
            return True

        google_service = GoogleService(session)
        try:
            access_token = google_service.get_valid_access_token(account)
            if not access_token or access_token.startswith("simulated_"):
                return True

            patch_body = {
                "start": {"dateTime": start_time_utc.isoformat()},
                "end": {"dateTime": end_time_utc.isoformat()},
            }
            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
            url = f"{GOOGLE_CALENDAR_API_BASE}/calendars/primary/events/{event_id}"

            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.patch(url, json=patch_body, headers=headers)
                return res.is_success
        except Exception as exc:
            logger.warning("Failed to patch Google Calendar event %s: %s", event_id, exc)
            return False

    async def cancel_google_calendar_event(
        self, session: Session, user_id: uuid.UUID, event_id: str
    ) -> bool:
        """Deletes or cancels event on Google Calendar."""
        account = session.exec(select(GoogleAccount).where(GoogleAccount.user_id == user_id)).first()
        if not account or not event_id or event_id.startswith("cal_evt_"):
            return True

        google_service = GoogleService(session)
        try:
            access_token = google_service.get_valid_access_token(account)
            if not access_token or access_token.startswith("simulated_"):
                return True

            headers = {"Authorization": f"Bearer {access_token}"}
            url = f"{GOOGLE_CALENDAR_API_BASE}/calendars/primary/events/{event_id}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.delete(url, headers=headers)
                return res.is_success
        except Exception as exc:
            logger.warning("Failed to delete Google Calendar event %s: %s", event_id, exc)
            return False

    # ── 4. Free/Busy Slot Computation Algorithm ───────────────────────────────

    async def compute_available_slots(
        self,
        session: Session,
        token: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        candidate_tz_str: Optional[str] = None,
    ) -> PublicSlotsResponse:
        """
        Computes candidate free slots from:
          1. Recruiter's weekly working availability
          2. Minus recruiter's Google Calendar freeBusy
          3. Minus already booked/scheduled interviews in DB
        Timezone-aware (defaults to Asia/Karachi).
        """
        link = session.exec(select(SchedulingLink).where(SchedulingLink.token == token)).first()
        if not link:
            raise HTTPException(status_code=404, detail="Invalid scheduling link.")

        now_utc = datetime.now(timezone.utc)
        link_status = link.status.value if hasattr(link.status, "value") else str(link.status)
        link_expires_at = ensure_utc(link.expires_at) or now_utc

        if link_status == "expired" or link_expires_at < now_utc:
            return PublicSlotsResponse(
                token=token,
                timezone=candidate_tz_str or "Asia/Karachi",
                slot_duration_minutes=link.slot_duration_minutes,
                slots_by_date={},
                total_slots_available=0,
            )

        avail = self.get_or_create_availability(session, link.user_id)
        hr_tz_str = avail.timezone or "Asia/Karachi"
        target_tz_str = candidate_tz_str or hr_tz_str

        try:
            hr_tz = ZoneInfo(hr_tz_str)
        except Exception:
            hr_tz = ZoneInfo("Asia/Karachi")

        try:
            candidate_tz = ZoneInfo(target_tz_str)
        except Exception:
            candidate_tz = ZoneInfo("Asia/Karachi")

        # Range to compute: default next 14 days
        now_hr = datetime.now(hr_tz)
        if start_date:
            try:
                dt_start = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                dt_start = now_hr.date()
        else:
            dt_start = now_hr.date()

        if end_date:
            try:
                dt_end = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                dt_end = dt_start + timedelta(days=14)
        else:
            dt_end = dt_start + timedelta(days=14)

        # Cap computation window to link expiry
        link_expiry_date = link_expires_at.astimezone(hr_tz).date()
        if dt_end > link_expiry_date:
            dt_end = link_expiry_date

        if dt_start > dt_end:
            dt_start = dt_end

        # Pre-fetch Google Calendar busy ranges in UTC
        start_utc_query = datetime.combine(dt_start, datetime.min.time(), tzinfo=hr_tz).astimezone(timezone.utc)
        end_utc_query = datetime.combine(dt_end, datetime.max.time(), tzinfo=hr_tz).astimezone(timezone.utc)

        google_busy_ranges = await self.get_google_calendar_busy_ranges(
            session=session,
            user_id=link.user_id,
            time_min_utc=start_utc_query,
            time_max_utc=end_utc_query,
        )

        # Pre-fetch DB booked interviews in UTC
        db_interviews = session.exec(
            select(Interview).where(
                Interview.user_id == link.user_id,
                Interview.status != InterviewStatus.cancelled,
                Interview.start_time < end_utc_query,
                Interview.end_time > start_utc_query,
            )
        ).all()
        db_busy_ranges = [(ensure_utc(inv.start_time), ensure_utc(inv.end_time)) for inv in db_interviews]

        all_busy_ranges = google_busy_ranges + db_busy_ranges

        # Discretize slots
        slot_duration = timedelta(minutes=link.slot_duration_minutes)
        buffer_duration = timedelta(minutes=avail.buffer_minutes)
        step_duration = slot_duration + buffer_duration

        weekday_keys = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        weekly_config = avail.weekly_hours or {}

        slots_by_date: Dict[str, List[TimeSlot]] = {}
        total_slots = 0

        curr_date = dt_start
        min_lead_time_utc = now_utc + timedelta(hours=1)  # No scheduling in the immediate past / 1h
        blocked_dates_set = set(getattr(avail, "blocked_dates", []) or [])

        while curr_date <= dt_end:
            date_key_str = curr_date.strftime("%Y-%m-%d")
            if date_key_str in blocked_dates_set:
                curr_date += timedelta(days=1)
                continue

            day_key = weekday_keys[curr_date.weekday()]
            day_blocks = weekly_config.get(day_key, [])

            for block in day_blocks:
                start_str = block.get("start")
                end_str = block.get("end")
                if not start_str or not end_str:
                    continue

                try:
                    s_h, s_m = map(int, start_str.split(":"))
                    e_h, e_m = map(int, end_str.split(":"))
                except ValueError:
                    continue

                block_start_dt = datetime.combine(curr_date, datetime.min.time(), tzinfo=hr_tz).replace(
                    hour=s_h, minute=s_m
                )
                block_end_dt = datetime.combine(curr_date, datetime.min.time(), tzinfo=hr_tz).replace(
                    hour=e_h, minute=e_m
                )

                curr_slot_start = block_start_dt
                while curr_slot_start + slot_duration <= block_end_dt:
                    curr_slot_end = curr_slot_start + slot_duration

                    # Convert to UTC for conflict checking
                    slot_start_utc = curr_slot_start.astimezone(timezone.utc)
                    slot_end_utc = curr_slot_end.astimezone(timezone.utc)

                    # Must be in future
                    if slot_start_utc >= min_lead_time_utc:
                        # Check collision with busy ranges
                        is_busy = False
                        for b_start, b_end in all_busy_ranges:
                            # Overlap condition: b_start < slot_end AND b_end > slot_start
                            if b_start < slot_end_utc and b_end > slot_start_utc:
                                is_busy = True
                                break

                        if not is_busy:
                            # Format in candidate's requested timezone
                            slot_cand_start = slot_start_utc.astimezone(candidate_tz)
                            slot_cand_end = slot_end_utc.astimezone(candidate_tz)
                            cand_date_str = slot_cand_start.strftime("%Y-%m-%d")

                            slot_item = TimeSlot(
                                start_time=slot_start_utc,
                                end_time=slot_end_utc,
                                start_time_local=slot_cand_start.strftime("%I:%M %p"),
                                end_time_local=slot_cand_end.strftime("%I:%M %p"),
                                date_str=cand_date_str,
                                timezone=target_tz_str,
                            )
                            if cand_date_str not in slots_by_date:
                                slots_by_date[cand_date_str] = []
                            slots_by_date[cand_date_str].append(slot_item)
                            total_slots += 1

                    curr_slot_start += step_duration

            curr_date += timedelta(days=1)

        return PublicSlotsResponse(
            token=token,
            timezone=target_tz_str,
            slot_duration_minutes=link.slot_duration_minutes,
            slots_by_date=slots_by_date,
            total_slots_available=total_slots,
        )

    # ── 5. Slot Selection & Booking ───────────────────────────────────────────

    async def book_slot(
        self,
        session: Session,
        token: str,
        start_time: datetime,
        booking_tz_str: Optional[str] = "Asia/Karachi",
        notes: Optional[str] = None,
    ) -> InterviewRead:
        """
        Candidate selects a free slot:
          1. Creates Calendar event with conferenceData (Google Meet) & invites emails
          2. Inserts into interviews with DB exclusion constraint preventing double-booking
          3. Marks token booked & updates candidate stage to 'interview'
          4. Dispatches confirmation via WhatsApp template & email
        """
        link = session.exec(select(SchedulingLink).where(SchedulingLink.token == token)).first()
        if not link:
            raise HTTPException(status_code=404, detail="Invalid scheduling link.")

        now_utc = datetime.now(timezone.utc)
        link_status = link.status.value if hasattr(link.status, "value") else str(link.status)
        link_expires_at = ensure_utc(link.expires_at) or now_utc

        if link_status == "expired" or link_expires_at < now_utc:
            raise HTTPException(status_code=400, detail="This scheduling link has expired.")

        if link_status == "booked":
            raise HTTPException(status_code=400, detail="This scheduling link has already been used to book an interview.")

        candidate = session.exec(select(Candidate).where(Candidate.id == link.candidate_id)).first()
        opening = session.exec(select(JobOpening).where(JobOpening.id == link.opening_id)).first()
        recruiter = session.exec(select(User).where(User.id == link.user_id)).first()

        if not candidate or not opening or not recruiter:
            raise HTTPException(status_code=404, detail="Candidate or Job Opening record not found.")

        # Ensure start_time has UTC timezone
        if start_time.tzinfo is None:
            start_time_utc = start_time.replace(tzinfo=timezone.utc)
        else:
            start_time_utc = start_time.astimezone(timezone.utc)

        end_time_utc = start_time_utc + timedelta(minutes=link.slot_duration_minutes)

        # ── Double-booking check in application level before DB constraint ────
        overlap = session.exec(
            select(Interview).where(
                Interview.user_id == link.user_id,
                Interview.status != InterviewStatus.cancelled,
                Interview.start_time < end_time_utc,
                Interview.end_time > start_time_utc,
            )
        ).first()

        if overlap:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Selected time slot has just been booked by another candidate. Please select another slot.",
            )

        # ── Create Google Calendar event with Google Meet ─────────────────────
        link_round = getattr(link, "round_type", "initial") or "initial"
        round_name_map = {
            "initial": "Initial Interview",
            "behavioral": "Behavioral Interview",
            "final": "Final Interview",
        }
        round_display = round_name_map.get(link_round.lower(), "Interview")
        summary = f"{round_display}: {candidate.name} - {opening.title}"
        description = (
            f"AI Candidate Screening Copilot Interview ({round_display})\n\n"
            f"Candidate: {candidate.name}\n"
            f"Email: {candidate.email}\n"
            f"Position: {opening.title}\n"
            f"Round: {round_display} ({link.slot_duration_minutes} minutes)\n"
            f"Recruiter: {recruiter.email}\n"
            f"Notes: {notes or 'None'}"
        )

        cal_event_id, meet_link = await self.create_google_calendar_event(
            session=session,
            user_id=link.user_id,
            summary=summary,
            description=description,
            start_time_utc=start_time_utc,
            end_time_utc=end_time_utc,
            candidate_email=candidate.email,
            recruiter_email=recruiter.email,
        )

        interview = Interview(
            user_id=link.user_id,
            candidate_id=candidate.id,
            opening_id=opening.id,
            scheduling_link_id=link.id,
            round_type=link_round,
            title=summary,
            start_time=start_time_utc,
            end_time=end_time_utc,
            timezone=booking_tz_str or "Asia/Karachi",
            google_calendar_event_id=cal_event_id,
            meet_link=meet_link,
            candidate_name=candidate.name,
            candidate_email=candidate.email,
            candidate_phone=candidate.phone,
            interviewer_email=recruiter.email,
            status=InterviewStatus.scheduled,
        )

        try:
            session.add(interview)
            link.status = SchedulingLinkStatus.booked
            link.updated_at = now_utc
            session.add(link)

            # Move candidate to scheduled stage
            old_stage_str = candidate.stage.value if hasattr(candidate.stage, "value") else str(candidate.stage)
            candidate.stage = CandidateStage.scheduled
            candidate.updated_at = now_utc
            session.add(candidate)

            session.commit()
            session.refresh(interview)

            # Audit log stage transition
            try:
                from app.services.audit_log_service import audit_log_service
                audit_log_service.record(
                    session=session,
                    user_id=link.user_id,
                    candidate_id=candidate.id,
                    opening_id=opening.id,
                    action="interview_scheduled",
                    from_stage=old_stage_str,
                    to_stage="scheduled",
                    details=f"Interview booked for {start_time_utc.isoformat()} (Google Meet: {meet_link})",
                )
            except Exception as audit_err:
                logger.warning("Failed to record booking audit log: %s", audit_err)
        except IntegrityError as exc:
            session.rollback()
            logger.warning("PostgreSQL double-booking exclusion constraint triggered: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This time slot conflicts with an existing interview. Please choose another slot.",
            )

        # ── Clear Calendar Events Cache for User ──────────────────────────────
        calendar_cache.clear_for_user(str(link.user_id))

        # ── Send Confirmation via WhatsApp template/email ─────────────────────
        await self._send_interview_notification(
            session=session,
            interview=interview,
            candidate=candidate,
            opening=opening,
            event_type="confirmation",
        )

        # ── Notify HR immediately by email ────────────────────────────────────
        try:
            from app.services.agent_settings_service import agent_settings_service
            agent_settings_service.notify_hr_instant(
                session=session,
                user_id=link.user_id,
                event_type="booking",
                candidate_name=candidate.name,
                opening_title=opening.title,
                details=f"Slot booked for {start_time_utc.strftime('%A, %b %d at %I:%M %p UTC')} ({link.slot_duration_minutes}m). Google Meet: {meet_link}",
            )
        except Exception as alert_err:
            logger.warning("Could not dispatch instant HR booking alert: %s", alert_err)

        return self._to_interview_read(interview, candidate, opening)

    # ── 6. Rescheduling & Cancellation ────────────────────────────────────────

    async def reschedule_interview(
        self,
        session: Session,
        interview_id: uuid.UUID,
        new_start_time: datetime,
        reschedule_tz_str: Optional[str] = "Asia/Karachi",
        reason: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> InterviewRead:
        """
        Reschedules an interview to a new time:
          1. Verifies slot availability (no double booking)
          2. Updates Google Calendar event time
          3. Updates interview record & resets reminder flags
          4. Dispatches reschedule notification via WhatsApp / email
        """
        query = select(Interview).where(Interview.id == interview_id)
        if user_id:
            query = query.where(Interview.user_id == user_id)
        interview = session.exec(query).first()
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found.")

        if interview.status == InterviewStatus.cancelled:
            raise HTTPException(status_code=400, detail="Cannot reschedule a cancelled interview.")

        if new_start_time.tzinfo is None:
            new_start_utc = new_start_time.replace(tzinfo=timezone.utc)
        else:
            new_start_utc = new_start_time.astimezone(timezone.utc)

        duration = interview.end_time - interview.start_time
        new_end_utc = new_start_utc + duration

        # Verify no double booking for recruiter
        conflict = session.exec(
            select(Interview).where(
                Interview.user_id == interview.user_id,
                Interview.id != interview.id,
                Interview.status != InterviewStatus.cancelled,
                Interview.start_time < new_end_utc,
                Interview.end_time > new_start_utc,
            )
        ).first()

        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The requested new time slot conflicts with an existing interview.",
            )

        # Update Google Calendar
        if interview.google_calendar_event_id:
            await self.update_google_calendar_event_time(
                session=session,
                user_id=interview.user_id,
                event_id=interview.google_calendar_event_id,
                start_time_utc=new_start_utc,
                end_time_utc=new_end_utc,
            )

        interview.start_time = new_start_utc
        interview.end_time = new_end_utc
        interview.timezone = reschedule_tz_str or interview.timezone
        interview.status = InterviewStatus.rescheduled
        interview.reminder_24h_sent = False
        interview.reminder_24h_sent_at = None
        interview.reminder_1h_sent = False
        interview.reminder_1h_sent_at = None
        interview.updated_at = datetime.now(timezone.utc)

        try:
            session.add(interview)
            session.commit()
            session.refresh(interview)
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Exclusion constraint: This slot was booked simultaneously.",
            )

        # Clear Calendar Events Cache for User
        calendar_cache.clear_for_user(str(interview.user_id))

        candidate = session.exec(select(Candidate).where(Candidate.id == interview.candidate_id)).first()
        opening = session.exec(select(JobOpening).where(JobOpening.id == interview.opening_id)).first()

        await self._send_interview_notification(
            session=session,
            interview=interview,
            candidate=candidate,
            opening=opening,
            event_type="reschedule",
        )

        return self._to_interview_read(interview, candidate, opening)

    async def cancel_interview(
        self,
        session: Session,
        interview_id: uuid.UUID,
        reason: Optional[str] = None,
        cancelled_by: Optional[str] = "hr",
        user_id: Optional[uuid.UUID] = None,
    ) -> InterviewRead:
        """
        Cancels an interview:
          1. Removes Google Calendar event
          2. Marks interview cancelled with reason & timestamp
          3. Frees up scheduling link or cancels it
          4. Dispatches cancellation notice
        """
        query = select(Interview).where(Interview.id == interview_id)
        if user_id:
            query = query.where(Interview.user_id == user_id)
        interview = session.exec(query).first()
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found.")

        if interview.status == InterviewStatus.cancelled:
            return self._to_interview_read(interview)

        # Cancel on Google Calendar
        if interview.google_calendar_event_id:
            await self.cancel_google_calendar_event(
                session=session,
                user_id=interview.user_id,
                event_id=interview.google_calendar_event_id,
            )

        now_utc = datetime.now(timezone.utc)
        interview.status = InterviewStatus.cancelled
        interview.cancellation_reason = reason or "Cancelled by user"
        interview.cancelled_at = now_utc
        interview.cancelled_by = cancelled_by or "hr"
        interview.updated_at = now_utc

        # Re-activate scheduling link so candidate can pick another time if needed
        if interview.scheduling_link_id:
            link = session.exec(
                select(SchedulingLink).where(SchedulingLink.id == interview.scheduling_link_id)
            ).first()
            link_exp = ensure_utc(link.expires_at) if link else None
            if link and link_exp and link_exp > now_utc:
                link.status = SchedulingLinkStatus.active
                session.add(link)

        session.add(interview)
        session.commit()
        session.refresh(interview)

        # Clear Calendar Events Cache for User
        calendar_cache.clear_for_user(str(interview.user_id))

        candidate = session.exec(select(Candidate).where(Candidate.id == interview.candidate_id)).first()
        opening = session.exec(select(JobOpening).where(JobOpening.id == interview.opening_id)).first()

        await self._send_interview_notification(
            session=session,
            interview=interview,
            candidate=candidate,
            opening=opening,
            event_type="cancellation",
        )

        return self._to_interview_read(interview, candidate, opening)

    # ── 7. Reminders (24h and 1h) ─────────────────────────────────────────────

    async def process_reminders(self, session: Session) -> ReminderProcessResult:
        """
        Background task / cron runner:
        Finds scheduled/rescheduled interviews due for:
          - 24-hour reminder (within [1h, 24h] from now, not yet sent)
          - 1-hour reminder (within [0, 1h] from now, not yet sent)
        Dispatches WhatsApp template / email.
        """
        now_utc = datetime.now(timezone.utc)
        in_24h = now_utc + timedelta(hours=24)
        in_1h = now_utc + timedelta(hours=1)

        active_interviews = session.exec(
            select(Interview).where(
                or_(
                    Interview.status == InterviewStatus.scheduled,
                    Interview.status == InterviewStatus.rescheduled,
                ),
                Interview.start_time > now_utc,
                Interview.start_time <= in_24h,
            )
        ).all()

        reminders_24h_count = 0
        reminders_1h_count = 0

        for inv in active_interviews:
            candidate = session.exec(select(Candidate).where(Candidate.id == inv.candidate_id)).first()
            opening = session.exec(select(JobOpening).where(JobOpening.id == inv.opening_id)).first()
            inv_start = ensure_utc(inv.start_time) or now_utc

            # Check 24-hour reminder
            if not inv.reminder_24h_sent and inv_start <= in_24h and inv_start > in_1h:
                await self._send_interview_notification(
                    session=session,
                    interview=inv,
                    candidate=candidate,
                    opening=opening,
                    event_type="reminder_24h",
                )
                inv.reminder_24h_sent = True
                inv.reminder_24h_sent_at = now_utc
                session.add(inv)
                reminders_24h_count += 1

            # Check 1-hour reminder
            if not inv.reminder_1h_sent and inv_start <= in_1h and inv_start > now_utc:
                await self._send_interview_notification(
                    session=session,
                    interview=inv,
                    candidate=candidate,
                    opening=opening,
                    event_type="reminder_1h",
                )
                inv.reminder_1h_sent = True
                inv.reminder_1h_sent_at = now_utc
                session.add(inv)
                reminders_1h_count += 1

        session.commit()
        return ReminderProcessResult(
            reminders_24h_sent=reminders_24h_count,
            reminders_1h_sent=reminders_1h_count,
            interviews_processed=len(active_interviews),
        )

    # ── 8. Notification Helper ────────────────────────────────────────────────

    async def _send_interview_notification(
        self,
        session: Session,
        interview: Interview,
        candidate: Optional[Candidate],
        opening: Optional[JobOpening],
        event_type: str,  # "confirmation" | "reschedule" | "cancellation" | "reminder_24h" | "reminder_1h"
    ) -> None:
        """
        Dispatches interview notification email to candidate and interviewer via GoogleService (Gmail).
        """
        if not candidate or not candidate.email:
            logger.info("Candidate has no email, skipping interview email notification for %s", event_type)
            return

        # Format date & time for human in interview timezone
        try:
            tz = ZoneInfo(interview.timezone)
        except Exception:
            tz = ZoneInfo("Asia/Karachi")

        local_dt = interview.start_time.astimezone(tz)
        date_str = local_dt.strftime("%A, %b %d at %I:%M %p (%Z)")
        job_title = opening.title if opening else "Position"

        meet_text = f"Google Meet Link: {interview.meet_link}" if interview.meet_link else "Meeting details will follow."

        cand_schedule_link = f"{settings.FRONTEND_URL.rstrip('/')}/schedule/{candidate.id}"
        stage_key = "rejection" if event_type == "cancellation" else "initial_interview"
        ctx = {
            "candidate_name": candidate.name,
            "role": job_title,
            "company": "Our Company",
            "hr_name": "Recruiting Team",
            "interview_date": local_dt.strftime("%A, %b %d"),
            "interview_time": local_dt.strftime("%I:%M %p (%Z)"),
            "meet_link": interview.meet_link or f"https://meet.google.com/interview-{interview.id}",
            "schedule_link": cand_schedule_link,
            "slot_link": cand_schedule_link,
            "booking_link": cand_schedule_link,
            "job_details": opening.description if opening else "Interview Details",
        }
        try:
            from app.models.onboarding import OnboardingSetup
            onboarding = session.exec(
                select(OnboardingSetup).where(OnboardingSetup.user_id == interview.user_id)
            ).first()
            if onboarding:
                if onboarding.company_name:
                    ctx["company"] = onboarding.company_name
                if onboarding.hr_name:
                    ctx["hr_name"] = onboarding.hr_name
        except Exception:
            pass

        subject, html_body, body, _ = render_user_template(
            session=session,
            user_id=interview.user_id,
            template_id=stage_key,
            context=ctx,
        )

        try:
            google_svc = GoogleService(session)
            google_svc.send_email(
                user_id=interview.user_id,
                request=GoogleSendEmailRequest(
                    candidate_id=candidate.id,
                    subject=subject,
                    body=body,
                    template_name=f"interview_{event_type}",
                ),
            )
            logger.info("Sent %s email via Gmail to %s for interview %s", event_type, candidate.email, interview.id)
        except Exception as exc:
            logger.warning("Could not dispatch Gmail notification for interview %s: %s", interview.id, exc)

    # ── 9. List & Read Helpers ────────────────────────────────────────────────

    def list_interviews(
        self,
        session: Session,
        user_id: uuid.UUID,
        opening_id: Optional[uuid.UUID] = None,
        candidate_id: Optional[uuid.UUID] = None,
        status_filter: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> List[InterviewRead]:
        """List recruiter's interviews with filtering."""
        # Auto-sync passed interviews to 'interviewed' stage
        try:
            from app.services.outreach_service import outreach_service
            outreach_service.sync_completed_interviews(session, user_id=user_id)
        except Exception as sync_err:
            logger.warning("Error syncing completed interview stages: %s", sync_err)

        query = select(Interview).where(Interview.user_id == user_id)
        if opening_id:
            query = query.where(Interview.opening_id == opening_id)
        if candidate_id:
            query = query.where(Interview.candidate_id == candidate_id)
        if status_filter:
            query = query.where(Interview.status == status_filter)
        if from_date:
            query = query.where(Interview.start_time >= from_date)
        if to_date:
            query = query.where(Interview.end_time <= to_date)

        query = query.order_by(Interview.start_time.asc())
        interviews = session.exec(query).all()

        results: List[InterviewRead] = []
        for inv in interviews:
            results.append(self._to_interview_read(inv))
        return results

    async def sync_google_calendar_events(
        self,
        session: Session,
        user_id: uuid.UUID,
    ) -> dict:
        """
        Reconciles interviews with Google Calendar:
        1. Checks status of existing Google Calendar events for the user's interviews.
        2. Detects if an event was cancelled or deleted on Google Calendar.
        3. If any scheduled interview is missing a Google Calendar event and Google is connected, creates it.
        4. Automatically advances past interviews to completed stage.
        """
        from app.models.google_account import GoogleAccount
        from app.services.google_service import GoogleService

        account = session.exec(select(GoogleAccount).where(GoogleAccount.user_id == user_id)).first()
        interviews = session.exec(
            select(Interview).where(Interview.user_id == user_id)
        ).all()

        synced_count = 0
        updated_count = 0
        cancelled_count = 0
        now_utc = datetime.now(timezone.utc)

        google_service = GoogleService(session)
        access_token = None
        if account:
            try:
                tok = google_service.get_valid_access_token(account)
                if tok and not tok.startswith("simulated_"):
                    access_token = tok
            except Exception:
                access_token = None

        for inv in interviews:
            synced_count += 1
            inv_end = ensure_utc(inv.end_time)

            # 1. Advance past interviews to completed if still scheduled
            if inv_end and inv_end < now_utc and inv.status == InterviewStatus.scheduled:
                inv.status = InterviewStatus.completed
                inv.updated_at = now_utc
                session.add(inv)
                updated_count += 1
                continue

            # 2. Check remote Google Calendar event if connected
            if access_token and inv.google_calendar_event_id and not inv.google_calendar_event_id.startswith("cal_evt_"):
                try:
                    headers = {"Authorization": f"Bearer {access_token}"}
                    url = f"{GOOGLE_CALENDAR_API_BASE}/calendars/primary/events/{inv.google_calendar_event_id}"
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        resp = await client.get(url, headers=headers)
                        if resp.status_code == 200:
                            data = resp.json()
                            if data.get("status") == "cancelled" and inv.status != InterviewStatus.cancelled:
                                inv.status = InterviewStatus.cancelled
                                inv.cancellation_reason = "Cancelled in Google Calendar"
                                inv.cancelled_at = now_utc
                                session.add(inv)
                                cancelled_count += 1
                            else:
                                hangout_link = data.get("hangoutLink") or data.get("conferenceData", {}).get("entryPoints", [{}])[0].get("uri")
                                if hangout_link and inv.meet_link != hangout_link:
                                    inv.meet_link = hangout_link
                                    session.add(inv)
                                    updated_count += 1
                        elif resp.status_code == 404 and inv.status != InterviewStatus.cancelled:
                            inv.status = InterviewStatus.cancelled
                            inv.cancellation_reason = "Deleted from Google Calendar"
                            inv.cancelled_at = now_utc
                            session.add(inv)
                            cancelled_count += 1
                except Exception as g_err:
                    logger.warning("Error syncing event %s from Google Calendar: %s", inv.google_calendar_event_id, g_err)

            # 3. Create missing Google Calendar event if Google account is connected
            elif access_token and inv.status == InterviewStatus.scheduled and (not inv.google_calendar_event_id or inv.google_calendar_event_id.startswith("cal_evt_")):
                try:
                    summary = f"Interview: {inv.candidate_name} - {inv.title}"
                    desc = f"Interview with {inv.candidate_name} ({inv.candidate_email}) via Hiring Loop."
                    cal_id, meet_link = await self.create_google_calendar_event(
                        session=session,
                        user_id=user_id,
                        summary=summary,
                        description=desc,
                        start_time_utc=ensure_utc(inv.start_time),
                        end_time_utc=ensure_utc(inv.end_time),
                        candidate_email=inv.candidate_email,
                        recruiter_email=inv.interviewer_email,
                    )
                    if cal_id and not cal_id.startswith("cal_evt_"):
                        inv.google_calendar_event_id = cal_id
                    if meet_link:
                        inv.meet_link = meet_link
                    session.add(inv)
                    updated_count += 1
                except Exception as c_err:
                    logger.warning("Error creating calendar event for interview %s: %s", inv.id, c_err)

        session.commit()
        detail_msg = f"Synced {synced_count} interviews with Google Calendar ({updated_count} updated, {cancelled_count} cancelled)."
        return {
            "synced_count": synced_count,
            "updated_count": updated_count,
            "cancelled_count": cancelled_count,
            "detail": detail_msg,
        }

    def get_or_create_recruiter_booking_link(
        self, session: Session, user_id: uuid.UUID
    ) -> SchedulingLinkRead:
        """
        Finds the most recent active candidate scheduling link for this recruiter,
        or creates a standard preview/booking link valid for 30 days.
        """
        now_utc = datetime.now(timezone.utc)
        link = session.exec(
            select(SchedulingLink)
            .where(
                SchedulingLink.user_id == user_id,
                SchedulingLink.status == SchedulingLinkStatus.active,
                SchedulingLink.expires_at > now_utc,
            )
            .order_by(SchedulingLink.created_at.desc())
        ).first()

        if link:
            cand = session.exec(select(Candidate).where(Candidate.id == link.candidate_id)).first()
            op = session.exec(select(JobOpening).where(JobOpening.id == link.opening_id)).first()
            return SchedulingLinkRead(
                id=link.id,
                token=link.token,
                user_id=link.user_id,
                candidate_id=link.candidate_id,
                candidate_name=cand.name if cand else "Candidate",
                candidate_email=cand.email if cand else "",
                opening_id=link.opening_id,
                opening_title=op.title if op else "Interview",
                slot_duration_minutes=link.slot_duration_minutes,
                status=link.status.value if hasattr(link.status, "value") else str(link.status),
                expires_at=ensure_utc(link.expires_at),
                public_url=f"/schedule/{link.token}",
                created_at=ensure_utc(link.created_at),
            )

        # If no active link exists, find an existing candidate
        candidate = session.exec(
            select(Candidate).where(Candidate.user_id == user_id).order_by(Candidate.created_at.desc())
        ).first()

        if not candidate:
            default_op = session.exec(
                select(JobOpening).where(JobOpening.user_id == user_id)
            ).first()
            if not default_op:
                default_op = JobOpening(
                    user_id=user_id,
                    title="General Application",
                    description="General introductory interview round.",
                    status=JobOpeningStatus.active,
                )
                session.add(default_op)
                session.commit()
                session.refresh(default_op)

            candidate = Candidate(
                user_id=user_id,
                opening_id=default_op.id,
                name="Applicant",
                email="applicant@example.com",
                cv_text="Standard applicant resume.",
                stage=CandidateStage.applied,
            )
            session.add(candidate)
            session.commit()
            session.refresh(candidate)

        avail = self.get_or_create_availability(session, user_id)
        slot_duration = avail.slot_duration_minutes or 30
        token = secrets.token_urlsafe(24)
        expires_at = now_utc + timedelta(days=30)

        new_link = SchedulingLink(
            token=token,
            user_id=user_id,
            candidate_id=candidate.id,
            opening_id=candidate.opening_id,
            slot_duration_minutes=slot_duration,
            status=SchedulingLinkStatus.active,
            expires_at=expires_at,
        )
        session.add(new_link)
        session.commit()
        session.refresh(new_link)

        op = session.exec(select(JobOpening).where(JobOpening.id == new_link.opening_id)).first()

        return SchedulingLinkRead(
            id=new_link.id,
            token=new_link.token,
            user_id=new_link.user_id,
            candidate_id=new_link.candidate_id,
            candidate_name=candidate.name,
            candidate_email=candidate.email,
            opening_id=new_link.opening_id,
            opening_title=op.title if op else "Interview",
            slot_duration_minutes=new_link.slot_duration_minutes,
            status=new_link.status.value if hasattr(new_link.status, "value") else str(new_link.status),
            expires_at=ensure_utc(new_link.expires_at),
            public_url=f"/schedule/{new_link.token}",
            created_at=ensure_utc(new_link.created_at),
        )

    async def get_availability_week_preview(
        self,
        session: Session,
        user_id: uuid.UUID,
        start_date_str: Optional[str] = None,
    ) -> AvailabilityWeekPreviewResponse:
        """
        Fetches a comprehensive 7-day week schedule view for the recruiter:
          1. Google Calendar busy events (purple)
          2. Platform booked interviews (green)
          3. Available free slots highlighted (blue)
          4. Active recruiter booking link for copying & preview
        """
        avail = self.get_or_create_availability(session, user_id)
        hr_tz_str = avail.timezone or "Asia/Karachi"
        try:
            hr_tz = ZoneInfo(hr_tz_str)
        except Exception:
            hr_tz = ZoneInfo("Asia/Karachi")

        now_hr = datetime.now(hr_tz)
        if start_date_str:
            try:
                parsed_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            except ValueError:
                parsed_date = now_hr.date()
        else:
            parsed_date = now_hr.date()

        # Align to Monday of the week
        monday = parsed_date - timedelta(days=parsed_date.weekday())
        sunday = monday + timedelta(days=6)

        week_start_str = monday.strftime("%Y-%m-%d")
        week_end_str = sunday.strftime("%Y-%m-%d")

        week_start_utc = datetime.combine(monday, datetime.min.time(), tzinfo=hr_tz).astimezone(timezone.utc)
        week_end_utc = datetime.combine(sunday, datetime.max.time(), tzinfo=hr_tz).astimezone(timezone.utc)

        # 1. Google Calendar busy ranges
        google_busy_ranges = await self.get_google_calendar_busy_ranges(
            session=session,
            user_id=user_id,
            time_min_utc=week_start_utc,
            time_max_utc=week_end_utc,
        )

        google_events: List[CalendarBusyEvent] = []
        for idx, (b_start, b_end) in enumerate(google_busy_ranges):
            b_start_local = b_start.astimezone(hr_tz)
            b_end_local = b_end.astimezone(hr_tz)
            google_events.append(
                CalendarBusyEvent(
                    id=f"gcal_{idx}_{int(b_start.timestamp())}",
                    title="Google Calendar Busy",
                    start_time=ensure_utc(b_start),
                    end_time=ensure_utc(b_end),
                    start_local=b_start_local.strftime("%I:%M %p"),
                    end_local=b_end_local.strftime("%I:%M %p"),
                    date_str=b_start_local.strftime("%Y-%m-%d"),
                )
            )

        # 2. DB booked interviews
        db_interviews = session.exec(
            select(Interview).where(
                Interview.user_id == user_id,
                Interview.status != InterviewStatus.cancelled,
                Interview.start_time <= week_end_utc,
                Interview.end_time >= week_start_utc,
            ).order_by(Interview.start_time.asc())
        ).all()

        platform_events: List[CalendarBookedInterview] = []
        db_busy_ranges: List[Tuple[datetime, datetime]] = []
        for inv in db_interviews:
            cand = session.exec(select(Candidate).where(Candidate.id == inv.candidate_id)).first()
            op = session.exec(select(JobOpening).where(JobOpening.id == inv.opening_id)).first()
            inv_start_utc = ensure_utc(inv.start_time)
            inv_end_utc = ensure_utc(inv.end_time)
            db_busy_ranges.append((inv_start_utc, inv_end_utc))
            inv_start_local = inv_start_utc.astimezone(hr_tz)
            inv_end_local = inv_end_utc.astimezone(hr_tz)

            platform_events.append(
                CalendarBookedInterview(
                    id=inv.id,
                    candidate_name=cand.name if cand else inv.title,
                    candidate_email=cand.email if cand else "",
                    opening_title=op.title if op else "Interview",
                    start_time=inv_start_utc,
                    end_time=inv_end_utc,
                    start_local=inv_start_local.strftime("%I:%M %p"),
                    end_local=inv_end_local.strftime("%I:%M %p"),
                    date_str=inv_start_local.strftime("%Y-%m-%d"),
                    meet_link=inv.meet_link,
                    status=inv.status.value if hasattr(inv.status, "value") else str(inv.status),
                )
            )

        # 3. Discretize free slots
        all_busy = google_busy_ranges + db_busy_ranges
        slot_duration = timedelta(minutes=avail.slot_duration_minutes)
        buffer_duration = timedelta(minutes=avail.buffer_minutes)
        step_duration = slot_duration + buffer_duration

        weekday_keys = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        weekly_config = avail.weekly_hours or {}
        blocked_dates_set = set(getattr(avail, "blocked_dates", []) or [])
        now_utc = datetime.now(timezone.utc)

        free_slots: List[CalendarFreeSlot] = []

        curr_date = monday
        while curr_date <= sunday:
            date_key_str = curr_date.strftime("%Y-%m-%d")
            if date_key_str in blocked_dates_set:
                curr_date += timedelta(days=1)
                continue

            day_key = weekday_keys[curr_date.weekday()]
            day_blocks = weekly_config.get(day_key, [])

            for block in day_blocks:
                start_str = block.get("start")
                end_str = block.get("end")
                if not start_str or not end_str:
                    continue

                try:
                    s_h, s_m = map(int, start_str.split(":"))
                    e_h, e_m = map(int, end_str.split(":"))
                except ValueError:
                    continue

                block_start_dt = datetime.combine(curr_date, datetime.min.time(), tzinfo=hr_tz).replace(
                    hour=s_h, minute=s_m
                )
                block_end_dt = datetime.combine(curr_date, datetime.min.time(), tzinfo=hr_tz).replace(
                    hour=e_h, minute=e_m
                )

                curr_slot_start = block_start_dt
                while curr_slot_start + slot_duration <= block_end_dt:
                    curr_slot_end = curr_slot_start + slot_duration
                    slot_start_utc = curr_slot_start.astimezone(timezone.utc)
                    slot_end_utc = curr_slot_end.astimezone(timezone.utc)

                    # Overlap check
                    is_busy = False
                    for b_start, b_end in all_busy:
                        if b_start < slot_end_utc and b_end > slot_start_utc:
                            is_busy = True
                            break

                    if not is_busy:
                        slot_start_local = slot_start_utc.astimezone(hr_tz)
                        slot_end_local = slot_end_utc.astimezone(hr_tz)
                        free_slots.append(
                            CalendarFreeSlot(
                                start_time=slot_start_utc,
                                end_time=slot_end_utc,
                                start_local=slot_start_local.strftime("%I:%M %p"),
                                end_local=slot_end_local.strftime("%I:%M %p"),
                                date_str=slot_start_local.strftime("%Y-%m-%d"),
                                is_past=(slot_start_utc < now_utc),
                            )
                        )

                    curr_slot_start += step_duration

            curr_date += timedelta(days=1)

        booking_link = self.get_or_create_recruiter_booking_link(session, user_id)

        return AvailabilityWeekPreviewResponse(
            week_start=week_start_str,
            week_end=week_end_str,
            timezone=hr_tz_str,
            slot_duration_minutes=avail.slot_duration_minutes,
            buffer_minutes=avail.buffer_minutes,
            google_busy_events=google_events,
            platform_interviews=platform_events,
            free_slots=free_slots,
            booking_link_token=booking_link.token,
            booking_link_url=booking_link.public_url,
        )

    def _to_interview_read(
        self,
        interview: Interview,
        candidate: Optional[Candidate] = None,
        opening: Optional[JobOpening] = None,
    ) -> InterviewRead:
        opening_title = opening.title if opening else (
            interview.opening.title if interview.opening else "Job Position"
        )
        return InterviewRead(
            id=interview.id,
            user_id=interview.user_id,
            candidate_id=interview.candidate_id,
            candidate_name=interview.candidate_name,
            candidate_email=interview.candidate_email,
            candidate_phone=interview.candidate_phone,
            opening_id=interview.opening_id,
            opening_title=opening_title,
            scheduling_link_id=interview.scheduling_link_id,
            round_type=getattr(interview, "round_type", "initial") or "initial",
            title=interview.title,
            start_time=ensure_utc(interview.start_time),
            end_time=ensure_utc(interview.end_time),
            timezone=interview.timezone,
            google_calendar_event_id=interview.google_calendar_event_id,
            meet_link=interview.meet_link,
            interviewer_email=interview.interviewer_email,
            status=interview.status.value if hasattr(interview.status, "value") else str(interview.status),
            result_status=getattr(interview, "result_status", None),
            feedback=getattr(interview, "feedback", None),
            result_recorded_at=ensure_utc(getattr(interview, "result_recorded_at", None)),
            cancellation_reason=interview.cancellation_reason,
            cancelled_at=ensure_utc(interview.cancelled_at),
            cancelled_by=interview.cancelled_by,
            reminder_24h_sent=interview.reminder_24h_sent,
            reminder_1h_sent=interview.reminder_1h_sent,
            created_at=ensure_utc(interview.created_at),
            updated_at=ensure_utc(interview.updated_at),
        )

    # ── 10. Interview Lifecycle & Result Recording ───────────────────────────

    def _try_send_gmail(
        self,
        session: Session,
        user_id: uuid.UUID,
        candidate_id: uuid.UUID,
        candidate_email: Optional[str],
        subject: str,
        body: str,
        template_name: str,
    ) -> None:
        """Safely dispatches email via Google Workspace integration if account is connected."""
        if not candidate_email or "@" not in candidate_email or candidate_email.endswith("@no-email.com"):
            return
        try:
            g_acct = session.exec(select(GoogleAccount).where(GoogleAccount.user_id == user_id)).first()
            if g_acct:
                g_service = GoogleService(session)
                g_service.send_email(
                    user_id=user_id,
                    request=GoogleSendEmailRequest(
                        candidate_id=candidate_id,
                        subject=subject,
                        body=body,
                        template_name=template_name,
                    ),
                )
        except Exception as exc:
            logger.info("Google Workspace email dispatch note for candidate %s (%s): %s", candidate_id, template_name, exc)

    def record_interview_result(
        self,
        session: Session,
        user_id: uuid.UUID,
        interview_id: uuid.UUID,
        result_status: str,
        feedback: Optional[str] = None,
    ) -> InterviewResultResponse:
        """
        Records the outcome of an interview (passed, failed, or no-show):
          - Passed (Initial)    -> Generates Behavioral scheduling link (45m) & dispatches Initial Passed email.
          - Passed (Behavioral) -> Generates Final scheduling link (60m) & dispatches Behavioral Passed email.
          - Passed (Final)      -> Generates Offer draft & moves stage to 'offer'. NEVER sends automatically!
          - Failed              -> Dispatches Rejection email & marks candidate 'rejected'.
          - No-show             -> Marks interview 'no_show'; stage preserved allowing rescheduling.
        Every decision and transition is recorded in the audit trail.
        """
        result_clean = result_status.lower().strip()
        if result_clean not in ("passed", "failed", "no_show"):
            raise HTTPException(
                status_code=400,
                detail="Invalid result_status. Must be one of: 'passed', 'failed', 'no_show'.",
            )

        interview = session.exec(
            select(Interview).where(
                Interview.id == interview_id,
                Interview.user_id == user_id,
            )
        ).first()
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found.")

        calendar_cache.clear_for_user(str(user_id))

        candidate = session.exec(
            select(Candidate).where(Candidate.id == interview.candidate_id)
        ).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found.")

        opening = session.exec(
            select(JobOpening).where(JobOpening.id == interview.opening_id)
        ).first()
        recruiter = session.exec(select(User).where(User.id == user_id)).first()

        onboarding = session.exec(
            select(OnboardingSetup).where(OnboardingSetup.user_id == user_id)
        ).first()
        hr_name = onboarding.hr_name if (onboarding and onboarding.hr_name) else (getattr(recruiter, "name", None) or "Our Team")
        company_name = onboarding.company_name if (onboarding and onboarding.company_name) else "Our Company"
        email_tone = onboarding.email_tone if (onboarding and onboarding.email_tone) else "warm_professional"
        user_templates = onboarding.templates if (onboarding and onboarding.templates) else {}
        defaults = get_default_templates(hr_name=hr_name, company_name=company_name, email_tone=email_tone)

        now_utc = datetime.now(timezone.utc)
        current_round = (getattr(interview, "round_type", "initial") or "initial").lower().strip()
        interview.result_status = result_clean
        interview.feedback = feedback
        interview.result_recorded_at = now_utc
        interview.updated_at = now_utc

        public_base = (getattr(settings, "FRONTEND_URL", None) or "http://localhost:3000").rstrip("/")
        role_title = opening.title if opening else "Position"

        # ── 1. Result: PASSED ──────────────────────────────────────────────────
        if result_clean == "passed":
            interview.status = InterviewStatus.passed

            # Case 1A: Initial Passed -> Behavioral invite (45m default)
            if current_round == "initial":
                next_round = "behavioral"
                dur = self.get_round_duration(session, user_id, "behavioral")
                next_link = self.create_scheduling_link(
                    session=session,
                    user_id=user_id,
                    candidate_id=candidate.id,
                    round_type="behavioral",
                    slot_duration_minutes=dur,
                    validity_days=7,
                )
                next_url = f"{public_base}/schedule/{next_link.token}"

                template_vars = {
                    "candidate_name": candidate.name,
                    "role": role_title,
                    "company": company_name,
                    "hr_name": hr_name,
                    "schedule_link": next_url,
                    "meet_link": next_url,
                    "interview_date": "Flexible self-scheduling",
                    "interview_time": f"{dur}-minute interview",
                    "job_details": opening.description if opening and opening.description else "",
                    "signature": f"Warm regards,\n{hr_name}\n{company_name}",
                }
                sub, _, body, _ = render_user_template(
                    session, user_id, "initial_passed", template_vars
                )

                # Record message
                msg = Message(
                    user_id=user_id,
                    candidate_id=candidate.id,
                    direction=MessageDirection.outbound,
                    message_type=MessageType.email,
                    channel="email",
                    body=body,
                    status=MessageStatus.sent,
                    hr_approved=True,
                    template_name="initial_passed",
                    template_variables={"subject": sub, "scheduling_url": next_url},
                    sent_at=now_utc,
                )
                session.add(msg)
                self._try_send_gmail(session, user_id, candidate.id, candidate.email, sub, body, "initial_passed")

                candidate.stage = CandidateStage.interview
                candidate.updated_at = now_utc
                session.add(candidate)
                session.add(interview)
                session.commit()
                session.refresh(interview)

                audit_log_service.record(
                    session=session,
                    user_id=user_id,
                    candidate_id=candidate.id,
                    opening_id=opening.id if opening else None,
                    action="interview_passed",
                    from_stage="scheduled",
                    to_stage="interview",
                    details=f"Initial Interview evaluated as Passed. Generated Behavioral scheduling link ({dur}m) and sent invitation.",
                )

                return InterviewResultResponse(
                    interview=self._to_interview_read(interview, candidate, opening),
                    interview_id=interview.id,
                    result=result_clean,
                    result_status="passed",
                    round_type=current_round,
                    candidate_id=candidate.id,
                    candidate_name=candidate.name,
                    next_action=f"Initial interview passed. Behavioral interview invitation ({dur}m) sent.",
                    message=f"Initial interview passed. Behavioral interview invitation ({dur}m) sent.",
                    next_round="behavioral",
                    scheduling_link_token=next_link.token,
                    scheduling_link_url=next_link.public_url,
                    next_scheduling_link=next_url,
                    email_dispatched="initial_passed",
                    offer_draft_ready=False,
                    offer_draft_created=False,
                )

            # Case 1B: Behavioral Passed -> Final invite (60m default)
            elif current_round == "behavioral":
                next_round = "final"
                dur = self.get_round_duration(session, user_id, "final")
                next_link = self.create_scheduling_link(
                    session=session,
                    user_id=user_id,
                    candidate_id=candidate.id,
                    round_type="final",
                    slot_duration_minutes=dur,
                    validity_days=7,
                )
                next_url = f"{public_base}/schedule/{next_link.token}"

                template_vars = {
                    "candidate_name": candidate.name,
                    "role": role_title,
                    "company": company_name,
                    "hr_name": hr_name,
                    "schedule_link": next_url,
                    "meet_link": next_url,
                    "interview_date": "Flexible self-scheduling",
                    "interview_time": f"{dur}-minute interview",
                    "job_details": opening.description if opening and opening.description else "",
                    "signature": f"Warm regards,\n{hr_name}\n{company_name}",
                }
                sub, _, body, _ = render_user_template(
                    session, user_id, "behavioral_passed", template_vars
                )

                # Record message
                msg = Message(
                    user_id=user_id,
                    candidate_id=candidate.id,
                    direction=MessageDirection.outbound,
                    message_type=MessageType.email,
                    channel="email",
                    body=body,
                    status=MessageStatus.sent,
                    hr_approved=True,
                    template_name="behavioral_passed",
                    template_variables={"subject": sub, "scheduling_url": next_url},
                    sent_at=now_utc,
                )
                session.add(msg)
                self._try_send_gmail(session, user_id, candidate.id, candidate.email, sub, body, "behavioral_passed")

                candidate.stage = CandidateStage.interview
                candidate.updated_at = now_utc
                session.add(candidate)
                session.add(interview)
                session.commit()
                session.refresh(interview)

                audit_log_service.record(
                    session=session,
                    user_id=user_id,
                    candidate_id=candidate.id,
                    opening_id=opening.id if opening else None,
                    action="interview_passed",
                    from_stage="scheduled",
                    to_stage="interview",
                    details=f"Behavioral Interview evaluated as Passed. Generated Final scheduling link ({dur}m) and sent invitation.",
                )

                return InterviewResultResponse(
                    interview=self._to_interview_read(interview, candidate, opening),
                    interview_id=interview.id,
                    result=result_clean,
                    result_status="passed",
                    round_type=current_round,
                    candidate_id=candidate.id,
                    candidate_name=candidate.name,
                    next_action=f"Behavioral interview passed. Final interview invitation ({dur}m) sent.",
                    message=f"Behavioral interview passed. Final interview invitation ({dur}m) sent.",
                    next_round="final",
                    scheduling_link_token=next_link.token,
                    scheduling_link_url=next_link.public_url,
                    next_scheduling_link=next_url,
                    email_dispatched="behavioral_passed",
                    offer_draft_ready=False,
                    offer_draft_created=False,
                )

            # Case 1C: Final Passed -> Creates Offer draft. NEVER SENDS AUTOMATICALLY!
            else:
                template_vars = {
                    "candidate_name": candidate.name,
                    "role": role_title,
                    "company": company_name,
                    "hr_name": hr_name,
                    "job_details": opening.description if opening and opening.description else "",
                    "signature": f"Warm regards,\n{hr_name}\n{company_name}",
                }
                offer_sub, _, offer_body, _ = render_user_template(
                    session, user_id, "offer_letter", template_vars
                )

                candidate.stage = CandidateStage.offer
                candidate.offer_letter_status = "draft"
                candidate.offer_letter_draft = {
                    "subject": offer_sub,
                    "body": offer_body,
                    "candidate_name": candidate.name,
                    "candidate_email": candidate.email,
                    "role": role_title,
                    "company": company_name,
                    "created_at": now_utc.isoformat(),
                }
                candidate.updated_at = now_utc

                session.add(candidate)
                session.add(interview)
                session.commit()
                session.refresh(interview)

                audit_log_service.record(
                    session=session,
                    user_id=user_id,
                    candidate_id=candidate.id,
                    opening_id=opening.id if opening else None,
                    action="interview_passed",
                    from_stage="scheduled",
                    to_stage="offer",
                    details="Final Interview evaluated as Passed. Offer letter draft created. Awaiting HR approval before sending.",
                )

                return InterviewResultResponse(
                    interview=self._to_interview_read(interview, candidate, opening),
                    interview_id=interview.id,
                    result=result_clean,
                    result_status="passed",
                    round_type=current_round,
                    candidate_id=candidate.id,
                    candidate_name=candidate.name,
                    next_action="Final interview passed. Offer letter draft generated and pending HR approval before sending.",
                    message="Final interview passed. Offer letter draft generated and pending HR approval before sending.",
                    next_round="offer",
                    scheduling_link_token=None,
                    scheduling_link_url=None,
                    next_scheduling_link=None,
                    email_dispatched=None,
                    offer_draft_ready=True,
                    offer_draft_created=True,
                )

        # ── 2. Result: FAILED ──────────────────────────────────────────────────
        elif result_clean == "failed":
            interview.status = InterviewStatus.failed
            candidate.stage = CandidateStage.rejected
            candidate.review_status = "rejected"
            candidate.updated_at = now_utc

            template_vars = {
                "candidate_name": candidate.name,
                "role": role_title,
                "company": company_name,
                "hr_name": hr_name,
                "signature": f"Warm regards,\n{hr_name}\n{company_name}",
            }
            sub, _, body, _ = render_user_template(
                session, user_id, "rejection", template_vars
            )

            msg = Message(
                user_id=user_id,
                candidate_id=candidate.id,
                direction=MessageDirection.outbound,
                message_type=MessageType.email,
                channel="email",
                body=body,
                status=MessageStatus.sent,
                hr_approved=True,
                template_name="rejection",
                template_variables={"subject": sub},
                sent_at=now_utc,
            )
            session.add(msg)
            self._try_send_gmail(session, user_id, candidate.id, candidate.email, sub, body, "rejection")

            try:
                agent_events.emit_sync(user_id, "status_changed", {
                    "candidate_id": str(candidate.id),
                    "candidate_name": candidate.name,
                    "status": "rejected",
                    "stage": "rejected",
                })
                agent_events.emit_sync(user_id, "email_sent", {
                    "candidate_id": str(candidate.id),
                    "candidate_name": candidate.name,
                    "template_id": "rejection",
                })
            except Exception:
                pass

            session.add(candidate)
            session.add(interview)
            session.commit()
            session.refresh(interview)

            audit_log_service.record(
                session=session,
                user_id=user_id,
                candidate_id=candidate.id,
                opening_id=opening.id if opening else None,
                action="interview_failed",
                from_stage="scheduled",
                to_stage="rejected",
                details=f"Interview ({current_round}) evaluated as Failed. Rejection email dispatched to {candidate.email}.",
            )

            return InterviewResultResponse(
                interview=self._to_interview_read(interview, candidate, opening),
                interview_id=interview.id,
                result=result_clean,
                result_status="failed",
                round_type=current_round,
                candidate_id=candidate.id,
                candidate_name=candidate.name,
                next_action="Interview evaluated as Failed. Rejection email sent to candidate.",
                message="Interview evaluated as Failed. Rejection email sent to candidate.",
                next_round=None,
                scheduling_link_token=None,
                scheduling_link_url=None,
                next_scheduling_link=None,
                email_dispatched="rejection",
                offer_draft_ready=False,
                offer_draft_created=False,
            )

        # ── 3. Result: NO-SHOW ─────────────────────────────────────────────────
        else:
            interview.status = InterviewStatus.no_show
            interview.updated_at = now_utc
            session.add(interview)
            session.commit()
            session.refresh(interview)

            audit_log_service.record(
                session=session,
                user_id=user_id,
                candidate_id=candidate.id,
                opening_id=opening.id if opening else None,
                action="interview_no_show",
                from_stage="scheduled",
                to_stage=candidate.stage.value if hasattr(candidate.stage, "value") else str(candidate.stage),
                details=f"Interview ({current_round}) marked as No-show. Candidate remains eligible for rescheduling.",
            )

            return InterviewResultResponse(
                interview=self._to_interview_read(interview, candidate, opening),
                interview_id=interview.id,
                result=result_clean,
                result_status="no_show",
                round_type=current_round,
                candidate_id=candidate.id,
                candidate_name=candidate.name,
                next_action="Interview marked as No-show. Candidate can reschedule if appropriate.",
                message="Interview marked as No-show. Candidate can reschedule if appropriate.",
                next_round=None,
                scheduling_link_token=None,
                scheduling_link_url=None,
                next_scheduling_link=None,
                email_dispatched=None,
                offer_draft_ready=False,
                offer_draft_created=False,
            )

    def get_offer_draft(
        self,
        session: Session,
        user_id: uuid.UUID,
        candidate_id: uuid.UUID,
    ) -> OfferDraftResponse:
        """
        Retrieves the Offer Letter draft for HR review.
        If no draft exists yet, populates default from the recruiter's offer_letter template.
        """
        candidate = session.exec(
            select(Candidate).where(
                Candidate.id == candidate_id,
                Candidate.user_id == user_id,
            )
        ).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found.")

        opening = session.exec(
            select(JobOpening).where(JobOpening.id == candidate.opening_id)
        ).first()
        recruiter = session.exec(select(User).where(User.id == user_id)).first()

        onboarding = session.exec(
            select(OnboardingSetup).where(OnboardingSetup.user_id == user_id)
        ).first()
        hr_name = onboarding.hr_name if (onboarding and onboarding.hr_name) else (getattr(recruiter, "name", None) or "Our Team")
        company_name = onboarding.company_name if (onboarding and onboarding.company_name) else "Our Company"
        email_tone = onboarding.email_tone if (onboarding and onboarding.email_tone) else "warm_professional"
        user_templates = onboarding.templates if (onboarding and onboarding.templates) else {}
        defaults = get_default_templates(hr_name=hr_name, company_name=company_name, email_tone=email_tone)

        role_title = opening.title if opening else "Position"

        draft_dict = candidate.offer_letter_draft or {}
        subject = draft_dict.get("subject")
        body = draft_dict.get("body")

        if not subject or not body:
            template_vars = {
                "candidate_name": candidate.name,
                "role": role_title,
                "company": company_name,
                "hr_name": hr_name,
                "job_details": opening.description if opening and opening.description else "",
                "signature": f"Warm regards,\n{hr_name}\n{company_name}",
            }
            subject, _, body, _ = render_user_template(
                session, user_id, "offer_letter", template_vars
            )
            candidate.offer_letter_draft = {
                "subject": subject,
                "body": body,
                "candidate_name": candidate.name,
                "candidate_email": candidate.email,
                "role": role_title,
                "company": company_name,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            if not candidate.offer_letter_status:
                candidate.offer_letter_status = "draft"
            session.add(candidate)
            session.commit()
            session.refresh(candidate)

        return OfferDraftResponse(
            candidate_id=candidate.id,
            candidate_name=candidate.name,
            candidate_email=candidate.email,
            opening_id=candidate.opening_id,
            opening_title=role_title,
            status=candidate.offer_letter_status or "draft",
            subject=subject,
            body=body,
            sent_at=ensure_utc(candidate.offer_letter_sent_at),
        )

    def approve_and_send_offer(
        self,
        session: Session,
        user_id: uuid.UUID,
        candidate_id: uuid.UUID,
        payload: OfferSendRequest,
    ) -> OfferDraftResponse:
        """
        HR approves and sends the Offer Letter email.
        STRICT SECURITY GATE: Offer letters are NEVER sent automatically without this explicit call.
        """
        candidate = session.exec(
            select(Candidate).where(
                Candidate.id == candidate_id,
                Candidate.user_id == user_id,
            )
        ).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found.")

        opening = session.exec(
            select(JobOpening).where(JobOpening.id == candidate.opening_id)
        ).first()

        subject = payload.subject.strip()
        body = payload.body.strip()
        if not subject or not body:
            raise HTTPException(status_code=400, detail="Offer letter subject and body cannot be empty.")

        now_utc = datetime.now(timezone.utc)
        candidate.stage = CandidateStage.offer
        candidate.offer_letter_status = "sent"
        candidate.offer_letter_sent_at = now_utc
        candidate.offer_letter_draft = {
            "subject": subject,
            "body": body,
            "candidate_name": candidate.name,
            "candidate_email": candidate.email,
            "role": opening.title if opening else "Position",
            "sent_at": now_utc.isoformat(),
        }
        candidate.updated_at = now_utc
        session.add(candidate)

        # Dispatch Message
        msg = Message(
            user_id=user_id,
            candidate_id=candidate.id,
            direction=MessageDirection.outbound,
            message_type=MessageType.email,
            channel="email",
            body=body,
            status=MessageStatus.sent,
            hr_approved=True,
            template_name="offer_letter",
            template_variables={"subject": subject},
            sent_at=now_utc,
        )
        session.add(msg)
        self._try_send_gmail(session, user_id, candidate.id, candidate.email, subject, body, "offer_letter")

        session.commit()
        session.refresh(candidate)

        audit_log_service.record(
            session=session,
            user_id=user_id,
            candidate_id=candidate.id,
            opening_id=candidate.opening_id,
            action="offer_letter_approved_and_sent",
            from_stage="offer",
            to_stage="offer",
            details=f"Offer letter approved and dispatched by HR to {candidate.email}. Subject: '{subject}'",
        )

        return OfferDraftResponse(
            candidate_id=candidate.id,
            candidate_name=candidate.name,
            candidate_email=candidate.email,
            opening_id=candidate.opening_id,
            opening_title=opening.title if opening else "Position",
            status="sent",
            subject=subject,
            body=body,
            sent_at=ensure_utc(candidate.offer_letter_sent_at),
        )


scheduling_service = SchedulingService()
