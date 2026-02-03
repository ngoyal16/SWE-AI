import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { agentApi } from '@/api/agent';
import { useAIProfile } from '@/context/ai-profile-context';
import { type Repository } from '@/api/git-provider';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { Loader2, ArrowRight, Sparkles, ShieldCheck, Zap, GitBranch } from 'lucide-react';
import { RepoSelectorTrigger } from '@/components/chat/RepoSelectorTrigger';
import { Switch } from "@/components/ui/switch"
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { Textarea } from '@/components/ui/textarea'

export default function NewSessionPage() {
    const navigate = useNavigate();
    const [selectedRepoId, setSelectedRepoId] = useState<string>('');
    const [selectedRepo, setSelectedRepo] = useState<Repository | null>(null);
    const [goal, setGoal] = useState('');
    const [baseBranch, setBaseBranch] = useState('');
    const { selectedProfileId } = useAIProfile();

    const createSessionMutation = useMutation({
        mutationFn: agentApi.createSession,
        onSuccess: (resp) => {
            toast.success('Session started successfully!');
            navigate(`/session/${resp.session_id}`);
        },
        onError: (error: any) => {
            const message = error.response?.data?.error || 'Failed to start session';
            toast.error(message);
        },
    });

    const handleSubmit = () => {
        if (!selectedRepo) {
            toast.error('Please select a repository first');
            return;
        }

        if (!goal.trim()) {
            toast.error('Please describe your goal');
            return;
        }

        createSessionMutation.mutate({
            goal,
            repo_url: selectedRepo.clone_url,
            repository_id: selectedRepo.id,
            base_branch: baseBranch || selectedRepo.default_branch,
            mode: 'auto',
            ai_profile_id: parseInt(selectedProfileId),
        });
    };

    return (
        <div className="flex flex-col h-full items-center justify-center p-4 md:p-8 max-w-5xl mx-auto w-full animate-in fade-in duration-500 bg-background text-foreground transition-colors">
            {/* Top Bar / Repo Selector */}
            <div className="w-full flex justify-center mb-8">
                <RepoSelectorTrigger
                    value={selectedRepoId}
                    onValueChange={(id, repo) => {
                        setSelectedRepoId(id);
                        setSelectedRepo(repo);
                        setBaseBranch(repo?.default_branch || '');
                    }}
                />
            </div>

            {/* Chat Input Area */}
            <div className="w-full max-w-3xl bg-zinc-100 dark:bg-zinc-900 border border-border rounded-3xl p-4 md:p-6 shadow-xl backdrop-blur-sm relative overflow-hidden group transition-colors">
                <div className="relative z-10">
                    <Textarea
                        placeholder="Ask SWE Agent to work on a session..."
                        className="w-full bg-transparent border-none resize-none text-lg md:text-xl placeholder:text-muted-foreground text-foreground focus-visible:ring-0 min-h-[120px] p-0 leading-relaxed font-light"
                        value={goal}
                        onChange={(e) => setGoal(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSubmit();
                            }
                        }}
                    />

                    <div className="flex items-center justify-between mt-6 pt-2">
                        <div className="flex items-center gap-2">
                            <div className="flex items-center h-8 rounded-full bg-background dark:bg-black/40 border border-border px-3 gap-2">
                                <GitBranch className="h-3.5 w-3.5 text-muted-foreground" />
                                <input
                                    type="text"
                                    value={baseBranch}
                                    onChange={(e) => setBaseBranch(e.target.value)}
                                    placeholder={selectedRepo?.default_branch || 'main'}
                                    className="bg-transparent border-none outline-none text-xs font-medium text-foreground w-24 placeholder:text-muted-foreground"
                                />
                            </div>
                        </div>

                        <div className="flex items-center gap-2">
                            <Button
                                variant="ghost"
                                size="sm"
                                className="h-9 px-3 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted"
                            >
                                <Sparkles className="h-4 w-4 mr-2" />
                                <span className="text-sm">Review</span>
                            </Button>
                            <Button
                                size="icon"
                                className={cn(
                                    "h-9 w-9 rounded-lg transition-all duration-300",
                                    goal.trim() ? "bg-primary text-primary-foreground shadow-sm" : "bg-muted text-muted-foreground cursor-not-allowed"
                                )}
                                disabled={!goal.trim() || createSessionMutation.isPending}
                                onClick={handleSubmit}
                            >
                                {createSessionMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />}
                            </Button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Footer Options */}
            <div className="w-full max-w-3xl mt-10 space-y-4 animate-in slide-in-from-bottom-5 duration-700 delay-100">
                <div className="text-sm text-zinc-500 font-medium ml-1">Continuously improve your codebase</div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl border border-border bg-muted/30 hover:bg-muted/50 transition-colors flex items-start gap-4 cursor-pointer group">
                        <div className="mt-1 p-1.5 rounded-lg bg-yellow-500/10 text-yellow-600 dark:text-yellow-500 group-hover:bg-yellow-500/20 transition-colors">
                            <Zap className="h-4 w-4" />
                        </div>
                        <div className="flex-1 space-y-1">
                            <div className="flex items-center justify-between">
                                <div className="font-medium text-foreground">Enable proactive suggestions</div>
                                <Switch id="proactive" className="scale-75 data-[state=checked]:bg-yellow-600" />
                            </div>
                            <div className="text-xs text-muted-foreground leading-relaxed">
                                Automatically find issues in your codebase. You decide which tasks to start. Expect new suggestions every few days.
                            </div>
                            <div className="pt-2">
                                <Badge variant="outline" className="text-[10px] py-0 h-5 border-border text-muted-foreground bg-muted/50">1 / 5 repo max</Badge>
                            </div>
                        </div>
                    </div>

                    <div className="p-4 rounded-xl border border-border bg-muted/30 hover:bg-muted/50 transition-colors flex items-center justify-between gap-4 cursor-pointer group h-full">
                        <div className="flex items-center gap-4">
                            <div className="p-1.5 rounded-lg bg-purple-500/10 text-purple-600 dark:text-purple-500 group-hover:bg-purple-500/20 transition-colors">
                                <ShieldCheck className="h-4 w-4" />
                            </div>
                            <div className="font-medium text-foreground text-sm">Schedule skill-based agents</div>
                        </div>
                        <div className="flex gap-2">
                            <Badge variant="secondary" className="bg-muted text-muted-foreground hover:bg-background cursor-pointer">Performance</Badge>
                            <Badge variant="secondary" className="bg-muted text-muted-foreground hover:bg-background cursor-pointer">Security</Badge>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
