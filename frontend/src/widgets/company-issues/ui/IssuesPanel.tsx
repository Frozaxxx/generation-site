import { useState } from "react";

import { sectionLabel, sectionOf, type Issue } from "@/entities/company";

const LONG = 160;

function IssueItem({ issue }: { issue: Issue }) {
  const [open, setOpen] = useState(false);
  const long = issue.message.length > LONG;
  const text = open || !long ? issue.message : `${issue.message.slice(0, LONG).trimEnd()}…`;
  return (
    <li className="text-sm leading-snug">
      <a
        href={`#${sectionOf(issue.path)}`}
        className="font-medium text-ink underline decoration-line underline-offset-2 hover:decoration-ink"
      >
        {sectionLabel(issue.path)}
      </a>
      <span className="text-muted">: {text}</span>
      {long && (
        <button type="button" onClick={() => setOpen(!open)} className="ml-1 text-xs text-accent hover:underline">
          {open ? "Свернуть" : "Полностью"}
        </button>
      )}
    </li>
  );
}

interface IssuesPanelProps {
  issues: Issue[];
  stale: boolean;
}

/** Результаты проверок: ошибки блокируют утверждение, предупреждения - нет. */
export function IssuesPanel({ issues, stale }: IssuesPanelProps) {
  const errors = issues.filter((issue) => issue.severity === "error");
  const warnings = issues.filter((issue) => issue.severity === "warning");

  if (stale) {
    return <p className="text-sm text-muted">Есть несохранённые правки. Проверки обновятся после сохранения.</p>;
  }
  if (!issues.length) {
    return <p className="text-sm text-accent-strong">Проверки пройдены, замечаний нет.</p>;
  }

  return (
    <div className="space-y-4">
      {[
        { title: `Ошибки: ${errors.length}`, items: errors, tone: "text-danger" },
        { title: `Предупреждения: ${warnings.length}`, items: warnings, tone: "text-warn" },
      ]
        .filter((group) => group.items.length)
        .map((group) => (
          <div key={group.title} className="space-y-2">
            <p className={`text-sm font-semibold ${group.tone}`}>{group.title}</p>
            <ul className="space-y-2">
              {group.items.map((issue, index) => (
                <IssueItem key={`${issue.code}-${index}`} issue={issue} />
              ))}
            </ul>
          </div>
        ))}
    </div>
  );
}
