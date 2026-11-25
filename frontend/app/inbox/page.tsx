"use client";

import React, { useState, useEffect, useRef, useMemo, Suspense } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { formatTime, formatDateTime } from "@/lib/format-date";
import { formatRelativeTime } from "@/lib/utils";
import {
  Mail,
  Search,
  Send,
  Sparkles,
  Clock,
  Check,
  CheckCheck,
  AlertCircle,
  RefreshCw,
  User,
  Briefcase,
  ChevronRight,
  Filter,
  Paperclip,
  Download,
  ExternalLink,
  Phone,
  Calendar,
  Layers,
  MessageCircle,
  FileText,
  CornerDownLeft,
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/ui/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { useToast } from "@/components/ui/use-toast";
import {
  googleApi,
  EmailConversationSummary,
  EmailThreadResponse,
  EmailMessageItem,
} from "@/lib/api";
import { CandidateDrawer } from "@/components/candidates/candidate-drawer";
import { ScheduleInviteModal } from "@/components/scheduling/schedule-invite-modal";
import { useAgentEvents } from "@/lib/use-agent-events";
import {
  ALL_RECRUITING_TEMPLATES,
  fillTemplate,
  normalizeCandidateName,
} from "@/lib/template-registry";

type FilterTab = "all" | "unread" | "awaiting_reply";

function InboxContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialCandidateId = searchParams.get("candidate_id") || null;
  const queryClient = useQueryClient();
  const { toast } = useToast();

  // Listen to real-time agent workflow events via SSE
  useAgentEvents();

  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(initialCandidateId);
  const [filterTab, setFilterTab] = useState<FilterTab>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [replyText, setReplyText] = useState("");
  const [replySubject, setReplySubject] = useState("");
  const [isDraftingAI, setIsDraftingAI] = useState(false);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>("");
  const [candidateDrawerOpen, setCandidateDrawerOpen] = useState(false);
  const [scheduleModalOpen, setScheduleModalOpen] = useState(false);
  const [page, setPage] = useState(0);
  const pageSize = 25;

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 1. Fetch conversations list with pagination (skip/limit)
  const {
    data: conversationsData,
    isLoading: isLoadingConvs,
    isRefetching: isRefetchingConvs,
    isError: isErrorConvs,
    error: errorConvs,
    refetch: refetchConvs,
  } = useQuery({
    queryKey: ["email-conversations", filterTab, page],
    queryFn: () =>
      googleApi.listConversations({
        filterStatus: filterTab,
        skip: page * pageSize,
        limit: pageSize,
      }),
    refetchInterval: 30000,
    retry: 1,
  });

  const conversations = conversationsData?.conversations || [];
  const awaitingReplyCount = conversationsData?.awaiting_reply_count || 0;
  const unreadTotal = conversationsData?.unread_count || 0;

  // Auto-select first conversation if none selected
  useEffect(() => {
    if (!selectedCandidateId && conversations.length > 0) {
      setSelectedCandidateId(conversations[0].candidate_id);
    }
  }, [conversations, selectedCandidateId]);

  // Keep selected candidate updated if URL changes
  useEffect(() => {
    const cid = searchParams.get("candidate_id");
    if (cid && cid !== selectedCandidateId) {
      setSelectedCandidateId(cid);
    }
  }, [searchParams, selectedCandidateId]);

  // 2. Fetch active thread
  const {
    data: threadData,
    isLoading: isLoadingThread,
    isRefetching: isRefetchingThread,
    refetch: refetchThread,
  } = useQuery({
    queryKey: ["email-thread", selectedCandidateId],
    queryFn: () => (selectedCandidateId ? googleApi.getThread(selectedCandidateId) : Promise.reject("No candidate")),
    enabled: !!selectedCandidateId,
    refetchInterval: 20000,
    retry: 1,
  });

  const selectedConv = conversations.find((c) => c.candidate_id === selectedCandidateId);

  // Auto prefill reply subject when thread changes
  useEffect(() => {
    if (threadData) {
      const lastMsg = threadData.messages[threadData.messages.length - 1];
      const prevSubj = lastMsg?.subject || `Application for ${threadData.opening_title || "Position"}`;
      setReplySubject(prevSubj.startsWith("Re:") ? prevSubj : `Re: ${prevSubj}`);
    }
  }, [threadData]);

  // Scroll to bottom on new messages or candidate change (open at latest message)
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "instant" });
  }, [threadData?.messages, selectedCandidateId]);

  // 3. Send reply mutation in same Gmail thread
  const sendMutation = useMutation({
    mutationFn: (text: string) =>
      googleApi.sendReply({
        candidate_id: selectedCandidateId!,
        message: text,
        subject: replySubject.trim() || undefined,
      }),
    onSuccess: () => {
      setReplyText("");
      setSelectedTemplateId("");
      queryClient.invalidateQueries({ queryKey: ["email-thread", selectedCandidateId] });
      queryClient.invalidateQueries({ queryKey: ["email-conversations"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
      toast({
        title: "Reply Sent Successfully",
        description: "Your message was transmitted in the Gmail conversation thread.",
      });
    },
    onError: (err: any) => {
      toast({
        title: "Failed to send email",
        description: err.response?.data?.detail || err.message || "Could not dispatch reply.",
        variant: "destructive",
      });
    },
  });

  // 4. AI draft reply
  const handleAIDraft = async () => {
    if (!selectedCandidateId || !threadData) return;
    setIsDraftingAI(true);
    try {
      const res = await googleApi.aiDraftReply({
        candidate_id: selectedCandidateId,
        instructions: "Follow up warmly about moving to the next conversation and ask for their availability this week.",
      });
      if (res.drafted_message) {
        setReplyText(res.drafted_message);
        if (res.drafted_subject) {
          setReplySubject(res.drafted_subject);
        }
        toast({
          title: "AI Draft Ready",
          description: "Review and approve the draft before sending.",
        });
      }
    } catch (err: any) {
      toast({
        title: "AI Draft Failed",
        description: err.message || "Could not generate reply draft.",
        variant: "destructive",
      });
    } finally {
      setIsDraftingAI(false);
    }
  };

  // 5. Handle Template Picker Selection
  const handleSelectTemplate = (templateId: string) => {
    setSelectedTemplateId(templateId);
    if (!templateId || !threadData) return;

    const tpl = ALL_RECRUITING_TEMPLATES.find((t) => t.id === templateId);
    if (tpl) {
      const ctx = {
        candidate_name: threadData.candidate_name,
        job_title: threadData.opening_title || "Open Position",
        company_name: "AivonTech",
        hr_name: "AivonTech",
      };

      setReplySubject(fillTemplate(tpl.subject, ctx));
      setReplyText(fillTemplate(tpl.body, ctx));
    }
  };

  // 6. Filter conversations locally by search query
  const filteredConversations = useMemo(() => {
    return conversations.filter((c) => {
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase();
      return (
        c.candidate_name.toLowerCase().includes(q) ||
        c.candidate_email.toLowerCase().includes(q) ||
        (c.opening_title && c.opening_title.toLowerCase().includes(q)) ||
        (c.last_message_body && c.last_message_body.toLowerCase().includes(q))
      );
    });
  }, [conversations, searchQuery]);

  const handleSelectConversation = (candidateId: string) => {
    setSelectedCandidateId(candidateId);
    router.replace(`/inbox?candidate_id=${candidateId}`, { scroll: false });
  };

  return (
    <div className="flex flex-col h-[calc(100vh-7.5rem)] w-full space-y-3.5">
      {/* ── Page Header ─────────────────────────────────────────────── */}
      <PageHeader
        title="Recruiting Inbox"
        description="Unified email client syncing candidate Gmail threads, attachments, and AI-assisted replies."
        badge={
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="gap-1.5 font-mono text-[11px] bg-card">
              <Mail className="h-3 w-3 text-primary" />
              <span>{conversations.length} Active Threads</span>
            </Badge>
            {awaitingReplyCount > 0 && (
              <Badge variant="secondary" className="gap-1 font-mono text-[11px] bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                <Clock className="h-3 w-3" />
                <span>{awaitingReplyCount} Awaiting Reply</span>
              </Badge>
            )}
          </div>
        }
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                refetchConvs();
                refetchThread();
              }}
              disabled={isRefetchingConvs || isRefetchingThread}
              className="h-8 gap-1.5 text-xs font-medium"
              title="Refresh inbox and active thread"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isRefetchingConvs || isRefetchingThread ? "animate-spin" : ""}`} />
              <span className="hidden sm:inline">Refresh</span>
            </Button>
            <Link href="/pipeline">
              <Button variant="outline" size="sm" className="h-8 gap-1.5 text-xs font-medium">
                <Layers className="h-3.5 w-3.5 text-muted-foreground" />
                <span>Pipeline</span>
              </Button>
            </Link>
          </div>
        }
      />

      {/* ── Main Dual-Pane Inbox Container ──────────────────────────── */}
      <div className="flex-1 min-h-0 flex flex-col md:flex-row rounded-2xl border border-border/70 dark:border-white/[0.08] bg-card shadow-xs overflow-hidden">
        {/* ── Left Pane: Conversation List ──────────────────────────── */}
        <div className="w-full md:w-80 lg:w-96 flex flex-col border-r border-border/70 dark:border-white/[0.08] bg-card/60 shrink-0 h-full">
          {/* Top Search Bar */}
          <div className="p-3 border-b border-border/60 space-y-2.5">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
              <Input
                placeholder="Search candidate, role, or message..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 text-xs h-8 bg-background/80"
              />
            </div>

            {/* Filter Tabs */}
            <div className="flex items-center gap-1 overflow-x-auto pb-0.5 no-scrollbar">
              {(
                [
                  { id: "all", label: "All Mail" },
                  { id: "unread", label: "Unread", count: unreadTotal },
                  { id: "awaiting_reply", label: "Awaiting Reply", count: awaitingReplyCount },
                ] as const
              ).map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setFilterTab(tab.id as FilterTab)}
                  className={`text-[11px] font-medium px-2 py-1 rounded-md shrink-0 transition-colors flex items-center gap-1 ${
                    filterTab === tab.id
                      ? "bg-primary text-primary-foreground shadow-xs"
                      : "text-muted-foreground hover:bg-muted/70 hover:text-foreground"
                  }`}
                >
                  <span>{tab.label}</span>
                  {"count" in tab && tab.count !== undefined && tab.count > 0 && (
                    <span
                      className={`text-[9.5px] px-1 py-0.2 rounded-full font-bold ${
                        filterTab === tab.id
                          ? "bg-primary-foreground/20 text-primary-foreground"
                          : "bg-amber-500/20 text-amber-600 dark:text-amber-400"
                      }`}
                    >
                      {tab.count}
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Conversation List Scroll Area */}
          <div className="flex-1 overflow-y-auto divide-y divide-border/50 scrollbar-thin scrollbar-thumb-muted-foreground/30 hover:scrollbar-thumb-muted-foreground/50">
            {isLoadingConvs ? (
              <div className="p-3 space-y-3">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="flex gap-2.5 items-center p-2">
                    <Skeleton className="w-8 h-8 rounded-full shrink-0" />
                    <div className="space-y-1.5 flex-1">
                      <Skeleton className="h-3.5 w-3/4" />
                      <Skeleton className="h-3 w-1/2" />
                    </div>
                  </div>
                ))}
              </div>
            ) : isErrorConvs ? (
              <div className="p-6">
                <ErrorState
                  title="Failed to load conversations"
                  message={(errorConvs as any)?.message || "Please check connection and retry."}
                  onRetry={() => refetchConvs()}
                />
              </div>
            ) : filteredConversations.length === 0 ? (
              <div className="p-6">
                <EmptyState
                  icon={Mail}
                  title="No conversations found"
                  description={
                    searchQuery
                      ? "No candidate threads matched your search."
                      : "Candidate emails synced from Gmail or applications will appear here."
                  }
                />
              </div>
            ) : (
              filteredConversations.map((conv) => {
                const isSelected = conv.candidate_id === selectedCandidateId;
                const isAwaiting = conv.last_message_direction === "inbound";

                return (
                  <button
                    key={conv.candidate_id}
                    onClick={() => handleSelectConversation(conv.candidate_id)}
                    className={`w-full text-left p-3 transition-all flex gap-2.5 items-start relative hover:bg-muted/40 cursor-pointer ${
                      isSelected
                        ? "bg-muted/70 border-l-3 border-primary"
                        : "border-l-3 border-transparent"
                    }`}
                  >
                    {/* Avatar with Channel Icon */}
                    <div className="relative shrink-0">
                      <div className="w-8 h-8 rounded-full bg-primary/10 text-primary font-semibold flex items-center justify-center text-xs">
                        {conv.candidate_name ? conv.candidate_name.charAt(0).toUpperCase() : "C"}
                      </div>
                      <div
                        className="absolute -bottom-1 -right-1 h-3.5 w-3.5 rounded-full border border-background bg-blue-500 text-white flex items-center justify-center text-[8px]"
                        title="Gmail Message"
                      >
                        <Mail className="h-2 w-2" />
                      </div>
                    </div>

                    {/* Conversation Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-1 mb-0.5">
                        <span
                          className={`text-xs truncate ${
                            conv.unread ? "font-bold text-foreground" : "font-semibold text-foreground/90"
                          }`}
                        >
                          {conv.candidate_name}
                        </span>
                        {conv.last_message_at && (
                          <span className="text-[10px] text-muted-foreground whitespace-nowrap">
                            {formatRelativeTime(conv.last_message_at)}
                          </span>
                        )}
                      </div>

                      <div className="text-[11px] text-muted-foreground flex items-center gap-1.5 mb-1 truncate">
                        <span className="truncate max-w-[140px] font-medium">
                          {conv.opening_title || "General Application"}
                        </span>
                        <span>•</span>
                        <span className="capitalize">{conv.candidate_stage}</span>
                      </div>

                      <p
                        className={`text-[11px] truncate leading-relaxed ${
                          conv.unread ? "font-medium text-foreground" : "text-muted-foreground"
                        }`}
                      >
                        {conv.last_message_body || "Application received."}
                      </p>
                    </div>

                    {/* Right Indicators: Unread dot & Paperclip */}
                    <div className="flex flex-col items-end gap-1.5 shrink-0 pt-0.5">
                      {conv.unread && (
                        <span className="h-2 w-2 rounded-full bg-primary shrink-0 ring-2 ring-primary/20" />
                      )}
                      {conv.has_attachments && (
                        <span title="Has attachment">
                          <Paperclip className="h-3 w-3 text-muted-foreground/80 shrink-0" />
                        </span>
                      )}
                    </div>
                  </button>
                );
              })
            )}
          </div>

          {/* Conversation List Pagination */}
          {conversationsData && conversationsData.total_conversations > pageSize && (
            <div className="p-2.5 border-t border-border/60 flex items-center justify-between text-xs text-muted-foreground bg-muted/20 shrink-0">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="px-2.5 py-1 rounded border border-border/60 text-xs font-medium disabled:opacity-40 hover:bg-muted transition-colors cursor-pointer"
              >
                Previous
              </button>
              <span className="text-[11px]">
                {page * pageSize + 1}-
                {Math.min((page + 1) * pageSize, conversationsData.total_conversations)} of{" "}
                {conversationsData.total_conversations}
              </span>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={(page + 1) * pageSize >= conversationsData.total_conversations}
                className="px-2.5 py-1 rounded border border-border/60 text-xs font-medium disabled:opacity-40 hover:bg-muted transition-colors cursor-pointer"
              >
                Next
              </button>
            </div>
          )}
        </div>

        {/* ── Right Pane: Active Thread History & Reply Composer ───── */}
        <div className="flex-1 flex flex-col min-w-0 h-full bg-background/50">
          {!selectedCandidateId ? (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
              <div className="h-12 w-12 rounded-2xl bg-muted/60 flex items-center justify-center text-muted-foreground mb-3">
                <Mail className="h-6 w-6" />
              </div>
              <h3 className="font-semibold text-sm text-foreground">Select a conversation</h3>
              <p className="text-xs text-muted-foreground mt-1 max-w-sm">
                Choose a candidate from the left panel to view their complete Gmail thread and send replies.
              </p>
            </div>
          ) : isLoadingThread ? (
            <div className="flex-1 p-6 space-y-4">
              <div className="flex items-center justify-between pb-4 border-b border-border/60">
                <Skeleton className="h-6 w-48" />
                <Skeleton className="h-8 w-28 rounded-lg" />
              </div>
              <Skeleton className="h-24 w-3/4 rounded-xl" />
              <Skeleton className="h-24 w-3/4 ml-auto rounded-xl" />
              <Skeleton className="h-24 w-3/4 rounded-xl" />
            </div>
          ) : !threadData ? (
            <div className="flex-1 flex items-center justify-center p-8 text-center">
              <ErrorState
                title="Thread not found"
                message="Could not load message history for this candidate."
                onRetry={() => refetchThread()}
              />
            </div>
          ) : (
            <>
              {/* ── Thread Header ────────────────────────────────────── */}
              <div className="p-3.5 border-b border-border/70 dark:border-white/[0.08] bg-card flex flex-wrap items-center justify-between gap-2 shrink-0">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-9 h-9 rounded-full bg-primary/10 text-primary font-bold flex items-center justify-center text-sm shrink-0">
                    {threadData.candidate_name ? threadData.candidate_name.charAt(0).toUpperCase() : "C"}
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-sm text-foreground truncate">
                        {threadData.candidate_name}
                      </h3>
                      <Badge variant="outline" className="text-[10px] font-semibold capitalize bg-muted/50">
                        {threadData.candidate_stage}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground truncate mt-0.5">
                      <span>{threadData.candidate_email}</span>
                      {selectedConv?.candidate_phone && (
                        <>
                          <span>•</span>
                          <span className="flex items-center gap-1">
                            <Phone className="h-3 w-3" />
                            {selectedConv.candidate_phone}
                          </span>
                        </>
                      )}
                      <span>•</span>
                      <span className="flex items-center gap-1 font-medium text-foreground/80">
                        <Briefcase className="h-3 w-3 text-primary" />
                        {threadData.opening_title || "General Application"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Header Action Buttons */}
                <div className="flex items-center gap-1.5 shrink-0">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setScheduleModalOpen(true)}
                    className="h-7 px-2.5 text-xs font-medium gap-1"
                    title="Schedule Interview"
                  >
                    <Calendar className="h-3 w-3 text-muted-foreground" />
                    <span>Schedule</span>
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCandidateDrawerOpen(true)}
                    className="h-7 px-2.5 text-xs font-medium gap-1"
                    title="Open Candidate Drawer"
                  >
                    <User className="h-3 w-3 text-muted-foreground" />
                    <span>Drawer</span>
                  </Button>
                </div>
              </div>

              {/* ── Thread Message History ──────────────────────────── */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-muted-foreground/30 hover:scrollbar-thumb-muted-foreground/50">
                {threadData.messages.length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground text-xs">
                    No messages yet in this candidate thread. Use the reply box below to start the conversation.
                  </div>
                ) : (
                  threadData.messages.map((msg) => {
                    const isInbound = msg.direction === "inbound";

                    return (
                      <div
                        key={msg.id}
                        className={`flex flex-col max-w-[85%] ${
                          isInbound ? "mr-auto items-start" : "ml-auto items-end"
                        }`}
                      >
                        {/* Sender Label & Timestamp */}
                        <div className="flex items-center gap-2 mb-1 text-[10.5px] text-muted-foreground">
                          <span className="font-semibold text-foreground/85">
                            {isInbound ? threadData.candidate_name : "You (Recruiter)"}
                          </span>
                          <span className="flex items-center gap-0.5">
                            <Badge variant="outline" className="text-[9px] px-1 py-0 bg-blue-500/10 text-blue-600 border-blue-500/20">
                              Gmail
                            </Badge>
                          </span>
                          <span>•</span>
                          <span>{formatDateTime(msg.sent_at || msg.created_at)}</span>
                        </div>

                        {/* Message Card Body */}
                        <div
                          className={`rounded-2xl p-3.5 shadow-xs text-xs leading-relaxed space-y-2 border ${
                            isInbound
                              ? "bg-card border-border/80 text-foreground rounded-tl-sm"
                              : "bg-primary/[0.07] border-primary/20 text-foreground rounded-tr-sm"
                          }`}
                        >
                          {/* Subject Header (if email) */}
                          {msg.subject && (
                            <div className="font-bold text-[11px] text-foreground/90 pb-1.5 border-b border-border/50">
                              {msg.subject}
                            </div>
                          )}

                          {/* Message Content */}
                          <div className="whitespace-pre-wrap select-text">
                            {msg.body}
                          </div>

                          {/* Attachments Section */}
                          {msg.attachments && msg.attachments.length > 0 && (
                            <div className="pt-2 border-t border-border/50 space-y-1.5">
                              <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1">
                                <Paperclip className="h-3 w-3" />
                                <span>Attachments ({msg.attachments.length})</span>
                              </p>
                              <div className="flex flex-wrap gap-1.5">
                                {msg.attachments.map((att, idx) => (
                                  <a
                                    key={idx}
                                    href={att.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-border bg-background hover:bg-muted text-[11px] font-medium text-foreground transition-colors group"
                                  >
                                    <FileText className="h-3 w-3 text-primary group-hover:scale-105 transition-transform" />
                                    <span className="truncate max-w-[180px]">{att.filename}</span>
                                    <Download className="h-2.5 w-2.5 text-muted-foreground" />
                                  </a>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Message Delivery & Sync Status indicator */}
                        <div className="flex items-center gap-1 mt-1 text-[10px] text-muted-foreground">
                          {isInbound ? (
                            <>
                              <CheckCheck className="h-3 w-3 text-emerald-500" />
                              <span className="text-emerald-600 dark:text-emerald-400 font-medium">Received via Gmail</span>
                            </>
                          ) : msg.status === "sent" ? (
                            <>
                              <Check className="h-3 w-3 text-muted-foreground" />
                              <span>Sent via Gmail</span>
                            </>
                          ) : msg.status === "delivered" || msg.status === "read" ? (
                            <>
                              <CheckCheck className="h-3 w-3 text-primary" />
                              <span>Delivered</span>
                            </>
                          ) : msg.status === "failed" ? (
                            <span className="text-rose-500 font-semibold flex items-center gap-1">
                              <AlertCircle className="h-3 w-3" />
                              <span>Delivery Failed</span>
                            </span>
                          ) : (
                            <span>Pending dispatch...</span>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* ── Reply Composer Box ──────────────────────────────── */}
              <div className="p-3.5 border-t border-border/70 dark:border-white/[0.08] bg-card space-y-2.5">
                {/* Subject & Controls Row */}
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2 flex-1 min-w-[240px]">
                    <span className="text-[11px] font-bold text-muted-foreground uppercase shrink-0">Subject:</span>
                    <Input
                      value={replySubject}
                      onChange={(e) => setReplySubject(e.target.value)}
                      placeholder="Email subject..."
                      className="text-xs h-7 bg-background/80 font-medium"
                    />
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {/* Template Picker Dropdown */}
                    <select
                      value={selectedTemplateId}
                      onChange={(e) => handleSelectTemplate(e.target.value)}
                      className="text-xs h-7 px-2 rounded-lg border border-border/80 bg-background font-medium focus:outline-none focus:ring-1 focus:ring-primary cursor-pointer max-w-[220px]"
                    >
                      <option value="">Insert Template (31 Available)...</option>
                      <optgroup label="Core Pipeline (9)">
                        {ALL_RECRUITING_TEMPLATES.filter((t) => t.category === "core").map((tpl) => (
                          <option key={tpl.id} value={tpl.id}>
                            {tpl.name}
                          </option>
                        ))}
                      </optgroup>
                      <optgroup label="Supporting Outreach (16)">
                        {ALL_RECRUITING_TEMPLATES.filter((t) => t.category === "supporting").map((tpl) => (
                          <option key={tpl.id} value={tpl.id}>
                            {tpl.name}
                          </option>
                        ))}
                      </optgroup>
                      <optgroup label="Internal Notifications (6)">
                        {ALL_RECRUITING_TEMPLATES.filter((t) => t.category === "internal").map((tpl) => (
                          <option key={tpl.id} value={tpl.id}>
                            {tpl.name}
                          </option>
                        ))}
                      </optgroup>
                    </select>

                    {/* AI Suggest Reply Button */}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleAIDraft}
                      disabled={isDraftingAI}
                      className="h-7 px-2.5 text-xs font-semibold gap-1 bg-primary/5 hover:bg-primary/10 text-primary border-primary/20"
                      title="AI drafts a warm, natural reply for your review"
                    >
                      <Sparkles className={`h-3 w-3 ${isDraftingAI ? "animate-spin" : ""}`} />
                      <span>{isDraftingAI ? "Drafting..." : "Suggest Reply"}</span>
                    </Button>
                  </div>
                </div>

                {/* Reply Message Textarea */}
                <Textarea
                  placeholder={`Write your reply to ${threadData.candidate_name}... (HR reviews and approves before sending)`}
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  className="min-h-[90px] text-xs leading-relaxed bg-background/80 resize-none font-normal"
                />

                {/* Footer Send Action */}
                <div className="flex items-center justify-between pt-1">
                  <p className="text-[10px] text-muted-foreground flex items-center gap-1">
                    <Mail className="h-3 w-3 text-muted-foreground" />
                    <span>Replies send directly in candidate's Gmail thread</span>
                  </p>

                  <Button
                    size="sm"
                    disabled={!replyText.trim() || sendMutation.isPending}
                    onClick={() => sendMutation.mutate(replyText)}
                    className="h-8 px-4 text-xs font-semibold gap-1.5 shadow-xs"
                  >
                    <Send className="h-3.5 w-3.5" />
                    <span>{sendMutation.isPending ? "Sending..." : "Approve & Send via Gmail"}</span>
                  </Button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* ── Candidate Detail Drawer ─────────────────────────────────── */}
      {selectedCandidateId && (
        <CandidateDrawer
          candidate={
            selectedConv
              ? ({
                  id: selectedConv.candidate_id,
                  name: selectedConv.candidate_name,
                  email: selectedConv.candidate_email,
                  phone: selectedConv.candidate_phone,
                  opening_id: "",
                  opening_title: selectedConv.opening_title || undefined,
                  stage: selectedConv.candidate_stage as any,
                  cv_text: "",
                  matched_skills: [],
                  missing_skills: [],
                  red_flags: [],
                  created_at: selectedConv.last_message_at || new Date().toISOString(),
                  updated_at: selectedConv.last_message_at || new Date().toISOString(),
                  user_id: "",
                } as any)
              : null
          }
          open={candidateDrawerOpen}
          onClose={() => setCandidateDrawerOpen(false)}
          onCandidateUpdated={() => {
            queryClient.invalidateQueries({ queryKey: ["email-conversations"] });
            queryClient.invalidateQueries({ queryKey: ["email-thread", selectedCandidateId] });
          }}
        />
      )}

      {/* ── Schedule Interview Modal ───────────────────────────────── */}
      {selectedCandidateId && scheduleModalOpen && selectedConv && (
        <ScheduleInviteModal
          isOpen={scheduleModalOpen}
          onClose={() => setScheduleModalOpen(false)}
          candidate={{
            id: selectedConv.candidate_id,
            name: selectedConv.candidate_name,
            email: selectedConv.candidate_email,
            phone: selectedConv.candidate_phone,
            opening_id: "",
            stage: selectedConv.candidate_stage as any,
            cv_text: "",
            matched_skills: [],
            missing_skills: [],
            red_flags: [],
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            user_id: "",
          }}
        />
      )}
    </div>
  );
}

export default function InboxPage() {
  return (
    <AppShell title="Recruiting Inbox">
      <Suspense
        fallback={
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4 h-[calc(100vh-8rem)]">
            <Skeleton className="md:col-span-4 h-full rounded-2xl" />
            <Skeleton className="md:col-span-8 h-full rounded-2xl" />
          </div>
        }
      >
        <InboxContent />
      </Suspense>
    </AppShell>
  );
}
