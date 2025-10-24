import clsx from 'clsx';
import { Sun, Moon } from 'lucide-react';
import type { ColorScheme } from '../../hooks/useColorScheme';

interface ThemeToggleButtonProps {
  scheme: ColorScheme;
  onToggle: (scheme: ColorScheme) => void;
}

export function ThemeToggleButton({ scheme, onToggle }: ThemeToggleButtonProps) {
  const handleToggle = () => {
    onToggle(scheme === 'dark' ? 'light' : 'dark');
  };

  return (
    <button
      onClick={handleToggle}
      className={clsx(
        'rounded-lg p-2 transition-all duration-200 ease-in-out',
        'hover:bg-slate-100 dark:hover:bg-slate-800',
        'text-slate-600 dark:text-slate-300',
        'transform hover:scale-110 active:scale-95',
        'hover:rotate-12'
      )}
      aria-label="Toggle theme"
      title="Cambiar tema"
    >
      {scheme === 'dark' ? (
        <Sun className="h-5 w-5 transition-transform duration-200 animate-in fade-in spin-in-12" />
      ) : (
        <Moon className="h-5 w-5 transition-transform duration-200 animate-in fade-in spin-in-12" />
      )}
    </button>
  );
}
