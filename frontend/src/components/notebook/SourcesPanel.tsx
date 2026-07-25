import React, { useState } from "react";
import { useParams } from "react-router-dom";
import {
  FileText,
  Globe,
  PlaySquare,
  Plus,
  Link2,
  UploadCloud,
  Trash2,
  AlertCircle,
  CheckCircle2,
  Loader2,
  FileSpreadsheet,
  File,
} from "lucide-react";
import { Input } from "@/components/ui/Input";
import { cn } from "@/lib/utils";
import { useNotebookStore } from "@/store/notebookStore";
import { useNotebook } from "@/hooks/useNotebooks";
import {
  useSources,
  useUploadSource,
  useAddUrlSource,
  useAddYoutubeSource,
  useDeleteSource,
} from "@/hooks/useSources";
import type { Source } from "@/types/api";
import { useToast } from "@/components/ui";

export function SourcesPanel() {
  const { id: notebookId } = useParams<{ id: string }>();
  const { data: notebook } = useNotebook(notebookId || "");
  const workspaceId = notebook?.workspace_id || "";

  const { data: sources = [], isLoading: isLoadingSources } = useSources(
    workspaceId,
    notebookId || "",
  );
  const uploadMutation = useUploadSource(workspaceId, notebookId || "");
  const addUrlMutation = useAddUrlSource(workspaceId, notebookId || "");
  const addYoutubeMutation = useAddYoutubeSource(workspaceId, notebookId || "");
  const deleteMutation = useDeleteSource(workspaceId, notebookId || "");
  const { toast } = useToast();

  const [inputUrl, setInputUrl] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);

  const handleAddUrl = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputUrl.trim() || !notebookId || !workspaceId) return;

    const isYoutube =
      inputUrl.includes("youtube.com") || inputUrl.includes("youtu.be");
    const urlStr = inputUrl.trim();

    if (isYoutube) {
      addYoutubeMutation.mutate(
        { name: "YouTube Video", url: urlStr },
        {
          onSuccess: () => {
            setInputUrl("");
            toast("Added YouTube source", "success");
          },
          onError: (err: any) => {
            toast(
              err?.response?.data?.error || "Failed to add YouTube source",
              "error",
            );
          },
        },
      );
    } else {
      addUrlMutation.mutate(
        { name: "Web Source", url: urlStr },
        {
          onSuccess: () => {
            setInputUrl("");
            toast("Added URL source", "success");
          },
          onError: (err: any) => {
            toast(
              err?.response?.data?.error || "Failed to add URL source",
              "error",
            );
          },
        },
      );
    }
  };

  const handleDeleteSource = (id: string) => {
    if (!notebookId || !workspaceId) return;
    deleteMutation.mutate(id, {
      onSuccess: () => {
        toast("Source deleted", "success");
      },
    });
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setUploadProgress(0);
      uploadMutation.mutate(
        {
          file,
          onProgress: (pct) => setUploadProgress(pct),
        },
        {
          onSuccess: () => {
            setUploadProgress(null);
            toast("File uploaded successfully", "success");
          },
          onError: (err: any) => {
            setUploadProgress(null);
            toast(err?.response?.data?.error || "Upload failed", "error");
          },
        },
      );
    }
  };

  const getSourceIcon = (type: Source["type"]) => {
    switch (type) {
      case "pdf":
        return <File className="w-4 h-4 text-terminal-red" />;
      case "docx":
      case "txt":
      case "markdown":
      case "text":
        return <FileText className="w-4 h-4 text-blue-400" />;
      case "xlsx":
      case "csv":
        return <FileSpreadsheet className="w-4 h-4 text-terminal-green" />;
      case "url":
        return <Globe className="w-4 h-4 text-primary" />;
      case "youtube":
        return <PlaySquare className="w-4 h-4 text-terminal-red" />;
      case "audio":
        return <PlaySquare className="w-4 h-4 text-orange-400" />;
      default:
        return <FileText className="w-4 h-4 text-primary" />;
    }
  };

  return (
    <div className="w-72 border-r border-border bg-card h-full flex flex-col z-10">
      {/* Sources Header */}
      <div className="p-4 border-b border-border flex justify-between items-center shrink-0">
        <h3 className="font-headline font-bold text-sm text-foreground flex items-center gap-2">
          Sources
          <span className="text-xs font-mono bg-background border border-border px-1.5 py-0.2 rounded-full text-muted-foreground">
            {sources.length}
          </span>
        </h3>
      </div>

      {/* Drag & Drop Upload Zone */}
      <div className="p-4 shrink-0 space-y-3">
        <label
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          className={cn(
            "relative border border-dashed rounded-xl p-4 text-center transition-all flex flex-col items-center justify-center bg-background",
            dragActive
              ? "border-primary bg-primary/5"
              : "border-border hover:border-primary/50 hover:bg-accent",
            uploadMutation.isPending && "pointer-events-none opacity-80",
          )}
        >
          <input
            type="file"
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                const file = e.target.files[0];
                setUploadProgress(0);
                uploadMutation.mutate(
                  {
                    file,
                    onProgress: (pct) => setUploadProgress(pct),
                  },
                  {
                    onSuccess: () => {
                      setUploadProgress(null);
                      toast("File uploaded successfully", "success");
                    },
                    onError: (err: any) => {
                      setUploadProgress(null);
                      toast(
                        err?.response?.data?.error || "Upload failed",
                        "error",
                      );
                    },
                  },
                );
              }
            }}
            disabled={uploadMutation.isPending}
            accept=".pdf,.txt,.md,.csv,.xlsx,.docx,.pptx,.epub"
          />
          {uploadMutation.isPending ? (
            <div className="flex flex-col items-center gap-2 w-full">
              <Loader2 className="w-6 h-6 animate-spin text-primary" />
              <p className="text-xs font-medium">Uploading...</p>
              <div className="w-full bg-secondary h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-primary h-full transition-all duration-300"
                  style={{ width: `${uploadProgress ?? 0}%` }}
                />
              </div>
            </div>
          ) : (
            <>
              <UploadCloud className="w-8 h-8 text-muted-foreground mb-2" />
              <span className="text-xs font-semibold text-foreground">
                Drop files here
              </span>
              <span className="text-[10px] text-muted-foreground mt-0.5">
                Supports PDF, TXT, MD, CSV, XLSX, DOCX
              </span>
            </>
          )}
        </label>

        {/* URL Input */}
        <form onSubmit={handleAddUrl} className="w-full">
          <Input
            value={inputUrl}
            onChange={(e) => setInputUrl(e.target.value)}
            placeholder="Add URL or YouTube link"
            startIcon={<Link2 className="w-3.5 h-3.5 text-muted-foreground" />}
            endIcon={
              <button
                type="submit"
                disabled={addUrlMutation.isPending || addYoutubeMutation.isPending}
                className="bg-primary/10 hover:bg-primary/20 text-primary p-1 rounded-md transition-colors disabled:opacity-50 active:scale-[0.98] -mr-1.5"
              >
                {addUrlMutation.isPending || addYoutubeMutation.isPending ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Plus className="w-3.5 h-3.5" />
                )}
              </button>
            }
            className="w-full text-xs bg-background border-border text-foreground h-8"
            disabled={addUrlMutation.isPending || addYoutubeMutation.isPending}
          />
        </form>
      </div>

      <div className="border-t border-border my-1 shrink-0" />

      {/* Source List */}
      <div className="flex-1 overflow-y-auto px-4 py-2 space-y-2">
        {isLoadingSources ? (
          <div className="flex justify-center p-4">
            <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
          </div>
        ) : sources.length === 0 ? (
          <div className="text-center p-4 text-xs text-muted-foreground">
            No sources yet. Upload a document or add a URL to get started.
          </div>
        ) : (
          sources.map((source) => (
            <div
              key={source.id}
              className="glass rounded-xl p-3 flex gap-2.5 items-start relative group hover:border-primary/50 transition-all duration-200 hover:-translate-y-0.5"
            >
              <div className="w-7 h-7 rounded-lg bg-background flex items-center justify-center border border-border shrink-0 mt-0.5">
                {getSourceIcon(source.type)}
              </div>

              <div className="flex-1 min-w-0 pr-5">
                <p
                  className="text-xs text-foreground font-medium truncate leading-tight"
                  title={source.name}
                >
                  {source.name}
                </p>
                <div className="flex items-center gap-1.5 mt-1">
                  {source.status === "ready" && (
                    <span className="badge-ready flex items-center gap-1 text-[9px] py-0">
                      <CheckCircle2 className="w-2.5 h-2.5" /> Ready
                    </span>
                  )}
                  {(source.status === "processing" ||
                    source.status === "pending") && (
                    <span className="badge-processing flex items-center gap-1 text-[9px] py-0">
                      <Loader2 className="w-2.5 h-2.5 animate-spin" />{" "}
                      {source.status}
                    </span>
                  )}
                  {source.status === "error" && (
                    <span
                      className="badge-error flex items-center gap-1 text-[9px] py-0"
                      title={source.error_message || "Error"}
                    >
                      <AlertCircle className="w-2.5 h-2.5" /> Error
                    </span>
                  )}
                  <span className="text-[9px] text-muted-foreground font-mono truncate">
                    {source.char_count
                      ? `${(source.char_count / 1000).toFixed(1)}k chars`
                      : ""}
                  </span>
                </div>
              </div>

              {/* Hover Delete Button */}
              <button
                onClick={() => handleDeleteSource(source.id)}
                disabled={deleteMutation.isPending}
                className="absolute right-2 top-2 p-1 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity rounded-md bg-surface/50 border border-outline/10 disabled:opacity-50"
                title="Delete source"
              >
                {deleteMutation.isPending ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <Trash2 className="w-3 h-3" />
                )}
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
