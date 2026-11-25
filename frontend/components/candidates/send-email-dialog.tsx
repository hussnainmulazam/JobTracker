"use client";

import React, { useState, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Mail,
  Send,
  RefreshCw,
  Eye,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Link as LinkIcon,
  Building2,
} from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/use-toast";
import { googleApi, Candidate } from "@/lib/api";

interface SendEmailDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  candidate: Candidate | null;
}

const EMAIL_TEMPLATES = [
  // Core Hiring & Screening
  { id: "interview_invitation", label: "Interview Invitation (Screening Round)", group: "Core Hiring" },
  { id: "application_approved", label: "Application Approved (Next Steps & Availability)", group: "Core Hiring" },
  { id: "interview_confirmed", label: "Interview Confirmed (Meeting & Calendar Details)", group: "Core Hiring" },
  { id: "alternate_slots", label: "Alternate Time Slots Proposed", group: "Core Hiring" },
  { id: "next_round_availability", label: "Next Round Availability Request", group: "Core Hiring" },
  { id: "interview_passed", label: "Interview Passed (Round Completed)", group: "Core Hiring" },
  { id: "all_rounds_cleared", label: "All Rounds Cleared (Offer Preparation)", group: "Core Hiring" },
  
  // Follow-ups & Reminders
  { id: "interview_reminder_24h", label: "Interview Reminder (24 Hours Prior)", group: "Follow-ups & Reminders" },
  { id: "interview_reminder_1h", label: "Interview Reminder (1 Hour Prior)", group: "Follow-ups & Reminders" },
  { id: "interview_rescheduled", label: "Interview Rescheduled Notice", group: "Follow-ups & Reminders" },
  { id: "no_response_followup", label: "Candidate Follow-up / Check-in", group: "Follow-ups & Reminders" },
  { id: "candidate_followup", label: "Candidate Status Update", group: "Follow-ups & Reminders" },
  { id: "application_on_hold", label: "Application Status: On Hold", group: "Follow-ups & Reminders" },
  
  // Offers & Onboarding
  { id: "offer_letter_cover", label: "Job Offer Letter & Compensation Package", group: "Offers & Onboarding" },
  { id: "offer_accepted_confirmation", label: "Offer Accepted Confirmation", group: "Offers & Onboarding" },
  { id: "welcome_onboarding", label: "Welcome to Team & Onboarding Guide", group: "Offers & Onboarding" },
  
  // Decisions
  { id: "rejection", label: "Application Update / Polite Rejection", group: "Decisions & Closure" },
  { id: "candidate_no_show", label: "Interview Follow-up (No-Show Check-in)", group: "Decisions & Closure" },
  
  // Custom
  { id: "custom", label: "Custom Message (Write Your Own)", group: "Custom" },
];

