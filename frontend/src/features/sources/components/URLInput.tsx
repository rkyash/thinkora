import { useState } from "react";
import { Link2, Play, Send } from "lucide-react";
import { useAddUrlSource, useAddYoutubeSource } from "@/hooks/useSources";
import { Button, Input } from "@/components/ui";
import { useToast } from '@/components/ui'

interface Props {
  workspaceId: string;
  notebookId: string;
}

export function URLInput({ workspaceId, notebookId }: Props) {
  const [url, setUrl] = useState("");
  const [name, setName] = useState("");
  const urlMutation = useAddUrlSource(workspaceId, notebookId);
  const youtubeMutation = useAddYoutubeSource(workspaceId, notebookId);
  const { toast } = useToast();

  const isYoutube = url.includes("youtube.com") || url.includes("youtu.be");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!url.trim()) return;

    const sourceName = name.trim() || "Imported Link";

    if (isYoutube) {
      youtubeMutation.mutate(
        { name: sourceName, url: url.trim() },
        {
          onSuccess: () => {
            setUrl("");
            setName("");
            toast("YouTube video added", "success");
          },
        },
      );
    } else {
      urlMutation.mutate(
        { name: sourceName, url: url.trim() },
        {
          onSuccess: () => {
            setUrl("");
            setName("");
            toast("URL added", "success");
          },
        },
      );
    }
  };

  const isPending = urlMutation.isPending || youtubeMutation.isPending;

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-col gap-3 p-4 bg-card rounded-lg border border-border shadow-sm"
    >
      <div className="flex items-center gap-2 mb-1">
        {isYoutube ? (
          <Play className="h-4 w-4 text-terminal-red" />
        ) : (
          <Link2 className="h-4 w-4 text-primary" />
        )}
        <span className="text-sm font-medium">Import from URL</span>
      </div>

      <div className="flex gap-2">
        <Input
          placeholder="Name (optional)"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="flex-1 max-w-[200px]"
          disabled={isPending}
        />
        <Input
          placeholder="https://example.com/article"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="flex-[2]"
          required
          type="url"
          disabled={isPending}
        />
        <Button type="submit" disabled={isPending || !url.trim()} className="active:scale-[0.98] transition-all duration-150">
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </form>
  );
}
