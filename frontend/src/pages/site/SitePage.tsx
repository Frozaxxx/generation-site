import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  deleteSite,
  fetchSite,
  LANGUAGE_LABELS,
  PAGE_LABELS,
  siteDownloadUrl,
  sitePreviewUrl,
  type SiteVersion,
} from "@/entities/site";
import { errorMessage } from "@/shared/api";
import { formatDateTime, formatUsd } from "@/shared/lib";
import { Badge, Button, Notice, Panel } from "@/shared/ui";

const WIDTHS = [
  { key: "desktop", label: "Компьютер", width: "100%" },
  { key: "mobile", label: "Телефон", width: "390px" },
] as const;

export function SitePage() {
  const { siteId = "" } = useParams();
  const [site, setSite] = useState<SiteVersion | null>(null);
  const [page, setPage] = useState("index.html");
  const [width, setWidth] = useState<(typeof WIDTHS)[number]["key"]>("desktop");
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchSite(siteId)
      .then(setSite)
      .catch((cause) => setError(errorMessage(cause)));
  }, [siteId]);

  if (error) return <Notice tone="error">{error}</Notice>;
  if (!site) return <p className="text-sm text-muted">Загружаю сайт…</p>;

  const errors = site.issues.filter((issue) => issue.severity === "error");
  const warnings = site.issues.filter((issue) => issue.severity === "warning");

  async function remove() {
    if (!site || !window.confirm(`Удалить версию ${site.number}?`)) return;
    try {
      await deleteSite(site.id);
      navigate(`/companies/${site.company_id}`);
    } catch (cause) {
      setError(errorMessage(cause));
    }
  }

  return (
    <div className="mx-auto max-w-7xl space-y-5">
      <header className="space-y-3">
        <Link to={`/companies/${site.company_id}`} className="text-sm text-muted hover:text-ink">
          {site.brand_name}
        </Link>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold">
              Сайт, версия {site.number}
            </h1>
            <p className="mt-1 text-sm text-muted">
              {LANGUAGE_LABELS[site.language]}, тема {site.theme}, из ревизии карточки{" "}
              {site.company_revision}, {formatDateTime(site.created_at)}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <a href={sitePreviewUrl(site.id, page)} target="_blank" rel="noreferrer">
              <Button>Открыть в новой вкладке</Button>
            </a>
            <a href={siteDownloadUrl(site.id)} download>
              <Button variant="primary">Скачать ZIP</Button>
            </a>
          </div>
        </div>
        {site.stale && (
          <Notice tone="info">
            Карточка компании изменилась после сборки. Эта версия показывает факты ревизии{" "}
            {site.company_revision}; чтобы применить правки, утвердите карточку и соберите новую
            версию.
          </Notice>
        )}
      </header>

      <div className="grid gap-5 xl:grid-cols-[1fr_18rem]">
        <section className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <nav className="flex flex-wrap gap-1" aria-label="Страницы сайта">
              {site.pages.map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => setPage(item)}
                  className={`rounded-md px-3 py-1.5 text-sm ${
                    page === item ? "bg-ink text-white" : "text-muted hover:bg-surface hover:text-ink"
                  }`}
                >
                  {PAGE_LABELS[item] ?? item}
                </button>
              ))}
            </nav>
            <div className="flex gap-1">
              {WIDTHS.map((item) => (
                <button
                  key={item.key}
                  type="button"
                  onClick={() => setWidth(item.key)}
                  className={`rounded-md px-2.5 py-1.5 text-xs ${
                    width === item.key ? "bg-surface font-medium text-ink shadow-sm" : "text-muted"
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>
          <div className="flex justify-center rounded-lg border border-line bg-sunken p-2">
            <iframe
              key={`${page}-${width}`}
              title={`Предпросмотр: ${PAGE_LABELS[page] ?? page}`}
              src={sitePreviewUrl(site.id, page)}
              className="h-[78vh] rounded border border-line bg-white"
              style={{ width: WIDTHS.find((item) => item.key === width)?.width }}
            />
          </div>
        </section>

        <aside className="space-y-5">
          <Panel title="Проверки сайта">
            {site.issues.length === 0 ? (
              <p className="text-sm text-accent-strong">
                Факты совпадают на всех страницах, метаданные, ссылки и разметка на месте.
              </p>
            ) : (
              <ul className="space-y-2 text-sm">
                {[...errors, ...warnings].map((issue, index) => (
                  <li key={`${issue.code}-${index}`}>
                    <Badge tone={issue.severity === "error" ? "danger" : "warn"}>{issue.path}</Badge>{" "}
                    <span className="text-muted">{issue.message}</span>
                  </li>
                ))}
              </ul>
            )}
          </Panel>
          <Panel title="Сборка">
            <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-sm">
              <dt className="text-muted">Домен</dt>
              <dd>{site.domain}</dd>
              <dt className="text-muted">Стоимость</dt>
              <dd>{formatUsd(site.cost_usd)}</dd>
              <dt className="text-muted">Запросов</dt>
              <dd>{site.requests}</dd>
              <dt className="text-muted">Тексты</dt>
              <dd>{site.reused_from ? "из прошлой версии" : "новые"}</dd>
            </dl>
          </Panel>
          <Button variant="danger" className="w-full" onClick={remove}>
            Удалить версию
          </Button>
        </aside>
      </div>
    </div>
  );
}
