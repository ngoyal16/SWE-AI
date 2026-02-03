import {
    Settings,
    LogOut,
    Command,
    Moon,
    Sun,
    Menu,
    Shield,
    GitBranch,
    Cpu
} from "lucide-react"
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom"
import { useTheme } from "@/components/theme-provider"
import { useAuth } from "@/context/auth-context"
import { useHeaderContext } from "@/context/page-header-context"
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
    const { title, description } = useHeaderContext()
    const isAdminMode = location.pathname.startsWith("/admin")

    // Admin menu items
    const adminItems = [
        { to: "/admin/git-providers", icon: GitBranch, label: "Git Providers" },
        { to: "/admin/ai-profiles", icon: Cpu, label: "AI Settings" },
    ]

    const NavLink = ({ item, isActive, className = "" }: { item: typeof adminItems[0], isActive: boolean, className?: string }) => (
        <Link
            to={item.to}
            className={`flex items-center gap-3 rounded-lg px-3 py-2 transition-all duration-200 group ${isActive
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-muted-foreground hover:text-primary hover:bg-muted"
                } ${className}`}
        >
            <item.icon className={`h-4 w-4 shrink-0 transition-transform duration-200 ${isActive ? "scale-110" : "group-hover:scale-110"}`} />
            <span>{item.label}</span>
        </Link>
    )

    return (
        <div className="bg-background min-h-screen w-full md:grid md:grid-cols-[220px_1fr] lg:grid-cols-[260px_1fr]">
            <div className="bg-muted/40 hidden border-r md:block">
                <div className="flex h-full max-h-screen flex-col gap-2">
                    <div className="flex h-16 items-center border-b px-6 lg:h-[72px]">
                        <Link to="/" className="flex items-center gap-2.5 transition-opacity hover:opacity-80">
                            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-md shadow-primary/20">
                                <Command className="h-5 w-5" />
                            </div>
                            <span className="text-lg font-bold tracking-tight">SWE Agent</span>
                        </Link>
                    </div>
                    <div className="flex-1 overflow-auto py-2">
                        {isAdminMode ? (
                            <nav className="grid items-start px-2 text-sm font-medium lg:px-4 gap-1">
                                {adminItems.map((item) => {
                                    const isActive = location.pathname === item.to;
                                    return <NavLink key={item.to} item={item} isActive={isActive} />;
                                })}
                            </nav>
                        ) : (
                            <SidebarSessionList />
                        )}
                    </div>
                </div>
            </div>
            <div className="flex flex-col">
                <header className="bg-muted/40 flex h-14 items-center gap-4 border-b px-4 lg:h-[60px] lg:px-6">
                    <Sheet>
                        <SheetTrigger asChild>
                            <Button
                                variant="outline"
                                size="icon"
                                className="shrink-0 md:hidden"
                            >
                                <Menu className="h-5 w-5" />
                                <span className="sr-only">Toggle navigation menu</span>
                            </Button>
                        </SheetTrigger>
                        <SheetContent side="left" className="flex flex-col">
                            <SheetTitle className="sr-only">Navigation Menu</SheetTitle>
                            <nav className="grid gap-2 text-lg font-medium pt-4">
                                <Link
                                    to="/"
                                    className="flex items-center gap-2 text-lg font-bold mb-4"
                                >
                                    <Command className="h-5 w-5" />
                                    <span>SWE Agent</span>
                                </Link>
                                {isAdminMode ? (
                                    adminItems.map((item) => {
                                        const isActive = location.pathname === item.to;
                                        return (
                                            <Link
                                                key={item.to}
                                                to={item.to}
                                                className={`flex items-center gap-4 rounded-xl px-3 py-3 transition-all ${isActive
                                                    ? "bg-primary text-primary-foreground"
                                                    : "text-muted-foreground hover:text-foreground"
                                                    }`}
                                            >
                                                <item.icon className="h-5 w-5" />
                                                {item.label}
                                            </Link>
                                        );
                                    })
                                ) : (
                                    <div className="h-full overflow-y-auto">
                                        <SidebarSessionList />
                                    </div>
                                )}
                            </nav>
                        </SheetContent>
                    </Sheet>
                    <div className="w-full flex-1 flex flex-col justify-center">
                        <div className="flex flex-col">
                            <h2 className="text-sm font-semibold tracking-tight leading-none">{title}</h2>
                            {description && (
                                <p className="text-[11px] text-muted-foreground line-clamp-1 mt-0.5">
                                    {description}
                                </p>
                            )}
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        {/* AI Profile Selector */}
                        {!isAdminMode && (
                            <div className="mr-2 hidden lg:block">
                                <AIProfileSelector />
                            </div>
                        )}

                        {/* Admin Mode Toggle Button */}
                        {user?.is_admin && (
                            <Button
                                variant={isAdminMode ? "default" : "outline"}
                                size="sm"
                                onClick={() => {
                                    if (isAdminMode) {
                                        navigate("/");
                                    } else {
                                        navigate("/admin/git-providers");
                                    }
                                }}
                                className="hidden md:flex gap-2 items-center"
                            >
                                <Shield className="h-4 w-4" />
                                <span>{isAdminMode ? "Exit Admin" : "Admin Mode"}</span>
                            </Button>
                        )}

                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                            className="rounded-full"
                        >
                            <Sun className="h-[1.2rem] w-[1.2rem] scale-100 transition-all rotate-0 dark:-rotate-90 dark:scale-0" />
                            <Moon className="absolute h-[1.2rem] w-[1.2rem] scale-0 transition-all rotate-90 dark:rotate-0 dark:scale-100" />
                            <span className="sr-only">Toggle theme</span>
                        </Button>

                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button variant="ghost" className="relative h-9 w-9 rounded-full">
                                    <Avatar className="h-9 w-9">
                                        <AvatarImage src={user?.avatar_url} alt={user?.name || user?.email} />
                                        <AvatarFallback className="bg-primary/10 text-primary">
                                            {(user?.name || user?.email || "U").charAt(0).toUpperCase()}
                                        </AvatarFallback>
                                    </Avatar>
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="w-56">
                                <DropdownMenuLabel className="font-normal">
                                    <div className="flex flex-col space-y-1">
                                        <p className="text-sm font-medium leading-none">{user?.name || "User"}</p>
                                        <p className="text-xs leading-none text-muted-foreground">
                                            {user?.email}
                                        </p>
                                    </div>
                                </DropdownMenuLabel>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem onClick={() => navigate("/settings")}>
                                    <Settings className="mr-2 h-4 w-4" />
                                    <span>Settings</span>
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem onClick={logout} className="text-destructive focus:text-destructive">
                                    <LogOut className="mr-2 h-4 w-4" />
                                    <span>Log out</span>
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>
                </header>
                <main className="flex flex-1 flex-col gap-4 p-4 lg:gap-6 lg:p-6 bg-background">
                    <Outlet />
                </main>
            </div>
        </div>
    )
}