export function SendEmailDialog({
  open,
  onOpenChange,
  candidate,
}: SendEmailDialogProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const [selectedTemplate, setSelectedTemplate] = useState("interview_invitation");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [companyName, setCompanyName] = useState("Talent Acquisition");
  const [slotLink, setSlotLink] = useState("");
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);

  // Initialize slot link and preview whenever candidate changes or dialog opens
  useEffect(() => {
    if (candidate && open) {
      const defaultSlot = typeof window !== "undefined"
        ? `${window.location.origin}/schedule/${candidate.id}`
        : `/schedule/${candidate.id}`;
      setSlotLink(defaultSlot);
      loadPreview("interview_invitation", defaultSlot, companyName);
    }
  }, [candidate, open]);

  const loadPreview = async (
    templateKey: string,
    currentSlot: string,
    currentCompany: string
  ) => {
    if (!candidate) return;
    setIsPreviewLoading(true);
    try {
      const res = await googleApi.previewEmail({
        candidate_id: candidate.id,
        template_name: templateKey,
        slot_link: currentSlot || undefined,
        company_name: currentCompany || undefined,
      });
      setSubject(res.subject);
      setBody(res.body);
    } catch (err: any) {
      toast({
        title: "Preview Generation Notice",
        description: err.message || "Using local fallback template.",
      });
    } finally {
      setIsPreviewLoading(false);
    }
  };

  const handleTemplateChange = (tmplId: string) => {
    setSelectedTemplate(tmplId);
    if (tmplId !== "custom") {
      loadPreview(tmplId, slotLink, companyName);
    }
  };

  const sendMutation = useMutation({
    mutationFn: async () => {
      if (!candidate) throw new Error("No candidate selected.");
      return googleApi.sendEmail({
        candidate_id: candidate.id,
        subject: subject.trim(),
        body: body.trim(),
        template_name: selectedTemplate,
      });
    },
    onSuccess: (data) => {
      toast({
        title: "Email Sent Successfully",
        description: `Delivered via Gmail API to ${data.recipient_email}.`,
      });
      queryClient.invalidateQueries({ queryKey: ["candidate", candidate?.id] });
      queryClient.invalidateQueries({ queryKey: ["candidate-audit-logs", candidate?.id] });
      queryClient.invalidateQueries({ queryKey: ["audit-logs"] });
      queryClient.invalidateQueries({ queryKey: ["messages"] });
      onOpenChange(false);
    },
    onError: (err: any) => {
      toast({
        title: "Email Delivery Failed",
        description: err.message || "Failed to send email via Gmail API.",
        variant: "destructive",
      });
    },
  });

  if (!candidate) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
              <Mail className="h-4 w-4" />
            </div>
            <div>
              <DialogTitle className="text-base font-bold">
                Send Candidate Email via Gmail
              </DialogTitle>
              <DialogDescription className="text-xs">
                Sends directly from your linked Google account with automatic audit trail recording.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* Recipient info badge */}
          <div className="flex flex-wrap items-center justify-between gap-2 p-2.5 rounded-lg border bg-muted/30 text-xs">
            <div className="space-y-0.5">
              <span className="text-[11px] text-muted-foreground font-medium">Recipient</span>
              <p className="font-semibold text-foreground flex items-center gap-1.5">
                <span>{candidate.name}</span>
                <span className="text-muted-foreground font-normal">({candidate.email})</span>
              </p>
            </div>
            {candidate.opening_title && (
              <Badge variant="outline" className="text-[10px] font-normal">
                {candidate.opening_title}
              </Badge>
            )}
          </div>

          {/* Template Selector */}
          <div className="space-y-1.5">
            <Label className="text-xs font-semibold">Email Template</Label>
            <select
              value={selectedTemplate}
              onChange={(e) => handleTemplateChange(e.target.value)}
              className="w-full text-xs h-9 px-3 rounded-md border border-input bg-background text-foreground focus:outline-none focus:ring-1 focus:ring-primary cursor-pointer"
            >
              {Array.from(new Set(EMAIL_TEMPLATES.map((t) => t.group))).map((group) => (
                <optgroup key={group} label={group}>
                  {EMAIL_TEMPLATES.filter((t) => t.group === group).map((tmpl) => (
                    <option key={tmpl.id} value={tmpl.id}>
                      {tmpl.label}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          </div>

          {/* Template Variables (Company Name & Slot Link) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label className="text-[11px] text-muted-foreground flex items-center gap-1">
                <Building2 className="h-3 w-3" />
                <span>Company / Team Name</span>
              </Label>
              <Input
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                onBlur={() => loadPreview(selectedTemplate, slotLink, companyName)}
                placeholder="Talent Acquisition"
                className="text-xs h-8"
              />
            </div>
            <div className="space-y-1">
              <Label className="text-[11px] text-muted-foreground flex items-center gap-1">
                <LinkIcon className="h-3 w-3" />
                <span>Scheduling Link</span>
              </Label>
              <Input
                value={slotLink}
                onChange={(e) => setSlotLink(e.target.value)}
                onBlur={() => loadPreview(selectedTemplate, slotLink, companyName)}
                placeholder="https://..."
                className="text-xs h-8 font-mono"
              />
            </div>
          </div>

          {/* Subject Line */}
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <Label className="text-xs font-semibold">Subject</Label>
              {isPreviewLoading && (
                <span className="text-[10px] text-muted-foreground flex items-center gap-1 animate-pulse">
                  <RefreshCw className="h-2.5 w-2.5 animate-spin" /> Rendering...
                </span>
              )}
            </div>
            <Input
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Email subject..."
              className="text-xs h-8 font-medium"
            />
          </div>

          {/* Email Body */}
          <div className="space-y-1">
            <Label className="text-xs font-semibold">Message Body</Label>
            <Textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="Write candidate message..."
              rows={8}
              className="text-xs font-sans leading-relaxed resize-none"
            />
          </div>

          {/* Variables Reference Pill */}
          <div className="flex flex-wrap items-center gap-1 text-[10px] text-muted-foreground bg-muted/20 p-2 rounded border border-border/40">
            <span className="font-medium mr-1">Variables supported:</span>
            <code className="bg-background px-1 py-0.5 rounded border">{"{candidate_name}"}</code>
            <code className="bg-background px-1 py-0.5 rounded border">{"{role}"}</code>
            <code className="bg-background px-1 py-0.5 rounded border">{"{company}"}</code>
            <code className="bg-background px-1 py-0.5 rounded border">{"{slot_link}"}</code>
          </div>
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => onOpenChange(false)}
            className="text-xs"
          >
            Cancel
          </Button>
          <Button
            type="button"
            size="sm"
            onClick={() => sendMutation.mutate()}
            disabled={sendMutation.isPending || !subject.trim() || !body.trim()}
            className="text-xs gap-1.5 font-medium"
          >
            {sendMutation.isPending ? (
              <RefreshCw className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Send className="h-3.5 w-3.5" />
            )}
            <span>{sendMutation.isPending ? "Sending via Gmail..." : "Send Email"}</span>
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
