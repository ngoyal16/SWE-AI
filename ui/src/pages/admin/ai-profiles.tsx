import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { usePageHeader } from '@/context/page-header-context';
import { aiProfileApi, type AIProfile, type AIProfileInput, AI_PROVIDERS } from '@/api/ai-profile';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from '@/components/ui/dialog';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import {
    Cpu,
    Plus,
    Settings2,
    Trash2,
    Loader2,
    ShieldCheck,
    AlertTriangle
} from 'lucide-react';
import { toast } from 'sonner';

export default function AIProfilesPage() {
    usePageHeader('AI Settings', 'Configure AI models and providers for workers');
    const queryClient = useQueryClient();
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [editingProfile, setEditingProfile] = useState<AIProfile | null>(null);

    const { data: profiles, isLoading } = useQuery({
        queryKey: ['admin-ai-profiles'],
        queryFn: async () => {
            const resp = await aiProfileApi.list();
            return resp;
        },
    });

    const createMutation = useMutation({
        mutationFn: aiProfileApi.create,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['admin-ai-profiles'] });
            toast.success('AI profile created successfully');
            setIsDialogOpen(false);
        },
    });

    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: number; data: AIProfileInput }) => aiProfileApi.update(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['admin-ai-profiles'] });
            toast.success('AI profile updated successfully');
            setIsDialogOpen(false);
            setEditingProfile(null);
        },
    });

    const toggleMutation = useMutation({
        mutationFn: aiProfileApi.toggle,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['admin-ai-profiles'] });
            toast.success('Status updated');
        },
    });

    const deleteMutation = useMutation({
        mutationFn: aiProfileApi.delete,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['admin-ai-profiles'] });
            toast.success('AI profile deleted');
        },
    });

    const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        const formData = new FormData(e.currentTarget);

        const apiKey = formData.get('api_key') as string;

        const data: AIProfileInput = {
            name: formData.get('name') as string,
            provider: formData.get('provider') as string,
            // If empty string (and we are editing), we might want to send undefined to keep existing?
            // Or usually the backend handles "if empty, don't update".
            // For now, let's treat empty string as undefined for optional fields.
            api_key: apiKey || undefined,
            base_url: (formData.get('base_url') as string) || undefined,
            default_model: (formData.get('default_model') as string) || undefined,
            is_enabled: true,
        };

        if (editingProfile) {
            updateMutation.mutate({ id: editingProfile.id, data });
        } else {
            createMutation.mutate(data);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium">AI Provider Profiles</h3>
                <Dialog open={isDialogOpen} onOpenChange={(open) => {
                    setIsDialogOpen(open);
                    if (!open) setEditingProfile(null);
                }}>
                    <DialogTrigger asChild>
                        <Button className="gap-2">
                            <Plus className="h-4 w-4" />
                            Add Profile
                        </Button>
                    </DialogTrigger>
                    <DialogContent className="sm:max-w-[525px]">
                        <form onSubmit={handleSubmit}>
                            <DialogHeader>
                                <DialogTitle>{editingProfile ? 'Edit AI Profile' : 'Add AI Profile'}</DialogTitle>
                                <DialogDescription>
                                    Configure a new AI model provider for the SWE agents.
                                </DialogDescription>
                            </DialogHeader>
                            <div className="grid gap-4 py-4">
                                <div className="grid gap-2">
                                    <Label htmlFor="name">Profile Name</Label>
                                    <Input
                                        id="name"
                                        name="name"
                                        defaultValue={editingProfile?.name}
                                        placeholder="e.g. Gemini 1.5 Pro"
                                        required
                                    />
                                </div>
                                <div className="grid gap-2">
                                    <Label htmlFor="provider">Provider Type</Label>
                                    <Select name="provider" defaultValue={editingProfile?.provider || 'gemini'}>
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select provider" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {AI_PROVIDERS.map((p) => (
                                                <SelectItem key={p.value} value={p.value}>
                                                    {p.label}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="grid gap-2">
                                    <Label htmlFor="api_key">API Key</Label>
                                    <Input
                                        id="api_key"
                                        name="api_key"
                                        type="password"
                                        placeholder={editingProfile ? "••••••••" : "Enter API key"}
                                    />
                                    {editingProfile && <p className="text-[10px] text-muted-foreground italic">Leave blank to keep existing key</p>}
                                </div>
                                <div className="grid gap-2">
                                    <Label htmlFor="default_model">Default Model</Label>
                                    <Input
                                        id="default_model"
                                        name="default_model"
                                        defaultValue={editingProfile?.default_model}
                                        placeholder="e.g. gemini-1.5-pro"
                                    />
                                </div>
                                <div className="grid gap-2">
                                    <Label htmlFor="base_url">Base URL (Optional)</Label>
                                    <Input
                                        id="base_url"
                                        name="base_url"
                                        defaultValue={editingProfile?.base_url}
                                        placeholder="https://api.openai.com/v1"
                                    />
                                </div>
                            </div>
                            <DialogFooter>
                                <Button type="submit" disabled={createMutation.isPending || updateMutation.isPending}>
                                    {(createMutation.isPending || updateMutation.isPending) && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                    {editingProfile ? 'Save Changes' : 'Create Profile'}
                                </Button>
                            </DialogFooter>
                        </form>
                    </DialogContent>
                </Dialog>
            </div>

            {isLoading ? (
                <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
            ) : profiles?.length === 0 ? (
                <Card className="border-dashed">
                    <CardContent className="flex flex-col items-center justify-center py-12 space-y-4">
                        <Cpu className="h-12 w-12 text-muted-foreground/50" />
                        <div className="text-center">
                            <p className="text-lg font-medium text-muted-foreground">No AI profiles configured</p>
                            <p className="text-sm text-muted-foreground mt-1">Add your first AI provider to get started.</p>
                        </div>
                    </CardContent>
                </Card>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {profiles?.map((profile) => (
                        <Card key={profile.id} className={`${!profile.is_enabled ? 'opacity-70 bg-muted/30' : 'bg-card/50 backdrop-blur-sm'}`}>
                            <CardHeader className="pb-2">
                                <div className="flex justify-between items-start">
                                    <div className="p-2 bg-primary/10 rounded-lg">
                                        <Cpu className="h-5 w-5 text-primary" />
                                    </div>
                                    <div className="flex gap-1">
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="h-8 w-8 text-muted-foreground hover:text-primary"
                                            onClick={() => {
                                                setEditingProfile(profile);
                                                setIsDialogOpen(true);
                                            }}
                                        >
                                            <Settings2 className="h-4 w-4" />
                                        </Button>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="h-8 w-8 text-muted-foreground hover:text-destructive"
                                            onClick={() => {
                                                if (confirm('Are you sure you want to delete this AI profile?')) {
                                                    deleteMutation.mutate(profile.id);
                                                }
                                            }}
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </Button>
                                    </div>
                                </div>
                                <CardTitle className="mt-4 flex items-center gap-2">
                                    {profile.name}
                                    {profile.is_default && (
                                        <span className="text-[10px] bg-amber-500/10 text-amber-500 px-1.5 py-0.5 rounded border border-amber-500/20 font-normal">
                                            Default
                                        </span>
                                    )}
                                </CardTitle>
                                <CardDescription className="capitalize font-mono text-xs">
                                    {profile.provider} • {profile.default_model || 'No model set'}
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="pt-2">
                                <div className="flex items-center justify-between mt-2">
                                    <div className="flex items-center gap-2">
                                        {profile.is_enabled ? (
                                            <ShieldCheck className="h-4 w-4 text-emerald-500" />
                                        ) : (
                                            <AlertTriangle className="h-4 w-4 text-amber-500" />
                                        )}
                                        <span className="text-xs font-medium">
                                            {profile.is_enabled ? 'Enabled' : 'Disabled'}
                                        </span>
                                    </div>
                                    <Switch
                                        checked={profile.is_enabled}
                                        onCheckedChange={() => toggleMutation.mutate(profile.id)}
                                        disabled={toggleMutation.isPending}
                                    />
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
}
