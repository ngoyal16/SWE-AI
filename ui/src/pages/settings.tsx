import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Github, Shield, Save, Key, Loader2, Link2, Unlink, Cpu, ShieldCheck } from 'lucide-react';
import { usePageHeader } from '@/context/page-header-context';
import { gitProviderApi } from '@/api/git-provider';
import type { EnabledProvider, LinkedIdentity } from '@/api/git-provider';
import { useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';
import { useAIProfile } from '@/context/ai-profile-context';

// GitLab icon
const GitLabIcon = ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
        <path d="M22.65 14.39L12 22.13 1.35 14.39a.84.84 0 0 1-.3-.94l1.22-3.78 2.44-7.51A.42.42 0 0 1 4.82 2a.43.43 0 0 1 .58 0 .42.42 0 0 1 .11.18l2.44 7.49h8.1l2.44-7.51A.42.42 0 0 1 18.6 2a.43.43 0 0 1 .58 0 .42.42 0 0 1 .11.18l2.44 7.51L23 13.45a.84.84 0 0 1-.35.94z" />
    </svg>
);

// Bitbucket icon
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
            return <Link2 className={className} />;
    }
};

export default function SettingsPage() {
    usePageHeader('Settings', 'Manage your Git accounts and security preferences');
    const [searchParams, setSearchParams] = useSearchParams();

    const [providers, setProviders] = useState<EnabledProvider[]>([]);
    const [loading, setLoading] = useState(true);
    const [linkedAccounts, setLinkedAccounts] = useState<LinkedIdentity[]>([]);
    const [linkingProvider, setLinkingProvider] = useState<string | null>(null);

    const { profiles: aiProfiles, selectedProfileId, setSelectedProfileId, isLoading: aiLoading } = useAIProfile();

    useEffect(() => {
        loadData();

        // Check for success/error from OAuth redirect
        const linked = searchParams.get('linked');
        const error = searchParams.get('error');

        if (linked) {
            toast.success(`Successfully connected ${linked}`);
            // Remove the param from URL
            searchParams.delete('linked');
            setSearchParams(searchParams);
        }

        if (error) {
            toast.error(error);
            searchParams.delete('error');
            setSearchParams(searchParams);
        }
    }, [searchParams]);

    const loadData = async () => {
        setLoading(true);
        try {
            const [providersData, identitiesData] = await Promise.all([
                gitProviderApi.getEnabledProviders(),
                gitProviderApi.getIdentities()
            ]);
            setProviders(providersData);
            setLinkedAccounts(identitiesData);
        } catch (err) {
            console.error('Failed to load data:', err);
            toast.error('Failed to load settings data');
        } finally {
            setLoading(false);
        }
    };

    const handleUpdateAIPreference = async (profileId: number) => {
        setSelectedProfileId(profileId.toString());
    };

    const handleLinkProvider = (providerName: string) => {
        setLinkingProvider(providerName);
        // Redirect to OAuth flow
        window.location.href = `/api/auth/oauth/${providerName}`;
    };

    const handleUnlinkProvider = async (providerName: string) => {
        if (!confirm(`Are you sure you want to disconnect ${providerName}?`)) return;

        try {
            await gitProviderApi.unlink(providerName);
            toast.success(`Successfully disconnected ${providerName}`);
            await loadData();
        } catch (err) {
            console.error('Failed to unlink provider:', err);
            toast.error('Failed to disconnect provider');
        }
    };

    const getLinkedAccount = (providerName: string): LinkedIdentity | undefined => {
        return linkedAccounts.find(a => a.provider === providerName);
    };

    return (
        <div className="container max-w-4xl py-6 space-y-8">
            <div className="grid gap-6">
                {/* Git Providers */}
                <Card>
                    <CardHeader>
                        <CardTitle className="text-lg flex items-center gap-2">
                            <Link2 className="h-5 w-5 text-blue-400" />
                            Linked Git Accounts
                        </CardTitle>
                        <CardDescription>
                            Connect your Git provider accounts to enable repository access.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {loading ? (
                            <div className="flex items-center justify-center py-8">
                                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                            </div>
                        ) : providers.length === 0 ? (
                            <div className="text-center py-8 text-muted-foreground">
                                <p>No Git providers are currently available.</p>
                                <p className="text-sm mt-1">Contact your administrator to enable providers.</p>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {providers.map((provider) => {
                                    const linked = getLinkedAccount(provider.name);
                                    const isLinking = linkingProvider === provider.name;

                                    return (
                                        <div
                                            key={provider.name}
                                            className="flex items-center justify-between p-4 rounded-xl border bg-muted/30"
                                        >
                                            <div className="flex items-center gap-3">
                                                <div className="p-2 rounded-lg bg-background border">
                                                    <ProviderIcon driver={provider.driver} className="h-5 w-5" />
                                                </div>
                                                <div>
                                                    <p className="text-sm font-medium">{provider.display_name}</p>
                                                    {linked ? (
                                                        <p className="text-xs text-green-500">
                                                            Linked as {linked.email}
                                                        </p>
                                                    ) : (
                                                        <p className="text-xs text-muted-foreground">Not connected</p>
                                                    )}
                                                </div>
                                            </div>
                                            {linked ? (
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() => handleUnlinkProvider(provider.name)}
                                                    className="gap-1"
                                                >
                                                    <Unlink className="h-3 w-3" />
                                                    Disconnect
                                                </Button>
                                            ) : (
                                                <Button
                                                    size="sm"
                                                    onClick={() => handleLinkProvider(provider.name)}
                                                    disabled={isLinking}
                                                    className="gap-1"
                                                >
                                                    {isLinking ? (
                                                        <Loader2 className="h-3 w-3 animate-spin" />
                                                    ) : (
                                                        <Link2 className="h-3 w-3" />
                                                    )}
                                                    Connect
                                                </Button>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* AI Preferences */}
                <Card>
                    <CardHeader>
                        <CardTitle className="text-lg flex items-center gap-2">
                            <Cpu className="h-5 w-5 text-amber-500" />
                            AI Model Preferences
                        </CardTitle>
                        <CardDescription>
                            Select the default AI model to be used for your agent sessions.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {aiLoading ? (
                            <div className="flex items-center justify-center py-8">
                                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                            </div>
                        ) : aiProfiles.length === 0 ? (
                            <div className="text-center py-8 text-muted-foreground bg-muted/20 rounded-xl border border-dashed text-sm">
                                No AI models are currently configured by the admin.
                            </div>
                        ) : (
                            <div className="grid gap-3">
                                {aiProfiles.map((profile) => (
                                    <div
                                        key={profile.id}
                                        className={`flex items-center justify-between p-4 rounded-xl border transition-all cursor-pointer ${selectedProfileId === profile.id.toString()
                                            ? 'border-primary bg-primary/5 shadow-sm'
                                            : 'bg-muted/30 hover:bg-muted/50'
                                            }`}
                                        onClick={() => handleUpdateAIPreference(profile.id)}
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className={`p-2 rounded-lg border ${selectedProfileId === profile.id.toString() ? 'bg-primary/10 border-primary/20' : 'bg-background'
                                                }`}>
                                                <Cpu className={`h-5 w-5 ${selectedProfileId === profile.id.toString() ? 'text-primary' : 'text-muted-foreground'
                                                    }`} />
                                            </div>
                                            <div>
                                                <p className="text-sm font-medium">{profile.name}</p>
                                                <p className="text-xs text-muted-foreground capitalize">
                                                    {profile.provider} • {profile.default_model}
                                                </p>
                                            </div>
                                        </div>
                                        <div className="flex items-center">
                                            {selectedProfileId === profile.id.toString() ? (
                                                <div className="flex h-5 w-5 items-center justify-center rounded-full bg-primary text-primary-foreground">
                                                    <ShieldCheck className="h-3 w-3" />
                                                </div>
                                            ) : (
                                                <div className="h-5 w-5 rounded-full border" />
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Security */}
                <Card>
                    <CardHeader>
                        <CardTitle className="text-lg flex items-center gap-2">
                            <Shield className="h-5 w-5 text-green-500" />
                            Security & Encryption
                        </CardTitle>
                        <CardDescription>Configure your master encryption key for token storage.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="bg-yellow-500/10 border border-yellow-500/20 p-4 rounded-xl text-yellow-500 text-xs mb-4">
                            <p className="font-semibold">Important:</p>
                            <p>Your tokens are encrypted using AES-256 before being stored. Ensure you save your encryption key securely.</p>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="master-key">Master Encryption Key</Label>
                            <div className="relative">
                                <Key className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                <Input id="master-key" type="password" value="••••••••••••••••" className="pl-10" readOnly />
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            <div className="flex justify-end pt-4">
                <Button className="gap-2">
                    <Save className="h-4 w-4" />
                    Save All Settings
                </Button>
            </div>
        </div>
    );
}
