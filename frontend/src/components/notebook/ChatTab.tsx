import React from 'react'
import { ChatLayout } from '@/features/chat/components/ChatLayout'

interface ChatTabProps {
  notebookId: string
}

export function ChatTab({ notebookId }: ChatTabProps) {
  if (!notebookId) {
    return (
      <div className="flex-1 flex items-center justify-center h-full bg-background text-muted-foreground text-sm">
        Select a notebook to start chatting.
      </div>
    )
  }

  return <ChatLayout notebookId={notebookId} />
}
