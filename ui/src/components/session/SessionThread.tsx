import { useEffect, useRef, useState } from "react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Loader2, Copy, Bot, ArrowDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"

interface SessionThreadProps {
    logs: string[]
    isLoading?: boolean
}

export function SessionThread({ logs, isLoading }: SessionThreadProps) {
    const scrollRef = useRef<HTMLDivElement>(null)
    const [shouldAutoScroll, setShouldAutoScroll] = useState(true)
    const [isAtBottom, setIsAtBottom] = useState(true)

    const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
        const { scrollTop, scrollHeight, clientHeight } = e.currentTarget
        const atBottom = scrollHeight - scrollTop - clientHeight < 100
        setShouldAutoScroll(atBottom)
        setIsAtBottom(atBottom)
    }

    useEffect(() => {
        if (shouldAutoScroll && scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: "smooth" })
        }
    }, [logs, shouldAutoScroll])

    const scrollToBottom = () => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: "smooth" })
            setShouldAutoScroll(true)
        }
    }

    const copyLogs = () => {
        if (!logs.length) return
        navigator.clipboard.writeText(logs.join("\n"))
        toast.success("Logs copied to clipboard")
    }

    return (
        <div className="flex flex-col h-full bg-card/50 relative group">
            <div className="absolute top-4 right-6 z-20 opacity-0 group-hover:opacity-100 transition-opacity flex gap-2">
                {!isAtBottom && (
                    <Button variant="outline" size="sm" className="h-8 gap-2 bg-background/80 backdrop-blur rounded-full" onClick={scrollToBottom}>
                        <ArrowDown className="h-3.5 w-3.5" />
                        <span className="text-xs">Scroll to Bottom</span>
                    </Button>
                )}
                <Button variant="outline" size="sm" className="h-8 gap-2 bg-background/80 backdrop-blur rounded-full" onClick={copyLogs}>
                    <Copy className="h-3.5 w-3.5" />
                    <span className="text-xs">Copy Logs</span>
                </Button>
            </div>

            <ScrollArea className="flex-1 w-full px-4 sm:px-6 md:px-8" onScroll={handleScroll}>
                <div className="py-8 space-y-6 min-h-full max-w-4xl mx-auto">
                    {logs && logs.length > 0 ? (
                        <>
                            {logs.map((log, i) => (
                                <div key={i} className="group/message flex gap-4 md:gap-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
                                    <Avatar className="h-8 w-8 md:h-10 md:w-10 mt-1 border border-border/50 shrink-0">
                                        <AvatarFallback className="bg-primary/10 text-primary">
                                            <Bot className="h-4 w-4 md:h-5 md:w-5" />
                                        </AvatarFallback>
                                    </Avatar>

                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="font-semibold text-sm">SWE AI Agent</span>
                                            <span className="text-[10px] text-muted-foreground uppercase tracking-widest opacity-0 group-hover/message:opacity-100 transition-opacity">
                                                {new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                                            </span>
                                        </div>
                                        <div className="bg-surface-container-low/50 rounded-2xl rounded-tl-none p-4 md:p-5 text-sm md:text-base leading-relaxed text-foreground/90 font-mono shadow-sm border border-border/30 whitespace-pre-wrap break-all">
                                            {log}
                                        </div>
                                    </div>
                                </div>
                            ))}
                            <div ref={scrollRef} className="pb-4" />
                        </>
                    ) : (
                        <div className="flex flex-col items-center justify-center h-[400px] text-muted-foreground/50 gap-6">
                            {isLoading ? (
                                <div className="flex flex-col items-center gap-4">
                                    <div className="relative">
                                        <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full animate-pulse"></div>
                                        <Loader2 className="h-12 w-12 animate-spin text-primary relative z-10" />
                                    </div>
                                    <p className="text-sm font-medium animate-pulse">Connecting to agent stream...</p>
                                </div>
                            ) : (
                                <div className="text-center space-y-2">
                                    <Bot className="h-16 w-16 mx-auto opacity-20" />
                                    <p className="text-lg font-medium">No activity yet</p>
                                    <p className="text-sm">Start a task to see SWE AI Agent in action.</p>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </ScrollArea>
        </div>
    )
}
