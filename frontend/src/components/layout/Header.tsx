import { Moon, Sun, Menu } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '../ui/button';
import { useTheme } from '../../hooks/useTheme';
import { useAppStore } from '../../stores/useAppStore';

export const Header: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const toggleSidebar = useAppStore((state) => state.toggleSidebar);

  return (
    <header className="sticky top-0 z-40 w-full bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-16 items-center px-4 gap-4">
        {/* Mobile menu button */}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleSidebar}
          className="lg:hidden"
          aria-label="Toggle menu"
        >
          <Menu className="h-5 w-5" />
        </Button>

        {/* Logo */}
        <Link to="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
          <img
            src={theme === 'light' ? '/B Dark.png' : '/B Light.png'}
            alt="BRAIN HR+"
            className="h-10 w-auto"
          />
          <span className="font-bold text-xl hidden sm:inline-block text-foreground">
            BRAIN HR<span className="text-primary">+</span>
          </span>
        </Link>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Theme toggle */}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
        >
          {theme === 'light' ? (
            <Moon className="h-5 w-5" />
          ) : (
            <Sun className="h-5 w-5" />
          )}
        </Button>
      </div>
    </header>
  );
};
