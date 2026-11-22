"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Sparkles,
  ArrowRight,
  CheckCircle2,
  Calendar,
  Zap,
  Bot,
  Video,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ThemeToggle } from "@/components/theme-toggle";

export default function LandingPage() {
  const [activeTab, setActiveTab] = useState<"screening" | "calendar">("screening");

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col justify-between selection:bg-primary/20 selection:text-primary transition-colors">
      {/* ── Main Navbar ─────────────────────────────────────────────── */}
      <header className="border-b border-border/70 bg-card/70 backdrop-blur-md sticky top-0 z-50">
        <div className="container mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 hover:opacity-90 transition-opacity">
            <img
              src="/brand/hiring-loop-logo.svg"
              alt="Hiring Loop"
              className="h-8 w-auto dark:hidden block object-contain"
            />
            <img
              src="/brand/hiring-loop-logo-dark.svg"
              alt="Hiring Loop"
              className="h-8 w-auto hidden dark:block object-contain"
            />
          </Link>

          <div className="flex items-center gap-3">
            <ThemeToggle />
            <Link href="/login">
              <Button variant="ghost" size="sm" className="text-xs h-9 font-semibold">
                Sign In
              </Button>
            </Link>
            <Link href="/register">
              <Button
                size="sm"
                className="text-xs h-9 px-4 font-bold shadow-xs bg-primary hover:bg-primary/90 text-primary-foreground"
              >
                Start Free Trial
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* ── Hero & Showcase ─────────────────────────────────────────── */}
      <main className="flex-1 container mx-auto px-4 sm:px-6 py-12 sm:py-16 flex flex-col items-center text-center max-w-4xl">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-primary/20 bg-primary/10 text-primary text-xs font-semibold mb-6 shadow-2xs">
          <Sparkles className="h-3.5 w-3.5" />
          <span>AI Screening • Google Calendar Sync • Recruiter Control</span>
        </div>

        {/* Headline */}
        <h1 className="text-4xl sm:text-6xl font-black tracking-tight text-foreground leading-[1.12]">
          Hire faster, with <span className="text-primary">you in control.</span>
        </h1>

        {/* Subtitle */}
        <p className="text-base sm:text-lg text-muted-foreground mt-5 max-w-2xl leading-relaxed">
          Hiring Loop automates resume parsing, skill matching, Google Calendar interviews, and candidate follow-ups — keeping your recruitment team in complete control with zero hallucinations.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center gap-3.5 mt-8 w-full sm:w-auto">
          <Link href="/register" className="w-full sm:w-auto">
            <Button
              size="lg"
              className="w-full sm:w-auto text-xs h-11 px-7 gap-2 shadow-sm font-bold bg-primary hover:bg-primary/90 text-primary-foreground"
            >
              <span>Start Screening Free</span>
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
          <Link href="/login" className="w-full sm:w-auto">
            <Button
              variant="outline"
              size="lg"
              className="w-full sm:w-auto text-xs h-11 px-6 font-semibold border-border/80 hover:bg-muted/60"
            >
              <span>Sign In to Dashboard</span>
            </Button>
          </Link>
        </div>

        {/* Trust Badges */}
        <div className="flex flex-wrap items-center justify-center gap-5 text-xs text-muted-foreground mt-7 font-medium">
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="h-4 w-4 text-emerald-500" /> Free to get started
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="h-4 w-4 text-emerald-500" /> Google Workspace OAuth
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="h-4 w-4 text-emerald-500" /> Strict database templates
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="h-4 w-4 text-emerald-500" /> Supabase encrypted
          </span>
        </div>

        {/* ── Product Preview Window ─────────────────────────────────── */}
        <div className="mt-12 w-full rounded-2xl border border-border/80 bg-card/60 backdrop-blur-md shadow-xl text-left overflow-hidden">
          {/* Window Topbar */}
          <div className="flex items-center justify-between p-3 sm:px-5 border-b border-border/60 bg-muted/30">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-red-400" />
              <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
              <span className="ml-2 font-mono text-[11px] text-muted-foreground hidden sm:inline">
                hiringloop.app/pipeline
              </span>
            </div>

            <div className="flex items-center bg-background/80 border border-border/60 rounded-xl p-0.5 text-xs font-semibold">
              <button
                type="button"
                onClick={() => setActiveTab("screening")}
                className={`px-3 py-1 rounded-lg transition-all ${
                  activeTab === "screening"
                    ? "bg-primary text-primary-foreground shadow-xs font-bold"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                AI Match Fit
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("calendar")}
                className={`px-3 py-1 rounded-lg transition-all ${
                  activeTab === "calendar"
                    ? "bg-primary text-primary-foreground shadow-xs font-bold"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Google Calendar Sync
              </button>
            </div>
          </div>

          {/* Window Content */}
          <div className="p-4 sm:p-6 bg-card">
            {activeTab === "screening" ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="md:col-span-2 p-5 rounded-xl border border-border/70 bg-background/90 shadow-2xs space-y-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="font-bold text-base text-foreground">Sarah Jenkins</h4>
                        <Badge className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20 text-xs font-bold">
                          96/100 FIT SCORE
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        Senior Full-Stack Engineer • Ingested via Gmail Sync • 8+ YOE
                      </p>
                    </div>
                    <div className="w-12 h-12 rounded-full border-4 border-emerald-500/30 border-t-emerald-500 flex items-center justify-center font-bold text-xs text-emerald-600 dark:text-emerald-400 shrink-0">
                      96%
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="text-[11px] font-bold text-muted-foreground tracking-wider uppercase">
                      MATCHED CORE SKILLS
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {["React 19", "Next.js 15", "FastAPI", "PostgreSQL", "TypeScript", "Tailwind CSS", "Redis L2"].map(
                        (skill) => (
                          <span
                            key={skill}
                            className="px-2.5 py-0.5 rounded-md bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 text-xs font-medium border border-emerald-500/20"
                          >
                            ✓ {skill}
                          </span>
                        )
                      )}
                    </div>
                  </div>

                  <div className="space-y-1 text-xs">
                    <div className="font-semibold text-foreground text-[11px]">AI SYNTHESIS & FIT REASONING</div>
                    <p className="text-muted-foreground text-[11px] leading-relaxed">
                      Strong architectural background with modern fullstack stacks. Built distributed APIs, managed state with TanStack Query, and optimized database indexing. Zero red flags detected.
                    </p>
                  </div>

                  <div className="pt-2 flex flex-wrap items-center gap-2 border-t border-border/50">
                    <Link href="/register">
                      <Button size="sm" className="h-8 text-xs font-bold bg-primary text-primary-foreground">
                        Invite to Technical Interview
                      </Button>
                    </Link>
                    <Link href="/login">
                      <Button variant="outline" size="sm" className="h-8 text-xs font-semibold">
                        View Full Dossier
                      </Button>
                    </Link>
                  </div>
                </div>

                <div className="p-5 rounded-xl border border-border/70 bg-background/90 shadow-2xs flex flex-col justify-between space-y-4">
                  <div>
                    <span className="text-xs font-bold text-foreground">Requisition Fit Metrics</span>
                    <div className="mt-3 space-y-2.5 text-xs">
                      <div>
                        <div className="flex justify-between text-[11px] text-muted-foreground mb-1">
                          <span>Technical Fit</span>
                          <span className="font-bold text-foreground">98%</span>
                        </div>
                        <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                          <div className="h-full bg-emerald-500 rounded-full w-[98%]" />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-[11px] text-muted-foreground mb-1">
                          <span>Years of Experience</span>
                          <span className="font-bold text-foreground">92%</span>
                        </div>
                        <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                          <div className="h-full bg-blue-500 rounded-full w-[92%]" />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-[11px] text-muted-foreground mb-1">
                          <span>Domain Knowledge</span>
                          <span className="font-bold text-foreground">94%</span>
                        </div>
                        <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                          <div className="h-full bg-purple-500 rounded-full w-[94%]" />
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="p-3 rounded-lg bg-primary/5 border border-primary/15 text-[11px] space-y-1">
                    <div className="font-bold text-primary flex items-center gap-1.5">
                      <Zap className="w-3.5 h-3.5" /> Deterministic Pipeline
                    </div>
                    <p className="text-muted-foreground">
                      Emails are filled from verified database templates with zero hallucinated dates or names.
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-5 rounded-xl border border-border/70 bg-background/90 shadow-2xs space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-border/60">
                  <div>
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-primary" />
                      <span className="font-bold text-sm text-foreground">Google Calendar Real-Time Sync</span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Two-way sync with working-hours shading and automated Google Meet generation.
                    </p>
                  </div>
                  <Badge
                    variant="outline"
                    className="text-xs bg-emerald-500/10 text-emerald-600 border-emerald-500/20 gap-1.5 w-fit"
                  >
                    Google Workspace Connected
                  </Badge>
                </div>

                <div className="p-4 rounded-xl border border-border bg-card shadow-2xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="w-3 h-3 rounded-full bg-indigo-500" />
                      <span className="font-bold text-sm text-foreground">
                        Technical Architecture Discussion — Sarah Jenkins
                      </span>
                      <Badge className="bg-indigo-500/10 text-indigo-600 text-[10px]">Technical Round</Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Tomorrow at 3:00 PM – 4:00 PM (1 hour) • Recruiter Working Hours: 9:00 AM – 5:00 PM
                    </p>
                  </div>

                  <a
                    href="https://meet.google.com"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-xs transition"
                  >
                    <Video className="w-3.5 h-3.5" />
                    <span>Join with Google Meet</span>
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* ── Minimal Clean Footer ────────────────────────────────────── */}
      <footer className="border-t border-border/80 py-6 text-xs text-muted-foreground bg-card/40">
        <div className="container mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <img
              src="/brand/hiring-loop-logo.svg"
              alt="Hiring Loop"
              className="h-6 w-auto dark:hidden block object-contain"
            />
            <img
              src="/brand/hiring-loop-logo-dark.svg"
              alt="Hiring Loop"
              className="h-6 w-auto hidden dark:block object-contain"
            />
            <span className="text-muted-foreground/60 text-[11px] ml-2">
              © {new Date().getFullYear()} Hiring Loop. All rights reserved.
            </span>
          </div>

          <div className="flex items-center gap-5 text-xs font-medium">
            <Link href="/login" className="hover:text-foreground transition-colors">
              Sign In
            </Link>
            <Link href="/register" className="font-semibold text-primary hover:underline">
              Start Free Trial
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
