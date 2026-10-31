import type { ReactNode } from "react";

interface PanelProps {
  title?: string;
  actions?: ReactNode;
  id?: string;
  children: ReactNode;
}

export function Panel({ title, actions, id, children }: PanelProps) {
  return (
    <section id={id} className="scroll-mt-6 rounded-lg border border-line bg-surface">
      {title && (
        <header className="flex items-center justify-between gap-3 border-b border-line px-5 py-3">
          <h2 className="text-base font-semibold">{title}</h2>
          {actions}
        </header>
      )}
      <div className="p-5">{children}</div>
    </section>
  );
}
