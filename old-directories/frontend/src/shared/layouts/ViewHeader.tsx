import type { ColorScheme } from "@/shared/hooks/useColorScheme";

interface ViewHeaderProps {
  icon: React.ReactNode;
  iconGradient: string;
  title: React.ReactNode; // Changed from string to ReactNode to accept components
  subtitle: string;
  scheme: ColorScheme;
  rightContent?: React.ReactNode;
}

export function ViewHeader({
  icon,
  iconGradient,
  title,
  subtitle,
  scheme,
  rightContent,
}: ViewHeaderProps) {
  return (
    <div className="flex-shrink-0 border-b border-slate-200/70 bg-white/50 px-6 py-3 backdrop-blur dark:border-slate-800/70 dark:bg-slate-900/50 transition-colors duration-300">
      <div className="flex items-center justify-between gap-4">
        {/* Left side - Icon and Title */}
        <div className="flex items-center gap-2.5 min-w-0 flex-1">
          <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center transition-all duration-300 hover:scale-105">
            {icon}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-base font-bold text-slate-900 dark:text-slate-100 transition-colors duration-300 min-w-0">
              {title}
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400 truncate transition-colors duration-300">
              {subtitle}
            </p>
          </div>
        </div>

        {/* Right side - Controls */}
        {rightContent && (
          <div className="flex items-center gap-3 flex-shrink-0">
            {rightContent}
          </div>
        )}
      </div>
    </div>
  );
}
