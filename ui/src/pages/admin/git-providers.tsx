import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { usePageHeader } from '@/context/page-header-context';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from '@/components/ui/dialog';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import {
    Github,
    GitBranch,
    Plus,
    Pencil,
    Trash2,
    Loader2,
    Check,
    X,
    Shield,
    Key,
    BookOpen,
} from 'lucide-react';
import {
    gitProviderApi,
    GIT_DRIVERS,
    AUTH_TYPES,
    DEFAULT_PROVIDER_URLS,
} from '@/api/git-provider';
import type { GitProvider, GitProviderInput } from '@/api/git-provider';

// GitLab icon SVG
const GitLabIcon = ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
        <path d="M22.65 14.39L12 22.13 1.35 14.39a.84.84 0 0 1-.3-.94l1.22-3.78 2.44-7.51A.42.42 0 0 1 4.82 2a.43.43 0 0 1 .58 0 .42.42 0 0 1 .11.18l2.44 7.49h8.1l2.44-7.51A.42.42 0 0 1 18.6 2a.43.43 0 0 1 .58 0 .42.42 0 0 1 .11.18l2.44 7.51L23 13.45a.84.84 0 0 1-.35.94z" />
    </svg>
);

// Bitbucket icon SVG
const BitbucketIcon = ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
        <path d="M.778 1.213a.768.768 0 0 0-.768.892l3.263 19.81c.084.5.515.868 1.022.873H19.95a.772.772 0 0 0 .77-.646l3.27-20.03a.768.768 0 0 0-.768-.891zM14.52 15.53H9.522L8.17 8.466h7.561z" />
    </svg>
);

// Provider icon component
const ProviderIcon = ({ driver, className }: { driver: string; className?: string }) => {
    switch (driver) {
        case 'github':
            return <Github className={className} />;
        case 'gitlab':
            return <GitLabIcon className={`${className} text-orange-500`} />;
        case 'bitbucket':
            return <BitbucketIcon className={`${className} text-blue-500`} />;
        default:
            return <GitBranch className={className} />;
    }
};

// Empty form state
const emptyFormState: GitProviderInput = {
    name: '',
    display_name: '',
    driver: 'github',
    enabled: false,
    auth_type: 'oauth',
    client_id: '',
    client_secret: '',
    auth_url: '',
    token_url: '',
    user_info_url: '',
    scopes: '',
    redirect_url: '',
    app_id: '',
    app_name: '',
    private_key: '',
    webhook_secret: '',
    base_url: '',
    project_access_token: '',
};

