import { useEffect, useRef } from "react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Loader2, Copy } from "lucide-react"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"
// import { cn } from "@/lib/utils"

interface SessionThreadProps {
    logs: string[]
    isLoading?: boolean
}

export function SessionThread({ logs, isLoading }: SessionThreadProps) {
    const scrollRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: "smooth" })
        }
    }, [logs])

    const copyLogs = () => {
        if (!logs.length) return
        navigator.clipboard.writeText(logs.join("\n"))
        toast.success("Logs copied to clipboard")
    }

    return (
        <div className="flex flex-col h-full bg-black/40 backdrop-blur rounded-lg border border-white/5 overflow-hidden relative group">
            <div className="absolute top-2 right-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity">
                <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-foreground" onClick={copyLogs}>
                    <Copy className="h-3 w-3" />
                </Button>
            </div>

            <ScrollArea className="flex-1 w-full">
                <div className="p-6 font-mono text-xs space-y-1.5 min-h-full">
                    {logs && logs.length > 0 ? (
                        <>
                            {logs.map((log, i) => (
                                <div key={i} className="flex gap-4 -mx-6 px-6 py-0.5 hover:bg-white/5 transition-colors">
                                    <span className="text-muted-foreground/30 select-none w-8 text-right shrink-0">{i + 1}</span>
                                    <span className="text-zinc-300 break-words flex-1 whitespace-pre-wrap leading-relaxed">
                                        {log}
                                    </span>
                                </div>
                            ))}
                            <div ref={scrollRef} className="pb-4" />
                        </>
                    ) : (
                        <div className="flex flex-col items-center justify-center h-[400px] text-muted-foreground/50 gap-3">
                            {isLoading ? (
                                <>
                                    <Loader2 className="h-6 w-6 animate-spin" />
                                    <p>Connecting to agent stream...</p>
                                </>
                            ) : (
                                <p>No logs available yet.</p>
                            )}
                        </div>
                    )}
                </div>
            </ScrollArea>

            {/* Live Indicator */}
            <div className="absolute bottom-2 right-4 flex items-center gap-1.5 pointer-events-none">
                <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                </span>
                <span className="text-[9px] font-mono text-muted-foreground/60 uppercase tracking-widest">Live</span>
            </div>
        </div>
    )
}
