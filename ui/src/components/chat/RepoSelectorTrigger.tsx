import { useState, useEffect } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { gitProviderApi, type Repository, type RepositoryResponse } from '@/api/git-provider';
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover"
import {
    Command,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
} from "@/components/ui/command"
import { Button } from '@/components/ui/button';
import { Check, ChevronsUpDown, GitBranch, Settings2, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
// import { Badge } from '@/components/ui/badge';

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
    const selectedRepo = repos.find(r => r.id.toString() === value);

    const handleSelect = (currentValue: string) => {
        console.log('handleSelect called with:', currentValue);
        const repo = repos.find((r) => r.id.toString() === currentValue) || null;
        console.log('Found repo:', repo);
        if (repo) {
            console.log('Calling onValueChange with:', repo.id, repo);
            onValueChange(repo.id.toString(), repo);
            setOpen(false);
        } else {
            console.log('Repo not found for value:', currentValue);
        }
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
                <PopoverContent className="w-[300px] p-0 bg-surface-container border-border/50 text-foreground shadow-xl rounded-xl" align="start">
                    <Command className="bg-transparent" shouldFilter={false}>
                        <CommandInput
                            placeholder="Search repo..."
                            value={repoSearch}
                            onValueChange={setRepoSearch}
                            className="h-9 border-none focus:ring-0"
                        />
                        <CommandList>
                            <CommandEmpty className="py-4 text-center text-xs text-muted-foreground">
                                {isFetching && !isFetchingNextPage ? <Loader2 className="h-4 w-4 animate-spin mx-auto" /> : "No repo found."}
                            </CommandEmpty>
                            <CommandGroup heading="Repositories" className="text-muted-foreground px-1 py-1">
                                {repos.map((repo) => (
                                    <CommandItem
                                        key={repo.id}
                                        value={repo.id.toString()}
                                        onSelect={() => handleSelect(repo.id.toString())}
                                        className="text-foreground aria-selected:bg-surface-container-highest aria-selected:text-foreground cursor-pointer rounded-lg my-0.5"
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
                                    </CommandItem>
                                ))}
                            </CommandGroup>
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
                        </CommandList>
                    </Command>
                </PopoverContent>
            </Popover>

            <Button variant="ghost" size="sm" className="h-10 gap-2 text-muted-foreground hover:text-foreground hover:bg-surface-container rounded-xl">
                <Settings2 className="h-4 w-4" />
                <span className="text-xs font-medium">Configure</span>
            </Button>
        </div>
    );
}
