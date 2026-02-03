import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
    GitBranch,
    CheckCircle2,
    XCircle,
    Loader2,
    Clock,
    MessageSquare,
    ArrowRight
} from 'lucide-react';
import { type SessionStatus } from '@/api/agent';
import { formatDistanceToNow } from 'date-fns';
import { cn } from '@/lib/utils';

interface SessionCardProps {
    session: SessionStatus;
}

export function SessionCard({ session }: SessionCardProps) {
    const navigate = useNavigate();

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'COMPLETED': return <CheckCircle2 className="h-4 w-4 text-green-500" />;
            case 'FAILED': return <XCircle className="h-4 w-4 text-destructive" />;
            case 'WAITING_FOR_USER': return <MessageSquare className="h-4 w-4 text-amber-500" />;
            case 'QUEUED': return <Clock className="h-4 w-4 text-muted-foreground" />;
            default: return <Loader2 className="h-4 w-4 animate-spin text-primary" />;
        }
    };

    const getStatusStyles = (status: string) => {
        switch (status) {
            case 'COMPLETED':
                return 'bg-green-100 dark:bg-green-950/50 text-green-700 dark:text-green-300 border-green-200 dark:border-green-900/50';
            case 'FAILED':
                return 'bg-red-100 dark:bg-red-950/50 text-red-700 dark:text-red-300 border-red-200 dark:border-red-900/50';
            case 'WAITING_FOR_USER':
                return 'bg-amber-100 dark:bg-amber-950/50 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-900/50';
            default:
                return 'bg-blue-100 dark:bg-blue-950/50 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-900/50';
        }
    };

    const lastActivity = session.updated_at
        ? formatDistanceToNow(new Date(session.updated_at), { addSuffix: true })
        : 'Unknown';

    return (
        <Card
            className="group hover:shadow-lg transition-all duration-300 border-border/40 bg-card/50 backdrop-blur-sm cursor-pointer overflow-hidden"
            onClick={() => navigate(`/session/${session.id}`)}
        >
            <CardHeader className="pb-3">
                <div className="flex justify-between items-start gap-4">
                    <div className="space-y-1 flex-1 min-w-0">
                        <CardTitle className="text-base font-semibold group-hover:text-primary transition-colors line-clamp-2 leading-tight">
                            {session.title || `Session #${session.id}`}
                        </CardTitle>
                        {session.repository && (
                            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                                <GitBranch className="h-3 w-3" />
                                <span className="truncate">{session.repository.full_name}</span>
                            </div>
                        )}
                    </div>
                    <Badge
                        variant="outline"
                        className={cn("px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider", getStatusStyles(session.status))}>
                        <div className="flex items-center gap-1.2">
                            {getStatusIcon(session.status)}
                            {session.status}
                        </div>
                    </Badge>
                </div>
            </CardHeader>
            <CardContent>
                <div className="flex items-center justify-between text-xs pt-2">
                    <div className="flex items-center gap-2 text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        <span>{lastActivity}</span>
                    </div>
                    <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                        <ArrowRight className="h-4 w-4" />
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
}
