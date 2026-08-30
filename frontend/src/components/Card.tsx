import type { ReactNode } from "react";

type CardProps = {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
};

export function Card({ title, subtitle, action, children, className = "" }: CardProps) {
  return (
    <section className={`card ${className}`.trim()}>
      <header className="card__header">
        <div>
          <h2>{title}</h2>
          {subtitle ? <p className="card__subtitle">{subtitle}</p> : null}
        </div>
        {action}
      </header>
      <div className="card__body">{children}</div>
    </section>
  );
}
