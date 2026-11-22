"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  DragStartEvent,
  DragEndEvent,
  closestCenter,
} from "@dnd-kit/core";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Plus,
  Search,
  RefreshCw,
  Briefcase,
  X,
  Filter,
  Download,
  Users,
  History,
  LayoutGrid,
  Table2,
  Calendar,
  Sparkles,
  Scale,
  RotateCcw,
} from "lucide-react";

import {
  Candidate,
  CandidateStage,
  candidatesApi,
  jobOpeningsApi,
  JobOpening,
  backendFetch,
  getAuthToken,
} from "@/lib/api";
import { useToast } from "@/components/ui/use-toast";
import { PIPELINE_COLUMNS, PipelineStage } from "./types";
import { KanbanColumn } from "./kanban-column";
import { KanbanCard } from "./kanban-card";
import { KanbanTable } from "./kanban-table";
import { PipelineAuditDrawer } from "./pipeline-audit-drawer";
import { BulkActionsToolbar } from "./bulk-actions-toolbar";
import { AddCandidateDialog } from "@/components/candidates/add-candidate-dialog";
import { CandidateDrawer } from "@/components/candidates/candidate-drawer";
import { ContactCandidateDialog } from "@/components/candidates/contact-candidate-dialog";
import { CompareDialog } from "@/components/candidates/compare-dialog";
import { ScheduleInviteModal } from "@/components/scheduling/schedule-invite-modal";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/ui/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";

interface KanbanBoardProps {
  defaultSelectedCandidateId?: string;
}

