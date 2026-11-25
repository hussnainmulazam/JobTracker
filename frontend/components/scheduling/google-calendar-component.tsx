"use client";

import React, { useState, useMemo, useEffect, useRef } from "react";
import {
  ChevronLeft,
  ChevronRight,
  Clock,
  RefreshCw,
  Video,
  User,
  Briefcase,
  Calendar as CalendarIcon,
  CheckCircle2,
  ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  CalendarEventItem,
  CalendarEventsResponse,
  BusinessHourPeriod,
} from "@/lib/api";

interface GoogleCalendarComponentProps {
  data: CalendarEventsResponse;
  onEventClick: (event: CalendarEventItem) => void;
  onDatesChange: (start: string, end: string) => void;
  onRefresh?: () => void;
  isRefetching?: boolean;
}

type CalendarViewMode = "month" | "week" | "day" | "agenda";

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const START_HOUR = 8; // 8:00 AM
const END_HOUR = 20; // 8:00 PM
const TOTAL_HOURS = END_HOUR - START_HOUR;

export default function GoogleCalendarComponent({
  data,
  onEventClick,
  onDatesChange,
  onRefresh,
  isRefetching = false,
}: GoogleCalendarComponentProps) {
  // Current anchor date
  const [currentDate, setCurrentDate] = useState<Date>(() => new Date());
  const [currentView, setCurrentView] = useState<CalendarViewMode>("week");
  const [is24Hour, setIs24Hour] = useState<boolean>(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("calendar_time_format") === "24h";
    }
    return false;
  });

  // Current real-time clock for now indicator
  const [nowDate, setNowDate] = useState<Date>(() => new Date());
  useEffect(() => {
    const timer = setInterval(() => setNowDate(new Date()), 60000);
    return () => clearInterval(timer);
  }, []);

  const toggleTimeFormat = () => {
    setIs24Hour((prev) => {
      const next = !prev;
      if (typeof window !== "undefined") {
        localStorage.setItem("calendar_time_format", next ? "24h" : "12h");
      }
      return next;
    });
  };

  // Helper date utilities
  const isSameDay = (d1: Date, d2: Date) =>
    d1.getFullYear() === d2.getFullYear() &&
    d1.getMonth() === d2.getMonth() &&
    d1.getDate() === d2.getDate();

  const isToday = (d: Date) => isSameDay(d, nowDate);

  // Format time label (e.g. "9 AM" or "09:00")
  const formatHourLabel = (hour: number) => {
    if (is24Hour) {
      return `${String(hour).padStart(2, "0")}:00`;
    }
    const h = hour % 12 === 0 ? 12 : hour % 12;
    const ampm = hour < 12 ? "AM" : "PM";
    return `${h} ${ampm}`;
  };

  // Format event time (e.g. "10:30 AM")
  const formatEventTime = (d: Date) => {
    return d.toLocaleTimeString([], {
      hour: is24Hour ? "2-digit" : "numeric",
      minute: "2-digit",
      hour12: !is24Hour,
    });
  };

  // Compute Monday of the week for given date
  const getMonday = (d: Date): Date => {
    const date = new Date(d);
    const day = date.getDay();
    const diff = (day === 0 ? -6 : 1) - day;
    date.setDate(date.getDate() + diff);
    date.setHours(0, 0, 0, 0);
    return date;
  };

  // Days of current week (7 days Mon -> Sun)
  const weekDays = useMemo(() => {
    const monday = getMonday(currentDate);
    return Array.from({ length: 7 }, (_, i) => {
      const day = new Date(monday);
      day.setDate(monday.getDate() + i);
      return day;
    });
  }, [currentDate]);

  // Days of current month grid (complete 6x7 or 5x7 matrix starting on Monday)
  const monthDays = useMemo(() => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();

    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);

    // Find the Monday on or before firstDay
    const start = getMonday(firstDay);

    const days: { date: Date; isCurrentMonth: boolean }[] = [];
    let cur = new Date(start);

    // Generate up to 42 days (6 full weeks)
    while (days.length < 42) {
      days.push({
        date: new Date(cur),
        isCurrentMonth: cur.getMonth() === month,
      });
      cur.setDate(cur.getDate() + 1);
      // If we finished at least 35 days and passed the end of month on Sunday, stop
      if (days.length >= 35 && cur.getMonth() !== month && cur.getDay() === 1) {
        break;
      }
    }
    return days;
  }, [currentDate]);

  // Navigation handlers
  const navPrev = () => {
    const next = new Date(currentDate);
    if (currentView === "month") {
      next.setMonth(next.getMonth() - 1);
    } else if (currentView === "week") {
      next.setDate(next.getDate() - 7);
    } else {
      next.setDate(next.getDate() - 1);
    }
    setCurrentDate(next);
  };

  const navNext = () => {
    const next = new Date(currentDate);
    if (currentView === "month") {
      next.setMonth(next.getMonth() + 1);
    } else if (currentView === "week") {
      next.setDate(next.getDate() + 7);
    } else {
      next.setDate(next.getDate() + 1);
    }
    setCurrentDate(next);
  };

  const navToday = () => {
    setCurrentDate(new Date());
  };

  // Title string for Google Calendar header
  const headerTitle = useMemo(() => {
    if (currentView === "month") {
      return currentDate.toLocaleDateString("en-US", {
        month: "long",
        year: "numeric",
      });
    }
    if (currentView === "week") {
      const mon = weekDays[0];
      const sun = weekDays[6];
      const sameMonth = mon.getMonth() === sun.getMonth();
      const sameYear = mon.getFullYear() === sun.getFullYear();

      if (sameMonth && sameYear) {
        return `${mon.toLocaleDateString("en-US", { month: "short" })} ${mon.getDate()} – ${sun.getDate()}, ${mon.getFullYear()}`;
      }
      return `${mon.toLocaleDateString("en-US", { month: "short", day: "numeric" })} – ${sun.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}`;
    }
    return currentDate.toLocaleDateString("en-US", {
      weekday: "long",
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }, [currentDate, currentView, weekDays]);

  // Notify parent of visible range
  useEffect(() => {
    if (!onDatesChange) return;
    if (currentView === "month") {
      const start = monthDays[0]?.date;
      const end = monthDays[monthDays.length - 1]?.date;
      if (start && end) {
        onDatesChange(start.toISOString(), end.toISOString());
      }
    } else if (currentView === "week") {
      const start = weekDays[0];
      const end = weekDays[6];
      if (start && end) {
        onDatesChange(start.toISOString(), end.toISOString());
      }
    } else {
      const start = new Date(currentDate);
      start.setHours(0, 0, 0, 0);
      const end = new Date(currentDate);
      end.setHours(23, 59, 59, 999);
      onDatesChange(start.toISOString(), end.toISOString());
    }
  }, [currentDate, currentView, monthDays, weekDays, onDatesChange]);

  // Map events to parsed start/end dates
  const parsedEvents = useMemo(() => {
    return (data.events || []).map((evt) => {
      const s = new Date(evt.start);
      const e = new Date(evt.end || evt.start);
      return {
        ...evt,
        startDate: s,
        endDate: e,
      };
    });
  }, [data.events]);

  // Filter events for a specific day
  const getEventsForDay = (targetDay: Date) => {
    return parsedEvents.filter((evt) => isSameDay(evt.startDate, targetDay));
  };

  // Calculate now indicator position for week/day view
  const nowIndicatorTop = useMemo(() => {
    const hours = nowDate.getHours() + nowDate.getMinutes() / 60;
    if (hours < START_HOUR || hours > END_HOUR) return null;
    return ((hours - START_HOUR) / TOTAL_HOURS) * 100;
  }, [nowDate]);

  return (
    <div className="bg-card rounded-2xl border border-border/70 dark:border-white/[0.08] shadow-xs flex flex-col overflow-hidden">
      {/* ── 1. Google Calendar Header Toolbar ──────────────────────── */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-3.5 sm:px-4 sm:py-3 border-b border-border/70 bg-card">
        {/* Left: Today, Prev/Next & Title */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={navToday}
            className="h-8 px-3 text-xs font-semibold rounded-lg border-border/80 hover:bg-muted/60"
          >
            Today
          </Button>

          <div className="flex items-center">
            <Button
              variant="ghost"
              size="sm"
              onClick={navPrev}
              className="h-8 w-8 p-0 rounded-lg text-muted-foreground hover:text-foreground"
              title="Previous"
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={navNext}
              className="h-8 w-8 p-0 rounded-lg text-muted-foreground hover:text-foreground"
              title="Next"
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>

          <h2 className="text-sm sm:text-base font-bold text-foreground ml-1 tracking-tight truncate">
            {headerTitle}
          </h2>
        </div>

        {/* Right: Time format, Refresh, and View Toggles */}
        <div className="flex items-center gap-2 shrink-0 self-end sm:self-auto">
          {/* 12h vs 24h Toggle */}
          <Button
            variant="outline"
            size="sm"
            onClick={toggleTimeFormat}
            className="h-8 px-2.5 text-[11px] font-mono font-semibold rounded-lg text-muted-foreground hover:text-foreground gap-1 border-border/70"
            title="Toggle between 12-hour and 24-hour format"
          >
            <Clock className="w-3 h-3" />
            <span>{is24Hour ? "24h" : "12h"}</span>
          </Button>

          {/* Refresh Button */}
          {onRefresh && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRefresh}
              disabled={isRefetching}
              className="h-8 w-8 p-0 rounded-lg border-border/70 text-muted-foreground hover:text-foreground"
              title="Refresh Calendar"
            >
              <RefreshCw
                className={`w-3.5 h-3.5 ${isRefetching ? "animate-spin" : ""}`}
              />
            </Button>
          )}

          {/* View Toggles: Month / Week / Day / Agenda */}
          <div className="flex bg-muted/60 p-0.5 rounded-xl border border-border/70 h-8 items-center">
            {(["month", "week", "day", "agenda"] as CalendarViewMode[]).map(
              (mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => setCurrentView(mode)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-semibold capitalize transition ${
                    currentView === mode
                      ? "bg-background text-foreground shadow-xs font-bold"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {mode}
                </button>
              )
            )}
          </div>
        </div>
      </div>

      {/* ── 2. View Content ────────────────────────────────────────── */}
      <div className="flex-1 min-h-[620px] bg-background/50 overflow-auto">
        {/* ─── A. MONTH VIEW ─────────────────────────────────────── */}
        {currentView === "month" && (
          <div className="flex flex-col h-full min-w-[700px]">
            {/* Weekday Header */}
            <div className="grid grid-cols-7 border-b border-border/70 bg-muted/30">
              {WEEKDAYS.map((wd) => (
                <div
                  key={wd}
                  className="py-2 text-center text-[11px] font-bold uppercase tracking-wider text-muted-foreground"
                >
                  {wd}
                </div>
              ))}
            </div>

            {/* Days Grid */}
            <div className="grid grid-cols-7 auto-rows-fr flex-1 border-b border-border/40">
              {monthDays.map(({ date: dayDate, isCurrentMonth }, idx) => {
                const dayEvents = getEventsForDay(dayDate);
                const dayIsToday = isToday(dayDate);

                return (
                  <div
                    key={idx}
                    className={`min-h-[110px] p-1.5 border-b border-r border-border/50 flex flex-col justify-between transition-colors ${
                      !isCurrentMonth ? "bg-muted/15 opacity-60" : "bg-card"
                    } ${dayIsToday ? "bg-primary/[0.035]" : ""}`}
                  >
                    {/* Day Number Header */}
                    <div className="flex items-center justify-between mb-1">
                      <span
                        className={`text-xs font-semibold px-1.5 py-0.5 rounded-full inline-flex items-center justify-center ${
                          dayIsToday
                            ? "bg-primary text-primary-foreground font-bold h-6 w-6"
                            : "text-foreground"
                        }`}
                      >
                        {dayDate.getDate()}
                      </span>
                      {dayEvents.length > 0 && (
                        <span className="text-[10px] text-muted-foreground font-mono">
                          {dayEvents.length}
                        </span>
                      )}
                    </div>

                    {/* Events List inside Day Cell */}
                    <div className="space-y-1 flex-1 overflow-hidden">
                      {dayEvents.slice(0, 3).map((evt) => {
                        const round = evt.interview_data?.round;
                        return (
                          <div
                            key={evt.id}
                            onClick={() => onEventClick(evt)}
                            className="px-1.5 py-1 rounded-md text-[11px] font-medium truncate cursor-pointer transition hover:brightness-95 flex items-center justify-between gap-1 shadow-2xs border-l-2"
                            style={{
                              borderLeftColor: evt.color || "#3B82F6",
                              backgroundColor: `${evt.color || "#3B82F6"}18`,
                              color: "inherit",
                            }}
                            title={`${evt.title} (${formatEventTime(evt.startDate)})`}
                          >
                            <span className="truncate text-foreground font-semibold">
                              {evt.title}
                            </span>
                            <div className="flex items-center gap-1 shrink-0">
                              {evt.meet_link && (
                                <Video className="w-2.5 h-2.5 text-emerald-600" />
                              )}
                              {round && (
                                <span
                                  className="text-[8.5px] uppercase font-bold px-1 rounded text-white"
                                  style={{
                                    backgroundColor: evt.color || "#3B82F6",
                                  }}
                                >
                                  {round.slice(0, 4)}
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                      {dayEvents.length > 3 && (
                        <span className="text-[10px] font-bold text-primary pl-1 cursor-pointer hover:underline block">
                          +{dayEvents.length - 3} more
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ─── B. WEEK VIEW ──────────────────────────────────────── */}
        {currentView === "week" && (
          <div className="flex flex-col min-w-[780px]">
            {/* Weekdays Top Header Row */}
            <div className="grid grid-cols-[60px_repeat(7,1fr)] border-b border-border/70 sticky top-0 bg-card z-10">
              <div className="p-2 border-r border-border/50 text-[10px] font-mono text-muted-foreground text-center flex items-center justify-center">
                GMT
              </div>
              {weekDays.map((d, i) => {
                const dayIsToday = isToday(d);
                return (
                  <div
                    key={i}
                    className={`py-2 px-1 text-center border-r border-border/50 ${
                      dayIsToday ? "bg-primary/[0.04]" : ""
                    }`}
                  >
                    <div className="text-[11px] font-bold uppercase text-muted-foreground">
                      {WEEKDAYS[i]}
                    </div>
                    <div
                      className={`text-sm font-extrabold inline-flex items-center justify-center mt-0.5 ${
                        dayIsToday
                          ? "bg-primary text-primary-foreground rounded-full w-6 h-6"
                          : "text-foreground"
                      }`}
                    >
                      {d.getDate()}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Time Grid Matrix */}
            <div className="relative grid grid-cols-[60px_repeat(7,1fr)]">
              {/* Left Column: Hour Labels */}
              <div className="border-r border-border/50 select-none">
                {Array.from({ length: TOTAL_HOURS }, (_, hIdx) => {
                  const hour = START_HOUR + hIdx;
                  return (
                    <div
                      key={hour}
                      className="h-16 text-[10.5px] font-mono text-muted-foreground text-right pr-2 pt-1 border-b border-border/40"
                    >
                      {formatHourLabel(hour)}
                    </div>
                  );
                })}
              </div>

              {/* 7 Columns: One for each day of the week */}
              {weekDays.map((colDay, colIdx) => {
                const dayEvents = getEventsForDay(colDay);
                const dayIsToday = isToday(colDay);

                return (
                  <div
                    key={colIdx}
                    className={`relative border-r border-border/50 ${
                      dayIsToday ? "bg-primary/[0.02]" : ""
                    }`}
                  >
                    {/* Hour Background Grid Lines */}
                    {Array.from({ length: TOTAL_HOURS }, (_, hIdx) => (
                      <div
                        key={hIdx}
                        className="h-16 border-b border-border/30 border-dashed"
                      />
                    ))}

                    {/* Red Current Time "Now" Indicator */}
                    {dayIsToday && nowIndicatorTop !== null && (
                      <div
                        className="absolute left-0 right-0 z-20 pointer-events-none flex items-center"
                        style={{ top: `${nowIndicatorTop}%` }}
                      >
                        <div className="w-2.5 h-2.5 rounded-full bg-rose-500 -ml-1.5 shadow-xs" />
                        <div className="w-full h-0.5 bg-rose-500 shadow-xs" />
                      </div>
                    )}

                    {/* Events positioned inside day column */}
                    {dayEvents.map((evt) => {
                      const sHours =
                        evt.startDate.getHours() +
                        evt.startDate.getMinutes() / 60;
                      const eHours =
                        evt.endDate.getHours() + evt.endDate.getMinutes() / 60;

                      // Bound hours within START_HOUR and END_HOUR
                      const boundedStart = Math.max(sHours, START_HOUR);
                      const boundedEnd = Math.min(
                        Math.max(eHours, boundedStart + 0.5),
                        END_HOUR
                      );

                      const topPct =
                        ((boundedStart - START_HOUR) / TOTAL_HOURS) * 100;
                      const heightPct = Math.max(
                        ((boundedEnd - boundedStart) / TOTAL_HOURS) * 100,
                        4.5
                      );

                      const round = evt.interview_data?.round;

                      return (
                        <div
                          key={evt.id}
                          onClick={() => onEventClick(evt)}
                          className="absolute left-1 right-1 rounded-lg p-1.5 text-xs overflow-hidden flex flex-col justify-between cursor-pointer transition hover:brightness-95 hover:shadow-md border-l-3 shadow-xs z-10"
                          style={{
                            top: `${topPct}%`,
                            height: `${heightPct}%`,
                            borderLeftColor: evt.color || "#3B82F6",
                            backgroundColor: `${evt.color || "#3B82F6"}22`,
                          }}
                          title={`${evt.title}\n${formatEventTime(evt.startDate)} – ${formatEventTime(evt.endDate)}`}
                        >
                          <div className="flex items-start justify-between gap-1">
                            <span className="font-bold text-[11px] leading-tight text-foreground truncate">
                              {evt.title}
                            </span>
                            {evt.meet_link && (
                              <Video className="w-3 h-3 text-emerald-600 shrink-0" />
                            )}
                          </div>

                          <div className="flex items-center justify-between text-[9.5px] font-mono text-muted-foreground mt-0.5">
                            <span className="truncate">
                              {formatEventTime(evt.startDate)}
                            </span>
                            {round && (
                              <span
                                className="text-[8.5px] font-bold px-1 rounded uppercase tracking-wider text-white shrink-0"
                                style={{
                                  backgroundColor: evt.color || "#3B82F6",
                                }}
                              >
                                {round}
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ─── C. DAY VIEW ───────────────────────────────────────── */}
        {currentView === "day" && (
          <div className="flex flex-col min-w-[500px]">
            {/* Day Header */}
            <div className="p-3 border-b border-border/70 bg-card flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div
                  className={`text-lg font-black inline-flex items-center justify-center ${
                    isToday(currentDate)
                      ? "bg-primary text-primary-foreground rounded-full w-8 h-8"
                      : "text-foreground"
                  }`}
                >
                  {currentDate.getDate()}
                </div>
                <div>
                  <h3 className="text-sm font-bold text-foreground">
                    {currentDate.toLocaleDateString("en-US", {
                      weekday: "long",
                      month: "long",
                      year: "numeric",
                    })}
                  </h3>
                  <p className="text-xs text-muted-foreground">
                    {getEventsForDay(currentDate).length} scheduled session(s)
                  </p>
                </div>
              </div>
            </div>

            {/* Day Time Grid */}
            <div className="relative grid grid-cols-[70px_1fr]">
              {/* Hour Labels */}
              <div className="border-r border-border/50 select-none">
                {Array.from({ length: TOTAL_HOURS }, (_, hIdx) => {
                  const hour = START_HOUR + hIdx;
                  return (
                    <div
                      key={hour}
                      className="h-20 text-xs font-mono text-muted-foreground text-right pr-3 pt-1 border-b border-border/40"
                    >
                      {formatHourLabel(hour)}
                    </div>
                  );
                })}
              </div>

              {/* Day Events Column */}
              <div className="relative border-r border-border/50">
                {/* Horizontal hour lines */}
                {Array.from({ length: TOTAL_HOURS }, (_, hIdx) => (
                  <div
                    key={hIdx}
                    className="h-20 border-b border-border/30 border-dashed"
                  />
                ))}

                {/* Real-time Indicator */}
                {isToday(currentDate) && nowIndicatorTop !== null && (
                  <div
                    className="absolute left-0 right-0 z-20 pointer-events-none flex items-center"
                    style={{ top: `${nowIndicatorTop}%` }}
                  >
                    <div className="w-3 h-3 rounded-full bg-rose-500 -ml-1.5 shadow-xs" />
                    <div className="w-full h-0.5 bg-rose-500 shadow-xs" />
                  </div>
                )}

                {/* Events list */}
                {getEventsForDay(currentDate).map((evt) => {
                  const sHours =
                    evt.startDate.getHours() + evt.startDate.getMinutes() / 60;
                  const eHours =
                    evt.endDate.getHours() + evt.endDate.getMinutes() / 60;

                  const boundedStart = Math.max(sHours, START_HOUR);
                  const boundedEnd = Math.min(
                    Math.max(eHours, boundedStart + 0.5),
                    END_HOUR
                  );

                  const topPct =
                    ((boundedStart - START_HOUR) / TOTAL_HOURS) * 100;
                  const heightPct = Math.max(
                    ((boundedEnd - boundedStart) / TOTAL_HOURS) * 100,
                    6
                  );

                  return (
                    <div
                      key={evt.id}
                      onClick={() => onEventClick(evt)}
                      className="absolute left-3 right-3 rounded-xl p-3 text-xs flex flex-col justify-between cursor-pointer transition hover:brightness-95 hover:shadow-lg border-l-4 shadow-sm z-10"
                      style={{
                        top: `${topPct}%`,
                        height: `${heightPct}%`,
                        borderLeftColor: evt.color || "#3B82F6",
                        backgroundColor: `${evt.color || "#3B82F6"}20`,
                      }}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <h4 className="font-bold text-sm text-foreground">
                            {evt.title}
                          </h4>
                          {evt.interview_data?.opening_title && (
                            <p className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                              <Briefcase className="w-3 h-3 text-primary" />
                              <span>{evt.interview_data.opening_title}</span>
                            </p>
                          )}
                        </div>
                        {evt.meet_link && (
                          <div className="flex items-center gap-1 text-xs text-emerald-600 bg-emerald-500/10 px-2 py-1 rounded-lg font-semibold">
                            <Video className="w-3.5 h-3.5" />
                            <span>Google Meet</span>
                          </div>
                        )}
                      </div>

                      <div className="flex items-center justify-between text-xs text-muted-foreground font-mono mt-2">
                        <span>
                          {formatEventTime(evt.startDate)} –{" "}
                          {formatEventTime(evt.endDate)}
                        </span>
                        {evt.interview_data?.round && (
                          <span
                            className="text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider text-white"
                            style={{ backgroundColor: evt.color || "#3B82F6" }}
                          >
                            {evt.interview_data.round} Round
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* ─── D. AGENDA / LIST VIEW ─────────────────────────────── */}
        {currentView === "agenda" && (
          <div className="p-4 space-y-4 max-w-4xl mx-auto">
            {parsedEvents.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground text-xs">
                No events scheduled in this time window.
              </div>
            ) : (
              parsedEvents.map((evt) => (
                <div
                  key={evt.id}
                  onClick={() => onEventClick(evt)}
                  className="bg-card p-3.5 rounded-xl border border-border/70 hover:border-primary/50 transition cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs"
                >
                  <div className="flex items-start sm:items-center gap-3">
                    <div
                      className="w-2.5 h-10 rounded-full shrink-0"
                      style={{ backgroundColor: evt.color || "#3B82F6" }}
                    />
                    <div>
                      <h4 className="font-bold text-xs text-foreground">
                        {evt.title}
                      </h4>
                      <p className="text-[11px] text-muted-foreground mt-0.5 flex items-center gap-2">
                        <span>
                          {evt.startDate.toLocaleDateString("en-US", {
                            weekday: "short",
                            month: "short",
                            day: "numeric",
                          })}
                        </span>
                        <span>•</span>
                        <span className="font-mono">
                          {formatEventTime(evt.startDate)} –{" "}
                          {formatEventTime(evt.endDate)}
                        </span>
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 self-end sm:self-auto">
                    {evt.meet_link && (
                      <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-600 bg-emerald-500/10 px-2 py-1 rounded-md">
                        <Video className="w-3 h-3" />
                        <span>Meet</span>
                      </span>
                    )}
                    {evt.interview_data?.round && (
                      <span
                        className="text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider text-white"
                        style={{ backgroundColor: evt.color || "#3B82F6" }}
                      >
                        {evt.interview_data.round}
                      </span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
