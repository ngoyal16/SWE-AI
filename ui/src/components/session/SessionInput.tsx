import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Play, SendHorizonal, Paperclip, Mic } from "lucide-react"

interface SessionInputProps {
    status: string
    isSubmitting: boolean
    onApprove: () => void
    onSend: (message: string) => void
}

export function SessionInput({ status, isSubmitting, onApprove, onSend }: SessionInputProps) {
    const [message, setMessage] = useState("")
    const textareaRef = useRef<HTMLTextAreaElement>(null)

    const handleSubmit = (e?: React.FormEvent) => {
        e?.preventDefault()
        if (!message.trim()) return
        onSend(message)
        setMessage("")
    }

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault()
            handleSubmit()
        }
    }

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
        }
    }, [message]);

    const needsApproval = status === 'WAITING_FOR_USER'

    return (
        <div className="max-w-4xl mx-auto flex flex-col gap-4 relative">
            {needsApproval && (
                <div className="flex items-center justify-between bg-amber-500/10 border border-amber-500/20 rounded-2xl p-4 animate-in slide-in-from-bottom-2 shadow-sm">
                    <div className="flex items-center gap-3 text-sm font-medium text-amber-700 dark:text-amber-400">
                        <span className="relative flex h-3 w-3">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-3 w-3 bg-amber-500"></span>
                        </span>
                        <span>Approvals needed to continue</span>
                    </div>
                    <Button
                        size="sm"
                        onClick={onApprove}
                        disabled={isSubmitting}
                        className="bg-amber-500 hover:bg-amber-600 text-white border-none shadow-md rounded-full px-6 font-semibold"
                    >
                        <Play className="h-4 w-4 mr-2 fill-current" />
                        Approve
                    </Button>
                </div>
            )}

            <div className={`relative group transition-all duration-200 ${isSubmitting ? 'opacity-70 pointer-events-none' : ''}`}>
                <div className="absolute inset-0 bg-gradient-to-r from-primary/20 via-purple-500/20 to-pink-500/20 rounded-[2rem] blur-md opacity-0 group-focus-within:opacity-100 transition-opacity duration-500"></div>

                <div className="relative bg-surface-container-low rounded-[2rem] border border-border/60 shadow-lg focus-within:shadow-xl focus-within:border-primary/50 transition-all flex flex-col p-2">
                    <Textarea
                        ref={textareaRef}
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={needsApproval ? "Provide feedback to guide the agent..." : "Ask SWE Agent anything..."}
                        className="min-h-[56px] max-h-[200px] w-full resize-none border-0 bg-transparent px-4 py-4 text-base placeholder:text-muted-foreground/60 focus-visible:ring-0 focus-visible:ring-offset-0"
                        rows={1}
                    />

                    <div className="flex items-center justify-between px-2 pb-1 pt-1">
                        <div className="flex items-center gap-1">
                            <Button variant="ghost" size="icon" className="h-9 w-9 rounded-full text-muted-foreground hover:bg-surface-container hover:text-foreground">
                                <Paperclip className="h-5 w-5" />
                            </Button>
                             <Button variant="ghost" size="icon" className="h-9 w-9 rounded-full text-muted-foreground hover:bg-surface-container hover:text-foreground">
                                <Mic className="h-5 w-5" />
                            </Button>
                        </div>

                        <Button
                            size="icon"
                            variant={message.trim() ? "default" : "ghost"}
                            className={`h-10 w-10 rounded-full transition-all duration-200 ${
                                message.trim()
                                ? "bg-primary text-primary-foreground shadow-md hover:bg-primary/90"
                                : "text-muted-foreground hover:bg-surface-container"
                            }`}
                            onClick={() => handleSubmit()}
                            disabled={!message.trim() || isSubmitting}
                        >
                            <SendHorizonal className="h-5 w-5 ml-0.5" />
                        </Button>
                    </div>
                </div>
            </div>

            <div className="text-[11px] text-muted-foreground text-center font-medium">
                SWE Agent can make mistakes. Please review code before executing. • Status: <span className={`font-mono ${status === 'CODING' ? 'text-primary animate-pulse' : ''}`}>{status}</span>
            </div>
        </div>
    )
}
