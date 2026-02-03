import { useState, useEffect } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { gitProviderApi, type Repository, type RepositoryResponse } from '@/api/git-provider';
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover"
import { Button } from '@/components/ui/button';
import { Check, ChevronsUpDown, GitBranch, Settings2, Loader2, Search } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Input } from '@/components/ui/input';

interface RepoSelectorTriggerProps {
    value: string;
    onValueChange: (id: string, repo: Repository | null) => void;
    repos?: Repository[];
}

export function RepoSelectorTrigger({ value, onValueChange }: RepoSelectorTriggerProps) {
    const [open, setOpen] = useState(false);
    const [repoSearch, setRepoSearch] = useState('');
    const [debouncedSearch, setDebouncedSearch] = useState('');

    // Debounce search
    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedSearch(repoSearch);
        }, 300);
        return () => clearTimeout(timer);
    }, [repoSearch]);

    const {
        data,
        fetchNextPage,
        hasNextPage,
        isFetching,
        isFetchingNextPage,
    } = useInfiniteQuery({
        queryKey: ['user-repositories-search', debouncedSearch],
        queryFn: ({ pageParam = 1 }) => gitProviderApi.getUserRepositories({
            q: debouncedSearch,
            page: pageParam as number,
            per_page: 20
        }),
        initialPageParam: 1,
        getNextPageParam: (lastPage: RepositoryResponse) => {
            const { page, per_page, total } = lastPage.meta;
            if (page * per_page < total) {
                return page + 1;
            }
            return undefined;
        },
        staleTime: 30000,
    });

    const repos = Array.from(
        new Map(
            (data?.pages.flatMap((page: RepositoryResponse) => page.data) || []).map(repo => [repo.id, repo])
        ).values()
    );
    // Find the selected repo in the current list, or use the value provided.
    // Note: If the repo is not in the loaded list, we might not have its name.
    // This is a limitation of not having a separate "fetch by id" or "initial repo" prop,
    // but typically the list starts with recent/relevant repos or the user searches for it.
    const selectedRepo = repos.find(r => r.id.toString() === value);

    const handleSelect = (repo: Repository) => {
        onValueChange(repo.id.toString(), repo);
        setOpen(false);
    }

    return (
        <div className="flex items-center gap-2">
            <Popover open={open} onOpenChange={setOpen}>
                <PopoverTrigger asChild>
                    <Button
                        variant="outline"
                        role="combobox"
                        aria-expanded={open}
                        className="w-[280px] justify-between bg-surface-container border-border/50 text-foreground hover:bg-surface-container-high hover:text-foreground rounded-xl h-10 shadow-sm transition-all"
                    >
                        {selectedRepo ? (
                            <span className="truncate flex items-center gap-2">
                                <GitBranch className="h-3.5 w-3.5 text-muted-foreground" />
                                {selectedRepo.full_name}
                            </span>
                        ) : (
                            <span className="text-muted-foreground">Select repository...</span>
                        )}
                        <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                    </Button>
                </PopoverTrigger>
                <PopoverContent className="w-[300px] p-0 bg-surface-container border-border/50 text-foreground shadow-xl rounded-xl overflow-hidden" align="start">
                    <div className="flex items-center border-b border-border/50 px-3">
                        <Search className="mr-2 h-4 w-4 shrink-0 opacity-50" />
                        <Input
                            placeholder="Search repo..."
                            value={repoSearch}
                            onChange={(e) => setRepoSearch(e.target.value)}
                            className="h-10 border-none shadow-none focus-visible:ring-0 px-0"
                        />
                    </div>

                    <div className="max-h-[300px] overflow-y-auto overflow-x-hidden p-1">
                        {repos.length === 0 && !isFetching && (
                             <div className="py-6 text-center text-xs text-muted-foreground">No repo found.</div>
                        )}
                        {isFetching && repos.length === 0 && (
                            <div className="py-6 text-center text-xs text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin mx-auto" /></div>
                        )}

                        {repos.length > 0 && (
                            <div className="px-1 py-1">
                                <div className="text-xs font-medium text-muted-foreground px-2 py-1.5">Repositories</div>
                                {repos.map((repo) => (
                                    <div
                                        key={repo.id}
                                        onClick={() => handleSelect(repo)}
                                        className={cn(
                                            "relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-surface-container-highest transition-colors",
                                            value === repo.id.toString() ? "bg-surface-container-highest" : ""
                                        )}
                                    >
                                        <Check
                                            className={cn(
                                                "mr-2 h-4 w-4 text-primary",
                                                value === repo.id.toString() ? "opacity-100" : "opacity-0"
                                            )}
                                        />
                                        <div className="flex flex-col truncate flex-1">
                                            <div className="flex items-center gap-2">
                                                <span className="truncate text-sm font-medium">{repo.full_name}</span>
                                                {repo.provider && (
                                                    <span className="text-[9px] px-1.5 py-0.5 rounded-md bg-background/50 text-muted-foreground shrink-0 border border-border/30">
                                                        {repo.provider.display_name}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {hasNextPage && (
                            <div className="p-1 border-t border-border/50">
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    className="w-full text-xs h-7 text-muted-foreground hover:bg-surface-container-highest rounded-lg"
                                    onClick={(e) => {
                                        e.preventDefault();
                                        fetchNextPage();
                                    }}
                                    disabled={isFetchingNextPage}
                                >
                                    {isFetchingNextPage ? <Loader2 className="h-3 w-3 animate-spin" /> : "Load more"}
                                </Button>
                            </div>
                        )}
                    </div>
                </PopoverContent>
            </Popover>

            <Button variant="ghost" size="sm" className="h-10 gap-2 text-muted-foreground hover:text-foreground hover:bg-surface-container rounded-xl">
                <Settings2 className="h-4 w-4" />
                <span className="text-xs font-medium">Configure</span>
            </Button>
        </div>
    );
}