export function KanbanBoard({ defaultSelectedCandidateId }: KanbanBoardProps = {}) {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  // View Mode: Board vs Table
  const [viewMode, setViewMode] = useState<"board" | "table">("board");

  // Search & Filter State
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedOpeningId, setSelectedOpeningId] = useState<string>("all");
  const [selectedScoreFilter, setSelectedScoreFilter] = useState<string>("all");
  const [selectedStageFilter, setSelectedStageFilter] = useState<string>("all");
  const [selectedDateFilter, setSelectedDateFilter] = useState<string>("all");
  const [mobileSelectedStage, setMobileSelectedStage] = useState<string>("all");

  // Dialog & Drawer States
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [auditDrawerOpen, setAuditDrawerOpen] = useState(false);
  const [compareOpen, setCompareOpen] = useState(false);

  // Quick Action Dialogs State
  const [contactCandidate, setContactCandidate] = useState<Candidate | null>(null);
  const [contactDialogOpen, setContactDialogOpen] = useState(false);
  const [scheduleCandidate, setScheduleCandidate] = useState<Candidate | null>(null);
  const [scheduleModalOpen, setScheduleModalOpen] = useState(false);

  // Bulk Selection States
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<string[]>([]);
  const [isBulkProcessing, setIsBulkProcessing] = useState(false);

  const handleToggleSelect = useCallback((candidateId: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setSelectedCandidateIds((prev) =>
      prev.includes(candidateId) ? prev.filter((id) => id !== candidateId) : [...prev, candidateId]
    );
  }, []);

  const handleSelectAll = useCallback((candidateIds: string[]) => {
    setSelectedCandidateIds(candidateIds);
  }, []);

  const handleClearSelection = useCallback(() => {
    setSelectedCandidateIds([]);
  }, []);

  // Active dragging item for DragOverlay
  const [activeCandidate, setActiveCandidate] = useState<Candidate | null>(null);

  // Configure Sensors (5px threshold prevents accidental drag on normal clicks)
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5,
      },
    })
  );

  // 1. Fetch Job Openings for filtering
  const { data: openingsData } = useQuery({
    queryKey: ["job-openings"],
    queryFn: () => jobOpeningsApi.list(),
  });
  const openings = openingsData?.items || [];

  // 2. Fetch Candidates
  const {
    data: candidatesData,
    isLoading,
    isRefetching,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["candidates", selectedOpeningId],
    queryFn: () =>
      candidatesApi.list({
        opening_id: selectedOpeningId !== "all" ? selectedOpeningId : undefined,
        limit: 500,
      }),
  });
  const candidates = candidatesData?.items || [];

  // Open drawer if default candidate passed
  useEffect(() => {
    if (defaultSelectedCandidateId && candidates.length > 0) {
      const match = candidates.find((c) => c.id === defaultSelectedCandidateId);
      if (match) {
        setSelectedCandidate(match);
        setDrawerOpen(true);
      }
    }
  }, [defaultSelectedCandidateId, candidates]);

  // 3. Stage Update Mutation with Optimistic Updates & Toast
  const updateStageMutation = useMutation({
    mutationFn: async ({
      id,
      stage,
      candidateName,
    }: {
      id: string;
      stage: CandidateStage;
      candidateName: string;
    }) => {
      return candidatesApi.updateStage(id, stage);
    },
    onMutate: async ({ id, stage }) => {
      await queryClient.cancelQueries({ queryKey: ["candidates"] });
      const previous = queryClient.getQueryData(["candidates", selectedOpeningId]);

      queryClient.setQueryData(
        ["candidates", selectedOpeningId],
        (old: { items: Candidate[]; total: number } | undefined) => {
          if (!old) return old;
          return {
            ...old,
            items: old.items.map((item) =>
              item.id === id ? { ...item, stage } : item
            ),
          };
        }
      );

      return { previous };
    },
    onError: (err: any, variables, context: any) => {
      if (context?.previous) {
        queryClient.setQueryData(["candidates", selectedOpeningId], context.previous);
      }
      toast({
        title: "Stage update failed",
        description: err.message || "Could not move candidate.",
        variant: "destructive",
      });
    },
    onSuccess: (updated) => {
      toast({
        title: "Candidate Moved",
        description: `${updated.name} transitioned to ${updated.stage}.`,
      });
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
    },
  });

  // Drag Handlers
  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event;
    const found = candidates.find((c) => c.id === active.id);
    if (found) {
      setActiveCandidate(found);
    }
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCandidate(null);

    if (!over) return;

    const candidateId = active.id as string;
    const currentCandidate = candidates.find((c) => c.id === candidateId);
    if (!currentCandidate) return;

    let targetStage: PipelineStage | null = null;

    if (PIPELINE_COLUMNS.some((col) => col.id === over.id)) {
      targetStage = over.id as PipelineStage;
    } else {
      const overCandidate = candidates.find((c) => c.id === over.id);
      if (overCandidate) {
        if (["scheduled", "contacted", "interviewed"].includes(overCandidate.stage)) {
          targetStage = "interview";
        } else {
          targetStage = overCandidate.stage;
        }
      }
    }

    if (targetStage && targetStage !== currentCandidate.stage) {
      updateStageMutation.mutate({
        id: candidateId,
        stage: targetStage,
        candidateName: currentCandidate.name,
      });
    }
  };

  // Quick Action Handlers
  const handleEmailAction = useCallback((candidate: Candidate) => {
    setContactCandidate(candidate);
    setContactDialogOpen(true);
  }, []);

  const handleWhatsAppAction = useCallback((candidate: Candidate) => {
    if (candidate.phone) {
      const cleanPhone = candidate.phone.replace(/[^0-9+]/g, "");
      window.open(`https://wa.me/${cleanPhone.replace("+", "")}`, "_blank");
    } else {
      setContactCandidate(candidate);
      setContactDialogOpen(true);
    }
  }, []);

  const handleScheduleAction = useCallback((candidate: Candidate) => {
    setScheduleCandidate(candidate);
    setScheduleModalOpen(true);
  }, []);

  const handleStageChangeFromTable = useCallback(
    (candidateId: string, newStage: CandidateStage, candidateName: string) => {
      updateStageMutation.mutate({
        id: candidateId,
        stage: newStage,
        candidateName,
      });
    },
    [updateStageMutation]
  );

  // Multi-Criteria Filtering
  const filteredCandidates = useMemo(() => {
    return candidates.filter((cand) => {
      // 1. Search Query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchName = cand.name?.toLowerCase().includes(q);
        const matchEmail = cand.email?.toLowerCase().includes(q);
        const matchOpening = cand.opening_title?.toLowerCase().includes(q);
        const matchSkills = cand.matched_skills?.some((s) => s.toLowerCase().includes(q));
        if (!matchName && !matchEmail && !matchOpening && !matchSkills) {
          return false;
        }
      }

      // 2. Stage Filter
      if (selectedStageFilter !== "all") {
        if (selectedStageFilter === "interview") {
          if (!["interview", "scheduled", "contacted", "interviewed"].includes(cand.stage)) {
            return false;
          }
        } else if (cand.stage !== selectedStageFilter) {
          return false;
        }
      }

      // 3. Score Filter
      if (selectedScoreFilter !== "all") {
        const score = cand.score;
        if (selectedScoreFilter === "high" && (score === null || score === undefined || score < 80)) {
          return false;
        }
        if (selectedScoreFilter === "medium" && (score === null || score === undefined || score < 60 || score >= 80)) {
          return false;
        }
        if (selectedScoreFilter === "low" && (score === null || score === undefined || score >= 60)) {
          return false;
        }
        if (selectedScoreFilter === "unscored" && score !== null && score !== undefined) {
          return false;
        }
      }

      // 4. Date Filter
      if (selectedDateFilter !== "all") {
        const candDate = new Date(cand.created_at || cand.updated_at);
        const now = new Date();
        const diffMs = now.getTime() - candDate.getTime();
        const diffHours = diffMs / (1000 * 60 * 60);

        if (selectedDateFilter === "today" && diffHours > 24) {
          return false;
        }
        if (selectedDateFilter === "7d" && diffHours > 24 * 7) {
          return false;
        }
        if (selectedDateFilter === "30d" && diffHours > 24 * 30) {
          return false;
        }
      }

      return true;
    });
  }, [candidates, searchQuery, selectedStageFilter, selectedScoreFilter, selectedDateFilter]);

  const hasActiveFilters =
    searchQuery.trim() !== "" ||
    selectedOpeningId !== "all" ||
    selectedScoreFilter !== "all" ||
    selectedStageFilter !== "all" ||
    selectedDateFilter !== "all";

  const handleResetFilters = () => {
    setSearchQuery("");
    setSelectedOpeningId("all");
    setSelectedScoreFilter("all");
    setSelectedStageFilter("all");
    setSelectedDateFilter("all");
  };

  // Shortlist CSV Export Download with Bearer Authentication
  const handleExportShortlist = async () => {
    const targetOpeningId =
      selectedOpeningId && selectedOpeningId !== "all"
        ? selectedOpeningId
        : openings[0]?.id;

    if (!targetOpeningId) {
      toast({
        title: "No Openings Available",
        description: "Create a job opening before exporting candidate shortlists.",
        variant: "destructive",
      });
      return;
    }

    try {
      const token = getAuthToken();
      const res = await backendFetch(
        `/api/v1/job-openings/${targetOpeningId}/shortlist/export`,
        {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        }
      );
      if (!res.ok) {
        throw new Error(`Export failed with status ${res.status}`);
      }
      const blob = await res.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = `shortlist_${targetOpeningId}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);
      toast({
        title: "Export Completed",
        description: "Candidate shortlist CSV downloaded successfully.",
      });
    } catch (err: any) {
      toast({
        title: "Export Failed",
        description: err.message || "Failed to download shortlist CSV.",
        variant: "destructive",
      });
    }
  };

  const handleBulkMoveStage = async (stage: CandidateStage) => {
    if (selectedCandidateIds.length === 0) return;
    setIsBulkProcessing(true);
    try {
      const res = await candidatesApi.bulkStage(selectedCandidateIds, stage);
      toast({
        title: "Bulk Stage Update",
        description: res.message,
      });
      setSelectedCandidateIds([]);
      queryClient.invalidateQueries({ queryKey: ["candidates"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
      queryClient.invalidateQueries({ queryKey: ["audit-logs-recent"] });
    } catch (err: any) {
      toast({
        title: "Bulk update failed",
        description: err.message || "Could not move candidates.",
        variant: "destructive",
      });
    } finally {
      setIsBulkProcessing(false);
    }
  };

  const handleBulkDelete = async () => {
    if (selectedCandidateIds.length === 0) return;
    if (
      !confirm(
        `Are you sure you want to permanently delete ${selectedCandidateIds.length} candidate(s)?`
      )
    )
      return;

    setIsBulkProcessing(true);
    try {
      const res = await candidatesApi.bulkDelete(selectedCandidateIds);
      toast({
        title: "Candidates Deleted",
        description: res.message,
      });
      setSelectedCandidateIds([]);
      queryClient.invalidateQueries({ queryKey: ["candidates"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
      queryClient.invalidateQueries({ queryKey: ["audit-logs-recent"] });
    } catch (err: any) {
      toast({
        title: "Bulk delete failed",
        description: err.message || "Could not delete candidates.",
        variant: "destructive",
      });
    } finally {
      setIsBulkProcessing(false);
    }
  };

  const handleBulkScore = async () => {
    if (selectedCandidateIds.length === 0) return;
    setIsBulkProcessing(true);
    try {
      let scored = 0;
      for (const cid of selectedCandidateIds) {
        await candidatesApi.score(cid);
        scored++;
      }
      toast({
        title: "Bulk AI Scoring Finished",
        description: `Successfully scored ${scored} candidate(s).`,
      });
      setSelectedCandidateIds([]);
      queryClient.invalidateQueries({ queryKey: ["candidates"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
    } catch (err: any) {
      toast({
        title: "Scoring Error",
        description: err.message || "Failed to complete AI scoring.",
        variant: "destructive",
      });
    } finally {
      setIsBulkProcessing(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-7.5rem)] w-full space-y-3.5">
      {/* ── Page Header & Top Toolbar ───────────────────────────────── */}
      <PageHeader
        title="Candidate Pipeline"
        description="Active candidate evaluation pipeline with real-time drag-and-drop, table views, and automated actions."
        badge={
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="gap-1 font-mono text-[11px] bg-card">
              <Users className="h-3 w-3 text-primary" />
              <span>{filteredCandidates.length} Active Candidates</span>
            </Badge>
            <Badge variant="outline" className="gap-1.5 font-mono text-[11px] bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span>Pipeline Agent Active</span>
            </Badge>
          </div>
        }
        actions={
          <div className="flex items-center gap-2">
            {/* View Mode Toggle: Board vs Table */}
            <div className="inline-flex rounded-lg border border-border/80 bg-muted/40 p-0.5">
              <Button
                variant={viewMode === "board" ? "default" : "ghost"}
                size="sm"
                onClick={() => setViewMode("board")}
                className="h-7 px-2.5 text-xs gap-1.5 font-medium rounded-md"
              >
                <LayoutGrid className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Board</span>
              </Button>
              <Button
                variant={viewMode === "table" ? "default" : "ghost"}
                size="sm"
                onClick={() => setViewMode("table")}
                className="h-7 px-2.5 text-xs gap-1.5 font-medium rounded-md"
              >
                <Table2 className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Table</span>
              </Button>
            </div>

            <Button
              id="btn-open-audit-drawer"
              variant="outline"
              size="sm"
              onClick={() => setAuditDrawerOpen(true)}
              className="gap-1.5 h-8 text-xs font-medium"
              title="View Pipeline Audit Trail"
            >
              <History className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="hidden sm:inline">Audit Trail</span>
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={handleExportShortlist}
              className="gap-1.5 h-8 text-xs font-medium"
              title="Download Shortlist CSV"
            >
              <Download className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Export CSV</span>
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              disabled={isRefetching}
              className="h-8 w-8 p-0"
              title="Refresh pipeline"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isRefetching ? "animate-spin" : ""}`} />
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setCompareOpen(true)}
              className="h-8 font-medium gap-1.5 text-xs shadow-xs"
              title="Side-by-side candidate comparison"
            >
              <Scale className="h-3.5 w-3.5 text-primary" />
              <span>Compare</span>
            </Button>

            <Button
              size="sm"
              onClick={() => setAddDialogOpen(true)}
              className="h-8 font-medium gap-1.5 text-xs shadow-xs"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Add Candidate</span>
            </Button>
          </div>
        }
      >
        {/* ── Filter Controls Row ───────────────────────────────────────── */}
        <div className="flex flex-wrap items-center gap-2 pt-1 w-full">
          {/* Search Input */}
          <div className="relative flex-1 min-w-[200px] max-w-sm">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              placeholder="Search by name, email, or skill..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 text-xs h-8 bg-card"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </div>

          {/* Requisition / Opening Filter */}
          <div className="flex items-center gap-1.5">
            <Briefcase className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
            <select
              value={selectedOpeningId}
              onChange={(e) => setSelectedOpeningId(e.target.value)}
              className="text-xs h-8 px-2.5 rounded-lg border border-border/80 bg-card font-medium focus:outline-none focus:ring-1 focus:ring-primary cursor-pointer max-w-[190px] truncate"
            >
              <option value="all">All Requisitions ({openings.length})</option>
              {openings.map((op) => (
                <option key={op.id} value={op.id}>
                  {op.title}
                </option>
              ))}
            </select>
          </div>

          {/* Stage Filter */}
          <select
            value={selectedStageFilter}
            onChange={(e) => setSelectedStageFilter(e.target.value)}
            className="text-xs h-8 px-2.5 rounded-lg border border-border/80 bg-card font-medium focus:outline-none focus:ring-1 focus:ring-primary cursor-pointer"
          >
            <option value="all">All Stages</option>
            {PIPELINE_COLUMNS.map((col) => (
              <option key={col.id} value={col.id}>
                {col.title}
              </option>
            ))}
          </select>

          {/* Score Filter */}
          <select
            value={selectedScoreFilter}
            onChange={(e) => setSelectedScoreFilter(e.target.value)}
            className="text-xs h-8 px-2.5 rounded-lg border border-border/80 bg-card font-medium focus:outline-none focus:ring-1 focus:ring-primary cursor-pointer"
          >
            <option value="all">All Scores</option>
            <option value="high">High Match (≥ 80%)</option>
            <option value="medium">Medium Match (60% - 79%)</option>
            <option value="low">Low Match (&lt; 60%)</option>
            <option value="unscored">Unscored / Pending</option>
          </select>

          {/* Date Filter */}
          <select
            value={selectedDateFilter}
            onChange={(e) => setSelectedDateFilter(e.target.value)}
            className="text-xs h-8 px-2.5 rounded-lg border border-border/80 bg-card font-medium focus:outline-none focus:ring-1 focus:ring-primary cursor-pointer"
          >
            <option value="all">All Time</option>
            <option value="today">Past 24 Hours</option>
            <option value="7d">Past 7 Days</option>
            <option value="30d">Past 30 Days</option>
          </select>

          {/* Reset Filters button */}
          {hasActiveFilters && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleResetFilters}
              className="h-8 px-2 text-xs text-muted-foreground hover:text-foreground gap-1"
            >
              <RotateCcw className="h-3 w-3" />
              <span>Reset Filters</span>
            </Button>
          )}
        </div>
      </PageHeader>

      {/* ── Mobile Column Tab Switcher (Board View Only) ─────────────── */}
      {viewMode === "board" && (
        <div className="flex lg:hidden gap-1 overflow-x-auto pb-1 shrink-0">
          <Button
            variant={mobileSelectedStage === "all" ? "default" : "outline"}
            size="sm"
            onClick={() => setMobileSelectedStage("all")}
            className="text-xs h-7 shrink-0"
          >
            All Stages
          </Button>
          {PIPELINE_COLUMNS.map((col) => (
            <Button
              key={col.id}
              variant={mobileSelectedStage === col.id ? "default" : "outline"}
              size="sm"
              onClick={() => setMobileSelectedStage(col.id)}
              className="text-xs h-7 shrink-0 gap-1"
            >
              <span className={`h-1.5 w-1.5 rounded-full ${col.dotColor}`} />
              {col.title}
            </Button>
          ))}
        </div>
      )}

      {/* ── Main Pipeline Content Body ───────────────────────────────── */}
      <div className="flex-1 min-h-0">
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-6 gap-3.5 h-full">
            {PIPELINE_COLUMNS.map((col) => (
              <div
                key={col.id}
                className="flex flex-col h-full rounded-2xl border border-border/60 bg-card/30 p-3 space-y-3"
              >
                <div className="flex items-center justify-between pb-2 border-b border-border/40">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-4 w-6 rounded-full" />
                </div>
                <Skeleton className="h-28 w-full rounded-xl" />
                <Skeleton className="h-28 w-full rounded-xl" />
              </div>
            ))}
          </div>
        ) : isError ? (
          <ErrorState
            title="Failed to load pipeline"
            message={(error as Error)?.message || "Could not fetch candidates."}
            onRetry={() => refetch()}
          />
        ) : candidates.length === 0 ? (
          <EmptyState
            icon={Users}
            title="Pipeline is empty"
            description="Add candidate profiles or upload resume PDFs with automatic AI text extraction."
            actionText="Add First Candidate"
            onAction={() => setAddDialogOpen(true)}
          />
        ) : viewMode === "table" ? (
          /* Table View */
          <KanbanTable
            candidates={filteredCandidates}
            selectedCandidateIds={selectedCandidateIds}
            onToggleSelect={handleToggleSelect}
            onSelectAll={handleSelectAll}
            onClearSelection={handleClearSelection}
            onCardClick={(cand) => {
              setSelectedCandidate(cand);
              setDrawerOpen(true);
            }}
            onStageChange={handleStageChangeFromTable}
            onEmail={handleEmailAction}
            onWhatsApp={handleWhatsAppAction}
            onSchedule={handleScheduleAction}
          />
        ) : (
          /* Board (Kanban) View */
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
          >
            <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-6 gap-3.5 h-full overflow-hidden">
              {PIPELINE_COLUMNS.map((col) => {
                if (mobileSelectedStage !== "all" && mobileSelectedStage !== col.id) {
                  return null;
                }

                const stageCandidates = filteredCandidates.filter((c) => {
                  if (col.id === c.stage) return true;
                  if (col.id === "interview" && ["scheduled", "contacted", "interviewed"].includes(c.stage)) {
                    return true;
                  }
                  return false;
                });

                return (
                  <KanbanColumn
                    key={col.id}
                    column={col}
                    candidates={stageCandidates}
                    selectedCandidateIds={selectedCandidateIds}
                    onToggleSelect={handleToggleSelect}
                    onCardClick={(cand) => {
                      setSelectedCandidate(cand);
                      setDrawerOpen(true);
                    }}
                    onAddClick={() => setAddDialogOpen(true)}
                    onEmail={handleEmailAction}
                    onWhatsApp={handleWhatsAppAction}
                    onSchedule={handleScheduleAction}
                  />
                );
              })}
            </div>

            {/* Drag Overlay for smooth preview */}
            <DragOverlay>
              {activeCandidate ? (
                <KanbanCard candidate={activeCandidate} isOverlay />
              ) : null}
            </DragOverlay>
          </DndContext>
        )}
      </div>

      {/* ── Floating Bulk Actions Bar ──────────────────────────────── */}
      <BulkActionsToolbar
        selectedCount={selectedCandidateIds.length}
        onMoveStage={handleBulkMoveStage}
        onBulkScore={handleBulkScore}
        onExportCsv={handleExportShortlist}
        onDelete={handleBulkDelete}
        onClear={handleClearSelection}
        isProcessing={isBulkProcessing}
      />

      {/* ── Pipeline Audit Log Drawer ──────────────────────────────── */}
      <PipelineAuditDrawer
        open={auditDrawerOpen}
        onClose={() => setAuditDrawerOpen(false)}
        openingId={selectedOpeningId}
      />

      {/* ── Add Candidate Modal ─────────────────────────────────────── */}
      <AddCandidateDialog
        open={addDialogOpen}
        onClose={() => setAddDialogOpen(false)}
        openings={openings}
        defaultOpeningId={selectedOpeningId !== "all" ? selectedOpeningId : undefined}
        onSuccess={() => refetch()}
      />

      {/* ── Candidate Detail Drawer ─────────────────────────────────── */}
      <CandidateDrawer
        candidate={selectedCandidate}
        open={drawerOpen}
        onClose={() => {
          setDrawerOpen(false);
          setSelectedCandidate(null);
        }}
        onCandidateUpdated={(updated) => {
          setSelectedCandidate(updated);
          queryClient.invalidateQueries({ queryKey: ["candidates"] });
        }}
      />

      {/* ── Quick Action: Email Candidate Dialog ───────────────────── */}
      {contactDialogOpen && (
        <ContactCandidateDialog
          open={contactDialogOpen}
          onOpenChange={(open) => {
            setContactDialogOpen(open);
            if (!open) setContactCandidate(null);
          }}
          candidate={contactCandidate}
        />
      )}

      {/* ── Quick Action: Schedule Interview Modal ─────────────────── */}
      {scheduleModalOpen && scheduleCandidate && (
        <ScheduleInviteModal
          isOpen={scheduleModalOpen}
          onClose={() => {
            setScheduleModalOpen(false);
            setScheduleCandidate(null);
          }}
          candidate={scheduleCandidate}
        />
      )}

      {/* ── Side-by-Side Candidate Comparison Modal ─────────────────── */}
      <CompareDialog
        open={compareOpen}
        onOpenChange={setCompareOpen}
        initialOpeningId={selectedOpeningId !== "all" ? selectedOpeningId : undefined}
      />
    </div>
  );
}
