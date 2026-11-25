"use client";

import React, { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import {
  Calendar as CalendarIcon,
  Clock,
  Video,
  Settings,
  Filter,
  Search,
  ExternalLink,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  CalendarDays,
  ListFilter,
  User,
  Briefcase,
  Mail,
  Phone,
  ChevronLeft,
  ChevronRight,
  FileText,
  Sparkles,
  History,
  X,
  Zap,
  Check,
  CalendarCheck,
  ArrowRight,
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/ui/page-header";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { useToast } from "@/components/ui/use-toast";
import {
  schedulingApi,
  jobOpeningsApi,
  candidatesApi,
  InterviewRead,
  Candidate,
} from "@/lib/api";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AvailabilityTab } from "@/components/scheduling/availability-tab";
import { AvailabilityModal } from "@/components/scheduling/availability-modal";
import { RescheduleCancelModal } from "@/components/scheduling/reschedule-cancel-modal";
import { InterviewResultModal } from "@/components/scheduling/interview-result-modal";
import { OfferLetterModal } from "@/components/scheduling/offer-letter-modal";
import { CandidateDrawer } from "@/components/candidates/candidate-drawer";
import { GoogleCalendarView } from "@/components/scheduling/google-calendar-view";
import { useAgentEvents } from "@/lib/use-agent-events";

type ViewTab = "upcoming" | "calendar" | "past";
type CalendarMode = "week" | "month";

// Helper date functions for week/month calendar computation
function isSameDate(d1: Date, d2: Date) {
  return (
    d1.getFullYear() === d2.getFullYear() &&
    d1.getMonth() === d2.getMonth() &&
    d1.getDate() === d2.getDate()
  );
}

function isTodayDate(d: Date) {
  return isSameDate(d, new Date());
}

function getStartOfWeek(date: Date): Date {
  const d = new Date(date);
  const day = d.getDay();
  // Adjust so Monday is day 0, Sunday is day 6
  const diff = (day === 0 ? -6 : 1) - day;
  d.setDate(d.getDate() + diff);
  d.setHours(0, 0, 0, 0);
  return d;
}

function addDays(date: Date, days: number): Date {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
}

export default function InterviewsPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [mainTab, setMainTab] = useState<string>("sessions");

  // Subscribe to realtime agent & interview updates
  useAgentEvents();

  // 1. Filter and View States
  const [activeTab, setActiveTab] = useState<ViewTab>("calendar");
  const [calendarMode, setCalendarMode] = useState<CalendarMode>("week");
  const [currentCalendarDate, setCurrentCalendarDate] = useState<Date>(new Date());
  const [selectedOpeningId, setSelectedOpeningId] = useState<string>("all");
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [onlyTodayFilter, setOnlyTodayFilter] = useState(false);

  // 2. Modals and Drawers
  const [availabilityOpen, setAvailabilityOpen] = useState(false);
  const [actionInterview, setActionInterview] = useState<InterviewRead | null>(null);
  const [actionModalMode, setActionModalMode] = useState<"reschedule" | "cancel">("reschedule");
  const [resultModalInterview, setResultModalInterview] = useState<InterviewRead | null>(null);
  const [offerModalCandidateId, setOfferModalCandidateId] = useState<string | null>(null);
  const [offerModalCandidateName, setOfferModalCandidateName] = useState<string | undefined>(undefined);
  const [offerModalRoleTitle, setOfferModalRoleTitle] = useState<string | undefined>(undefined);
  const [drawerCandidate, setDrawerCandidate] = useState<Candidate | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [isLoadingCandidate, setIsLoadingCandidate] = useState(false);

  // 3. Fetch Job Openings for filter dropdown
  const { data: openingsData } = useQuery({
    queryKey: ["jobOpenings"],
    queryFn: () => jobOpeningsApi.list(undefined, 100),
  });

  // 4. Fetch All Interviews from Database
  const {
    data: rawInterviews = [],
    isLoading,
    isRefetching,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["interviewsList", selectedOpeningId, selectedStatus],
    queryFn: () =>
      schedulingApi.listInterviews({
        opening_id: selectedOpeningId !== "all" ? selectedOpeningId : undefined,
        status: selectedStatus !== "all" ? selectedStatus : undefined,
      }),
    refetchInterval: 15000,
  });

  // 5. Google Calendar Sync Mutation
  const syncCalendarMutation = useMutation({
    mutationFn: () => schedulingApi.syncCalendar(),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["interviewsList"] });
      toast({
        title: "Google Calendar Synced",
        description: data.detail || "Interview sessions reconciled with Google Calendar.",
      });
    },
    onError: (err: any) => {
      toast({
        title: "Calendar Sync Failed",
        description: err.response?.data?.detail || err.message || "Could not sync with Google Calendar.",
        variant: "destructive",
      });
    },
  });

  // 6. Handle Opening Candidate Scorecard in Drawer
  const handleOpenScorecard = async (candidateId: string) => {
    setIsLoadingCandidate(true);
    try {
      const cand = await candidatesApi.get(candidateId);
      setDrawerCandidate(cand);
      setDrawerOpen(true);
    } catch (err: any) {
      toast({
        title: "Failed to open scorecard",
        description: err.message || "Could not load candidate information.",
        variant: "destructive",
      });
    } finally {
      setIsLoadingCandidate(false);
    }
  };

  const openingItems = openingsData?.items || [];
  const now = new Date();

  // Search filtering
  const searchFilteredInterviews = useMemo(() => {
    return rawInterviews.filter((inv) => {
      if (onlyTodayFilter && !isTodayDate(new Date(inv.start_time))) {
        return false;
      }
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase();
      return (
        inv.candidate_name.toLowerCase().includes(q) ||
        inv.candidate_email.toLowerCase().includes(q) ||
        inv.opening_title.toLowerCase().includes(q) ||
        inv.title.toLowerCase().includes(q)
      );
    });
  }, [rawInterviews, searchQuery, onlyTodayFilter]);

  // View Segregation: Upcoming vs Past
  const { upcomingInterviews, pastInterviews, todayInterviews } = useMemo(() => {
    const upcoming: InterviewRead[] = [];
    const past: InterviewRead[] = [];
    const today: InterviewRead[] = [];

    const nowTime = now.getTime();

    for (const inv of searchFilteredInterviews) {
      const start = new Date(inv.start_time);
      const startTime = start.getTime();
      const end = new Date(inv.end_time);
      const endTime = end.getTime();

      if (isTodayDate(start) && inv.status !== "cancelled") {
        today.push(inv);
      }

      // Past condition: already ended OR status is completed/cancelled
      if (inv.status === "completed" || inv.status === "cancelled" || endTime < nowTime) {
        past.push(inv);
      } else {
        // Upcoming condition: currently happening or future
        upcoming.push(inv);
      }
    }

    // Sort upcoming soonest first (asc)
    upcoming.sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime());

    // Sort past most recent first (desc)
    past.sort((a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime());

    // Sort today chronologically
    today.sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime());

    return {
      upcomingInterviews: upcoming,
      pastInterviews: past,
      todayInterviews: today,
    };
  }, [searchFilteredInterviews]);

  // Calendar View Helpers
  const calendarRangeLabel = useMemo(() => {
    if (calendarMode === "week") {
      const startWeek = getStartOfWeek(currentCalendarDate);
      const endWeek = addDays(startWeek, 6);
      const startStr = startWeek.toLocaleDateString("en-US", { month: "short", day: "numeric" });
      const endStr = endWeek.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
      return `${startStr} – ${endStr}`;
    } else {
      return currentCalendarDate.toLocaleDateString("en-US", { month: "long", year: "numeric" });
    }
  }, [calendarMode, currentCalendarDate]);

  const handlePrevCalendar = () => {
    if (calendarMode === "week") {
      setCurrentCalendarDate((prev) => addDays(prev, -7));
    } else {
      setCurrentCalendarDate((prev) => {
        const next = new Date(prev);
        next.setMonth(next.getMonth() - 1);
        return next;
      });
    }
  };

  const handleNextCalendar = () => {
    if (calendarMode === "week") {
      setCurrentCalendarDate((prev) => addDays(prev, 7));
    } else {
      setCurrentCalendarDate((prev) => {
        const next = new Date(prev);
        next.setMonth(next.getMonth() + 1);
        return next;
      });
    }
  };

  const handleTodayCalendar = () => {
    setCurrentCalendarDate(new Date());
  };

  // Status Badge Rendering
  const renderStatusBadge = (status: string) => {
    switch (status) {
      case "scheduled":
        return (
          <Badge variant="outline" className="text-[10.5px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20 gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            Scheduled
          </Badge>
        );
      case "rescheduled":
        return (
          <Badge variant="outline" className="text-[10.5px] font-semibold bg-sky-500/10 text-sky-600 dark:text-sky-400 border-sky-500/20 gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-sky-500" />
            Rescheduled
          </Badge>
        );
      case "completed":
        return (
          <Badge variant="secondary" className="text-[10.5px] font-semibold bg-muted text-muted-foreground gap-1">
            <Check className="w-3 h-3 text-muted-foreground" />
            Completed
          </Badge>
        );
      case "passed":
        return (
          <Badge variant="outline" className="text-[10.5px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20 gap-1">
            <Check className="w-3 h-3 text-emerald-500" />
            Passed
          </Badge>
        );
      case "failed":
        return (
          <Badge variant="outline" className="text-[10.5px] font-semibold bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20 gap-1">
            <X className="w-3 h-3 text-rose-500" />
            Failed
          </Badge>
        );
      case "no_show":
        return (
          <Badge variant="outline" className="text-[10.5px] font-semibold bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20 gap-1">
            <Clock className="w-3 h-3 text-amber-500" />
            No-show
          </Badge>
        );
      case "cancelled":
        return (
          <Badge variant="outline" className="text-[10.5px] font-semibold bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20 gap-1">
            <X className="w-3 h-3 text-rose-500" />
            Cancelled
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" className="text-[10.5px] capitalize">
            {status}
          </Badge>
        );
    }
  };

  // ── Render Interview Card ──────────────────────────────────────────────────
  const renderInterviewCard = (inv: InterviewRead, isTodayHighlight = false) => {
    const start = new Date(inv.start_time);
    const end = new Date(inv.end_time);
    const durationMinutes = Math.round((end.getTime() - start.getTime()) / (1000 * 60));
    const isToday = isTodayDate(start);

    const round = (inv.round_type || "initial").toLowerCase();
    const roundLabel =
      round === "behavioral"
        ? "Behavioral (45m)"
        : round === "final"
        ? "Final (60m)"
        : "Initial (30m)";

    const dateFormatted = start.toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
      year: "numeric",
    });

    const timeRangeFormatted = `${start.toLocaleTimeString([], {
      hour: "numeric",
      minute: "2-digit",
    })} – ${end.toLocaleTimeString([], {
      hour: "numeric",
      minute: "2-digit",
    })}`;

    const hasMeetLink = Boolean(inv.meet_link && inv.meet_link.startsWith("http"));
    const isCancelled = inv.status === "cancelled";

    return (
      <div
        key={inv.id}
        className={`bg-card rounded-2xl border transition-all flex flex-col justify-between p-4 shadow-xs hover:shadow-card-hover ${
          isToday || isTodayHighlight
            ? "border-emerald-500/40 ring-1 ring-emerald-500/20 bg-emerald-500/[0.015]"
            : "border-border/70 dark:border-white/[0.08] hover:border-border"
        }`}
      >
        {/* Top Header: Badges & Timezone */}
        <div className="space-y-3">
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <div className="flex items-center gap-1.5 flex-wrap">
              {renderStatusBadge(inv.status)}
              <Badge variant="secondary" className="text-[10px] font-medium bg-muted/80 text-foreground">
                {roundLabel}
              </Badge>
              {inv.result_status && (
                <Badge
                  variant="outline"
                  className={`text-[9.5px] font-bold uppercase tracking-wider px-1.5 py-0 h-4.5 gap-1 ${
                    inv.result_status === "passed"
                      ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30"
                      : inv.result_status === "failed"
                      ? "bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30"
                      : "bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30"
                  }`}
                >
                  {inv.result_status === "passed" ? (
                    <Check className="w-2.5 h-2.5" />
                  ) : inv.result_status === "failed" ? (
                    <X className="w-2.5 h-2.5" />
                  ) : (
                    <Clock className="w-2.5 h-2.5" />
                  )}
                  <span>{inv.result_status === "no_show" ? "No-show" : inv.result_status}</span>
                </Badge>
              )}
              {isToday && (
                <Badge className="text-[9.5px] font-bold uppercase tracking-wider bg-emerald-600 text-white gap-1 px-1.5 py-0 h-4.5">
                  <Zap className="h-2.5 w-2.5 fill-white" />
                  <span>Today</span>
                </Badge>
              )}
            </div>
            <span className="text-[10.5px] text-muted-foreground font-mono flex items-center gap-1">
              <Clock className="w-3 h-3 text-muted-foreground/70" />
              <span>{inv.timezone || "UTC"}</span>
            </span>
          </div>

          {/* Candidate Info */}
          <div className="flex items-start gap-2.5">
            <div className="w-8 h-8 rounded-full bg-primary/10 text-primary font-bold flex items-center justify-center text-xs shrink-0 mt-0.5">
              {inv.candidate_name ? inv.candidate_name.charAt(0).toUpperCase() : "C"}
            </div>
            <div className="min-w-0 flex-1">
              <h4 className="text-xs font-bold text-foreground truncate">
                {inv.candidate_name}
              </h4>
              <p className="text-[11px] text-muted-foreground flex items-center gap-1 truncate mt-0.5">
                <Briefcase className="w-3 h-3 text-primary shrink-0" />
                <span className="truncate">{inv.opening_title}</span>
              </p>
            </div>
          </div>

          {/* Date, Time & Duration Card */}
          <div className="p-2.5 rounded-xl bg-muted/40 border border-border/60 space-y-1">
            <div className="text-xs font-semibold text-foreground flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <CalendarIcon className="w-3.5 h-3.5 text-primary" />
                <span>{dateFormatted}</span>
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-md bg-background border border-border/80 text-muted-foreground">
                {durationMinutes}m
              </span>
            </div>
            <div className="text-[11px] text-muted-foreground font-mono flex items-center gap-1.5">
              <Clock className="w-3 h-3" />
              <span>{timeRangeFormatted}</span>
            </div>
          </div>

          {/* Candidate Contact */}
          <div className="space-y-1 text-[11px] text-muted-foreground pt-0.5">
            <div className="flex items-center gap-1.5 truncate">
              <Mail className="w-3 h-3 shrink-0 text-muted-foreground/70" />
              <span className="truncate">{inv.candidate_email}</span>
            </div>
            {inv.candidate_phone && (
              <div className="flex items-center gap-1.5 truncate">
                <Phone className="w-3 h-3 shrink-0 text-muted-foreground/70" />
                <span>{inv.candidate_phone}</span>
              </div>
            )}
          </div>

          {/* Feedback note preview if recorded */}
          {inv.feedback && (
            <div className="p-2 rounded-lg bg-muted/30 border border-border/50 text-[11px] text-muted-foreground italic">
              &ldquo;{inv.feedback}&rdquo;
            </div>
          )}

          {/* Cancellation Notice */}
          {isCancelled && inv.cancellation_reason && (
            <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-[11px] text-rose-600 dark:text-rose-400 italic">
              <span className="font-semibold not-italic">Cancelled: </span>
              {inv.cancellation_reason}
            </div>
          )}
        </div>

        {/* Action Blocks */}
        <div className="space-y-2 mt-3">
          {/* Lifecycle Result Evaluation Section */}
          {!isCancelled && (
            <div className="pt-2.5 border-t border-border/60 flex items-center justify-between gap-1.5 flex-wrap">
              <div className="flex items-center gap-1">
                <span className="text-[10.5px] font-semibold text-muted-foreground mr-1">Result:</span>
                <Button
                  size="sm"
                  variant={inv.result_status === "passed" ? "secondary" : "outline"}
                  onClick={() => setResultModalInterview(inv)}
                  className={`h-6.5 px-2 text-[10.5px] font-semibold gap-1 ${
                    inv.result_status === "passed"
                      ? "bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border-emerald-500/40"
                      : "hover:bg-emerald-500/10 hover:text-emerald-600 hover:border-emerald-500/30"
                  }`}
                  title="Mark Passed -> triggers next round invite or creates offer draft"
                >
                  <Check className="w-3 h-3 text-emerald-500" />
                  <span>Passed</span>
                </Button>

                <Button
                  size="sm"
                  variant={inv.result_status === "failed" ? "secondary" : "outline"}
                  onClick={() => setResultModalInterview(inv)}
                  className={`h-6.5 px-2 text-[10.5px] font-semibold gap-1 ${
                    inv.result_status === "failed"
                      ? "bg-rose-500/20 text-rose-600 dark:text-rose-400 border-rose-500/40"
                      : "hover:bg-rose-500/10 hover:text-rose-600 hover:border-rose-500/30"
                  }`}
                  title="Mark Failed -> triggers rejection email"
                >
                  <X className="w-3 h-3 text-rose-500" />
                  <span>Failed</span>
                </Button>

                <Button
                  size="sm"
                  variant={inv.result_status === "no_show" ? "secondary" : "outline"}
                  onClick={() => setResultModalInterview(inv)}
                  className={`h-6.5 px-2 text-[10.5px] font-semibold gap-1 ${
                    inv.result_status === "no_show"
                      ? "bg-amber-500/20 text-amber-600 dark:text-amber-400 border-amber-500/40"
                      : "hover:bg-amber-500/10 hover:text-amber-600 hover:border-amber-500/30"
                  }`}
                  title="Mark No-show -> preserves stage allowing reschedule"
                >
                  <Clock className="w-3 h-3 text-amber-500" />
                  <span>No-show</span>
                </Button>
              </div>

              {/* Review Offer Button: shown for final round & passed */}
              {round === "final" && inv.result_status === "passed" && (
                <Button
                  size="sm"
                  onClick={() => {
                    setOfferModalCandidateId(inv.candidate_id);
                    setOfferModalCandidateName(inv.candidate_name);
                    setOfferModalRoleTitle(inv.opening_title);
                  }}
                  className="h-6.5 px-2.5 text-[10.5px] font-bold bg-primary hover:bg-primary/90 text-primary-foreground gap-1 shadow-xs"
                  title="Review Offer Letter draft and approve sending"
                >
                  <Sparkles className="w-3 h-3" />
                  <span>Review Offer</span>
                </Button>
              )}
            </div>
          )}

          {/* Bottom Actions Footer */}
          <div className="pt-2 border-t border-border/40 flex items-center justify-between gap-1.5">
            {/* Left: Google Meet Join Button */}
            {hasMeetLink && !isCancelled ? (
              <a
                href={inv.meet_link!}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs transition shadow-xs"
                title="Open Google Meet room"
              >
                <Video className="w-3.5 h-3.5" />
                <span>Join Meet</span>
                <ExternalLink className="w-2.5 h-2.5 opacity-70" />
              </a>
            ) : (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleOpenScorecard(inv.candidate_id)}
                className="h-7 text-[11px] font-semibold gap-1 text-primary border-primary/20 hover:bg-primary/5"
              >
                <FileText className="w-3 h-3" />
                <span>Scorecard</span>
              </Button>
            )}

            {/* Right Action Buttons */}
            <div className="flex items-center gap-1">
              {hasMeetLink && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleOpenScorecard(inv.candidate_id)}
                  className="h-7 px-2 text-[11px] font-medium text-muted-foreground hover:text-foreground"
                  title="View candidate scorecard and interview notes"
                >
                  <FileText className="w-3 h-3 mr-1" />
                  <span>Scorecard</span>
                </Button>
              )}

              {!isCancelled && (
                <>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      setActionInterview(inv);
                      setActionModalMode("reschedule");
                    }}
                    className="h-7 px-2 text-[11px] font-medium text-muted-foreground hover:text-foreground"
                  >
                    Reschedule
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      setActionInterview(inv);
                      setActionModalMode("cancel");
                    }}
                    className="h-7 px-2 text-[11px] font-medium text-rose-500 hover:text-rose-600 hover:bg-rose-500/10"
                  >
                    Cancel
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <AppShell title="Interviews">
      <div className="max-w-7xl mx-auto space-y-4 pb-16">
        {/* ── Page Header ─────────────────────────────────────────────── */}
        <PageHeader
          title="Interviews"
          description="Track confirmed interview sessions, Google Meet rooms, and automated calendar scheduling."
          badge={
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="gap-1 font-mono text-[11px] bg-card">
                <CalendarIcon className="h-3 w-3 text-primary" />
                <span>{rawInterviews.length} Total Sessions</span>
              </Badge>
              {todayInterviews.length > 0 && (
                <Badge className="gap-1 font-mono text-[11px] bg-emerald-600 text-white font-bold border-0 animate-pulse">
                  <Zap className="h-3 w-3 fill-white" />
                  <span>{todayInterviews.length} Today</span>
                </Badge>
              )}
            </div>
          }
          actions={
            <div className="flex items-center gap-2">
              {/* Google Calendar Sync Button */}
              <Button
                variant="outline"
                size="sm"
                onClick={() => syncCalendarMutation.mutate()}
                disabled={syncCalendarMutation.isPending || isRefetching}
                className="h-8 gap-1.5 text-xs font-semibold"
                title="Synchronize Google Calendar events created by the app"
              >
                <RefreshCw
                  className={`w-3.5 h-3.5 text-primary ${
                    syncCalendarMutation.isPending || isRefetching ? "animate-spin" : ""
                  }`}
                />
                <span className="hidden sm:inline">Sync Google Calendar</span>
              </Button>

              {/* Weekly Availability Rules */}
              <Button
                size="sm"
                variant="outline"
                onClick={() => setAvailabilityOpen(true)}
                className="h-8 gap-1.5 text-xs font-semibold"
              >
                <Settings className="w-3.5 h-3.5 text-muted-foreground" />
                <span className="hidden sm:inline">Availability Rules</span>
              </Button>
            </div>
          }
        />

        <Tabs value={mainTab} onValueChange={setMainTab} className="space-y-6">
          <TabsList className="bg-muted/40 p-1 border border-border/70 rounded-xl flex gap-1 w-full justify-start overflow-x-auto">
            <TabsTrigger value="sessions" className="gap-2 text-xs font-semibold px-4 py-2 rounded-lg data-[state=active]:bg-background data-[state=active]:shadow-xs">
              <CalendarIcon className="w-3.5 h-3.5 text-primary" />
              <span>Scheduled Sessions ({rawInterviews.length})</span>
            </TabsTrigger>
            <TabsTrigger value="availability" className="gap-2 text-xs font-semibold px-4 py-2 rounded-lg data-[state=active]:bg-background data-[state=active]:shadow-xs">
              <Clock className="w-3.5 h-3.5 text-amber-500" />
              <span>Working Availability & Schedule</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="sessions" className="space-y-4">
            {/* ── Clear Explanation Banner ─────────────────────────────────── */}
        <div className="rounded-2xl border border-primary/20 bg-primary/[0.035] p-3.5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-xs">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-primary/10 text-primary flex items-center justify-center shrink-0">
              <CalendarCheck className="w-4 h-4" />
            </div>
            <div>
              <p className="text-xs font-semibold text-foreground">
                Interviews booked by candidates through your schedule link appear here and in your Google Calendar.
              </p>
              <p className="text-[11px] text-muted-foreground mt-0.5">
                Google Meet video conference links and reminders are automatically synchronized both ways.
              </p>
            </div>
          </div>

          {todayInterviews.length > 0 && (
            <Button
              size="sm"
              variant={onlyTodayFilter ? "default" : "outline"}
              onClick={() => setOnlyTodayFilter(!onlyTodayFilter)}
              className="h-7 text-xs font-semibold gap-1.5 shrink-0"
            >
              <Zap className="w-3 h-3 fill-current" />
              <span>{onlyTodayFilter ? "Show All Days" : `Filter Today (${todayInterviews.length})`}</span>
            </Button>
          )}
        </div>

        {/* ── Controls Bar: Search, Filters & View Toggles ─────────────── */}
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 bg-card p-3 rounded-2xl border border-border/70 dark:border-white/[0.08] shadow-xs">
          {/* Search Bar */}
          <div className="relative flex-1 max-w-sm">
            <Search className="w-3.5 h-3.5 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
            <Input
              placeholder="Search candidate name, email, role..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 text-xs h-8 bg-background border-border/70"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground text-xs"
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </div>

          {/* Filters & View Switcher */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Opening Dropdown */}
            <select
              value={selectedOpeningId}
              onChange={(e) => setSelectedOpeningId(e.target.value)}
              className="bg-background border border-border/70 rounded-xl px-2.5 py-1 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary cursor-pointer h-8"
            >
              <option value="all">All Requisitions</option>
              {openingItems.map((op) => (
                <option key={op.id} value={op.id}>
                  {op.title}
                </option>
              ))}
            </select>

            {/* Status Dropdown */}
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="bg-background border border-border/70 rounded-xl px-2.5 py-1 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary cursor-pointer h-8"
            >
              <option value="all">All Statuses</option>
              <option value="scheduled">Scheduled</option>
              <option value="rescheduled">Rescheduled</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>

            {/* View Switcher: Upcoming, Calendar, Past */}
            <div className="flex bg-muted/60 p-0.5 rounded-xl border border-border/70 h-8 items-center">
              <button
                onClick={() => setActiveTab("upcoming")}
                className={`px-3 py-1 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                  activeTab === "upcoming"
                    ? "bg-background text-foreground shadow-xs"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <ListFilter className="w-3.5 h-3.5" />
                <span>Upcoming</span>
                <span className="text-[10px] font-mono px-1 py-0.2 rounded-full bg-primary/10 text-primary font-bold">
                  {upcomingInterviews.length}
                </span>
              </button>

              <button
                onClick={() => setActiveTab("calendar")}
                className={`px-3 py-1 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                  activeTab === "calendar"
                    ? "bg-background text-foreground shadow-xs"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <CalendarDays className="w-3.5 h-3.5" />
                <span>Calendar</span>
              </button>

              <button
                onClick={() => setActiveTab("past")}
                className={`px-3 py-1 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                  activeTab === "past"
                    ? "bg-background text-foreground shadow-xs"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <History className="w-3.5 h-3.5" />
                <span>Past</span>
                <span className="text-[10px] font-mono px-1 py-0.2 rounded-full bg-muted text-muted-foreground font-bold">
                  {pastInterviews.length}
                </span>
              </button>
            </div>
          </div>
        </div>

        {/* ── Content View Rendering ───────────────────────────────────── */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="bg-card rounded-2xl border border-border/70 p-4 space-y-3">
                <div className="flex justify-between items-center">
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-3 w-16" />
                </div>
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
                <Skeleton className="h-14 w-full rounded-xl" />
                <div className="flex justify-between pt-2">
                  <Skeleton className="h-7 w-24 rounded-lg" />
                  <Skeleton className="h-7 w-16 rounded-lg" />
                </div>
              </div>
            ))}
          </div>
        ) : isError ? (
          <div className="py-16">
            <ErrorState
              title="Failed to load scheduled interviews"
              message={(error as any)?.message || "Please check your network connection and retry."}
              onRetry={() => refetch()}
            />
          </div>
        ) : activeTab === "upcoming" ? (
          /* ── 1. UPCOMING LIST VIEW ────────────────────────────────────── */
          <div className="space-y-6">
            {/* If Today has interviews, highlight section */}
            {todayInterviews.length > 0 && !onlyTodayFilter && (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-emerald-500 fill-emerald-500" />
                  <h3 className="font-bold text-xs uppercase tracking-wider text-foreground">
                    Today's Schedule ({todayInterviews.length})
                  </h3>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {todayInterviews.map((inv) => renderInterviewCard(inv, true))}
                </div>
              </div>
            )}

            {/* Upcoming Ahead Section */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-xs uppercase tracking-wider text-muted-foreground">
                  {todayInterviews.length > 0 && !onlyTodayFilter ? "Upcoming Ahead" : "Upcoming Interviews"}
                </h3>
                <span className="text-xs text-muted-foreground font-mono">
                  {upcomingInterviews.length} Scheduled
                </span>
              </div>

              {upcomingInterviews.length === 0 ? (
                <EmptyState
                  icon={CalendarIcon}
                  title="No Upcoming Interviews"
                  description="When candidates book an interview slot using your self-scheduling link, confirmed sessions with Google Meet links will appear right here."
                  actionText="Open Candidate Pipeline"
                  onAction={() => (window.location.href = "/pipeline")}
                />
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {upcomingInterviews.map((inv) => renderInterviewCard(inv))}
                </div>
              )}
            </div>
          </div>
        ) : activeTab === "calendar" ? (
          /* ── 2. GOOGLE CALENDAR VIEW (FullCalendar) ───────────────────── */
          <GoogleCalendarView
            onReschedule={(inv) => {
              setActionInterview(inv);
              setActionModalMode("reschedule");
            }}
            onCancel={(inv) => {
              setActionInterview(inv);
              setActionModalMode("cancel");
            }}
            onRecordResult={(inv) => {
              setResultModalInterview(inv);
            }}
            onOpenScorecard={(candidateId) => {
              handleOpenScorecard(candidateId);
            }}
          />
        ) : (
          /* ── 3. PAST LIST VIEW ────────────────────────────────────────── */
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-xs uppercase tracking-wider text-muted-foreground">
                Past Completed & Cancelled Interviews
              </h3>
              <span className="text-xs text-muted-foreground font-mono">
                {pastInterviews.length} Sessions Logged
              </span>
            </div>

            {pastInterviews.length === 0 ? (
              <EmptyState
                icon={History}
                title="No Past Interviews Recorded"
                description="Completed interview sessions or cancelled meetings will be archived in this view."
              />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {pastInterviews.map((inv) => renderInterviewCard(inv))}
              </div>
            )}
          </div>
        )}
          </TabsContent>

          <TabsContent value="availability" className="space-y-4">
            <AvailabilityTab />
          </TabsContent>
        </Tabs>
      </div>

      {/* Availability Configuration Drawer/Modal */}
      <AvailabilityModal
        isOpen={availabilityOpen}
        onClose={() => setAvailabilityOpen(false)}
      />

      {/* Reschedule / Cancel Modal */}
      {actionInterview && (
        <RescheduleCancelModal
          interview={actionInterview}
          mode={actionModalMode}
          isOpen={!!actionInterview}
          onClose={() => setActionInterview(null)}
        />
      )}

      {/* Record Interview Result Modal */}
      <InterviewResultModal
        interview={resultModalInterview}
        isOpen={!!resultModalInterview}
        onClose={() => setResultModalInterview(null)}
        onOpenOfferReview={(candidateId) => {
          setOfferModalCandidateId(candidateId);
          if (resultModalInterview) {
            setOfferModalCandidateName(resultModalInterview.candidate_name);
            setOfferModalRoleTitle(resultModalInterview.opening_title);
          }
        }}
      />

      {/* Offer Letter Review & Dispatch Modal */}
      <OfferLetterModal
        candidateId={offerModalCandidateId}
        candidateName={offerModalCandidateName}
        roleTitle={offerModalRoleTitle}
        isOpen={!!offerModalCandidateId}
        onClose={() => {
          setOfferModalCandidateId(null);
          setOfferModalCandidateName(undefined);
          setOfferModalRoleTitle(undefined);
        }}
      />

      {/* Candidate Scorecard Drawer */}
      {drawerCandidate && (
        <CandidateDrawer
          candidate={drawerCandidate}
          open={drawerOpen}
          onClose={() => {
            setDrawerOpen(false);
            setDrawerCandidate(null);
          }}
          onCandidateUpdated={() => {
            refetch();
          }}
        />
      )}
    </AppShell>
  );
}
