import { useSources } from '@/hooks/useSources'
import { SourceItem } from './SourceItem'
import { Spinner } from '@/components/ui'
import { Database } from 'lucide-react'

interface Props {
  workspaceId: string
  notebookId: string
}

export function SourceList({ workspaceId, notebookId }: Props) {
  const { data: sources, isLoading, error } = useSources(workspaceId, notebookId)

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 text-sm text-destructive bg-destructive/10 rounded-lg">
        Failed to load sources. Please try again.
      </div>
    )
  }

  if (!sources || sources.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground bg-muted/20 rounded-xl border border-dashed border-border">
        <Database className="h-10 w-10 mb-4 opacity-50" />
        <p className="font-medium">No sources yet</p>
        <p className="text-sm opacity-80 mt-1">Upload a document or add a URL to get started</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      {sources.map(source => (
        <SourceItem 
          key={source.id} 
          workspaceId={workspaceId} 
          notebookId={notebookId} 
          source={source} 
        />
      ))}
    </div>
  )
}
