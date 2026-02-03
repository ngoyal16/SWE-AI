import { useState, useEffect } from 'react';
import { Command, Loader2, AlertCircle, User, Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { apiClient } from '@/lib/api-client';

interface LoginResponse {
    message: string;
    user: {
        id: number;
        username: string;
        email: string;
    };
}

export default function LoginPage() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Username/password form state
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');

    // Check for any error from URL params
    useEffect(() => {
        const urlParams = new URLSearchParams(window.location.search);
        const errorMsg = urlParams.get('error');

        if (errorMsg) {
            setError(errorMsg);
            // Clean up URL
            window.history.replaceState({}, '', '/login');
        }
    }, []);

    const handlePasswordLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!username || !password) {
            setError('Please enter username and password');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            await apiClient.post<LoginResponse>('/auth/login', {
                username,
                password,
            });
            // Cookie is set by server, just redirect
            window.location.href = '/';
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Login failed');
            setLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-muted/20 px-4 py-12 sm:px-6 lg:px-8">
            <Card className="w-full max-w-md">
                <CardHeader className="text-center space-y-2">
                    <div className="flex justify-center mb-2">
                        <div className="p-3 rounded-2xl bg-primary text-primary-foreground shadow-xl shadow-primary/20">
                            <Command className="h-8 w-8" />
                        </div>
                    </div>
                    <CardTitle className="text-3xl font-bold tracking-tight">SWE Agent</CardTitle>
                    <CardDescription>
                        Sign in to start building
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6 pt-4">
                    {error && (
                        <div className="flex items-center gap-2 rounded-lg bg-destructive/15 p-3 text-sm text-destructive border border-destructive/20 animate-in fade-in zoom-in duration-300">
                            <AlertCircle className="h-4 w-4 flex-shrink-0" />
                            <p>{error}</p>
                        </div>
                    )}

                    {/* Username/Password Form */}
                    <form onSubmit={handlePasswordLogin} className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="username">Username</Label>
                            <div className="relative">
                                <User className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                                <Input
                                    id="username"
                                    type="text"
                                    placeholder="Enter your username"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    className="pl-10"
                                    disabled={loading}
                                />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="password">Password</Label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                                <Input
                                    id="password"
                                    type="password"
                                    placeholder="Enter your password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="pl-10"
                                    disabled={loading}
                                />
                            </div>
                        </div>
                        <Button
                            type="submit"
                            className="w-full"
                            disabled={loading}
                        >
                            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Sign In
                        </Button>
                    </form>
                </CardContent>
                <CardFooter className="flex flex-col border-t mt-4 pt-6 text-center">
                    <p className="text-xs text-muted-foreground">
                        By signing in, you agree to our Terms of Service.
                    </p>
                </CardFooter>
            </Card>
        </div>
    );
}
