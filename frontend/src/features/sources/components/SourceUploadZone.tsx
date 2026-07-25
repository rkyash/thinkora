import { useCallback, useState } from 'react'
import { UploadCloud, File as FileIcon, X } from 'lucide-react'
import { useUploadSource } from '@/hooks/useSources'
import { Button } from '@/components/ui'
import { cn } from '@/lib/utils'

interface Props {
  workspaceId: string
  notebookId: string
}

export function SourceUploadZone({ workspaceId, notebookId }: Props) {
  const [isDragging, setIsDragging] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<number | null>(null)
  const uploadMutation = useUploadSource(workspaceId, notebookId)

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragging(true)
    } else if (e.type === 'dragleave') {
      setIsDragging(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }, [workspaceId, notebookId])

  const handleFile = (file: File) => {
    setUploadProgress(0)
    uploadMutation.mutate({
      file,
      onProgress: (pct) => setUploadProgress(pct)
    }, {
      onSettled: () => setUploadProgress(null)
    })
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  return (
    <div
      className={cn(
        "relative flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-xl transition-all",
        isDragging ? "border-primary bg-primary/5" : "border-border hover:border-primary/50 hover:bg-card",
        uploadMutation.isPending && "pointer-events-none opacity-80"
      )}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
      <input 
        type="file" 
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" 
        onChange={handleChange}
        disabled={uploadMutation.isPending}
        accept=".pdf,.txt,.md,.csv,.xlsx,.docx,.pptx,.epub"
      />
      
      <div className="flex flex-col items-center gap-3 text-center">
        <div className="p-4 bg-background rounded-full shadow-sm">
          <UploadCloud className="h-8 w-8 text-primary/80" />
        </div>
        
        {uploadMutation.isPending ? (
          <div className="flex flex-col items-center gap-2 w-full max-w-xs">
            <p className="text-sm font-medium">Uploading source...</p>
            <div className="w-full bg-secondary h-2 rounded-full overflow-hidden">
              <div 
                className="bg-primary h-full transition-all duration-300" 
                style={{ width: `${uploadProgress ?? 0}%` }}
              />
            </div>
            <p className="text-xs text-muted-foreground">{uploadProgress}%</p>
          </div>
        ) : (
          <>
            <div>
              <p className="text-sm font-semibold">Click to upload or drag and drop</p>
              <p className="text-xs text-muted-foreground mt-1">
                PDF, DOCX, XLSX, CSV, Markdown, TXT (max. 100MB)
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
