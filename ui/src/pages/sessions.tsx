import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { usePageHeader } from '@/context/page-header-context';
import { agentApi } from '@/api/agent';
import { SessionCard } from '@/components/sessions/SessionCard';
import { Button } from '@/components/ui/button';
import { Loader2, Plus, LayoutGrid } from 'lucide-react';

export default function SessionsPage() {
    usePageHeader('Sessions', 'View and manage your AI agent sessions');
    const navigate = useNavigate();

    const { data: sessionsResponse, isLoading } = useQuery({
        queryKey: ['sessions'],
        queryFn: () => agentApi.listSessions({ page: 1, per_page: 20 }),
        refetchInterval: 10000,
    });

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center py-24 space-y-4">
                <Loader2 className="h-10 w-10 animate-spin text-primary opacity-50" />
                <p className="text-muted-foreground animate-pulse">Loading your sessions...</p>
            </div>
        );
    }

    const sessions = sessionsResponse?.data || [];
    const runningSessions = sessions.filter(s => s.status === 'CODING' || s.status === 'PLANNING' || s.status === 'REVIEWING');
    const otherSessions = sessions.filter(s => !['CODING', 'PLANNING', 'REVIEWING'].includes(s.status));

    return (
        <div className="max-w-7xl mx-auto space-y-8 px-4">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-border/40 pb-6">
                <div className="space-y-1">
                    <h2 className="text-2xl font-bold tracking-tight">Your Activity</h2>
                    <p className="text-sm text-muted-foreground">Manage your ongoing and past AI agent tasks</p>
                </div>
                <Button onClick={() => navigate('/new-session')} className="shadow-lg shadow-primary/20">
                    <Plus className="mr-2 h-4 w-4" />
                    New Session
                </Button>
            </div>

            {sessions.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 text-center">
                    <div className="bg-primary/5 p-6 rounded-full mb-4">
                        <LayoutGrid className="h-12 w-12 text-primary/40" />
                    </div>
                    <h3 className="text-xl font-semibold">No sessions found</h3>
                    <p className="text-muted-foreground mt-2 max-w-xs mx-auto">
                        You haven't started any AI agent tasks yet. Start your first session to see it here!
                    </p>
                    <Button variant="outline" onClick={() => navigate('/new-session')} className="mt-6">
                        Start First Session
                    </Button>
                </div>
            ) : (
                <div className="space-y-12">
                    {runningSessions.length > 0 && (
                        <section className="space-y-4">
                            <h3 className="text-lg font-semibold flex items-center gap-2 px-1">
                                <Loader2 className="h-4 w-4 animate-spin text-primary" />
                                Recent & Running
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {runningSessions.map((session) => (
                                    <SessionCard key={session.id} session={session} />
                                ))}
                            </div>
                        </section>
                    )}

                    {otherSessions.length > 0 && (
                        <section className="space-y-4">
                            <h3 className="text-lg font-semibold px-1">History</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {otherSessions.map((session) => (
                                    <SessionCard key={session.id} session={session} />
                                ))}
                            </div>
                        </section>
                    )}
                </div>
            )}
        </div>
    );
}
