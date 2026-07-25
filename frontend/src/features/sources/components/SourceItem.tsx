import type { Source } from '@/types/api'
import { FileText, Link, Video, FileOutput, FileSpreadsheet, PlaySquare, File, Trash2, AlertCircle } from 'lucide-react'
import { SourceStatusBadge } from './SourceStatusBadge'
import { Button } from '@/components/ui'
import { useDeleteSource } from '@/hooks/useSources'

const SOURCE_ICONS = {
  pdf: <FileText className="w-5 h-5 text-terminal-red" />,
  docx: <FileText className="w-5 h-5 text-blue-500" />,
  xlsx: <FileSpreadsheet className="w-5 h-5 text-terminal-green" />,
  csv: <FileSpreadsheet className="w-5 h-5 text-terminal-green" />,
  markdown: <FileOutput className="w-5 h-5 text-slate-500" />,
  pptx: <PlaySquare className="w-5 h-5 text-orange-500" />,
  epub: <FileText className="w-5 h-5 text-primary" />,
  youtube: <Video className="w-5 h-5 text-terminal-red" />,
  url: <Link className="w-5 h-5 text-blue-400" />,
  text: <FileText className="w-5 h-5 text-slate-400" />,
  txt: <FileText className="w-5 h-5 text-slate-400" />,
}

interface Props {
  workspaceId: string
  notebookId: string
  source: Source
}

export function SourceItem({ workspaceId, notebookId, source }: Props) {
  const deleteMutation = useDeleteSource(workspaceId, notebookId)

  const handleDelete = () => {
    if (confirm('Are you sure you want to delete this source?')) {
      deleteMutation.mutate(source.id)
    }
  }

  const getIcon = () => {
    const typeStr = source.type.toLowerCase();
    return SOURCE_ICONS[typeStr as keyof typeof SOURCE_ICONS] || <File className="w-5 h-5 text-muted-foreground" />
  }

  return (
    <div className="flex items-center justify-between p-4 bg-card border border-border rounded-lg shadow-sm hover:border-primary/30 transition-all duration-200 hover:-translate-y-0.5 group">
      <div className="flex items-center gap-4 overflow-hidden">
        <div className="p-2 bg-background rounded-md border border-border">
          {getIcon()}
        </div>
        
        <div className="flex flex-col min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium truncate max-w-[300px]" title={source.name}>
              {source.name}
            </span>
            <SourceStatusBadge status={source.status} />
          </div>
          
          <div className="text-xs text-muted-foreground flex items-center gap-3 mt-1">
            <span>{new Date(source.created_at).toLocaleDateString()}</span>
            {source.char_count ? (
              <span>{(source.char_count / 1000).toFixed(1)}k chars</span>
            ) : null}
            <span className="uppercase">{source.type}</span>
          </div>

          {source.status === 'error' && source.error_message && (
            <div className="text-xs text-destructive flex items-center gap-1 mt-2">
              <AlertCircle className="h-3 w-3" />
              <span className="truncate">{source.error_message}</span>
            </div>
          )}
        </div>
      </div>
      
      <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center">
        <Button 
          variant="ghost" 
          size="sm" 
          onClick={handleDelete}
          disabled={deleteMutation.isPending}
          className="text-destructive hover:text-destructive hover:bg-destructive/10 active:scale-[0.98] transition-all duration-150"
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
