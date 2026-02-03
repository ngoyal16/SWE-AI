import { useNavigate, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { agentApi } from "@/api/agent";
import { cn } from "@/lib/utils";
import { Loader2, MessageSquare, Plus, Archive } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { formatDistanceToNow } from "date-fns";

export function SidebarSessionList() {
    const navigate = useNavigate();
    const location = useLocation();

    const { data: sessionsResponse, isLoading } = useQuery({
        queryKey: ['recent-sessions'],
        queryFn: () => agentApi.listSessions({ page: 1, per_page: 20 }),
        refetchInterval: 30000,
    });

    const sessions = sessionsResponse?.data || [];

    return (
        <div className="flex flex-col h-full gap-2">
            <div className="px-3 py-2">
                <Button
                    variant="outline"
                    className="w-full justify-start gap-2 bg-background/50 border-dashed hover:bg-background hover:border-solid hover:border-primary/50 transition-all font-normal text-muted-foreground hover:text-foreground"
                    onClick={() => navigate('/')}
                >
                    <Plus className="h-4 w-4" />
                    New Session
                </Button>
            </div>

            <div className="px-4 pb-1 pt-2">
                <h3 className="text-xs font-semibold text-muted-foreground/60 uppercase tracking-wider">Recent Sessions</h3>
            </div>

            <ScrollArea className="flex-1 px-3">
                {isLoading ? (
                    <div className="flex flex-col items-center justify-center p-4 gap-2 opacity-50">
                        <Loader2 className="h-4 w-4 animate-spin" />
                    </div>
                ) : (
                    <div className="space-y-1 pb-4">
                        {sessions.length === 0 ? (
                            <div className="text-center p-4 text-xs text-muted-foreground italic">
                                No recent sessions
                            </div>
                        ) : (
                            sessions.map((session) => (
                                <button
                                    key={session.id}
                                    onClick={() => navigate(`/session/${session.session_id || session.id}`)}
                                    className={cn(
                                        "w-full text-left flex flex-col gap-0.5 rounded-lg px-3 py-2.5 transition-all duration-200 group relative overflow-hidden",
                                        location.pathname === `/session/${session.session_id || session.id}`
                                            ? "bg-accent text-accent-foreground shadow-sm"
                                            : "hover:bg-muted/50 text-muted-foreground hover:text-foreground"
                                    )}
                                >
                                    {/* Active Indicator */}
                                    {location.pathname === `/session/${session.session_id || session.id}` && (
                                        <div className="absolute left-0 top-1/2 -translate-y-1/2 h-6 w-1 bg-primary rounded-r-full" />
                                    )}

                                    <div className="flex items-center justify-between w-full">
                                        <span className="text-sm font-medium leading-none truncate pr-2">
                                            {session.title || `Session #${session.session_id || session.id}`}
                                        </span>
                                        {['CODING', 'PLANNING', 'REVIEWING'].includes(session.status) && (
                                            <span className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse shrink-0" />
                                        )}
                                    </div>
                                    <div className="flex items-center gap-1.5 text-[10px] opacity-70">
                                        <MessageSquare className="h-3 w-3" />
                                        <span className="truncate max-w-[120px]">
                                            {sessionStateToText(session)}
                                        </span>
                                        <span className="text-[9px] ml-auto">
                                            {formatDistanceToNow(new Date(session.updated_at || new Date()), { addSuffix: false }).replace('about ', '')}
                                        </span>
                                    </div>
                                </button>
                            ))
                        )}
                        <Button
                            variant="ghost"
                            size="sm"
                            className="w-full text-xs text-muted-foreground hover:text-primary justify-start gap-2 h-8 mt-2"
                            onClick={() => navigate('/sessions')}
                        >
                            <Archive className="h-3 w-3" />
                            View All Sessions
                        </Button>
                    </div>
                )}
            </ScrollArea>
        </div>
    );
}

function sessionStateToText(session: any) {
    if (session.status === 'WAITING_FOR_USER') return 'Waiting for you';
    if (session.status === 'COMPLETED') return 'Completed';
    if (session.status === 'FAILED') return 'Failed';
    return session.status; // Default
}
