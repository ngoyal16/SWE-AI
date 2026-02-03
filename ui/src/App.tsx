
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes, Navigate } from "react-router-dom"
import { Loader2 } from "lucide-react"
import { ThemeProvider } from "@/components/theme-provider"
import { AuthProvider, useAuth } from "@/context/auth-context"
import { Toaster } from 'sonner';
import { PageHeaderProvider } from "@/context/page-header-context"
import { AIProfileProvider } from "@/context/ai-profile-context"
import Layout from "@/components/layout"
import LoginPage from "@/pages/login"
import SettingsPage from "@/pages/settings"
import GitProvidersPage from "@/pages/admin/git-providers"
import AIProfilesPage from "@/pages/admin/ai-profiles"
import GitProviderInstructionsPage from "@/pages/admin/git-provider-instructions"
import SessionsPage from "@/pages/sessions"
import NewSessionPage from "@/pages/new-session"
import SessionDetailPage from "@/pages/session-detail"

const queryClient = new QueryClient()

function ProtectedRoute({ children }: { children: React.ReactNode }) {
    const { user, loading } = useAuth();

    if (loading) {
        return (
            <div className="flex h-screen items-center justify-center bg-background text-foreground">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    if (!user) {
        return <Navigate to="/login" replace />;
    }

    return <>{children}</>;
}

function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <ThemeProvider defaultTheme="dark" storageKey="swe-ai-theme">
                <AuthProvider>
                    <AIProfileProvider>
                        <PageHeaderProvider>
                            <BrowserRouter>
                                <Routes>
                                    <Route path="/login" element={<LoginPage />} />
                                    <Route
                                        path="/"
                                        element={
                                            <ProtectedRoute>
                                                <Layout />
                                            </ProtectedRoute>
                                        }
                                    >
                                        <Route index element={<NewSessionPage />} />
                                        <Route path="sessions" element={<SessionsPage />} />
                                        <Route path="session/:sessionId" element={<SessionDetailPage />} />
                                        <Route path="settings" element={<SettingsPage />} />
                                        <Route path="admin/git-providers" element={<GitProvidersPage />} />
                                        <Route path="admin/ai-profiles" element={<AIProfilesPage />} />
                                        <Route path="admin/git-provider-setup" element={<GitProviderInstructionsPage />} />
                                    </Route>
                                    <Route path="*" element={<div className="flex items-center justify-center h-screen bg-background text-foreground">404 - Not Found</div>} />
                                </Routes>
                            </BrowserRouter>
                            <Toaster position="bottom-right" richColors />
                        </PageHeaderProvider>
                    </AIProfileProvider>
                </AuthProvider>
            </ThemeProvider>
        </QueryClientProvider>
    )
}

export default App
