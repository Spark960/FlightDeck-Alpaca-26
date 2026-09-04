import React from "react";
import { LucideIcon } from "lucide-react";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  isLoading?: boolean;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon,
  title,
  description,
  actionLabel,
  onAction,
  isLoading = false,
}) => {
  return (
    <div className="flex flex-col items-start justify-center py-10 px-5 gap-3 border-l-4 border-rule2">
      <div className="font-mono font-bold text-[11px] uppercase tracking-widest text-muted">
        // NO DATA
      </div>
      <div className="font-mono font-bold text-base text-paper">
        {(title ?? "").toUpperCase()}
      </div>
      {description && (
        <p className="text-[11px] font-mono text-muted leading-relaxed max-w-sm">
          {description}
        </p>
      )}
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          disabled={isLoading}
          className="mt-2 px-4 py-2 bg-y text-ink font-mono font-bold text-[11px] uppercase tracking-widest border-2 border-y hover:bg-ink hover:text-y disabled:opacity-40 cursor-pointer shadow-hard-sm"
        >
          {isLoading ? "LOADING..." : `> ${actionLabel.toUpperCase()}`}
        </button>
      )}
    </div>
  );
};
