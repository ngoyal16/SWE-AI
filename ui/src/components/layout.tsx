import {
    Settings,
    LogOut,
    Command,
    Moon,
    Sun,
    Menu,
    Shield,
    GitBranch,
    Cpu,
    Plus
} from "lucide-react"
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom"
import { useTheme } from "@/components/theme-provider"
import { useAuth } from "@/context/auth-context"
// import { useHeaderContext } from "@/context/page-header-context"
import { Button } from "@/components/ui/button"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
    DropdownMenuSeparator,
    DropdownMenuLabel
} from "@/components/ui/dropdown-menu"
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from "@/components/ui/sheet"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { AIProfileSelector } from "@/components/ai-profile-selector"
import { SidebarSessionList } from "@/components/layout/SidebarSessionList"

export default function Layout() {
    const { setTheme, theme } = useTheme()
    const { user, logout } = useAuth()
    const navigate = useNavigate()
    const location = useLocation()
    // const { title, description } = useHeaderContext()
    const isAdminMode = location.pathname.startsWith("/admin")

    // Admin menu items
    const adminItems = [
        { to: "/admin/git-providers", icon: GitBranch, label: "Git Providers" },
        { to: "/admin/ai-profiles", icon: Cpu, label: "AI Settings" },
    ]

    const NavLink = ({ item, isActive, className = "" }: { item: typeof adminItems[0], isActive: boolean, className?: string }) => (
        <Link
            to={item.to}
            className={`flex items-center gap-3 rounded-full px-4 py-3 text-sm font-medium transition-all duration-200 group ${isActive
                ? "bg-primary/10 text-primary"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
                } ${className}`}
        >
            <item.icon className={`h-5 w-5 shrink-0 ${isActive ? "text-primary" : ""}`} />
            <span>{item.label}</span>
        </Link>
    )

    return (
        <div className="bg-background min-h-screen w-full md:grid md:grid-cols-[280px_1fr] lg:grid-cols-[300px_1fr]">
            {/* Sidebar */}
            <div className="bg-sidebar-background hidden border-r border-sidebar-border md:block sticky top-0 h-screen">
                <div className="flex h-full flex-col gap-4 p-4">
                    {/* Logo Area */}
                    <div className="flex h-16 items-center px-2">
                        <Link to="/" className="flex items-center gap-3 transition-opacity hover:opacity-80">
                            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-lg shadow-primary/20">
                                <Command className="h-6 w-6" />
                            </div>
                            <span className="text-xl font-semibold tracking-tight text-sidebar-foreground">SWE AI Agent</span>
                        </Link>
                    </div>

                    {/* New Session Button */}
                    {!isAdminMode && (
                        <Button
                            className="w-full justify-start gap-3 rounded-2xl h-14 px-4 shadow-md bg-primary/10 hover:bg-primary/20 text-primary border-none"
                            variant="outline"
                            onClick={() => navigate('/')}
                        >
                            <Plus className="h-6 w-6" />
                            <span className="font-medium text-base">New Session</span>
                        </Button>
                    )}

                    {/* Navigation */}
                    <div className="flex-1 overflow-auto py-2 -mx-2 px-2">
                        {isAdminMode ? (
                            <nav className="grid items-start gap-1">
                                {adminItems.map((item) => {
                                    const isActive = location.pathname === item.to;
                                    return <NavLink key={item.to} item={item} isActive={isActive} />;
                                })}
                            </nav>
                        ) : (
                            <SidebarSessionList />
                        )}
                    </div>

                    {/* Sidebar Footer (User Profile) */}
                     <div className="mt-auto pt-4 border-t border-sidebar-border">
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button variant="ghost" className="w-full justify-start h-auto py-2 px-2 gap-3 hover:bg-sidebar-accent rounded-xl">
                                    <Avatar className="h-9 w-9 border border-border">
                                        <AvatarImage src={user?.avatar_url} alt={user?.name || user?.email} />
                                        <AvatarFallback className="bg-primary/10 text-primary font-medium">
                                            {(user?.name || user?.email || "U").charAt(0).toUpperCase()}
                                        </AvatarFallback>
                                    </Avatar>
                                    <div className="flex flex-col items-start text-left overflow-hidden">
                                        <span className="text-sm font-medium truncate w-full text-sidebar-foreground">{user?.name || "User"}</span>
                                        <span className="text-xs text-muted-foreground truncate w-full">{user?.email}</span>
                                    </div>
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="start" className="w-56 rounded-xl shadow-lg border-border/50 bg-popover/95 backdrop-blur-sm">
                                <DropdownMenuLabel>My Account</DropdownMenuLabel>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem onClick={() => navigate("/settings")} className="rounded-lg cursor-pointer">
                                    <Settings className="mr-2 h-4 w-4" />
                                    <span>Settings</span>
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem onClick={logout} className="text-destructive focus:text-destructive rounded-lg cursor-pointer">
                                    <LogOut className="mr-2 h-4 w-4" />
                                    <span>Log out</span>
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>
                </div>
            </div>

            {/* Main Content Area */}
            <div className="flex flex-col min-h-screen">
                <header className="flex h-16 items-center gap-4 px-6 lg:h-[72px] sticky top-0 z-10 bg-background/80 backdrop-blur-md">
                    <Sheet>
                        <SheetTrigger asChild>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="shrink-0 md:hidden rounded-full"
                            >
                                <Menu className="h-6 w-6" />
                                <span className="sr-only">Toggle navigation menu</span>
                            </Button>
                        </SheetTrigger>
                        <SheetContent side="left" className="flex flex-col w-[300px] p-4 rounded-r-2xl border-none">
                            <SheetTitle className="sr-only">Navigation Menu</SheetTitle>
                             <div className="flex h-16 items-center px-2 mb-4">
                                <Link to="/" className="flex items-center gap-3">
                                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground">
                                        <Command className="h-6 w-6" />
                                    </div>
                                    <span className="text-xl font-semibold tracking-tight">SWE AI Agent</span>
                                </Link>
                            </div>

                            {!isAdminMode && (
                                <Button
                                    className="w-full justify-start gap-3 rounded-2xl h-14 px-4 shadow-none bg-secondary/50 text-foreground mb-4"
                                    variant="ghost"
                                    onClick={() => navigate('/')}
                                >
                                    <Plus className="h-6 w-6" />
                                    <span className="font-medium">New Session</span>
                                </Button>
                            )}

                            <nav className="flex-1 overflow-y-auto -mx-2 px-2">
                                {isAdminMode ? (
                                    adminItems.map((item) => {
                                        const isActive = location.pathname === item.to;
                                        return (
                                            <Link
                                                key={item.to}
                                                to={item.to}
                                                className={`flex items-center gap-4 rounded-full px-4 py-3 mb-1 transition-all ${isActive
                                                    ? "bg-primary/10 text-primary font-medium"
                                                    : "text-muted-foreground hover:bg-muted"
                                                    }`}
                                            >
                                                <item.icon className="h-5 w-5" />
                                                {item.label}
                                            </Link>
                                        );
                                    })
                                ) : (
                                    <SidebarSessionList />
                                )}
                            </nav>
                        </SheetContent>
                    </Sheet>

                    {/* Page Title / Breadcrumb */}
                    <div className="w-full flex-1 flex flex-col justify-center">
                       {/* Simplified header logic - mostly rely on page content */}
                    </div>

                    <div className="flex items-center gap-3">
                        {/* AI Profile Selector */}
                        {!isAdminMode && (
                            <div className="hidden lg:block">
                                <AIProfileSelector />
                            </div>
                        )}

                        {/* Admin Mode Toggle Button */}
                        {user?.is_admin && (
                            <Button
                                variant={isAdminMode ? "default" : "secondary"}
                                size="sm"
                                onClick={() => {
                                    if (isAdminMode) {
                                        navigate("/");
                                    } else {
                                        navigate("/admin/git-providers");
                                    }
                                }}
                                className="hidden md:flex gap-2 items-center rounded-full px-4"
                            >
                                <Shield className="h-4 w-4" />
                                <span>{isAdminMode ? "Exit Admin" : "Admin"}</span>
                            </Button>
                        )}

                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                            className="rounded-full h-10 w-10"
                        >
                            <Sun className="h-[1.4rem] w-[1.4rem] scale-100 transition-all rotate-0 dark:-rotate-90 dark:scale-0 text-orange-500" />
                            <Moon className="absolute h-[1.4rem] w-[1.4rem] scale-0 transition-all rotate-90 dark:rotate-0 dark:scale-100 text-blue-400" />
                            <span className="sr-only">Toggle theme</span>
                        </Button>
                    </div>
                </header>
                <main className="flex flex-1 flex-col gap-4 p-4 lg:gap-8 lg:p-8 bg-background max-w-[1600px] w-full mx-auto">
                    <Outlet />
                </main>
            </div>
        </div>
    )
}
