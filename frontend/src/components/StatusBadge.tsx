import React from "react";
import { LucideIcon } from "lucide-react";

interface StatusBadgeProps {
  variant?: "ok" | "danger" | "warn" | "info" | "violet" | "neutral" | "cyan" | "yellow";
  size?: "sm" | "md";
  pulse?: boolean;
  children: React.ReactNode;
}

const variantMap: Record<string, string> = {
  ok:      "bg-pos text-ink border-pos",
  danger:  "bg-neg text-paper border-neg",
  warn:    "bg-warn text-ink border-warn",
  info:    "bg-ink text-info border-info",
  cyan:    "bg-ink text-info border-info",
  violet:  "bg-ink text-violet border-violet",
  neutral: "bg-slab text-muted border-rule2",
  yellow:  "bg-y text-ink border-y",
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  variant = "neutral",
  size = "md",
  pulse = false,
  children,
}) => {
  const base = size === "sm"
    ? "inline-flex items-center gap-1 px-1.5 py-px text-[9px] font-bold uppercase tracking-widest border-2"
    : "inline-flex items-center gap-1.5 px-2 py-0.5 text-[10px] font-bold uppercase tracking-widest border-2";

  return (
    <span className={`${base} ${variantMap[variant] ?? variantMap.neutral} font-mono`}>
      {pulse && (
        <span className={`blink ${size === "sm" ? "text-[8px]" : "text-[10px]"}`}>
          ■
        </span>
      )}
      {children}
    </span>
  );
};