export default function GitProvidersPage() {
    const [providers, setProviders] = useState<GitProvider[]>([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [dialogOpen, setDialogOpen] = useState(false);
    const [editingId, setEditingId] = useState<number | null>(null);
    const [formData, setFormData] = useState<GitProviderInput>(emptyFormState);
    const [togglingId, setTogglingId] = useState<number | null>(null);

    // Fetch providers
    const fetchProviders = async () => {
        try {
            const data = await gitProviderApi.list();
            setProviders(data);
        } catch (err) {
            console.error('Failed to fetch providers:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchProviders();
    }, []);

    // Handle driver change - auto-fill URLs
    const handleDriverChange = (driver: string) => {
        const defaults = DEFAULT_PROVIDER_URLS[driver];
        if (defaults && !editingId) {
            setFormData({
                ...formData,
                driver,
                auth_url: defaults.authUrl,
                token_url: defaults.tokenUrl,
                user_info_url: defaults.userInfoUrl,
                scopes: defaults.scopes,
            });
        } else {
            setFormData({ ...formData, driver });
        }
    };

    // Open dialog for creating new provider
    const handleCreate = () => {
        setEditingId(null);
        setFormData(emptyFormState);
        setDialogOpen(true);
    };

    // Open dialog for editing provider
    const handleEdit = (provider: GitProvider) => {
        setEditingId(provider.id);
        setFormData({
            name: provider.name,
            display_name: provider.display_name,
            driver: provider.driver,
            enabled: provider.enabled,
            auth_type: provider.auth_type || 'oauth',
            client_id: provider.client_id,
            client_secret: '', // Don't prefill secrets
            auth_url: provider.auth_url,
            token_url: provider.token_url,
            user_info_url: provider.user_info_url,
            scopes: provider.scopes,
            redirect_url: provider.redirect_url,
            app_id: provider.app_id,
            app_name: provider.app_name,
            private_key: '',
            webhook_secret: '',
            base_url: provider.base_url,
            project_access_token: '',
        });
        setDialogOpen(true);
    };

    // Save provider (create or update)
    const handleSave = async () => {
        setSaving(true);
        try {
            // Sanitize data based on driver
            const dataToSave = { ...formData };
            if (dataToSave.driver === 'github') {
                // For GitHub, service account credentials are generated at runtime or handled via OAuth.
                // Clear these fields to ensure backend logic doesn't use stale/invalid values.
                // Note: app_name is preserved as it's used for GitHub App settings.
                dataToSave.project_access_token = '';
                dataToSave.app_username = '';
                dataToSave.app_email = '';
            }

            if (editingId) {
                await gitProviderApi.update(editingId, dataToSave);
            } else {
                await gitProviderApi.create(dataToSave);
            }
            await fetchProviders();
            setDialogOpen(false);
        } catch (err) {
            console.error('Failed to save provider:', err);
        } finally {
            setSaving(false);
        }
    };

    // Delete provider
    const handleDelete = async (id: number) => {
        if (!confirm('Are you sure you want to delete this provider?')) return;
        try {
            await gitProviderApi.delete(id);
            await fetchProviders();
        } catch (err) {
            console.error('Failed to delete provider:', err);
        }
    };

    // Toggle provider enabled status
    const handleToggle = async (id: number) => {
        setTogglingId(id);
        try {
            const result = await gitProviderApi.toggle(id);
            setProviders(providers.map(p =>
                p.id === id ? { ...p, enabled: result.enabled } : p
            ));
        } catch (err) {
            console.error('Failed to toggle provider:', err);
        } finally {
            setTogglingId(null);
        }
    };

    const isGitHubApp = formData.auth_type === 'github_app';

    usePageHeader('Git Providers', 'Configure authentication for Git hosting services');

    return (
        <div className="container max-w-5xl py-6 space-y-6">
            <div className="flex items-center justify-end gap-2">
                <Button variant="outline" asChild>
                    <Link to="/admin/git-provider-setup" className="gap-2">
                        <BookOpen className="h-4 w-4" />
                        Setup Guide
                    </Link>
                </Button>
                <Button onClick={handleCreate} className="gap-2">
                    <Plus className="h-4 w-4" />
                    Add Provider
                </Button>
            </div>

            {loading ? (
                <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
            ) : providers.length === 0 ? (
                <Card>
                    <CardContent className="flex flex-col items-center justify-center py-12">
                        <GitBranch className="h-12 w-12 text-muted-foreground mb-4" />
                        <p className="text-lg font-medium">No providers configured</p>
                        <p className="text-sm text-muted-foreground mt-1">
                            Add a Git provider to enable OAuth login.
                        </p>
                        <Button onClick={handleCreate} className="mt-4 gap-2">
                            <Plus className="h-4 w-4" />
                            Add First Provider
                        </Button>
                    </CardContent>
                </Card>
            ) : (
                <div className="grid gap-4">
                    {providers.map((provider) => (
                        <Card key={provider.id}>
                            <CardContent className="p-6">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className="p-3 rounded-xl bg-muted border">
                                            <ProviderIcon driver={provider.driver} className="h-6 w-6" />
                                        </div>
                                        <div>
                                            <div className="flex items-center gap-2">
                                                <h3 className="font-semibold">{provider.display_name}</h3>
                                                <span className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground">
                                                    {provider.auth_type === 'github_app' ? 'GitHub App' : 'OAuth'}
                                                </span>
                                            </div>
                                            <p className="text-sm text-muted-foreground">
                                                {provider.name} • {provider.driver}
                                            </p>
                                            <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                                                {provider.has_client_secret && (
                                                    <span className="flex items-center gap-1">
                                                        <Key className="h-3 w-3" />
                                                        Client Secret
                                                    </span>
                                                )}
                                                {provider.has_private_key && (
                                                    <span className="flex items-center gap-1">
                                                        <Shield className="h-3 w-3" />
                                                        Private Key
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <div className="flex items-center gap-2">
                                            {togglingId === provider.id ? (
                                                <Loader2 className="h-4 w-4 animate-spin" />
                                            ) : provider.enabled ? (
                                                <Check className="h-4 w-4 text-green-500" />
                                            ) : (
                                                <X className="h-4 w-4 text-red-500" />
                                            )}
                                            <Switch
                                                checked={provider.enabled}
                                                onCheckedChange={() => handleToggle(provider.id)}
                                                disabled={togglingId === provider.id}
                                            />
                                        </div>
                                        <Button
                                            variant="outline"
                                            size="icon"
                                            onClick={() => handleEdit(provider)}
                                        >
                                            <Pencil className="h-4 w-4" />
                                        </Button>
                                        <Button
                                            variant="outline"
                                            size="icon"
                                            className=" hover:bg-red-900/20 hover:border-red-900 hover:text-red-500"
                                            onClick={() => handleDelete(provider.id)}
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </Button>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}

            {/* Create/Edit Dialog */}
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto ">
                    <DialogHeader>
                        <DialogTitle>
                            {editingId ? 'Edit Provider' : 'Add Provider'}
                        </DialogTitle>
                    </DialogHeader>

                    <div className="grid gap-6 py-4">
                        {/* Basic Info */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="name">Name (slug)</Label>
                                <Input
                                    id="name"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    placeholder="e.g. github, gitlab-internal"

                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="display_name">Display Name</Label>
                                <Input
                                    id="display_name"
                                    value={formData.display_name}
                                    onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                                    placeholder="e.g. GitHub, Company GitLab"

                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Driver</Label>
                                <Select
                                    value={formData.driver}
                                    onValueChange={handleDriverChange}
                                >
                                    <SelectTrigger >
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {GIT_DRIVERS.map((d) => (
                                            <SelectItem key={d.value} value={d.value}>
                                                {d.label}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-2">
                                <Label>Auth Type</Label>
                                <Select
                                    value={formData.auth_type}
                                    onValueChange={(v: string) => setFormData({ ...formData, auth_type: v })}
                                >
                                    <SelectTrigger >
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {AUTH_TYPES.map((t) => (
                                            <SelectItem key={t.value} value={t.value}>
                                                {t.label}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>

                        <Separator />

                        {/* OAuth Settings */}
                        <div className="space-y-4">
                            <h3 className="text-sm font-medium">OAuth Settings</h3>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="client_id">Client ID</Label>
                                    <Input
                                        id="client_id"
                                        value={formData.client_id}
                                        onChange={(e) => setFormData({ ...formData, client_id: e.target.value })}

                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="client_secret">
                                        Client Secret {editingId && <span className="text-xs text-muted-foreground">(leave blank to keep existing)</span>}
                                    </Label>
                                    <Input
                                        id="client_secret"
                                        type="password"
                                        value={formData.client_secret}
                                        onChange={(e) => setFormData({ ...formData, client_secret: e.target.value })}

                                    />
                                </div>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="redirect_url">Redirect URL</Label>
                                <Input
                                    id="redirect_url"
                                    value={formData.redirect_url}
                                    onChange={(e) => setFormData({ ...formData, redirect_url: e.target.value })}
                                    placeholder="Auto-generated based on App URL and name"
                                    readOnly
                                    className="bg-muted"
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="auth_url">Auth URL</Label>
                                    <Input
                                        id="auth_url"
                                        value={formData.auth_url}
                                        onChange={(e) => setFormData({ ...formData, auth_url: e.target.value })}

                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="token_url">Token URL</Label>
                                    <Input
                                        id="token_url"
                                        value={formData.token_url}
                                        onChange={(e) => setFormData({ ...formData, token_url: e.target.value })}

                                    />
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="user_info_url">User Info URL</Label>
                                    <Input
                                        id="user_info_url"
                                        value={formData.user_info_url}
                                        onChange={(e) => setFormData({ ...formData, user_info_url: e.target.value })}

                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="scopes">Scopes</Label>
                                    <Input
                                        id="scopes"
                                        value={formData.scopes}
                                        onChange={(e) => setFormData({ ...formData, scopes: e.target.value })}
                                        placeholder="repo,user:email"

                                    />
                                </div>
                            </div>
                        </div>

                        {/* GitHub App Settings (conditional) */}
                        {isGitHubApp && (
                            <>
                                <Separator />
                                <div className="space-y-4">
                                    <h3 className="text-sm font-medium">GitHub App Settings</h3>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <Label htmlFor="app_id">App ID</Label>
                                            <Input
                                                id="app_id"
                                                value={formData.app_id}
                                                onChange={(e) => setFormData({ ...formData, app_id: e.target.value })}

                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label htmlFor="app_name">App Name</Label>
                                            <Input
                                                id="app_name"
                                                value={formData.app_name}
                                                onChange={(e) => setFormData({ ...formData, app_name: e.target.value })}

                                            />
                                        </div>
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="private_key">
                                            Private Key (PEM) {editingId && <span className="text-xs text-muted-foreground">(leave blank to keep existing)</span>}
                                        </Label>
                                        <textarea
                                            id="private_key"
                                            value={formData.private_key}
                                            onChange={(e) => setFormData({ ...formData, private_key: e.target.value })}
                                            className="w-full h-32 px-3 py-2 text-sm bg-background border rounded-md font-mono"
                                            placeholder="-----BEGIN RSA PRIVATE KEY-----&#10;...&#10;-----END RSA PRIVATE KEY-----"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="webhook_secret">
                                            Webhook Secret {editingId && <span className="text-xs text-muted-foreground">(leave blank to keep existing)</span>}
                                        </Label>
                                        <Input
                                            id="webhook_secret"
                                            type="password"
                                            value={formData.webhook_secret}
                                            onChange={(e) => setFormData({ ...formData, webhook_secret: e.target.value })}

                                        />
                                    </div>
                                </div>
                            </>
                        )}

                        {/* GitLab Self-hosted (conditional) */}
                        {formData.driver === 'gitlab' && (
                            <>
                                <Separator />
                                <div className="space-y-4">
                                    <h3 className="text-sm font-medium">GitLab Settings</h3>
                                    <div className="space-y-2">
                                        <Label htmlFor="base_url">Base URL (for self-hosted)</Label>
                                        <Input
                                            id="base_url"
                                            value={formData.base_url}
                                            onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
                                            placeholder="https://gitlab.yourcompany.com"

                                        />
                                    </div>
                                </div>
                            </>
                        )}

                        <Separator />

                        {/* Service Account / Bot Config */}
                        {formData.driver !== 'github' && (
                            <div className="space-y-4">
                                <div className="flex items-center gap-2">
                                    <h3 className="text-sm font-medium">Service Account (Bot User)</h3>
                                    <div className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                                        Optional
                                    </div>
                                </div>
                                <p className="text-xs text-muted-foreground">
                                    Override OAuth user credentials for Git operations. Useful for using a dedicated bot account for commits.
                                </p>

                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="service_name">Service Name (App Name)</Label>
                                        <Input
                                            id="service_name"
                                            value={formData.app_name}
                                            onChange={(e) => setFormData({ ...formData, app_name: e.target.value })}
                                            placeholder="e.g. SWE-Agent Bot"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="project_token">
                                            Service Token (PAT) {editingId && formData.project_access_token === "" && <span className="text-xs text-muted-foreground">(leave blank to keep existing)</span>}
                                        </Label>
                                        <Input
                                            id="project_token"
                                            type="password"
                                            value={formData.project_access_token}
                                            onChange={(e) => setFormData({ ...formData, project_access_token: e.target.value })}
                                            placeholder="Personal Access Token"
                                        />
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="app_username">App Username</Label>
                                        <Input
                                            id="app_username"
                                            value={formData.app_username}
                                            onChange={(e) => setFormData({ ...formData, app_username: e.target.value })}
                                            placeholder="e.g. swe-bot-user"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="app_email">App Email</Label>
                                        <Input
                                            id="app_email"
                                            value={formData.app_email}
                                            onChange={(e) => setFormData({ ...formData, app_email: e.target.value })}
                                            placeholder="e.g. bot@example.com"
                                        />
                                    </div>
                                </div>
                            </div>
                        )}

                    </div>

                    <DialogFooter>
                        <Button
                            variant="outline"
                            onClick={() => setDialogOpen(false)}

                        >
                            Cancel
                        </Button>
                        <Button onClick={handleSave} disabled={saving}>
                            {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            {editingId ? 'Save Changes' : 'Create Provider'}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div >
    );
}
