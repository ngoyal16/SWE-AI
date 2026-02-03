import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { gitProviderApi, type Repository } from '@/api/git-provider';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Search, Loader2 } from 'lucide-react';

interface RepoSelectorProps {
    value: string;
    onValueChange: (id: string, repo: Repository | null) => void;
}

export function RepoSelector({ value, onValueChange }: RepoSelectorProps) {
    const [repoSearch, setRepoSearch] = useState('');
    const [debouncedRepoSearch, setDebouncedRepoSearch] = useState('');
    const [repoPage, setRepoPage] = useState(1);
    const [allRepos, setAllRepos] = useState<Repository[]>([]);

    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedRepoSearch(repoSearch);
        }, 300);
        return () => clearTimeout(timer);
    }, [repoSearch]);

    // Reset page and local list when search changes
    useEffect(() => {
        setRepoPage(1);
    }, [debouncedRepoSearch]);

    const { data: repoResponse, isLoading } = useQuery({
        queryKey: ['user-repositories', debouncedRepoSearch, repoPage],
        queryFn: async () => {
            const resp = await gitProviderApi.getUserRepositories({
                q: debouncedRepoSearch,
                page: repoPage,
                per_page: 20
            });
            if (repoPage === 1) {
                setAllRepos(resp.data);
            } else {
                setAllRepos(prev => [...prev, ...resp.data]);
            }
            return resp;
        },
    });

    const handleSelect = (repoId: string) => {
        const repo = allRepos.find(r => r.id.toString() === repoId) || null;
        onValueChange(repoId, repo);
    };

    return (
        <Select
            value={value}
            onValueChange={handleSelect}
            disabled={isLoading && allRepos.length === 0}
        >
            <SelectTrigger className="w-full bg-background/50 border-border/40 hover:border-primary/50 transition-colors h-11">
                <SelectValue placeholder={isLoading && allRepos.length === 0 ? "Loading repositories..." : "Select a repository"} />
            </SelectTrigger>
            <SelectContent className="w-[var(--radix-select-trigger-width)] max-h-[400px]">
                <div className="p-2 sticky top-0 bg-popover z-10 border-b">
                    <div className="relative">
                        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Search repositories..."
                            className="pl-9 h-9 border-none bg-muted/50 focus-visible:ring-0"
                            value={repoSearch}
                            onChange={(e) => setRepoSearch(e.target.value)}
                            onKeyDown={(e) => e.stopPropagation()}
                        />
                    </div>
                </div>
                <div className="overflow-y-auto">
                    {allRepos.map((repo: Repository) => (
                        <SelectItem key={repo.id} value={repo.id.toString()} className="cursor-pointer py-3">
                            <div className="flex flex-col gap-0.5">
                                <div className="flex items-center gap-2">
                                    <span className="font-semibold text-sm">{repo.full_name}</span>
                                    {repo.provider && (
                                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground font-medium">
                                            {repo.provider.display_name}
                                        </span>
                                    )}
                                </div>
                                <span className="text-[10px] text-muted-foreground opacity-70">
                                    {repo.language || 'Plain Text'} • {repo.stars} stars
                                </span>
                            </div>
                        </SelectItem>
                    ))}
                    {allRepos.length === 0 && !isLoading && (
                        <div className="p-8 text-center text-sm text-muted-foreground italic">
                            No repositories found
                        </div>
                    )}
                    {repoResponse?.meta && allRepos.length < repoResponse.meta.total && (
                        <div className="p-2 border-t">
                            <Button
                                variant="ghost"
                                size="sm"
                                className="w-full text-xs font-medium text-primary hover:bg-primary/5"
                                onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    setRepoPage(prev => prev + 1);
                                }}
                                disabled={isLoading}
                            >
                                {isLoading ? (
                                    <Loader2 className="h-3 w-3 animate-spin mr-2" />
                                ) : (
                                    <PlusIcon className="h-3 w-3 mr-2" />
                                )}
                                Load More ({allRepos.length} of {repoResponse.meta.total})
                            </Button>
                        </div>
                    )}
                </div>
            </SelectContent>
        </Select>
    );
}

function PlusIcon(props: any) {
    return (
        <svg
            {...props}
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <path d="M5 12h14" />
            <path d="M12 5v14" />
        </svg>
    );
}
