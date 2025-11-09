import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { Toaster } from '../ui/toaster';
import { useAppStore } from '../../stores/useAppStore';
import { cn } from '../../lib/utils';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const sidebarCollapsed = useAppStore((state) => state.sidebarCollapsed);

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <div className="flex pt-16">
        <Sidebar />
        <main
          className={cn(
            'flex-1 p-6 transition-all duration-300 w-full',
            sidebarCollapsed ? 'lg:pl-20' : 'lg:pl-[272px]'
          )}
        >
          {children}
        </main>
      </div>
      <Toaster />
    </div>
  );
};
