import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Play, SendHorizonal } from "lucide-react"

interface SessionInputProps {
    status: string
    isSubmitting: boolean
    onApprove: () => void
    onSend: (message: string) => void
}

export function SessionInput({ status, isSubmitting, onApprove, onSend }: SessionInputProps) {
    const [message, setMessage] = useState("")

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

    const needsApproval = status === 'WAITING_FOR_USER'

    return (
        <div className="bg-background/80 backdrop-blur-md border-t p-4 pb-6 absolute bottom-0 left-0 right-0 z-20">
            <div className="max-w-4xl mx-auto flex flex-col gap-3">
                {needsApproval && (
                    <div className="flex items-center justify-between bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 animate-in slide-in-from-bottom-2">
                        <div className="flex items-center gap-2 text-sm text-amber-500">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
                            </span>
                            Agent is waiting for your approval to proceed.
                        </div>
                        <Button
                            size="sm"
                            onClick={onApprove}
                            disabled={isSubmitting}
                            className="bg-amber-500 hover:bg-amber-600 text-white border-none shadow-sm"
                        >
                            <Play className="h-3.5 w-3.5 mr-1.5" />
                            Approve
                        </Button>
                    </div>
                )}

                <div className="relative">
                    <Textarea
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={needsApproval ? "Or provide feedback to guide the agent..." : "Send a message to the agent..."}
                        className="min-h-[50px] max-h-[200px] resize-none pr-12 bg-zinc-900/50 border-white/10 focus-visible:ring-primary/20"
                    />
                    <Button
                        size="icon"
                        variant="ghost"
                        className="absolute right-2 bottom-2 h-8 w-8 text-primary hover:bg-primary/10"
                        onClick={() => handleSubmit()}
                        disabled={!message.trim() || isSubmitting}
                    >
                        <SendHorizonal className="h-4 w-4" />
                    </Button>
                </div>
                <div className="text-[10px] text-muted-foreground text-center">
                    Agent processes inputs sequentially. Status: <span className="font-mono text-primary">{status}</span>
                </div>
            </div>
        </div>
    )
}
