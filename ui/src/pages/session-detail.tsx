import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { agentApi, type SessionStatus } from '@/api/agent';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Loader2, XCircle, Clock, Target, GitBranch, ArrowLeft, MoreHorizontal } from 'lucide-react';
import { toast } from 'sonner';
import { SessionThread } from '@/components/session/SessionThread';
import { SessionInput } from '@/components/session/SessionInput';
import { Button } from '@/components/ui/button';

export default function SessionDetailPage() {
    const { sessionId } = useParams<{ sessionId: string }>();
    const navigate = useNavigate();
    const [session, setSession] = useState<SessionStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const fetchSession = async () => {
        if (!sessionId) return;
        try {
            const response = await agentApi.getSessionStatus(sessionId);
            setSession(response);
            setLoading(false);
        } catch (error) {
            console.error('Failed to fetch session:', error);
            // toast.error('Failed to load session details');
        }
    };

    useEffect(() => {
        fetchSession();
        // Poll more frequently for "Live" feel
        const interval = setInterval(fetchSession, 2000);
        return () => clearInterval(interval);
    }, [sessionId]);

    const handleApprove = async () => {
        if (!sessionId) return;
        setIsSubmitting(true);
        try {
            await agentApi.approveSession(sessionId);
            toast.success('Session resumed');
            fetchSession();
        } catch (error) {
            toast.error('Failed to approve session');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleSendInput = async (message: string) => {
        if (!sessionId) return;
        setIsSubmitting(true);
        try {
            await agentApi.addInput(sessionId, message);
            toast.success('Input sent');
            fetchSession();
        } catch (error) {
            toast.error('Failed to send input');
        } finally {
            setIsSubmitting(false);
        }
    };

    if (loading && !session) {
        return (
            <div className="flex flex-col items-center justify-center h-screen gap-2">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <p className="text-muted-foreground text-sm animate-pulse">Initializing session view...</p>
            </div>
        );
    }

    if (!session) {
        return (
            <div className="flex flex-col items-center justify-center h-screen space-y-4">
                <div className="h-12 w-12 rounded-full bg-destructive/10 flex items-center justify-center">
                    <XCircle className="h-6 w-6 text-destructive" />
                </div>
                <h2 className="text-xl font-semibold">Session not found</h2>
                <Button variant="outline" onClick={() => navigate('/sessions')}>Go Back</Button>
            </div>
        );
    }

    const state = session.state || {};
    const status = session.status || 'UNKNOWN';

    // Status Indicator Logic
    const getStatusColor = (s: string) => {
        switch (s) {
            case 'COMPLETED': return 'text-green-500 bg-green-500/10 border-green-500/20';
            case 'FAILED': return 'text-destructive bg-destructive/10 border-destructive/20';
            case 'WAITING_FOR_USER': return 'text-amber-500 bg-amber-500/10 border-amber-500/20';
            case 'CODING': return 'text-blue-500 bg-blue-500/10 border-blue-500/20';
            default: return 'text-muted-foreground bg-muted/10 border-muted/20';
        }
    };

    return (
        <div className="flex h-screen bg-background overflow-hidden">
            {/* LEFT: Main Thread */}
            <div className="flex-1 flex flex-col relative min-w-0">
                {/* Header */}
                <header className="h-14 border-b flex items-center justify-between px-6 bg-background/50 backdrop-blur shrink-0">
                    <div className="flex items-center gap-4">
                        <Button variant="ghost" size="icon" className="-ml-2 h-8 w-8 text-muted-foreground" onClick={() => navigate('/')}>
                            <ArrowLeft className="h-4 w-4" />
                        </Button>
                        <div className="flex flex-col">
                            <h1 className="text-sm font-semibold flex items-center gap-2">
                                {session.title || `Session ${session.session_id || session.id}`}
                                <Badge variant="outline" className={`h-5 px-1.5 text-[10px] uppercase border font-mono tracking-wider ${getStatusColor(status)}`}>
                                    {status}
                                </Badge>
                            </h1>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        {/* Future actions */}
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                            <MoreHorizontal className="h-4 w-4" />
                        </Button>
                    </div>
                </header>

                {/* Thread Area */}
                <div className="flex-1 overflow-hidden p-0 relative pb-[100px]"> {/* Padding for sticky input */}
                    <SessionThread logs={session.logs} isLoading={status === 'QUEUED' || !session.logs?.length} />
                </div>

                {/* Sticky Input */}
                <SessionInput
                    status={status}
                    isSubmitting={isSubmitting}
                    onApprove={handleApprove}
                    onSend={handleSendInput}
                />
            </div>

            {/* RIGHT: Context Sidebar */}
            <div className="w-[350px] border-l bg-muted/5 flex flex-col shrink-0 hidden lg:flex">
                <ScrollArea className="h-full">
                    <div className="p-6 space-y-8">
                        {/* Goal Section */}
                        <div className="space-y-3">
                            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-widest flex items-center gap-2">
                                <Target className="h-3 w-3" /> Goal
                            </h3>
                            <div className="bg-card border rounded-lg p-4 shadow-sm text-sm leading-relaxed text-card-foreground">
                                {state.goal || session.title || 'No goal specified'}
                            </div>
                        </div>

                        <Separator />

                        {/* Repo Details */}
                        <div className="space-y-3">
                            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-widest flex items-center gap-2">
                                <GitBranch className="h-3 w-3" /> Context
                            </h3>
                            <Card className="shadow-sm">
                                <CardContent className="p-0">
                                    <div className="p-3 text-sm flex items-center gap-2 border-b">
                                        <span className="text-muted-foreground">Repo:</span>
                                        <span className="font-medium truncate" title={state.repo_url}>
                                            {session.repository?.full_name || state.repo_url || 'Unknown'}
                                        </span>
                                    </div>
                                    <div className="p-3 text-sm flex items-center gap-2">
                                        <span className="text-muted-foreground">Branch:</span>
                                        <span className="font-mono text-xs bg-muted px-1.5 py-0.5 rounded">
                                            {state.base_branch || 'HEAD'}
                                        </span>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>

                        <Separator />

                        {/* Plan / Status */}
                        <div className="space-y-3">
                            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-widest flex items-center gap-2">
                                <Clock className="h-3 w-3" /> Current Plan
                            </h3>
                            {state.plan ? (
                                <div className="text-xs text-muted-foreground whitespace-pre-wrap leading-relaxed bg-black/5 dark:bg-white/5 p-4 rounded-lg font-mono border">
                                    {state.plan}
                                </div>
                            ) : (
                                <div className="text-xs italic text-muted-foreground text-center py-8 opacity-50 border border-dashed rounded-lg">
                                    Agent is planning...
                                </div>
                            )}
                        </div>
                    </div>
                </ScrollArea>
            </div>
        </div>
    );
}
