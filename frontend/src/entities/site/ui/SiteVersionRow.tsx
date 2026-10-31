import { Link } from "react-router-dom";

import { formatDateTime } from "@/shared/lib";
import { Badge } from "@/shared/ui";

import { LANGUAGE_LABELS, type SiteVersion } from "../model/types";

export function SiteVersionRow({ site }: { site: SiteVersion }) {
  return (
    <Link
      to={`/sites/${site.id}`}
      className="block rounded-md border border-line px-3 py-2.5 hover:border-muted"
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-medium">
          Версия {site.number}, {LANGUAGE_LABELS[site.language].toLowerCase()}
        </span>
        {site.status === "ready" ? (
          <Badge tone="accent">Готов</Badge>
        ) : (
          <Badge tone="danger">Ошибки</Badge>
        )}
      </div>
      <p className="mt-1 text-xs text-muted">
        Тема {site.theme}, ревизия {site.company_revision}, {formatDateTime(site.created_at)}
      </p>
      {site.stale && (
        <p className="mt-1 text-xs text-warn">Карточка изменилась после сборки</p>
      )}
    </Link>
  );
}
