import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { fetchSites, LANGUAGE_LABELS, sitePreviewUrl, type SiteVersion } from "@/entities/site";
import { errorMessage } from "@/shared/api";
import { formatDateTime } from "@/shared/lib";
import { Badge, Button, Notice } from "@/shared/ui";

export function SitesPage() {
  const [sites, setSites] = useState<SiteVersion[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSites()
      .then(setSites)
      .catch((cause) => setError(errorMessage(cause)));
  }, []);

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Сайты</h1>
        <p className="mt-1 text-sm text-muted">
          Собранные версии сайтов. Новый сайт собирается в карточке утверждённой компании, в блоке
          «Сайт» справа.
        </p>
      </header>

      {error && <Notice tone="error">{error}</Notice>}

      {sites && sites.length === 0 && (
        <div className="rounded-lg border border-dashed border-line bg-surface px-6 py-12 text-center">
          <p className="font-medium">Сайтов пока нет</p>
          <p className="mx-auto mt-1 max-w-md text-sm text-muted">
            Откройте компанию, утвердите карточку и нажмите «Собрать сайт» в правой колонке.
            Готовая версия появится здесь и в карточке.
          </p>
          <Link to="/companies" className="mt-4 inline-block">
            <Button>К компаниям</Button>
          </Link>
        </div>
      )}

      {sites && sites.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-line bg-surface">
          <table className="w-full min-w-[46rem] text-left text-sm">
            <thead className="border-b border-line text-xs text-muted">
              <tr>
                <th className="px-4 py-3 font-medium">Компания</th>
                <th className="px-4 py-3 font-medium">Версия</th>
                <th className="px-4 py-3 font-medium">Оформление</th>
                <th className="px-4 py-3 font-medium">Статус</th>
                <th className="px-4 py-3 font-medium">Собран</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {sites.map((site) => (
                <tr key={site.id} className="border-b border-line last:border-0">
                  <td className="px-4 py-3">
                    <Link to={`/companies/${site.company_id}`} className="font-medium hover:text-accent">
                      {site.brand_name}
                    </Link>
                    <p className="text-xs text-muted">{site.domain}</p>
                  </td>
                  <td className="px-4 py-3">
                    {site.number}, {LANGUAGE_LABELS[site.language].toLowerCase()}
                    {site.stale && <p className="text-xs text-warn">карточка изменилась</p>}
                  </td>
                  <td className="px-4 py-3 text-muted">{site.theme}</td>
                  <td className="px-4 py-3">
                    {site.status === "ready" ? (
                      <Badge tone="accent">Готов</Badge>
                    ) : (
                      <Badge tone="danger">Ошибки</Badge>
                    )}
                  </td>
                  <td className="px-4 py-3 text-muted">{formatDateTime(site.created_at)}</td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-2">
                      <a href={sitePreviewUrl(site.id)} target="_blank" rel="noreferrer">
                        <Button variant="ghost">Предпросмотр</Button>
                      </a>
                      <Link to={`/sites/${site.id}`}>
                        <Button>Открыть</Button>
                      </Link>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
