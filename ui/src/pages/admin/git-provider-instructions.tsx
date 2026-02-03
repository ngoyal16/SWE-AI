import { useState } from 'react';
import { usePageHeader } from '@/context/page-header-context';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Github, ExternalLink, Copy, Check, ChevronDown, ChevronRight } from 'lucide-react';

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

const CopyButton = ({ text }: { text: string }) => {
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <Button variant="ghost" size="sm" onClick={handleCopy} className="h-6 px-2">
            {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
        </Button>
    );
};

const CodeBlock = ({ code }: { code: string }) => (
    <div className="relative bg-muted rounded-md p-3 font-mono text-sm">
        <code>{code}</code>
        <div className="absolute top-2 right-2">
            <CopyButton text={code} />
        </div>
    </div>
);

interface CollapsibleSectionProps {
    title: string;
    icon: React.ReactNode;
    defaultOpen?: boolean;
    children: React.ReactNode;
}

const CollapsibleSection = ({ title, icon, defaultOpen = false, children }: CollapsibleSectionProps) => {
    const [isOpen, setIsOpen] = useState(defaultOpen);

    return (
        <Card>
            <CardHeader
                className="cursor-pointer select-none"
                onClick={() => setIsOpen(!isOpen)}
            >
                <CardTitle className="text-lg flex items-center gap-3">
                    {icon}
                    <span className="flex-1">{title}</span>
                    {isOpen ? <ChevronDown className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
                </CardTitle>
            </CardHeader>
            {isOpen && <CardContent>{children}</CardContent>}
        </Card>
    );
};

export default function GitProviderInstructionsPage() {
    usePageHeader('Provider Setup Guide', 'Step-by-step instructions for configuring Git providers');

    const baseUrl = window.location.origin;

    return (
        <div className="container max-w-4xl py-6 space-y-6">
            {/* GitHub App */}
            <CollapsibleSection
                title="GitHub App Setup"
                icon={<Github className="h-6 w-6" />}
                defaultOpen={true}
            >
                <div className="space-y-6">
                    <CardDescription>
                        GitHub Apps provide fine-grained permissions and better security compared to OAuth apps.
                    </CardDescription>

                    <div className="space-y-4">
                        <h4 className="font-medium">Step 1: Create a GitHub App</h4>
                        <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
                            <li>Go to GitHub → Settings → Developer settings → GitHub Apps</li>
                            <li>Click "New GitHub App"</li>
                            <li>Fill in the required details:</li>
                        </ol>
                        <div className="space-y-3 pl-6">
                            <div>
                                <p className="text-sm font-medium mb-1">GitHub App name:</p>
                                <CodeBlock code="SWE-AI-Agent" />
                            </div>
                            <div>
                                <p className="text-sm font-medium mb-1">Homepage URL:</p>
                                <CodeBlock code={baseUrl} />
                            </div>
                            <div>
                                <p className="text-sm font-medium mb-1">Callback URL:</p>
                                <CodeBlock code={`${baseUrl}/api/auth/oauth/github/callback`} />
                            </div>
                            <div>
                                <p className="text-sm font-medium mb-1">Webhook URL (optional):</p>
                                <CodeBlock code={`${baseUrl}/api/webhooks/github`} />
                            </div>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <h4 className="font-medium">Step 2: Configure Permissions</h4>
                        <p className="text-sm text-muted-foreground">Set the following repository permissions:</p>
                        <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground pl-4">
                            <li><strong>Contents:</strong> Read & Write</li>
                            <li><strong>Issues:</strong> Read & Write</li>
                            <li><strong>Pull requests:</strong> Read & Write</li>
                            <li><strong>Metadata:</strong> Read-only</li>
                        </ul>
                        <p className="text-sm text-muted-foreground">Account permissions:</p>
                        <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground pl-4">
                            <li><strong>Email addresses:</strong> Read-only</li>
                        </ul>
                    </div>

                    <div className="space-y-4">
                        <h4 className="font-medium">Step 3: Generate Private Key</h4>
                        <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
                            <li>After creating the app, scroll down to "Private keys"</li>
                            <li>Click "Generate a private key"</li>
                            <li>Save the downloaded .pem file securely</li>
                            <li>Copy the contents into the "Private Key" field when adding the provider</li>
                        </ol>
                    </div>

                    <div className="space-y-4">
                        <h4 className="font-medium">Step 4: Note Required Values</h4>
                        <p className="text-sm text-muted-foreground">From the GitHub App settings page, copy:</p>
                        <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground pl-4">
                            <li><strong>App ID:</strong> Found at the top of the page</li>
                            <li><strong>Client ID:</strong> For OAuth authentication</li>
                            <li><strong>Client Secret:</strong> Generate one if not already created</li>
                        </ul>
                    </div>

                    <Button variant="outline" asChild>
                        <a href="https://github.com/settings/apps/new" target="_blank" rel="noopener noreferrer">
                            <ExternalLink className="h-4 w-4 mr-2" />
                            Create GitHub App
                        </a>
                    </Button>
                </div>
            </CollapsibleSection>

            {/* GitLab OAuth */}
            <CollapsibleSection
                title="GitLab OAuth Setup"
                icon={<GitLabIcon className="h-6 w-6 text-orange-500" />}
            >
                <div className="space-y-6">
                    <CardDescription>
                        Configure GitLab OAuth for both GitLab.com and self-hosted GitLab instances.
                    </CardDescription>

                    <div className="space-y-4">
                        <h4 className="font-medium">Step 1: Create an OAuth Application</h4>
                        <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
                            <li>Go to GitLab → User Settings → Applications</li>
                            <li>Or for group-level: Group → Settings → Applications</li>
                            <li>Click "Add new application"</li>
                        </ol>
                    </div>

                    <div className="space-y-4">
                        <h4 className="font-medium">Step 2: Configure Application</h4>
                        <div className="space-y-3 pl-6">
                            <div>
                                <p className="text-sm font-medium mb-1">Name:</p>
                                <CodeBlock code="SWE-AI-Agent" />
                            </div>
                            <div>
                                <p className="text-sm font-medium mb-1">Redirect URI:</p>
                                <CodeBlock code={`${baseUrl}/api/auth/oauth/gitlab/callback`} />
                            </div>
                            <div>
                                <p className="text-sm font-medium mb-1">Scopes (select all):</p>
                                <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                                    <li><code>api</code> - Full API access</li>
                                    <li><code>read_user</code> - Read user information</li>
                                    <li><code>read_repository</code> - Read repository</li>
                                    <li><code>write_repository</code> - Write repository</li>
                                </ul>
                            </div>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <h4 className="font-medium">Step 3: Save Credentials</h4>
                        <p className="text-sm text-muted-foreground">After saving, copy:</p>
                        <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground pl-4">
                            <li><strong>Application ID:</strong> Use as Client ID</li>
                            <li><strong>Secret:</strong> Use as Client Secret</li>
                        </ul>
                    </div>

                    <div className="space-y-4">
                        <h4 className="font-medium">For Self-Hosted GitLab</h4>
                        <p className="text-sm text-muted-foreground">
                            Set the Base URL when adding the provider (e.g., <code>https://gitlab.yourcompany.com</code>).
                            The OAuth URLs will be automatically configured based on your base URL.
                        </p>
                    </div>

                    <Button variant="outline" asChild>
                        <a href="https://gitlab.com/-/user_settings/applications" target="_blank" rel="noopener noreferrer">
                            <ExternalLink className="h-4 w-4 mr-2" />
                            Create GitLab Application
                        </a>
                    </Button>
                </div>
            </CollapsibleSection>

            {/* Bitbucket OAuth */}
            <CollapsibleSection
                title="Bitbucket OAuth Setup"
                icon={<BitbucketIcon className="h-6 w-6 text-blue-500" />}
            >
                <div className="space-y-6">
                    <CardDescription>
                        Configure Bitbucket OAuth consumer for authentication and repository access.
                    </CardDescription>

                    <div className="space-y-4">
                        <h4 className="font-medium">Step 1: Create an OAuth Consumer</h4>
                        <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
                            <li>Go to Bitbucket → Workspace settings</li>
                            <li>Navigate to OAuth consumers</li>
                            <li>Click "Add consumer"</li>
                        </ol>
                    </div>

                    <div className="space-y-4">
                        <h4 className="font-medium">Step 2: Configure OAuth Consumer</h4>
                        <div className="space-y-3 pl-6">
                            <div>
                                <p className="text-sm font-medium mb-1">Name:</p>
                                <CodeBlock code="SWE-AI-Agent" />
                            </div>
                            <div>
                                <p className="text-sm font-medium mb-1">Callback URL:</p>
                                <CodeBlock code={`${baseUrl}/api/auth/oauth/bitbucket/callback`} />
                            </div>
                            <div>
                                <p className="text-sm font-medium mb-1">Permissions (select):</p>
                                <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                                    <li><strong>Account:</strong> Read</li>
                                    <li><strong>Repositories:</strong> Read, Write</li>
                                    <li><strong>Pull requests:</strong> Read, Write</li>
                                    <li><strong>Issues:</strong> Read, Write</li>
                                </ul>
                            </div>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <h4 className="font-medium">Step 3: Save Credentials</h4>
                        <p className="text-sm text-muted-foreground">After saving, you'll see:</p>
                        <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground pl-4">
                            <li><strong>Key:</strong> Use as Client ID</li>
                            <li><strong>Secret:</strong> Use as Client Secret</li>
                        </ul>
                    </div>

                    <Button variant="outline" asChild>
                        <a href="https://bitbucket.org/workspace/settings/oauth-consumers/new" target="_blank" rel="noopener noreferrer">
                            <ExternalLink className="h-4 w-4 mr-2" />
                            Create Bitbucket Consumer
                        </a>
                    </Button>
                </div>
            </CollapsibleSection>
        </div>
    );
}
