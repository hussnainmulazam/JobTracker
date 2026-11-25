"use client";

import React, { useEffect, useState, useMemo, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Settings,
  User as UserIcon,
  Moon,
  Sun,
  Monitor,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Cpu,
  Database,
  Shield,
  LogOut,
  ExternalLink,
  Mail,
  Calendar,
  FileSpreadsheet,
  Check,
  Unlink,
  Save,
  KeyRound,
  Inbox,
  Filter,
  AlertTriangle,
  Clock,
  MessageSquare,
  UserCheck,
  FileText,
  Activity,
  Layers,
  Copy,
  Search,
  ArrowRight,
  ShieldCheck,
  Zap,
  Sparkles,
  Eye,
  Edit3,
  Plus,
  Trash2,
  Star,
} from "lucide-react";

import {
  api,
  apiFetch,
  API_BASE_URL,
  googleApi,
  jobOpeningsApi,
  healthApi,
  auditLogsApi,
  onboardingApi,
  DbHealthResponse,
  PineconeHealthResponse,
  GoogleAccountStatus,
  GmailSyncResponse,
  AuditLog,
  removeAuthToken,
  recruitingTemplatesApi,
  RecruitingTemplateModel,
} from "@/lib/api";
import { ALL_RECRUITING_TEMPLATES } from "@/lib/template-registry";
import {
  LIFECYCLE_TEMPLATES,
  DEFAULT_LIFECYCLE_TEMPLATES,
  VARIABLE_CHIPS,
} from "@/components/setup/setup-wizard-dialog";
import { useTheme } from "@/components/theme-provider";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/ui/page-header";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/use-toast";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { AgentControlHub } from "@/components/agent/agent-control-hub";

interface UserProfile {
  id: string;
  email: string;
  created_at: string;
}

interface ModelHealthItem {
  model: string;
  role?: string;
  task?: string;
  status: "ok" | "fail";
  latency_ms: number;
  error?: string | null;
  error_type?: string | null;
}

interface AIModelsHealthResponse {
  status: "healthy" | "degraded" | "failing" | "unconfigured";
  models?: Record<string, ModelHealthItem> | ModelHealthItem[];
  openrouter_base_url?: string;
  grok_base_url?: string;
  active_provider?: string;
}

function SettingsPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialTab = searchParams.get("tab") || "general";
  const [activeTab, setActiveTab] = useState<string>(initialTab);

  const { theme, setTheme } = useTheme();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Local state for Gmail sync filters
  const [filterQuery, setFilterQuery] = useState("");
  const [filterLabel, setFilterLabel] = useState("");
  const [defaultOpeningId, setDefaultOpeningId] = useState("");
  const [autoReplyEnabled, setAutoReplyEnabled] = useState(true);
  const [filterInitialized, setFilterInitialized] = useState(false);
  const [lastSyncResult, setLastSyncResult] = useState<GmailSyncResponse | null>(null);

  // Audit trail search & filter
  const [auditActionFilter, setAuditActionFilter] = useState<string>("all");
  const [auditSearchQuery, setAuditSearchQuery] = useState<string>("");

  // Sync tab with URL
  const handleTabChange = (val: string) => {
    setActiveTab(val);
    const url = new URL(window.location.href);
    url.searchParams.set("tab", val);
    window.history.replaceState({}, "", url.toString());
  };

  // Fetch active job openings for Gmail resume assignment
  const { data: openingsData } = useQuery({
    queryKey: ["settings-job-openings"],
    queryFn: () => jobOpeningsApi.list("active", 100),
    retry: false,
  });
  const activeOpenings = openingsData?.items || [];

  // 1. Fetch User Profile
  const { data: user, isLoading: isUserLoading } = useQuery<UserProfile>({
    queryKey: ["current-user"],
    queryFn: async () => apiFetch<UserProfile>("/api/v1/auth/me"),
    retry: false,
  });

  // 2. Fetch Backend Health
  const {
    data: backendHealth,
    isLoading: isHealthLoading,
    refetch: refetchBackendHealth,
  } = useQuery({
    queryKey: ["backend-health"],
    queryFn: async () => {
      return api.get<{
        status: string;
        database?: string;
        app: string;
        version: string;
        environment: string;
      }>("/health");
    },
  });

  // 2b. Fetch Live PostgreSQL Database Latency & Health
  const {
    data: dbHealth,
    isLoading: isDbHealthLoading,
    isFetching: isDbHealthFetching,
    refetch: refetchDbHealth,
  } = useQuery<DbHealthResponse>({
    queryKey: ["db-health"],
    queryFn: () => healthApi.checkDb(),
    retry: false,
  });

  // 2c. Fetch Live Pinecone Vector Database Latency & Health
  const {
    data: pineconeHealth,
    isLoading: isPineconeLoading,
    isFetching: isPineconeFetching,
    refetch: refetchPineconeHealth,
  } = useQuery<PineconeHealthResponse>({
    queryKey: ["pinecone-health"],
    queryFn: () => healthApi.checkPinecone(),
    retry: false,
  });

  // 3. Fetch Live AI Model Health
  const {
    data: aiHealth,
    isLoading: isAIHealthLoading,
    isRefetching: isAIRefetching,
    refetch: refetchAIHealth,
  } = useQuery<AIModelsHealthResponse>({
    queryKey: ["ai-models-health"],
    queryFn: async () => api.get<AIModelsHealthResponse>("/api/v1/ai/models/health"),
  });

  const modelList: ModelHealthItem[] = useMemo(() => {
    if (!aiHealth?.models) return [];
    if (Array.isArray(aiHealth.models)) return aiHealth.models;
    return Object.values(aiHealth.models);
  }, [aiHealth]);

  // 4. Fetch Google Account Status
  const {
    data: googleStatus,
    isLoading: isGoogleStatusLoading,
    refetch: refetchGoogleStatus,
  } = useQuery<GoogleAccountStatus>({
    queryKey: ["google-status"],
    queryFn: () => googleApi.getStatus(),
    retry: false,
  });

  // 5. Fetch Audit Trail Log
  const {
    data: auditData,
    isLoading: isAuditLoading,
    isFetching: isAuditFetching,
    refetch: refetchAudit,
  } = useQuery({
    queryKey: ["recentAuditLogs", auditActionFilter],
    queryFn: () => auditLogsApi.listRecent({ limit: 100 }),
  });
  const auditLogs = auditData?.items || [];

  // 6. Fetch Onboarding & Lifecycle Recruiting Templates
  const { data: onboardingData } = useQuery({
    queryKey: ["onboarding-status"],
    queryFn: () => onboardingApi.getStatus(),
    retry: false,
  });

  // Query DB templates (Single Source of Truth)
  const {
    data: dbTemplatesList,
    refetch: refetchDbTemplates,
    isLoading: isLoadingTemplates,
  } = useQuery({
    queryKey: ["recruiting-templates"],
    queryFn: () => recruitingTemplatesApi.list(),
  });

  const [activeSettingsTemplate, setActiveSettingsTemplate] = useState("cv_received");
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [settingsCategoryFilter, setSettingsCategoryFilter] = useState<"all" | "core" | "supporting" | "internal">("all");
  const [settingsTemplates, setSettingsTemplates] = useState<
    Record<string, { id?: string; subject: string; body: string; name?: string; is_active?: boolean; is_default?: boolean; is_custom?: boolean; stage_key?: string; category?: string }>
  >(DEFAULT_LIFECYCLE_TEMPLATES as any);
  const [settingsPreviewMode, setSettingsPreviewMode] = useState(false);
  const [isGeneratingAllSettingsAI, setIsGeneratingAllSettingsAI] = useState(false);
  const [regeneratingSettingsKey, setRegeneratingSettingsKey] = useState<string | null>(null);

  const [isAddingCustom, setIsAddingCustom] = useState(false);
  const [newCustomStage, setNewCustomStage] = useState("custom_stage");
  const [newCustomName, setNewCustomName] = useState("");
  const [newCustomSubject, setNewCustomSubject] = useState("");
  const [newCustomBody, setNewCustomBody] = useState("");

  useEffect(() => {
    const dict: Record<string, any> = {};

    // 1. Preload all 31 production templates from registry
    ALL_RECRUITING_TEMPLATES.forEach((tpl) => {
      dict[tpl.id] = {
        id: tpl.id,
        name: tpl.name,
        subject: tpl.subject,
        body: tpl.body,
        is_active: true,
        is_default: true,
        is_custom: false,
        stage_key: tpl.id,
        category: tpl.category,
      };
    });

    // 2. Overlay user database edits if present
    if (dbTemplatesList && dbTemplatesList.length > 0) {
      dbTemplatesList.forEach((t) => {
        const cat = ALL_RECRUITING_TEMPLATES.find((at) => at.id === t.stage_key)?.category || "core";
        dict[t.id] = {
          id: t.id,
          name: t.name,
          subject: t.subject,
          body: t.body,
          is_active: t.is_active,
          is_default: t.is_default,
          is_custom: t.is_custom,
          stage_key: t.stage_key,
          category: cat,
        };
        // Also map by stage_key for backwards lookup
        if (t.is_default || !dict[t.stage_key]) {
          dict[t.stage_key] = dict[t.id];
        }
      });
    }

    setSettingsTemplates(dict);

    if (!selectedTemplateId) {
      setSelectedTemplateId("cv_received");
      setActiveSettingsTemplate("cv_received");
    }
  }, [dbTemplatesList]);

  const saveSettingsTemplatesMutation = useMutation({
    mutationFn: async () => {
      const sanitizedBatch: Record<string, any> = {};
      const sanitizedStep4: Record<string, any> = {};

      Object.entries(settingsTemplates).forEach(([k, v]) => {
        if (!v) return;
        const key = v.stage_key || k;
        sanitizedBatch[v.id || key] = {
          id: v.id,
          name: v.name || key,
          subject: (v.subject || "").trim() || "Application Status Update",
          body: (v.body || "").trim() || "Thank you for connecting with our recruiting team.",
          is_active: v.is_active !== false,
        };
        sanitizedStep4[key] = {
          name: v.name || key,
          subject: (v.subject || "").trim() || "Application Status Update",
          body: (v.body || "").trim() || "Thank you for connecting with our recruiting team.",
        };
      });

      await recruitingTemplatesApi.batchSave(sanitizedBatch);
      return onboardingApi.saveStep4({ templates: sanitizedStep4 });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recruiting-templates"] });
      queryClient.invalidateQueries({ queryKey: ["onboarding-status"] });
      toast({
        title: "Templates Saved",
        description: "Recruiting templates updated and saved to PostgreSQL database.",
      });
    },
    onError: (err: any) => {
      toast({
        title: "Failed to save templates",
        description: err.message || "Could not save templates.",
        variant: "destructive",
      });
    },
  });

  const duplicateTemplateMutation = useMutation({
    mutationFn: (templateId: string) => recruitingTemplatesApi.duplicate(templateId),
    onSuccess: (newTmpl) => {
      queryClient.invalidateQueries({ queryKey: ["recruiting-templates"] });
      setSelectedTemplateId(newTmpl.id);
      setActiveSettingsTemplate(newTmpl.stage_key);
      toast({
        title: "Template Duplicated",
        description: `Created copy: "${newTmpl.name}".`,
      });
    },
    onError: (err: any) => {
      toast({
        title: "Failed to duplicate template",
        description: err.message || "Could not duplicate template.",
        variant: "destructive",
      });
    },
  });

  const toggleTemplateActiveMutation = useMutation({
    mutationFn: (templateId: string) => recruitingTemplatesApi.toggle(templateId),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["recruiting-templates"] });
      toast({
        title: updated.is_active ? "Template Activated" : "Template Disabled",
        description: `"${updated.name}" is now ${updated.is_active ? "active" : "disabled"}.`,
      });
    },
    onError: (err: any) => {
      toast({
        title: "Failed to toggle template",
        description: err.message || "Could not toggle template.",
        variant: "destructive",
      });
    },
  });

  const setDefaultTemplateMutation = useMutation({
    mutationFn: (templateId: string) => recruitingTemplatesApi.setDefault(templateId),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["recruiting-templates"] });
      toast({
        title: "Default Template Set",
        description: `"${updated.name}" is now the default template for ${updated.stage_key}.`,
      });
    },
    onError: (err: any) => {
      toast({
        title: "Failed to set default template",
        description: err.message || "Could not set default template.",
        variant: "destructive",
      });
    },
  });

  const deleteTemplateMutation = useMutation({
    mutationFn: (templateId: string) => recruitingTemplatesApi.delete(templateId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recruiting-templates"] });
      setSelectedTemplateId(null);
      toast({
        title: "Template Deleted",
        description: "Custom template removed successfully.",
      });
    },
    onError: (err: any) => {
      toast({
        title: "Failed to delete template",
        description: err.message || "Could not delete template.",
        variant: "destructive",
      });
    },
  });

  const createCustomTemplateMutation = useMutation({
    mutationFn: (data: { stage_key: string; name: string; subject: string; body: string }) =>
      recruitingTemplatesApi.create({ ...data, is_custom: true, is_active: true }),
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: ["recruiting-templates"] });
      setIsAddingCustom(false);
      setNewCustomName("");
      setNewCustomSubject("");
      setNewCustomBody("");
      setSelectedTemplateId(created.id);
      setActiveSettingsTemplate(created.stage_key);
      toast({
        title: "Custom Template Created",
        description: `Created template "${created.name}".`,
      });
    },
    onError: (err: any) => {
      toast({
        title: "Failed to create template",
        description: err.message || "Could not create custom template.",
        variant: "destructive",
      });
    },
  });

  const handleSettingsGenerateAllAI = async () => {
    setIsGeneratingAllSettingsAI(true);
    try {
      const res = await recruitingTemplatesApi.regenerate();
      if (res?.templates) {
        queryClient.invalidateQueries({ queryKey: ["recruiting-templates"] });
        queryClient.invalidateQueries({ queryKey: ["onboarding-status"] });
        toast({
          title: "✨ All 11 Templates Generated with AI",
          description: `Generated in ${res.latency_seconds || 3.5}s using ${res.model_used || "AI"}. Short, warm, and human.`,
        });
      }
    } catch (err: any) {
      toast({
        title: "Generation error",
        description: err.message || "Failed to generate templates.",
        variant: "destructive",
      });
    } finally {
      setIsGeneratingAllSettingsAI(false);
    }
  };

  const handleSettingsRegenerateSingleAI = async (keyOrId: string, stageKey?: string) => {
    const targetKey = stageKey || keyOrId;
    setRegeneratingSettingsKey(keyOrId);
    try {
      const res = await recruitingTemplatesApi.regenerate({ single_template_key: targetKey });
      if (res?.templates && res.templates[targetKey]) {
        const item = res.templates[targetKey];
        setSettingsTemplates((prev: any) => ({
          ...prev,
          [keyOrId]: {
            ...prev[keyOrId],
            subject: item.subject,
            body: item.body,
            name: item.name || prev[keyOrId]?.name,
          },
        }));
        queryClient.invalidateQueries({ queryKey: ["recruiting-templates"] });
        queryClient.invalidateQueries({ queryKey: ["onboarding-status"] });
        toast({
          title: `✨ Template Regenerated with AI`,
          description: `Fresh human draft generated in ${res.latency_seconds || 1.2}s.`,
        });
      }
    } catch (err: any) {
      toast({
        title: "Regeneration failed",
        description: err.message || "Failed to regenerate template.",
        variant: "destructive",
      });
    } finally {
      setRegeneratingSettingsKey(null);
    }
  };

  const handleInsertVariableSettings = (token: string) => {
    const targetKey = selectedTemplateId || activeSettingsTemplate;
    const cur = settingsTemplates[targetKey] || { subject: "", body: "" };
    setSettingsTemplates({
      ...settingsTemplates,
      [targetKey]: {
        ...cur,
        body: cur.body ? `${cur.body} ${token}` : token,
      },
    });
  };

  // Synchronize filter input defaults with backend status
  useEffect(() => {
    if (googleStatus && !filterInitialized) {
      setFilterQuery(
        googleStatus.sync_query || "has:attachment (filename:pdf OR filename:docx) newer_than:30d"
      );
      setFilterLabel(googleStatus.sync_label || "INBOX");
      setDefaultOpeningId(googleStatus.default_opening_id || "");
      setAutoReplyEnabled(googleStatus.auto_reply_enabled ?? true);
      setFilterInitialized(true);
    }
  }, [googleStatus, filterInitialized]);

  // Handle OAuth callback parameters
  useEffect(() => {
    if (typeof window === "undefined") return;
    const urlParams = new URLSearchParams(window.location.search);
    const connectedParam = urlParams.get("google_connected");
    const partialParam = urlParams.get("partial");
    const errorParam = urlParams.get("google_error");

    if (connectedParam === "1") {
      if (partialParam === "1") {
        toast({
          title: "Partial Access Granted",
          description: "Some permissions were unticked. Reconnect your account to grant full Workspace access.",
          variant: "destructive",
        });
      } else {
        toast({
          title: "Google Workspace Connected",
          description: "Your Google account was linked with encrypted offline refresh credentials.",
        });
      }
      refetchGoogleStatus();
      const cleanUrl = window.location.pathname + "?tab=google";
      window.history.replaceState({}, document.title, cleanUrl);
    } else if (errorParam) {
      toast({
        title: "Google Connection Failed",
        description: decodeURIComponent(errorParam),
        variant: "destructive",
      });
      const cleanUrl = window.location.pathname + "?tab=google";
      window.history.replaceState({}, document.title, cleanUrl);
    }
  }, [toast, refetchGoogleStatus]);

  // Mutations for Google actions
  const connectMutation = useMutation({
    mutationFn: () => googleApi.getLoginUrl(),
    onSuccess: (data) => {
      if (data?.auth_url) window.location.href = data.auth_url;
    },
    onError: (err: any) => {
      const isNetworkErr = err?.message === "Failed to fetch" || err?.message?.includes("fetch");
      toast({
        title: "OAuth Initialization Failed",
        description: isNetworkErr
          ? `Unable to reach backend server. Please verify that the FastAPI backend is running on ${API_BASE_URL}.`
          : (err.message || "Failed to initialize Google authorization flow."),
        variant: "destructive",
      });
    },
  });

  const disconnectMutation = useMutation({
    mutationFn: () => googleApi.disconnect(),
    onSuccess: () => {
      toast({
        title: "Google Account Disconnected",
        description: "Integration disconnected and encrypted tokens cleared.",
      });
      setLastSyncResult(null);
      queryClient.invalidateQueries({ queryKey: ["google-status"] });
    },
    onError: (err: any) => {
      toast({
        title: "Disconnection Failed",
        description: err.message || "Could not disconnect Google account.",
        variant: "destructive",
      });
    },
  });

  const syncMutation = useMutation({
    mutationFn: () =>
      googleApi.syncGmail({
        query: filterQuery || undefined,
        label: filterLabel || undefined,
      }),
    onSuccess: (data) => {
      setLastSyncResult(data);
      queryClient.invalidateQueries({ queryKey: ["google-status"] });
      queryClient.invalidateQueries({ queryKey: ["candidates"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
      toast({
        title: "Gmail Sync Completed",
        description: `Found ${data.messages_found} messages. Processed ${data.messages_processed}, saved ${data.attachments_saved} resumes, created ${data.candidates_created} candidates.`,
      });
    },
    onError: (err: any) => {
      toast({
        title: "Gmail Sync Failed",
        description: err.message || "An error occurred while fetching candidate resumes.",
        variant: "destructive",
      });
    },
  });

  const saveSettingsMutation = useMutation({
    mutationFn: () =>
      googleApi.updateSettings({
        sync_query: filterQuery,
        sync_label: filterLabel,
        default_opening_id: defaultOpeningId || null,
        auto_reply_enabled: autoReplyEnabled,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["google-status"] });
      toast({
        title: "Filter Settings Saved",
        description: "Gmail resume search query, default opening, and auto-reply preference updated.",
      });
    },
    onError: (err: any) => {
      toast({
        title: "Failed to Save Settings",
        description: err.message || "Could not update filter settings.",
        variant: "destructive",
      });
    },
  });

  const handleLogout = async () => {
    try {
      removeAuthToken();
      await fetch("/api/auth/logout", { method: "POST" });
    } finally {
      window.location.href = "/login";
    }
  };

  const filteredAuditLogs = useMemo(() => {
    let list = auditLogs;
    if (auditActionFilter !== "all") {
      list = list.filter((item) => item.action === auditActionFilter);
    }
    if (auditSearchQuery.trim()) {
      const q = auditSearchQuery.toLowerCase();
      list = list.filter(
        (item) =>
          (item.candidate_name && item.candidate_name.toLowerCase().includes(q)) ||
          (item.opening_title && item.opening_title.toLowerCase().includes(q)) ||
          (item.details && item.details.toLowerCase().includes(q)) ||
          item.action.toLowerCase().includes(q)
      );
    }
    return list;
  }, [auditLogs, auditActionFilter, auditSearchQuery]);

  return (
    <AppShell title="Settings & Infrastructure">
      <div className="space-y-6 max-w-5xl pb-20">
        {/* Page Header */}
        <PageHeader
          title="Settings & Workspace Hub"
          description="Manage recruiter preferences, Google Workspace integrations, system health latency, message templates, and audit logs."
          badge={
            <Badge variant="outline" className="gap-1.5 font-mono text-[11px] px-2.5 py-1">
              <Shield className="h-3 w-3 text-primary" />
              <span>System Hub</span>
            </Badge>
          }
        />

        {/* Unified Tabs Navigation */}
        <Tabs value={activeTab} onValueChange={handleTabChange} className="space-y-6">
          <TabsList className="bg-muted/40 p-1 border border-border/70 rounded-xl flex flex-wrap gap-1 w-full justify-start overflow-x-auto">
            <TabsTrigger value="general" className="gap-1.5 text-xs font-semibold px-3 py-1.5">
              <UserIcon className="w-3.5 h-3.5" />
              <span>General & Account</span>
            </TabsTrigger>
            <TabsTrigger value="agent" className="gap-1.5 text-xs font-semibold px-3 py-1.5">
              <Sparkles className="w-3.5 h-3.5 text-amber-500" />
              <span>Agent Settings</span>
            </TabsTrigger>
            <TabsTrigger value="google" className="gap-1.5 text-xs font-semibold px-3 py-1.5">
              <Mail className="w-3.5 h-3.5" />
              <span>Google Workspace</span>
            </TabsTrigger>
            <TabsTrigger value="health" className="gap-1.5 text-xs font-semibold px-3 py-1.5">
              <Activity className="w-3.5 h-3.5 text-emerald-500" />
              <span>Integration Health</span>
            </TabsTrigger>
            <TabsTrigger value="templates" className="gap-1.5 text-xs font-semibold px-3 py-1.5">
              <MessageSquare className="w-3.5 h-3.5" />
              <span>Recruiting Templates</span>
            </TabsTrigger>
            <TabsTrigger value="audit" className="gap-1.5 text-xs font-semibold px-3 py-1.5">
              <Clock className="w-3.5 h-3.5" />
              <span>Audit Trail</span>
            </TabsTrigger>
          </TabsList>

          {/* ── TAB 1: GENERAL & ACCOUNT ──────────────────────────────────── */}
          <TabsContent value="general" className="space-y-5">
            {/* User Profile Card */}
            <Card className="border border-border/80 dark:border-white/[0.08] shadow-xs rounded-xl">
              <CardHeader className="pb-3 border-b border-border/50">
                <CardTitle className="text-sm font-semibold tracking-tight flex items-center gap-2">
                  <UserIcon className="h-4 w-4 text-primary" />
                  <span>Recruiter Profile & Session</span>
                </CardTitle>
                <CardDescription className="text-xs text-muted-foreground">
                  Your authenticated identity and Supabase session credentials
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 pt-4">
                {isUserLoading ? (
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-48" />
                    <Skeleton className="h-4 w-72" />
                  </div>
                ) : user ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                    <div className="p-3.5 rounded-lg border border-border/70 bg-muted/20 space-y-1">
                      <span className="text-[11px] text-muted-foreground font-medium">Email Address</span>
                      <p className="font-semibold text-foreground truncate">{user.email}</p>
                    </div>
                    <div className="p-3.5 rounded-lg border border-border/70 bg-muted/20 space-y-1">
                      <span className="text-[11px] text-muted-foreground font-medium">Recruiter Identifier (UUID)</span>
                      <p className="font-mono text-[11px] text-foreground truncate">{user.id}</p>
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground">No active session.</p>
                )}
              </CardContent>
            </Card>

            {/* Appearance & Theme Selector */}
            <Card className="border border-border/80 dark:border-white/[0.08] shadow-xs rounded-xl">
              <CardHeader className="pb-3 border-b border-border/50">
                <CardTitle className="text-sm font-semibold tracking-tight flex items-center gap-2">
                  <Sun className="h-4 w-4 text-primary" />
                  <span>Interface Theme & Styling</span>
                </CardTitle>
                <CardDescription className="text-xs text-muted-foreground">
                  Choose between Light, Dark, or System visual mode
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-4">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {[
                    { key: "light" as const, label: "Light", icon: Sun, desc: "Crisp neutral canvas" },
                    { key: "dark" as const, label: "Dark", icon: Moon, desc: "High contrast dark mode" },
                    { key: "system" as const, label: "System", icon: Monitor, desc: "Matches OS preferences" },
                  ].map((t) => {
                    const IconComp = t.icon;
                    const isSelected = theme === t.key;
                    return (
                      <button
                        key={t.key}
                        onClick={() => setTheme(t.key)}
                        className={`p-3.5 rounded-xl border text-left transition-all ${
                          isSelected
                            ? "bg-primary/[0.04] border-primary shadow-xs ring-1 ring-primary/30"
                            : "bg-card border-border/70 hover:border-border hover:bg-muted/30"
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <IconComp className={`w-4 h-4 ${isSelected ? "text-primary" : "text-muted-foreground"}`} />
                          {isSelected && <Check className="w-3.5 h-3.5 text-primary" />}
                        </div>
                        <span className="text-xs font-semibold text-foreground block">{t.label}</span>
                        <span className="text-[11px] text-muted-foreground">{t.desc}</span>
                      </button>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            {/* Sign Out Card */}
            <Card className="border border-border/80 dark:border-white/[0.08] shadow-xs rounded-xl">
              <CardContent className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="space-y-0.5">
                  <span className="text-xs font-semibold text-foreground">Sign Out of Hiring Loop</span>
                  <p className="text-[11px] text-muted-foreground">
                    End your active session securely.
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleLogout}
                  className="gap-1.5 text-xs text-destructive hover:bg-destructive/10 border-destructive/20 h-8"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Log Out</span>
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* ── TAB 2: GOOGLE WORKSPACE ───────────────────────────────────── */}
          <TabsContent value="google" className="space-y-5">
            <Card className="border border-border/80 dark:border-white/[0.08] shadow-xs rounded-xl">
              <CardHeader className="flex flex-row items-start justify-between pb-3 border-b border-border/50">
                <div className="space-y-0.5">
                  <CardTitle className="text-sm font-semibold tracking-tight flex items-center gap-2">
                    <Mail className="h-4 w-4 text-primary" />
                    <span>Google Workspace Integration</span>
                  </CardTitle>
                  <CardDescription className="text-xs text-muted-foreground">
                    OAuth2 offline authorization for candidate resume ingestion, Gmail threads, and Google Meet
                  </CardDescription>
                </div>
                {isGoogleStatusLoading ? (
                  <Skeleton className="h-6 w-20" />
                ) : (
                  <Badge
                    className={`text-[11px] font-medium capitalize ${
                      googleStatus?.is_connected
                        ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20"
                        : "bg-muted text-muted-foreground border-border"
                    }`}
                  >
                    {googleStatus?.is_connected ? "Connected" : "Not Connected"}
                  </Badge>
                )}
              </CardHeader>

              <CardContent className="space-y-5 pt-4 text-xs">
                {isGoogleStatusLoading ? (
                  <div className="space-y-3">
                    <Skeleton className="h-10 w-full" />
                    <Skeleton className="h-20 w-full" />
                  </div>
                ) : googleStatus?.is_connected ? (
                  <div className="space-y-4">
                    {/* Reconnect Needed Alert */}
                    {googleStatus.reconnect_needed && (
                      <div className="p-4 rounded-xl border border-amber-500/40 bg-amber-500/10 text-amber-900 dark:text-amber-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-xs">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2 font-semibold text-xs">
                            <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400 shrink-0" />
                            <span>{googleStatus.reconnect_reason?.includes("Partial") ? "Partial Google Access Detected" : "Google Permissions Update Needed"}</span>
                          </div>
                          <p className="text-[11px] text-amber-800 dark:text-amber-300">
                            {googleStatus.reconnect_reason || "Partial access, reconnect to grant all"}
                          </p>
                        </div>
                        <Button
                          size="sm"
                          onClick={() => connectMutation.mutate()}
                          disabled={connectMutation.isPending}
                          className="bg-amber-600 hover:bg-amber-700 text-white text-xs shrink-0 font-medium h-8 gap-1.5"
                        >
                          <RefreshCw className={`h-3.5 w-3.5 ${connectMutation.isPending ? "animate-spin" : ""}`} />
                          <span>Reconnect</span>
                        </Button>
                      </div>
                    )}

                    {/* Connected Account Details */}
                    <div className="p-4 rounded-xl border border-border/70 bg-muted/20 space-y-3">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="space-y-0.5">
                          <span className="text-[11px] text-muted-foreground font-medium">Linked Account</span>
                          <p className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                            <span>{googleStatus.email}</span>
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => syncMutation.mutate()}
                            disabled={syncMutation.isPending}
                            className="h-8 text-xs gap-1.5 font-medium"
                          >
                            <RefreshCw className={`h-3.5 w-3.5 ${syncMutation.isPending ? "animate-spin" : ""}`} />
                            <span>{syncMutation.isPending ? "Syncing..." : "Sync Resumes Now"}</span>
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => disconnectMutation.mutate()}
                            disabled={disconnectMutation.isPending}
                            className="h-8 text-xs gap-1.5 text-destructive hover:bg-destructive/10"
                          >
                            <Unlink className="h-3.5 w-3.5" />
                            <span>Disconnect</span>
                          </Button>
                        </div>
                      </div>

                      {/* Workspace Services Granted Status */}
                      <div className="pt-2 border-t border-border/60 space-y-2">
                        <span className="text-[11px] text-muted-foreground flex items-center gap-1 font-medium">
                          <ShieldCheck className="h-3.5 w-3.5 text-primary" />
                          <span>Connected Workspace Services</span>
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {["Gmail", "Calendar", "Meet", "Sheets", "Docs", "Drive"].map((srv) => {
                            const isGranted = googleStatus.granted_services
                              ? Boolean(googleStatus.granted_services[srv])
                              : true;
                            return (
                              <Badge
                                key={srv}
                                variant={isGranted ? "secondary" : "outline"}
                                className={`text-[10px] font-medium px-2 py-0.5 flex items-center gap-1 ${
                                  isGranted
                                    ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20"
                                    : "bg-destructive/10 text-destructive border-destructive/20 line-through opacity-70"
                                }`}
                              >
                                {isGranted ? (
                                  <CheckCircle2 className="h-2.5 w-2.5 text-emerald-500" />
                                ) : (
                                  <AlertCircle className="h-2.5 w-2.5 text-destructive" />
                                )}
                                <span>{srv}</span>
                              </Badge>
                            );
                          })}
                        </div>
                      </div>
                    </div>

                    {/* Filter Settings Form */}
                    <div className="p-4 rounded-xl border border-border/70 bg-card space-y-4">
                      <h3 className="text-xs font-bold text-foreground flex items-center gap-2">
                        <Filter className="w-3.5 h-3.5 text-primary" />
                        <span>Resume Ingestion Filters & Auto-Reply Rules</span>
                      </h3>

                      <div className="space-y-3">
                        <div>
                          <label className="text-xs font-medium text-foreground block mb-1">
                            Gmail Search Query
                          </label>
                          <input
                            type="text"
                            value={filterQuery}
                            onChange={(e) => setFilterQuery(e.target.value)}
                            className="w-full bg-background border border-input rounded-lg px-3 py-1.5 text-xs font-mono text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                          />
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          <div>
                            <label className="text-xs font-medium text-foreground block mb-1">
                              Default Job Opening
                            </label>
                            <select
                              value={defaultOpeningId}
                              onChange={(e) => setDefaultOpeningId(e.target.value)}
                              className="w-full bg-background border border-input rounded-lg px-3 py-1.5 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                            >
                              <option value="">Unassigned (Route to General)</option>
                              {activeOpenings.map((op) => (
                                <option key={op.id} value={op.id}>
                                  {op.title}
                                </option>
                              ))}
                            </select>
                          </div>

                          <div className="flex items-center justify-between p-3 rounded-lg border border-border/70 bg-muted/20">
                            <div className="space-y-0.5">
                              <span className="text-xs font-medium text-foreground block">
                                Automated &ldquo;CV Received&rdquo; Auto-Reply
                              </span>
                              <p className="text-[10px] text-muted-foreground">
                                Dispatches acknowledgment email from HR Gmail
                              </p>
                            </div>
                            <input
                              type="checkbox"
                              checked={autoReplyEnabled}
                              onChange={(e) => setAutoReplyEnabled(e.target.checked)}
                              className="w-4 h-4 rounded text-primary focus:ring-primary cursor-pointer accent-primary"
                            />
                          </div>
                        </div>

                        <div className="pt-2 flex justify-end">
                          <Button
                            size="sm"
                            onClick={() => saveSettingsMutation.mutate()}
                            disabled={saveSettingsMutation.isPending}
                            className="gap-1.5 text-xs font-semibold"
                          >
                            <Save className="w-3.5 h-3.5" />
                            <span>Save Filter Preferences</span>
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="p-8 text-center border border-dashed rounded-xl space-y-3">
                    <Mail className="w-8 h-8 text-muted-foreground mx-auto" />
                    <h3 className="text-xs font-semibold text-foreground">Connect Google Workspace</h3>
                    <p className="text-[11px] text-muted-foreground max-w-md mx-auto">
                      Link your corporate Google account to enable automated CV syncing from Gmail, Google Meet interview scheduling, and bidirectional thread updates.
                    </p>
                    <Button
                      size="sm"
                      onClick={() => connectMutation.mutate()}
                      disabled={connectMutation.isPending}
                      className="gap-1.5 text-xs font-semibold"
                    >
                      <Zap className="w-3.5 h-3.5" />
                      <span>Connect with Google</span>
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* ── TAB 3: INTEGRATION HEALTH ─────────────────────────────────── */}
          <TabsContent value="health" className="space-y-5">
            {/* Database & Runtime Health Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* PostgreSQL Database Live Ping */}
              <Card className="border border-border/80 dark:border-white/[0.08] shadow-xs rounded-xl">
                <CardHeader className="pb-3 border-b border-border/50">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-semibold tracking-tight flex items-center gap-2">
                      <Database className="w-4 h-4 text-primary" />
                      <span>PostgreSQL Database</span>
                    </CardTitle>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => refetchDbHealth()}
                      disabled={isDbHealthFetching}
                      className="h-7 w-7 p-0"
                      title="Ping Database"
                    >
                      <RefreshCw className={`w-3 h-3 ${isDbHealthFetching ? "animate-spin" : ""}`} />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="pt-4 space-y-3 text-xs">
                  {isDbHealthLoading ? (
                    <Skeleton className="h-16 w-full" />
                  ) : (
                    <div className="grid grid-cols-2 gap-2">
                      <div className="p-3 rounded-lg border border-border/70 bg-muted/20">
                        <span className="text-[10px] text-muted-foreground uppercase font-bold">Latency</span>
                        <p className="text-base font-mono font-bold text-emerald-600 dark:text-emerald-400 mt-0.5">
                          {dbHealth?.latency_ms ?? 0} ms
                        </p>
                      </div>
                      <div className="p-3 rounded-lg border border-border/70 bg-muted/20">
                        <span className="text-[10px] text-muted-foreground uppercase font-bold">Connection Mode</span>
                        <p className="text-xs font-mono font-semibold text-foreground mt-1 capitalize">
                          {dbHealth?.mode ?? "Session Pooler"}
                        </p>
                      </div>
                    </div>
                  )}
                  <p className="text-[11px] text-muted-foreground">
                    Connected to Supabase PostgreSQL cluster with connection pool health verified.
                  </p>
                </CardContent>
              </Card>

              {/* Pinecone Vector Database & Fast Response Cache */}
              <Card className="border border-border/80 dark:border-white/[0.08] shadow-xs rounded-xl">
                <CardHeader className="pb-3 border-b border-border/50">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-semibold tracking-tight flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-indigo-500" />
                      <span>Pinecone Vector Cache</span>
                    </CardTitle>
                    <div className="flex items-center gap-1.5">
                      <Badge
                        variant={pineconeHealth?.is_connected ? "success" : "warning"}
                        className="text-[10px] font-mono px-2 py-0"
                      >
                        {pineconeHealth?.is_connected ? "Connected" : (pineconeHealth?.status || "Checking")}
                      </Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => refetchPineconeHealth()}
                        disabled={isPineconeFetching}
                        className="h-7 w-7 p-0"
                        title="Ping Pinecone Vector DB"
                      >
                        <RefreshCw className={`w-3 h-3 ${isPineconeFetching ? "animate-spin" : ""}`} />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-4 space-y-3 text-xs">
                  {isPineconeLoading ? (
                    <Skeleton className="h-16 w-full" />
                  ) : (
                    <div className="grid grid-cols-2 gap-2">
                      <div className="p-3 rounded-lg border border-border/70 bg-muted/20">
                        <span className="text-[10px] text-muted-foreground uppercase font-bold">Latency</span>
                        <p className="text-base font-mono font-bold text-indigo-600 dark:text-indigo-400 mt-0.5">
                          {pineconeHealth?.latency_ms ?? 0} ms
                        </p>
                      </div>
                      <div className="p-3 rounded-lg border border-border/70 bg-muted/20">
                        <span className="text-[10px] text-muted-foreground uppercase font-bold">Vectors Stored</span>
                        <p className="text-base font-mono font-bold text-foreground mt-0.5">
                          {pineconeHealth?.total_vectors ?? 0}
                        </p>
                      </div>
                    </div>
                  )}
                  <p className="text-[11px] text-muted-foreground">
                    Index: <code className="font-mono text-[10px] font-bold">{pineconeHealth?.index_name || "job-tracker-cache"}</code> ({pineconeHealth?.cloud || "aws"}:{pineconeHealth?.region || "us-east-1"}, 1024-dim). Ultra-fast semantic response &amp; CV scoring caching enabled.
                  </p>
                </CardContent>
              </Card>

              {/* Backend System Environment */}
              <Card className="border border-border/80 dark:border-white/[0.08] shadow-xs rounded-xl">
                <CardHeader className="pb-3 border-b border-border/50">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-semibold tracking-tight flex items-center gap-2">
                      <Cpu className="w-4 h-4 text-primary" />
                      <span>Backend Application</span>
                    </CardTitle>
                    <Badge variant="outline" className="text-[10px] font-mono">
                      v{backendHealth?.version || "1.0.0"}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="pt-4 space-y-3 text-xs">
                  <div className="grid grid-cols-2 gap-2">
                    <div className="p-3 rounded-lg border border-border/70 bg-muted/20">
                      <span className="text-[10px] text-muted-foreground uppercase font-bold">Status</span>
                      <p className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 mt-1 flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Healthy & Live</span>
                      </p>
                    </div>
                    <div className="p-3 rounded-lg border border-border/70 bg-muted/20">
                      <span className="text-[10px] text-muted-foreground uppercase font-bold">Environment</span>
                      <p className="text-xs font-mono font-semibold text-foreground mt-1 uppercase">
                        {backendHealth?.environment || "Development"}
                      </p>
                    </div>
                  </div>
                  <p className="text-[11px] text-muted-foreground">
                    FastAPI asynchronous engine running on Python 3.12 with background task worker queues.
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Live AI Models Health Table */}
            <Card className="border border-border/80 dark:border-white/[0.08] shadow-xs rounded-xl overflow-hidden">
              <CardHeader className="flex flex-row items-center justify-between pb-3 border-b border-border/50">
                <div className="space-y-0.5">
                  <CardTitle className="text-sm font-semibold tracking-tight flex items-center gap-2">
                    <Zap className="w-4 h-4 text-amber-500" />
                    <span>AI Model Inference Health & Latencies</span>
                  </CardTitle>
                  <CardDescription className="text-xs text-muted-foreground">
                    Latency and availability benchmarks for all screening and extraction LLM model chains
                  </CardDescription>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => refetchAIHealth()}
                  disabled={isAIRefetching}
                  className="gap-1.5 text-xs h-8"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isAIRefetching ? "animate-spin" : ""}`} />
                  <span>Test Latency</span>
                </Button>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-muted/40 border-b border-border/80 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                        <th className="py-2.5 px-4">Task & Role</th>
                        <th className="py-2.5 px-3">Model Chain</th>
                        <th className="py-2.5 px-3">Latency</th>
                        <th className="py-2.5 px-4 text-right">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/60">
                      {isAIHealthLoading ? (
                        <tr>
                          <td colSpan={4} className="p-4 text-center">
                            <Skeleton className="h-6 w-full" />
                          </td>
                        </tr>
                      ) : modelList.length === 0 ? (
                        <tr>
                          <td colSpan={4} className="p-6 text-center text-muted-foreground italic">
                            No model benchmark telemetry recorded.
                          </td>
                        </tr>
                      ) : (
                        modelList.map((m, idx) => (
                          <tr key={idx} className="hover:bg-muted/20 transition-colors">
                            <td className="py-2.5 px-4">
                              <span className="font-semibold text-foreground capitalize">
                                {m.task || m.role || "Screening"}
                              </span>
                            </td>
                            <td className="py-2.5 px-3 font-mono text-[11px] text-muted-foreground">
                              {m.model}
                            </td>
                            <td className="py-2.5 px-3 font-mono text-[11px] font-bold text-foreground">
                              {m.latency_ms} ms
                            </td>
                            <td className="py-2.5 px-4 text-right">
                              <Badge
                                variant={m.status === "ok" ? "success" : "destructive"}
                                className="text-[10px] uppercase font-bold px-1.5 py-0"
                              >
                                {m.status === "ok" ? "Healthy" : "Degraded"}
                              </Badge>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* ── TAB 4: RECRUITING TEMPLATES (11 Lifecycle Stages + AI Generator) ──── */}
          <TabsContent value="templates" className="space-y-4">
            {/* Header & One-Click AI Generator Banner */}
            <div className="p-4 rounded-xl border border-primary/20 bg-primary/5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-foreground">
                    Candidate Lifecycle Email Templates
                  </h3>
                  <Badge variant="outline" className="text-[10px] font-semibold text-primary border-primary/30">
                    11 Stages
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Short, warm, and human. AI generation runs using your HR profile &amp; tone. Sending never calls AI; it only fills variables deterministically.
                </p>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <Button
                  type="button"
                  onClick={handleSettingsGenerateAllAI}
                  disabled={isGeneratingAllSettingsAI}
                  size="sm"
                  variant="outline"
                  className="border-primary/40 hover:bg-primary/10 text-primary text-xs font-semibold gap-1.5 shadow-xs"
                >
                  <Sparkles className={`w-3.5 h-3.5 ${isGeneratingAllSettingsAI ? "animate-spin" : ""}`} />
                  <span>{isGeneratingAllSettingsAI ? "Generating 11..." : "Generate All with AI"}</span>
                </Button>

                <Button
                  type="button"
                  onClick={() => saveSettingsTemplatesMutation.mutate()}
                  disabled={saveSettingsTemplatesMutation.isPending}
                  size="sm"
                  className="bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-semibold gap-1.5 shadow-xs"
                >
                  <Save className={`w-3.5 h-3.5 ${saveSettingsTemplatesMutation.isPending ? "animate-spin" : ""}`} />
                  <span>{saveSettingsTemplatesMutation.isPending ? "Saving..." : "Save Templates"}</span>
                </Button>
              </div>
            </div>

            {/* All Templates Pill Navigation (from DB + Custom) */}
            <div className="relative space-y-2.5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mr-1">
                    Templates (31):
                  </span>
                  {(
                    [
                      { id: "all", label: "All (31)" },
                      { id: "core", label: "Core (9)" },
                      { id: "supporting", label: "Supporting (16)" },
                      { id: "internal", label: "Internal (6)" },
                    ] as const
                  ).map((cat) => (
                    <button
                      key={cat.id}
                      type="button"
                      onClick={() => setSettingsCategoryFilter(cat.id)}
                      className={`px-2 py-0.5 rounded-md text-[11px] font-semibold transition ${
                        settingsCategoryFilter === cat.id
                          ? "bg-primary text-primary-foreground shadow-xs"
                          : "bg-muted/50 text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      {cat.label}
                    </button>
                  ))}
                </div>

                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsAddingCustom(!isAddingCustom)}
                  className="h-7 text-xs px-2.5 gap-1 border-primary/30 text-primary hover:bg-primary/10 self-start sm:self-auto"
                >
                  <Plus className="w-3 h-3" />
                  <span>{isAddingCustom ? "Cancel" : "Add Custom Template"}</span>
                </Button>
              </div>

              {/* Inline Custom Template Creator */}
              {isAddingCustom && (
                <Card className="border border-primary/30 bg-primary/5 p-3.5 rounded-xl space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-foreground">Create New Recruiting Template</h4>
                    <span className="text-[10px] text-muted-foreground">Saved directly to PostgreSQL</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    <div className="space-y-1">
                      <label className="text-[11px] font-semibold text-muted-foreground">Template Name</label>
                      <Input
                        value={newCustomName}
                        onChange={(e) => setNewCustomName(e.target.value)}
                        placeholder="e.g. Technical Deep Dive Invite"
                        className="text-xs h-8 bg-background"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[11px] font-semibold text-muted-foreground">Stage Key</label>
                      <Input
                        value={newCustomStage}
                        onChange={(e) => setNewCustomStage(e.target.value.toLowerCase().replace(/\s+/g, "_"))}
                        placeholder="e.g. technical_interview"
                        className="text-xs h-8 bg-background font-mono"
                      />
                    </div>
                  </div>
                  <div className="space-y-1">
                    <label className="text-[11px] font-semibold text-muted-foreground">Subject Line</label>
                    <Input
                      value={newCustomSubject}
                      onChange={(e) => setNewCustomSubject(e.target.value)}
                      placeholder="e.g. Next Step: Technical Discussion for {role} at {company}"
                      className="text-xs h-8 bg-background font-mono"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[11px] font-semibold text-muted-foreground">Body</label>
                    <Textarea
                      rows={4}
                      value={newCustomBody}
                      onChange={(e) => setNewCustomBody(e.target.value)}
                      placeholder="Hi {candidate_name}, we'd love to invite you to..."
                      className="text-xs bg-background"
                    />
                  </div>
                  <div className="flex justify-end gap-2">
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => setIsAddingCustom(false)}
                      className="h-7 text-xs"
                    >
                      Cancel
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      disabled={createCustomTemplateMutation.isPending || !newCustomName || !newCustomSubject || !newCustomBody}
                      onClick={() =>
                        createCustomTemplateMutation.mutate({
                          stage_key: newCustomStage || "custom_stage",
                          name: newCustomName,
                          subject: newCustomSubject,
                          body: newCustomBody,
                        })
                      }
                      className="h-7 text-xs bg-primary text-primary-foreground gap-1"
                    >
                      <Save className="w-3 h-3" />
                      <span>{createCustomTemplateMutation.isPending ? "Saving..." : "Save New Template"}</span>
                    </Button>
                  </div>
                </Card>
              )}

              <div className="flex items-center gap-1.5 overflow-x-auto pb-1.5 scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent">
                {ALL_RECRUITING_TEMPLATES.filter(
                  (tpl) => settingsCategoryFilter === "all" || tpl.category === settingsCategoryFilter
                ).map((tpl) => {
                  const itemKey = tpl.id;
                  const itemStageKey = tpl.id;
                  const itemName = tpl.name;
                  const isActive = selectedTemplateId === itemKey || activeSettingsTemplate === itemStageKey;
                  const dbMatch = dbTemplatesList?.find((d) => d.stage_key === tpl.id || d.id === tpl.id);
                  const isDbActive = dbMatch ? dbMatch.is_active !== false : true;

                  return (
                    <button
                      key={itemKey}
                      type="button"
                      onClick={() => {
                        setSelectedTemplateId(itemKey);
                        setActiveSettingsTemplate(itemStageKey);
                        setSettingsPreviewMode(false);
                      }}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium shrink-0 flex items-center gap-1.5 transition-all border ${
                        isActive
                          ? "bg-primary text-primary-foreground border-primary shadow-xs"
                          : "bg-muted/30 text-muted-foreground hover:bg-muted/60 hover:text-foreground border-border/60"
                      }`}
                    >
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          isActive
                            ? "bg-white"
                            : isDbActive
                            ? "bg-emerald-500"
                            : "bg-muted-foreground/40"
                        }`}
                      />
                      <span>{itemName}</span>
                      {dbMatch?.is_default && <Star className="w-2.5 h-2.5 text-amber-400 fill-amber-400 ml-0.5" />}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Active Template Card */}
            {(() => {
              const activeItem =
                (dbTemplatesList || []).find((t) => t.id === selectedTemplateId) ||
                (dbTemplatesList || []).find((t) => t.stage_key === activeSettingsTemplate) ||
                null;

              const currentConfig =
                LIFECYCLE_TEMPLATES.find((t) => t.key === activeSettingsTemplate) ||
                (activeItem
                  ? {
                      name: activeItem.name,
                      shortName: activeItem.name,
                      key: activeItem.stage_key,
                      description: activeItem.description || `Template for stage: ${activeItem.stage_key}`,
                    }
                  : LIFECYCLE_TEMPLATES[0]);

              const activeKey = selectedTemplateId || activeSettingsTemplate;
              const tmpl = settingsTemplates[activeKey] || settingsTemplates[activeSettingsTemplate] || {
                subject: activeItem?.subject || "",
                body: activeItem?.body || "",
                name: activeItem?.name || currentConfig.name,
                is_active: activeItem?.is_active ?? true,
                is_default: activeItem?.is_default ?? true,
                is_custom: activeItem?.is_custom ?? false,
              };

              const hrInfo = onboardingData?.step_1;
              const sampleVars: Record<string, string> = {
                candidate_name: "Alex Morgan",
                role: onboardingData?.step_2?.job_title || "Senior Software Engineer",
                company: hrInfo?.company_name || "Our Company",
                hr_name: hrInfo?.hr_name || "Sarah Jenkins",
                interview_date: "Thursday, Nov 26",
                interview_time: "2:30 PM PKT",
                meet_link: "https://meet.google.com/abc-defg-hij",
                schedule_link: "https://app.hiringloop.ai/schedule/invite-demo",
                job_details:
                  "Designing scalable microservices, creating high-performance PostgreSQL queries, and deploying cloud services.",
                booking_link: "https://app.hiringloop.ai/schedule/invite-demo",
                job_title: onboardingData?.step_2?.job_title || "Senior Software Engineer",
                company_name: hrInfo?.company_name || "Our Company",
                signature:
                  hrInfo?.signature ||
                  `Warm regards,\n${hrInfo?.hr_name || "Talent Lead"}\n${hrInfo?.company_name || "Our Company"}`,
              };

              const resolvedSubject = (() => {
                let s = tmpl.subject || "";
                Object.entries(sampleVars).forEach(([k, v]) => {
                  s = s.split(`{${k}}`).join(v);
                  s = s.split(`{{${k}}}`).join(v);
                });
                return s;
              })();

              const resolvedBody = (() => {
                let b = tmpl.body || "";
                Object.entries(sampleVars).forEach(([k, v]) => {
                  b = b.split(`{${k}}`).join(v);
                  b = b.split(`{{${k}}}`).join(v);
                });
                return b;
              })();

              const isDefaultTmpl = activeItem?.is_default ?? tmpl.is_default ?? false;
              const isActiveTmpl = activeItem?.is_active ?? tmpl.is_active ?? true;
              const isCustomTmpl = activeItem?.is_custom ?? tmpl.is_custom ?? false;

              return (
                <Card className="border border-border/80 dark:border-white/[0.08] bg-card shadow-xs rounded-xl overflow-hidden">
                  <CardHeader className="pb-3 border-b border-border/50">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2 flex-wrap">
                          <CardTitle className="text-sm font-bold text-foreground">
                            {tmpl.name || currentConfig.name}
                          </CardTitle>
                          <Badge variant="secondary" className="text-[10px] font-mono">
                            {activeItem?.stage_key || activeSettingsTemplate}
                          </Badge>
                          {isDefaultTmpl && (
                            <Badge variant="outline" className="text-[10px] text-amber-500 border-amber-300 dark:border-amber-800 flex items-center gap-0.5">
                              <Star className="w-2.5 h-2.5 fill-amber-400" /> Default
                            </Badge>
                          )}
                          <Badge
                            variant={isActiveTmpl ? "default" : "destructive"}
                            className="text-[10px] font-semibold"
                          >
                            {isActiveTmpl ? "Active" : "Disabled"}
                          </Badge>
                          {isCustomTmpl && (
                            <Badge variant="outline" className="text-[10px] text-muted-foreground">
                              Custom
                            </Badge>
                          )}
                        </div>
                        <CardDescription className="text-xs text-muted-foreground">
                          {currentConfig.description}
                        </CardDescription>
                      </div>

                      <div className="flex items-center gap-1.5 flex-wrap shrink-0">
                        {/* Set Default */}
                        {activeItem && !isDefaultTmpl && (
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => setDefaultTemplateMutation.mutate(activeItem.id)}
                            disabled={setDefaultTemplateMutation.isPending}
                            className="h-7 text-xs px-2 gap-1 text-muted-foreground hover:text-foreground"
                            title="Set this template as default for this stage"
                          >
                            <Star className="w-3 h-3 text-amber-500" />
                            <span>Set Default</span>
                          </Button>
                        )}

                        {/* Toggle Active / Disabled */}
                        {activeItem && (
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => toggleTemplateActiveMutation.mutate(activeItem.id)}
                            disabled={toggleTemplateActiveMutation.isPending}
                            className={`h-7 text-xs px-2 gap-1 ${
                              isActiveTmpl
                                ? "text-amber-600 dark:text-amber-400 border-amber-200 dark:border-amber-800"
                                : "text-emerald-600 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800"
                            }`}
                            title={isActiveTmpl ? "Disable template (will pause if triggered)" : "Activate template"}
                          >
                            <span>{isActiveTmpl ? "Disable" : "Enable"}</span>
                          </Button>
                        )}

                        {/* Duplicate */}
                        {activeItem && (
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => duplicateTemplateMutation.mutate(activeItem.id)}
                            disabled={duplicateTemplateMutation.isPending}
                            className="h-7 text-xs px-2 gap-1 text-muted-foreground hover:text-foreground"
                            title="Duplicate this template"
                          >
                            <Copy className="w-3 h-3" />
                            <span>Duplicate</span>
                          </Button>
                        )}

                        {/* Regenerate this template with AI */}
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => handleSettingsRegenerateSingleAI(activeKey, activeItem?.stage_key || activeSettingsTemplate)}
                          disabled={regeneratingSettingsKey === activeKey}
                          className="h-7 text-xs px-2.5 gap-1 border-border/80 hover:border-primary/50 text-foreground"
                          title="Regenerate this specific template with AI"
                        >
                          <RefreshCw
                            className={`w-3 h-3 text-primary ${
                              regeneratingSettingsKey === activeKey ? "animate-spin" : ""
                            }`}
                          />
                          <span>
                            {regeneratingSettingsKey === activeKey ? "Regenerating..." : "Regenerate AI"}
                          </span>
                        </Button>

                        {/* Delete Custom/Duplicate */}
                        {activeItem && isCustomTmpl && (
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              if (confirm(`Delete template "${tmpl.name}"?`)) {
                                deleteTemplateMutation.mutate(activeItem.id);
                              }
                            }}
                            disabled={deleteTemplateMutation.isPending}
                            className="h-7 text-xs px-2 gap-1 text-destructive hover:bg-destructive/10 border-destructive/30"
                            title="Delete custom template"
                          >
                            <Trash2 className="w-3 h-3" />
                            <span>Delete</span>
                          </Button>
                        )}

                        {/* Edit vs Preview Toggle */}
                        <div className="flex items-center bg-muted/60 p-0.5 rounded-lg border border-border/60 text-xs">
                          <button
                            type="button"
                            onClick={() => setSettingsPreviewMode(false)}
                            className={`px-2 py-1 rounded text-[11px] font-medium flex items-center gap-1 transition-colors ${
                              !settingsPreviewMode
                                ? "bg-background text-foreground shadow-xs font-semibold"
                                : "text-muted-foreground hover:text-foreground"
                            }`}
                          >
                            <Edit3 className="w-3 h-3" />
                            <span>Edit</span>
                          </button>
                          <button
                            type="button"
                            onClick={() => setSettingsPreviewMode(true)}
                            className={`px-2 py-1 rounded text-[11px] font-medium flex items-center gap-1 transition-colors ${
                              settingsPreviewMode
                                ? "bg-background text-foreground shadow-xs font-semibold"
                                : "text-muted-foreground hover:text-foreground"
                            }`}
                          >
                            <Eye className="w-3 h-3" />
                            <span>Preview</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  </CardHeader>

                  <CardContent className="space-y-4 pt-4">
                    {!settingsPreviewMode ? (
                      /* ── EDIT MODE ────────────────────────────────────────── */
                      <div className="space-y-3.5">
                        {/* Variable insertion chips */}
                        <div className="space-y-1">
                          <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                            Insert Dynamic Variable:
                          </span>
                          <div className="flex flex-wrap items-center gap-1 text-xs">
                            {VARIABLE_CHIPS.map((chip) => (
                              <button
                                key={chip.token}
                                type="button"
                                onClick={() => handleInsertVariableSettings(chip.token)}
                                className="px-1.5 py-0.5 rounded-md border border-border/80 bg-muted/30 font-mono text-[10px] text-primary hover:bg-primary/10 hover:border-primary/40 transition-colors"
                                title={`Insert ${chip.label} into message body`}
                              >
                                {chip.token}
                              </button>
                            ))}
                          </div>
                        </div>

                        {/* Subject Line */}
                        <div className="space-y-1">
                          <label className="text-xs font-semibold text-foreground">Subject Line</label>
                          <Input
                            value={tmpl.subject}
                            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                              setSettingsTemplates({
                                ...settingsTemplates,
                                [activeKey]: { ...tmpl, subject: e.target.value },
                                [activeSettingsTemplate]: { ...tmpl, subject: e.target.value },
                              })
                            }
                            placeholder="e.g. Got your application for {role} at {company}!"
                            className="text-xs h-9 bg-background font-medium font-mono"
                          />
                        </div>

                        {/* Message Body */}
                        <div className="space-y-1">
                          <label className="text-xs font-semibold text-foreground">Message Body</label>
                          <Textarea
                            rows={8}
                            value={tmpl.body}
                            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                              setSettingsTemplates({
                                ...settingsTemplates,
                                [activeKey]: { ...tmpl, body: e.target.value },
                                [activeSettingsTemplate]: { ...tmpl, body: e.target.value },
                              })
                            }
                            placeholder="Write message body with variables..."
                            className="text-xs bg-background leading-relaxed font-sans"
                          />
                        </div>
                      </div>
                    ) : (
                      /* ── PREVIEW MODE ─────────────────────────────────────── */
                      <div className="space-y-2.5 bg-muted/20 rounded-xl p-3.5 border border-border/60">
                        <div className="flex items-center justify-between text-[11px] pb-2 border-b border-border/50 text-muted-foreground">
                          <span className="flex items-center gap-1.5">
                            <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
                            Live Candidate View (Variables Interpolated Deterministically)
                          </span>
                          <span className="text-[10px] bg-background px-2 py-0.5 rounded border border-border/60">
                            Sample: Alex Morgan
                          </span>
                        </div>

                        <div className="space-y-1 text-xs">
                          <div className="flex gap-1.5 text-muted-foreground text-[11px]">
                            <span className="font-semibold text-foreground/80 w-14 shrink-0">Subject:</span>
                            <span className="font-medium text-foreground">{resolvedSubject || "(No subject)"}</span>
                          </div>
                          <div className="flex gap-1.5 text-muted-foreground text-[11px]">
                            <span className="font-semibold text-foreground/80 w-14 shrink-0">Recipient:</span>
                            <span>Alex Morgan &lt;alex.morgan@example.com&gt;</span>
                          </div>
                          <div className="flex gap-1.5 text-muted-foreground text-[11px]">
                            <span className="font-semibold text-foreground/80 w-14 shrink-0">Sender:</span>
                            <span>{hrInfo?.hr_name || "Talent Lead"} &lt;recruiting@{hrInfo?.company_name ? hrInfo.company_name.toLowerCase().replace(/\s+/g, '') + '.com' : 'company.com'}&gt;</span>
                          </div>
                        </div>

                        <div className="mt-2 pt-2 border-t border-border/50 bg-background/80 rounded-lg p-3 border border-border/60 text-xs text-foreground font-sans whitespace-pre-wrap leading-relaxed">
                          {resolvedBody || "(No message body content)"}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })()}
          </TabsContent>

          {/* ── TAB 5: AUDIT TRAIL ────────────────────────────────────────── */}
          <TabsContent value="audit" className="space-y-4">
            <Card className="border border-border/80 dark:border-white/[0.08] shadow-xs rounded-xl overflow-hidden">
              <CardHeader className="pb-3 border-b border-border/50">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="space-y-0.5">
                    <CardTitle className="text-sm font-semibold tracking-tight flex items-center gap-2">
                      <Clock className="w-4 h-4 text-primary" />
                      <span>Recruiter Audit Trail & Activity Log</span>
                    </CardTitle>
                    <CardDescription className="text-xs text-muted-foreground">
                      Chronological history of candidate stage updates, email deliveries, and recruiter actions
                    </CardDescription>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => refetchAudit()}
                      disabled={isAuditFetching}
                      className="gap-1.5 text-xs h-8"
                    >
                      <RefreshCw className={`w-3 h-3 ${isAuditFetching ? "animate-spin" : ""}`} />
                      <span>Refresh</span>
                    </Button>
                  </div>
                </div>

                {/* Audit Search & Action Filter Bar */}
                <div className="flex flex-col sm:flex-row sm:items-center gap-2.5 pt-3">
                  <div className="relative flex-1">
                    <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                    <input
                      type="text"
                      value={auditSearchQuery}
                      onChange={(e) => setAuditSearchQuery(e.target.value)}
                      placeholder="Filter by candidate, requisition, action..."
                      className="w-full bg-background border border-input rounded-lg pl-9 pr-3 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                    />
                  </div>

                  <select
                    value={auditActionFilter}
                    onChange={(e) => setAuditActionFilter(e.target.value)}
                    className="bg-background border border-input rounded-lg px-2.5 py-1.5 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                  >
                    <option value="all">All Actions</option>
                    <option value="stage_update">Stage Updates</option>
                    <option value="auto_reply_sent">Emails Sent</option>
                    <option value="screening_scored">Screening Evaluations</option>
                    <option value="candidate_created">Candidate Ingestions</option>
                  </select>
                </div>
              </CardHeader>

              <CardContent className="p-0">
                {isAuditLoading ? (
                  <div className="p-6 space-y-3">
                    <Skeleton className="h-6 w-full" />
                    <Skeleton className="h-6 w-full" />
                    <Skeleton className="h-6 w-full" />
                  </div>
                ) : filteredAuditLogs.length === 0 ? (
                  <div className="p-8 text-center text-muted-foreground space-y-1">
                    <Clock className="w-6 h-6 mx-auto mb-2 opacity-50" />
                    <p className="text-xs font-semibold">No audit events found</p>
                    <p className="text-[11px]">
                      Candidate pipeline transitions and outreach events will be logged here automatically.
                    </p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="bg-muted/40 border-b border-border/80 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                          <th className="py-2.5 px-4 w-36">Action</th>
                          <th className="py-2.5 px-3 min-w-[160px]">Candidate & Opening</th>
                          <th className="py-2.5 px-3 min-w-[140px]">Transition</th>
                          <th className="py-2.5 px-3 min-w-[200px]">Details</th>
                          <th className="py-2.5 px-4 text-right w-36">Timestamp</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/60">
                        {filteredAuditLogs.map((log) => (
                          <tr key={log.id} className="hover:bg-muted/20 transition-colors">
                            <td className="py-2.5 px-4">
                              <Badge variant="outline" className="text-[10px] font-mono capitalize px-1.5 py-0">
                                {log.action.replace(/_/g, " ")}
                              </Badge>
                            </td>
                            <td className="py-2.5 px-3">
                              <span className="font-semibold text-foreground block">
                                {log.candidate_name || "—"}
                              </span>
                              {log.opening_title && (
                                <span className="text-[10px] text-muted-foreground">
                                  {log.opening_title}
                                </span>
                              )}
                            </td>
                            <td className="py-2.5 px-3">
                              {log.from_stage || log.to_stage ? (
                                <div className="flex items-center gap-1 font-mono text-[10px]">
                                  <span className="text-muted-foreground">{log.from_stage || "—"}</span>
                                  <ArrowRight className="w-2.5 h-2.5 text-muted-foreground" />
                                  <span className="font-semibold text-foreground">{log.to_stage || "—"}</span>
                                </div>
                              ) : (
                                <span className="text-muted-foreground">—</span>
                              )}
                            </td>
                            <td className="py-2.5 px-3 text-[11px] text-muted-foreground line-clamp-2">
                              {log.details || "—"}
                            </td>
                            <td className="py-2.5 px-4 text-right font-mono text-[10px] text-muted-foreground">
                              {new Date(log.created_at).toLocaleDateString()}{" "}
                              {new Date(log.created_at).toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* ── TAB 6: AGENT SETTINGS & TODAY'S ACTIVITY ──────────────────── */}
          <TabsContent value="agent" className="space-y-5">
            <AgentControlHub />
          </TabsContent>
        </Tabs>
      </div>
    </AppShell>
  );
}

export default function SettingsPage() {
  return (
    <Suspense
      fallback={
        <AppShell title="Settings">
          <div className="space-y-4 max-w-5xl">
            <Skeleton className="h-10 w-48" />
            <Skeleton className="h-64 w-full" />
          </div>
        </AppShell>
      }
    >
      <SettingsPageInner />
    </Suspense>
  );
}
