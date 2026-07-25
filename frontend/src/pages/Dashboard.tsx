import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQueryClient, useMutation } from "@tanstack/react-query";
import {
  Folder,
  Plus,
  Edit2,
  Trash2,
  BookOpen,
  ArrowRight,
  Sparkles,
  Layers,
} from "lucide-react";
import { Layout } from "@/components/layout/Layout";
import { Button } from "@/components/ui/Button";
import { Modal, ModalFooter } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { Textarea } from "@/components/ui/Textarea";
import { useAuth } from "@/hooks/useAuth";
import {
  useWorkspaces,
  useCreateWorkspace,
  useDeleteWorkspace,
} from "@/hooks/useWorkspaces";
import * as workspacesApi from "@/api/workspaces";
import { workspaceKeys } from "@/utils/queryKeys";
import { ROUTES } from "@/utils/constants";

export function Dashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const queryClient = useQueryClient();

  // Queries & Mutations
  const { data: workspaces = [], isLoading } = useWorkspaces();
  const createWorkspaceMutation = useCreateWorkspace();
  const deleteWorkspaceMutation = useDeleteWorkspace();

  // Flexible update mutation to handle any workspace ID dynamically
  const updateWorkspaceMutation = useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string;
      data: { name: string; description?: string };
    }) => workspacesApi.updateWorkspace(id, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: workspaceKeys.lists() });
    },
  });

  // Modals state
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [createName, setCreateName] = useState("");
  const [createDescription, setCreateDescription] = useState("");

  const [editingWorkspace, setEditingWorkspace] = useState<{
    id: string;
    name: string;
    description: string;
  } | null>(null);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");

  const [deletingWorkspace, setDeletingWorkspace] = useState<{
    id: string;
    name: string;
  } | null>(null);

  // Greeting
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  };

  // Handlers
  const handleCreateWorkspace = () => {
    setCreateName("");
    setCreateDescription("");
    setIsCreateOpen(true);
  };

  const handleEditWorkspace = (
    e: React.MouseEvent,
    id: string,
    currentName: string,
    currentDesc?: string | null,
  ) => {
    e.stopPropagation(); // Prevent navigating to notebooks
    setEditName(currentName);
    setEditDescription(currentDesc ?? "");
    setEditingWorkspace({
      id,
      name: currentName,
      description: currentDesc ?? "",
    });
  };

  const handleDeleteWorkspace = (
    e: React.MouseEvent,
    id: string,
    name: string,
  ) => {
    e.stopPropagation(); // Prevent navigating to notebooks
    setDeletingWorkspace({ id, name });
  };

  const submitCreateWorkspace = (e: React.FormEvent) => {
    e.preventDefault();
    if (!createName.trim()) return;
    createWorkspaceMutation.mutate(
      {
        name: createName,
        description: createDescription,
      },
      {
        onSuccess: () => {
          setIsCreateOpen(false);
          setCreateName("");
          setCreateDescription("");
        },
      },
    );
  };

  const submitEditWorkspace = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingWorkspace || !editName.trim()) return;
    updateWorkspaceMutation.mutate(
      {
        id: editingWorkspace.id,
        data: { name: editName, description: editDescription },
      },
      {
        onSuccess: () => {
          setEditingWorkspace(null);
        },
      },
    );
  };

  const submitDeleteWorkspace = () => {
    if (!deletingWorkspace) return;
    deleteWorkspaceMutation.mutate(deletingWorkspace.id, {
      onSuccess: () => {
        setDeletingWorkspace(null);
      },
    });
  };

  return (
    <Layout
      title="Workspace Dashboard"
      activeWorkspaceId={null} // Don't highlight any single workspace when on global dashboard
      showSearch={false}
    >
      <div className="max-w-6xl mx-auto px-6 py-8 space-y-8 animate-fade-in">
        {/* Header Greeting */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-3xl font-headline font-bold gradient-text tracking-tight">
              {getGreeting()}, {user?.username || "Researcher"}
            </h1>
            <p className="text-muted-foreground text-sm mt-1">
              Select a workspace below to access your notebooks and study
              resources.
            </p>
          </div>
          <Button
            onClick={handleCreateWorkspace}
            className="btn-glow bg-primary hover:bg-violet-primary text-primary-foreground font-semibold flex items-center gap-2 h-10 shadow-sm active:scale-[0.98] transition-all duration-150"
          >
            <Plus className="w-4 h-4" />
            New Workspace
          </Button>
        </div>

        {/* Dashboard Stats / Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="glass-panel rounded-xl p-5 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0 border border-border text-primary bg-primary/10">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="text-2xl font-headline font-bold text-foreground">
                {workspaces.length}
              </div>
              <div className="text-xs text-muted-foreground font-medium mt-0.5">
                Total Workspaces
              </div>
            </div>
          </div>

          <div className="glass-panel rounded-xl p-5 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0 border border-border text-secondary bg-secondary/10">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <div className="text-sm font-headline font-bold text-foreground truncate max-w-[180px]">
                {user?.email || "Active User"}
              </div>
              <div className="text-xs text-muted-foreground font-medium mt-0.5">
                User Account
              </div>
            </div>
          </div>

          <div className="glass-panel rounded-xl p-5 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0 border border-border text-terminal-green bg-terminal-green/10">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="text-2xl font-headline font-bold text-foreground">
                Local-first
              </div>
              <div className="text-xs text-muted-foreground font-medium mt-0.5">
                Storage Backend
              </div>
            </div>
          </div>
        </div>

        {/* Workspaces List Section */}
        <div className="space-y-6">
          <h2 className="text-xl font-headline font-bold text-foreground flex items-center gap-2">
            Your Workspaces
            <span className="text-xs font-mono text-muted-foreground font-normal border border-border rounded px-1.5 py-0.5 bg-background">
              {workspaces.length}
            </span>
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {isLoading ? (
              <div className="col-span-full py-12 flex justify-center text-muted-foreground text-sm">
                Loading workspaces...
              </div>
            ) : workspaces.length === 0 ? (
              <div className="col-span-full py-12 text-center text-muted-foreground">
                <p>No workspaces found. Create one to get started!</p>
              </div>
            ) : (
              workspaces.map((ws, idx) => (
                <div
                  key={ws.id}
                  onClick={() => navigate(ROUTES.workspace(ws.id))}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      navigate(ROUTES.workspace(ws.id));
                    }
                  }}
                  className="glass-panel rounded-xl p-5 hover:border-primary/20 hover:glow-sm hover:-translate-y-0.5 transition-all duration-200 cursor-pointer flex flex-col justify-between group relative"
                  style={{ animationDelay: `${idx * 0.05}s` }}
                >
                  <div className="space-y-3">
                    <div className="flex justify-between items-start">
                      <div className="w-10 h-10 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
                        <Folder className="w-5 h-5" />
                      </div>

                      {/* Action buttons */}
                      <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          type="button"
                          aria-label="Edit workspace"
                          onClick={(e) =>
                            handleEditWorkspace(
                              e,
                              ws.id,
                              ws.name,
                              ws.description,
                            )
                          }
                          className="p-1.5 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          type="button"
                          aria-label="Delete workspace"
                          onClick={(e) =>
                            handleDeleteWorkspace(e, ws.id, ws.name)
                          }
                          className="p-1.5 rounded-md hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    <div>
                      <h3 className="font-headline font-bold text-lg text-foreground group-hover:text-primary transition-colors truncate">
                        {ws.name}
                      </h3>
                      <p className="text-xs text-muted-foreground line-clamp-2 mt-2 leading-relaxed h-8">
                        {ws.description || "No description provided."}
                      </p>
                    </div>
                  </div>

                  <div className="flex justify-between items-center border-t border-border pt-3 mt-4 text-[10px] text-muted-foreground font-mono">
                    <span className="flex items-center gap-1.5 text-primary">
                      <BookOpen className="w-3.5 h-3.5" />
                      View Notebooks
                    </span>
                    <ArrowRight className="w-3.5 h-3.5 text-primary opacity-0 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all" />
                  </div>
                </div>
              ))
            )}

            {/* Create Workspace Card Placeholder */}
            <div
              onClick={handleCreateWorkspace}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleCreateWorkspace();
                }
              }}
              className="rounded-xl border border-dashed border-border hover:border-primary/50 bg-background hover:bg-accent flex flex-col items-center justify-center p-6 text-center cursor-pointer transition-all duration-200 group hover:glow-sm min-h-[180px] hover:-translate-y-0.5"
            >
              <div className="w-10 h-10 rounded-full bg-card flex items-center justify-center mb-3 border border-border group-hover:bg-primary/10 group-hover:border-primary/20 transition-colors">
                <Plus className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
              </div>
              <span className="font-semibold text-sm text-foreground">
                Create Workspace
              </span>
              <p className="text-xs text-muted-foreground mt-1 max-w-[200px]">
                Set up a new workspace context for your studies.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Create Workspace Modal */}
      <Modal
        open={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Create Workspace"
        description="Set up a new workspace context for your study notebooks."
      >
        <form onSubmit={submitCreateWorkspace} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Workspace Name
            </label>
            <Input
              required
              value={createName}
              onChange={(e) => setCreateName(e.target.value)}
              placeholder="e.g. Hospital Analytics, Biology Semester 1"
              autoFocus
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Description (optional)
            </label>
            <Textarea
              value={createDescription}
              onChange={(e) => setCreateDescription(e.target.value)}
              placeholder="Describe the topics, courses, or purpose of this workspace..."
              rows={3}
            />
          </div>
          <ModalFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsCreateOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={createWorkspaceMutation.isPending}
              className="bg-primary hover:bg-violet-primary text-primary-foreground font-semibold active:scale-[0.98] transition-all duration-150"
            >
              {createWorkspaceMutation.isPending ? "Creating..." : "Create"}
            </Button>
          </ModalFooter>
        </form>
      </Modal>

      {/* Edit Workspace Modal */}
      <Modal
        open={Boolean(editingWorkspace)}
        onClose={() => setEditingWorkspace(null)}
        title="Edit Workspace"
        description="Update the workspace context details."
      >
        <form onSubmit={submitEditWorkspace} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Workspace Name
            </label>
            <Input
              required
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              placeholder="Workspace Name"
              autoFocus
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Description (optional)
            </label>
            <Textarea
              value={editDescription}
              onChange={(e) => setEditDescription(e.target.value)}
              placeholder="Workspace Description"
              rows={3}
            />
          </div>
          <ModalFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setEditingWorkspace(null)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={updateWorkspaceMutation.isPending}
              className="bg-primary hover:bg-violet-primary text-primary-foreground font-semibold active:scale-[0.98] transition-all duration-150"
            >
              {updateWorkspaceMutation.isPending ? "Saving..." : "Save Changes"}
            </Button>
          </ModalFooter>
        </form>
      </Modal>

      {/* Delete Workspace Confirmation Modal */}
      <Modal
        open={Boolean(deletingWorkspace)}
        onClose={() => setDeletingWorkspace(null)}
        title="Delete Workspace"
        description={`Are you sure you want to delete the workspace "${deletingWorkspace?.name}"?`}
      >
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground leading-relaxed">
            This action is permanent and will delete all associated notebooks,
            sources, flashcards, and study sessions within this workspace.
          </p>
          <ModalFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setDeletingWorkspace(null)}
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={submitDeleteWorkspace}
              disabled={deleteWorkspaceMutation.isPending}
              className="bg-destructive hover:bg-destructive/90 text-destructive-foreground font-semibold active:scale-[0.98] transition-all duration-150"
            >
              {deleteWorkspaceMutation.isPending
                ? "Deleting..."
                : "Delete Workspace"}
            </Button>
          </ModalFooter>
        </div>
      </Modal>
    </Layout>
  );
}
