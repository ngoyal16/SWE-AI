import { usePageHeader } from '@/context/page-header-context';

export default function DashboardPage() {
    usePageHeader('Dashboard', 'Overview of your AI agent activity');

    return (
        <div className="flex flex-col items-center justify-center py-12">
            <h2 className="text-2xl font-semibold text-muted-foreground">Coming Soon</h2>
            <p className="text-muted-foreground mt-2">The dashboard is under development.</p>
        </div>
    );
}
