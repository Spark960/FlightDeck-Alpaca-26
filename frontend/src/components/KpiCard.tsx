import React from "react";
import { LucideIcon } from "lucide-react";

interface KpiCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  delta?: string;
  deltaPositive?: boolean;
  icon?: LucideIcon;
  variant?: "default" | "positive" | "negative" | "warn" | "cyan" | "violet" | "yellow";
  loading?: boolean;
}

const valueColorClassMap: Record<string, string> = {
  default:  "text-paper",
  positive: "text-pos",
  negative: "text-neg",
  warn:     "text-warn",
  cyan:     "text-info",
  violet:   "text-violet",
  yellow:   "text-y",
};

const borderColorClassMap: Record<string, string> = {
  default:  "border-rule2",
  positive: "border-pos",
  negative: "border-neg",
  warn:     "border-warn",
  cyan:     "border-info",
  violet:   "border-violet",
  yellow:   "border-y",
};

export const KpiCard: React.FC<KpiCardProps> = ({
  label,
  value,
  subtitle,
  delta,
  deltaPositive,
  icon: Icon,
  variant = "default",
  loading = false,
}) => {
  const borderClass = borderColorClassMap[variant] ?? "border-rule2";
  const valueClass  = valueColorClassMap[variant]  ?? "text-paper";

  return (
    <div className={`bg-slab p-4 flex flex-col gap-2 border-[2px] ${borderClass}`}>
      <div className="flex items-start justify-between gap-2">
        <span className="text-[9px] font-bold uppercase tracking-widest text-muted font-mono">
          {label}
        </span>
        {Icon && <Icon className="w-3.5 h-3.5 text-rule2 shrink-0" />}
      </div>

      {loading ? (
        <div className="text-rule2 font-mono text-2xl font-bold">...</div>
      ) : (
        <div className={`font-mono font-bold text-2xl tabular-nums leading-none ${valueClass}`}>
          {value}
        </div>
      )}

      <div className="flex items-center justify-between gap-2 min-h-[14px]">
        {subtitle && (
          <span className="text-[9px] text-muted font-mono">{subtitle}</span>
        )}
        {delta && (
          <span className={`text-[10px] font-bold font-mono ml-auto ${deltaPositive ? "text-pos" : "text-neg"}`}>
            {delta}
          </span>
        )}
      </div>
    </div>
  );
};
