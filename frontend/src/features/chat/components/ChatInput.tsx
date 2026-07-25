import React, { useState, useRef, useEffect } from 'react'
import { Send, Paperclip, X } from 'lucide-react'
import { Button } from '@/components/ui'

interface ChatInputProps {
  onSend: (text: string) => void
  disabled?: boolean
  editValue?: string          // pre-fill text when editing a message
  onCancelEdit?: () => void   // called when user cancels an edit
}

export function ChatInput({ onSend, disabled, editValue, onCancelEdit }: ChatInputProps) {
  const [inputVal, setInputVal] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Pre-fill textarea when editValue changes (user clicked Edit on a message)
  useEffect(() => {
    if (editValue !== undefined) {
      setInputVal(editValue)
      // Focus and move cursor to end
      setTimeout(() => {
        const ta = textareaRef.current
        if (ta) { ta.focus(); ta.selectionStart = ta.selectionEnd = ta.value.length }
      }, 0)
    }
  }, [editValue])

  // Fix #5 — auto-resize textarea as user types
  useEffect(() => {
    const ta = textareaRef.current
    if (!ta) return
    ta.style.height = 'auto'
    ta.style.height = Math.min(ta.scrollHeight, 128) + 'px'
  }, [inputVal])

  const handleSend = () => {
    if (!inputVal.trim() || disabled) return
    onSend(inputVal.trim())
    setInputVal('')
    // Reset height after clear
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const isEditing = editValue !== undefined

  return (
    <div className="p-4 bg-background/50 border-t border-border shrink-0 z-10 backdrop-blur-md">
      {/* Editing banner */}
      {isEditing && (
        <div className="max-w-4xl mx-auto mb-2 flex items-center gap-2 px-1">
          <span className="text-[11px] text-primary font-mono bg-primary/10 border border-primary/20 rounded px-2 py-0.5">
            ✏️ Editing message
          </span>
          <button
            onClick={onCancelEdit}
            className="ml-auto text-[11px] text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors"
          >
            <X className="w-3 h-3" /> Cancel
          </button>
        </div>
      )}
      <div className="max-w-4xl mx-auto flex items-end gap-3">
        <Button
          variant="outline"
          size="sm"
          className="h-11 w-11 border-border bg-card hover:bg-accent text-muted-foreground hover:text-foreground shrink-0 rounded-xl mb-0.5"
          title="Attach documents"
          onClick={() => alert('Document attachment coming soon')}
          disabled={disabled}
        >
          <Paperclip className="w-5 h-5" />
        </Button>

        <div className="flex-grow relative flex items-end">
          <textarea
            ref={textareaRef}
            rows={1}
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSend()
              }
              if (e.key === 'Escape' && isEditing) {
                onCancelEdit?.()
              }
            }}
            placeholder={isEditing ? 'Edit your message… (Enter to send, Esc to cancel)' : 'Ask a question about your sources… (Shift+Enter for new line)'}
            disabled={disabled}
            className={`w-full rounded-xl bg-background border px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all resize-none pr-12 min-h-[46px] max-h-32 disabled:opacity-50 overflow-y-auto ${
              isEditing ? 'border-primary/40 ring-1 ring-primary/20' : 'border-border'
            }`}
          />
          <button
            onClick={handleSend}
            disabled={!inputVal.trim() || disabled}
            className="absolute right-3.5 bottom-3 text-primary hover:text-white disabled:text-muted-foreground disabled:hover:text-muted-foreground p-1 transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
