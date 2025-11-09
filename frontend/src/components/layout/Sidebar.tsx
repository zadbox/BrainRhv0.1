import { useMemo, useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  Building2,
  FolderOpen,
  FileText,
  Target,
  BarChart3,
  ChevronLeft,
  Home,
  ClipboardList,
  Search,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { useAppStore } from '../../stores/useAppStore';
import { Button } from '../ui/button';

interface NavItem {
  to: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
}

const navItems: NavItem[] = [
  { to: '/', icon: Home, label: 'Home' },
  { to: '/enterprises', icon: Building2, label: 'Companies' },
  { to: '/projects', icon: FolderOpen, label: 'Projects' },
  { to: '/cvs', icon: FileText, label: 'CV Library' },
  { to: '/interviews', icon: ClipboardList, label: 'Candidate Sheets' },
  { to: '/matching', icon: Target, label: 'Matching' },
  { to: '/results', icon: BarChart3, label: 'Results' },
];

export const Sidebar: React.FC = () => {
  const { sidebarCollapsed, toggleSidebar } = useAppStore();
  const [searchTerm, setSearchTerm] = useState('');

  const normalizedQuery = searchTerm.trim().toLowerCase();
  const filteredNavItems = useMemo(() => {
    if (!normalizedQuery) {
      return navItems;
    }

    return navItems.filter((item) =>
      item.label.toLowerCase().includes(normalizedQuery)
    );
  }, [normalizedQuery]);

  return (
    <>
      {/* Overlay for mobile */}
      {!sidebarCollapsed && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={toggleSidebar}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed left-0 top-0 z-50 h-full bg-background transition-all duration-300',
          'lg:fixed lg:top-16 lg:h-[calc(100vh-4rem)]',
          sidebarCollapsed ? '-translate-x-full lg:translate-x-0 lg:w-16' : 'w-64'
        )}
      >
        <div className="flex h-full flex-col">
          {/* Toggle button (desktop only) */}
          <div className="hidden lg:flex justify-end p-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleSidebar}
              aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              <ChevronLeft
                className={cn(
                  'h-5 w-5 transition-transform',
                  sidebarCollapsed && 'rotate-180'
                )}
              />
            </Button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto p-4 space-y-3">
            {!sidebarCollapsed && (
              <div className="relative">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="search"
                  value={searchTerm}
                  onChange={(event) => setSearchTerm(event.target.value)}
                  placeholder="Search..."
                  className="w-full rounded-md bg-muted/30 px-9 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                />
              </div>
            )}

            <div className="space-y-2">
              {filteredNavItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center gap-3 rounded-md px-4 py-2 transition-colors text-sm font-medium',
                      'hover:bg-accent hover:text-foreground',
                      'focus-visible:outline-none',
                      isActive
                        ? 'bg-accent text-foreground'
                        : 'text-muted-foreground',
                      sidebarCollapsed && 'justify-center'
                    )
                  }
                  title={sidebarCollapsed ? item.label : undefined}
                >
                  <item.icon className={cn('h-5 w-5 flex-shrink-0')} />
                  {!sidebarCollapsed && <span>{item.label}</span>}
                </NavLink>
              ))}
              {filteredNavItems.length === 0 && !sidebarCollapsed && (
                <p className="rounded-md bg-muted/20 px-4 py-2 text-xs text-muted-foreground">
                  No results found
                </p>
              )}
            </div>
          </nav>
        </div>
      </aside>
    </>
  );
};
