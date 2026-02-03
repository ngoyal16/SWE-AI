import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { agentApi, type SessionStatus } from '@/api/agent';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Loader2, XCircle, Clock, Target, GitBranch, ArrowLeft, MoreHorizontal, Sparkles } from 'lucide-react';
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
        } catch {
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
        } catch {
            toast.error('Failed to send input');
        } finally {
            setIsSubmitting(false);
        }
    };

    if (loading && !session) {
        return (
            <div className="flex flex-col items-center justify-center h-[calc(100vh-100px)] gap-4">
                <div className="relative">
                    <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full animate-pulse"></div>
                    <Loader2 className="h-10 w-10 animate-spin text-primary relative z-10" />
                </div>
                <p className="text-muted-foreground text-sm font-medium animate-pulse">Loading session...</p>
            </div>
        );
    }

    if (!session) {
        return (
            <div className="flex flex-col items-center justify-center h-[calc(100vh-100px)] space-y-6">
                <div className="h-20 w-20 rounded-full bg-destructive/10 flex items-center justify-center">
                    <XCircle className="h-10 w-10 text-destructive" />
                </div>
                <div className="text-center">
                    <h2 className="text-2xl font-semibold">Session not found</h2>
                    <p className="text-muted-foreground mt-2">The session you are looking for does not exist or has been deleted.</p>
                </div>
                <Button variant="outline" className="rounded-full px-6" onClick={() => navigate('/sessions')}>Go Back</Button>
            </div>
        );
    }

    const state = session.state || {};
    const status = session.status || 'UNKNOWN';

    // Status Indicator Logic
    const getStatusColor = (s: string) => {
        switch (s) {
            case 'COMPLETED': return 'bg-green-500/15 text-green-700 dark:text-green-400 border-green-500/20';
            case 'FAILED': return 'bg-red-500/15 text-red-700 dark:text-red-400 border-red-500/20';
            case 'WAITING_FOR_USER': return 'bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-500/20';
            case 'CODING': return 'bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-500/20';
            default: return 'bg-muted text-muted-foreground border-border';
        }
    };

    return (
        <div className="flex h-[calc(100vh-100px)] gap-6 overflow-hidden">
            {/* LEFT: Main Thread */}
            <div className="flex-1 flex flex-col relative min-w-0 bg-surface-container rounded-3xl overflow-hidden shadow-sm border border-border/50">
                {/* Header */}
                <header className="h-16 flex items-center justify-between px-6 border-b border-border/40 bg-card/50 backdrop-blur-sm shrink-0 z-10">
                    <div className="flex items-center gap-4 min-w-0">
                        <Button
                            variant="ghost"
                            size="icon"
                            className="rounded-full h-10 w-10 -ml-2 text-muted-foreground hover:bg-muted"
                            onClick={() => navigate('/')}
                        >
                            <ArrowLeft className="h-5 w-5" />
                        </Button>
                        <div className="flex flex-col min-w-0">
                            <h1 className="text-lg font-semibold truncate flex items-center gap-3">
                                <span className="truncate">{session.title || `Session ${session.session_id || session.id}`}</span>
                            </h1>
                        </div>
                         <Badge variant="outline" className={`ml-2 h-6 px-2.5 text-xs font-medium rounded-md uppercase tracking-wider border-0 ${getStatusColor(status)}`}>
                            {status}
                        </Badge>
                    </div>
                    <div className="flex items-center gap-2">
                        {/* Future actions */}
                        <Button variant="ghost" size="icon" className="rounded-full h-10 w-10">
                            <MoreHorizontal className="h-5 w-5" />
                        </Button>
                    </div>
                </header>

                {/* Thread Area */}
                <div className="flex-1 overflow-hidden p-0 relative">
                    <SessionThread logs={session.logs} isLoading={status === 'QUEUED' || !session.logs?.length} />
                </div>

                {/* Sticky Input */}
                <div className="p-4 bg-card/80 backdrop-blur border-t border-border/40">
                    <SessionInput
                        status={status}
                        isSubmitting={isSubmitting}
                        onApprove={handleApprove}
                        onSend={handleSendInput}
                    />
                </div>
            </div>

            {/* RIGHT: Context Sidebar */}
            <div className="w-[360px] flex flex-col gap-4 shrink-0 hidden xl:flex">
                 {/* Repo Details Card */}
                <Card className="border-none shadow-sm bg-surface-container-low rounded-3xl overflow-hidden">
                    <CardHeader className="pb-3 pt-5 px-6">
                        <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-widest flex items-center gap-2">
                            <GitBranch className="h-4 w-4" /> Context
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="px-0 pb-0">
                         <div className="px-6 py-3 text-sm flex items-center gap-3 border-b border-border/40 hover:bg-surface-container transition-colors cursor-default">
                            <div className="h-8 w-8 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-500">
                                <GitBranch className="h-4 w-4" />
                            </div>
                            <div className="flex flex-col min-w-0">
                                <span className="text-xs text-muted-foreground">Repository</span>
                                <span className="font-medium truncate" title={state.repo_url}>
                                    {session.repository?.full_name || state.repo_url || 'Unknown'}
                                </span>
                            </div>
                        </div>
                        <div className="px-6 py-3 text-sm flex items-center gap-3 hover:bg-surface-container transition-colors cursor-default">
                            <div className="h-8 w-8 rounded-full bg-purple-500/10 flex items-center justify-center text-purple-500">
                                <Target className="h-4 w-4" />
                            </div>
                            <div className="flex flex-col min-w-0">
                                <span className="text-xs text-muted-foreground">Branch</span>
                                <span className="font-medium font-mono text-xs">
                                    {state.base_branch || 'HEAD'}
                                </span>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                 {/* Goal Card */}
                <Card className="border-none shadow-sm bg-surface-container-low rounded-3xl overflow-hidden flex-1 flex flex-col min-h-0">
                    <CardHeader className="pb-3 pt-5 px-6">
                        <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-widest flex items-center gap-2">
                            <Sparkles className="h-4 w-4" /> Goal
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="px-6 pb-6 overflow-y-auto">
                         <p className="text-sm leading-relaxed text-foreground/90">
                            {state.goal || session.title || 'No goal specified'}
                        </p>
                    </CardContent>
                </Card>

                {/* Plan Card */}
                <Card className="border-none shadow-sm bg-surface-container-low rounded-3xl overflow-hidden flex-[2] flex flex-col min-h-0">
                    <CardHeader className="pb-3 pt-5 px-6 bg-surface-container-low sticky top-0 z-10">
                        <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-widest flex items-center gap-2">
                            <Clock className="h-4 w-4" /> Plan
                        </CardTitle>
                    </CardHeader>
                    <ScrollArea className="flex-1">
                        <CardContent className="px-6 pb-6 pt-0">
                            {state.plan ? (
                                <div className="text-sm text-foreground/80 whitespace-pre-wrap leading-relaxed font-mono bg-surface-container p-4 rounded-xl border border-border/40">
                                    {state.plan}
                                </div>
                            ) : (
                                <div className="flex flex-col items-center justify-center py-12 text-center opacity-50 space-y-3">
                                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                                    <p className="text-xs italic text-muted-foreground">Formulating plan...</p>
                                </div>
                            )}
                        </CardContent>
                    </ScrollArea>
                </Card>
            </div>
        </div>
    );
}
