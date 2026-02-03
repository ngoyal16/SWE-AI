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
                        className="w-[280px] justify-between bg-black border-black text-white hover:bg-zinc-800 rounded-lg h-9"
                    >
                        {selectedRepo ? (
                            <span className="truncate flex items-center gap-2">
                                <GitBranch className="h-3.5 w-3.5 text-muted-foreground" />
                                {selectedRepo.full_name}
                            </span>
                        ) : (
                            <span className="text-zinc-400">Select repository...</span>
                        )}
                        <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                    </Button>
                </PopoverTrigger>
                <PopoverContent className="w-[300px] p-0 bg-popover border-border text-popover-foreground" align="start">
                    <Command className="bg-transparent" shouldFilter={false}>
                        <CommandInput
                            placeholder="Search repo..."
                            value={repoSearch}
                            onValueChange={setRepoSearch}
                            className="h-9 border-none focus:ring-0"
                        />
                        <CommandList>
                            <CommandEmpty className="py-2 text-center text-xs text-muted-foreground">
                                {isFetching && !isFetchingNextPage ? <Loader2 className="h-4 w-4 animate-spin mx-auto" /> : "No repo found."}
                            </CommandEmpty>
                            <CommandGroup heading="Repositories" className="text-muted-foreground">
                                {repos.map((repo) => (
                                    <CommandItem
                                        key={repo.id}
                                        value={repo.id.toString()}
                                        onSelect={() => handleSelect(repo.id.toString())}
                                        className="text-foreground aria-selected:bg-accent aria-selected:text-accent-foreground cursor-pointer"
                                    >
                                        <Check
                                            className={cn(
                                                "mr-2 h-4 w-4",
                                                value === repo.id.toString() ? "opacity-100" : "opacity-0"
                                            )}
                                        />
                                        <div className="flex flex-col truncate flex-1">
                                            <div className="flex items-center gap-2">
                                                <span className="truncate text-sm">{repo.full_name}</span>
                                                {repo.provider && (
                                                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground shrink-0">
                                                        {repo.provider.display_name}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </CommandItem>
                                ))}
                            </CommandGroup>
                            {hasNextPage && (
                                <div className="p-1 border-t border-border">
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        className="w-full text-xs h-7 text-muted-foreground"
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

            <Button variant="ghost" size="sm" className="h-9 gap-1 text-zinc-500 hover:text-zinc-900">
                <Settings2 className="h-4 w-4" />
                <span className="text-xs font-medium">Configure repo</span>
            </Button>
        </div>
    );
}
