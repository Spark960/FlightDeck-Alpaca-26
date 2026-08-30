type StatusBadgeProps = {
  label: string;
  tone?: "ok" | "warn" | "danger" | "neutral";
};

export function StatusBadge({ label, tone = "neutral" }: StatusBadgeProps) {
  return <span className={`badge badge--${tone}`}>{label}</span>;
}
