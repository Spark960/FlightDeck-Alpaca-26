type StateProps = {
  title: string;
  message?: string;
};

export function LoadingState({ title, message = "Loading…" }: StateProps) {
  return (
    <div className="state-view">
      <div className="spinner" aria-hidden />
      <h3>{title}</h3>
      <p>{message}</p>
    </div>
  );
}

export function EmptyState({ title, message }: StateProps) {
  return (
    <div className="state-view">
      <h3>{title}</h3>
      {message ? <p>{message}</p> : null}
    </div>
  );
}

export function ErrorState({ title, message }: StateProps) {
  return (
    <div className="state-view state-view--error">
      <h3>{title}</h3>
      {message ? <p>{message}</p> : null}
    </div>
  );
}
