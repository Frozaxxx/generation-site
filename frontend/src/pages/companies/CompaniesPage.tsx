import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  fetchCompanies,
  SCALE_LABELS,
  StatusBadge,
  type CompanyListItem,
  type CompanyStatus,
} from "@/entities/company";
import { useCatalogStore } from "@/entities/catalog";
import { errorMessage } from "@/shared/api";
import { formatDateTime } from "@/shared/lib";
import { Button, Notice, Select, TextInput } from "@/shared/ui";

export function CompaniesPage() {
  const [items, setItems] = useState<CompanyListItem[] | null>(null);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState<string | null>(null);
  const { catalog, load } = useCatalogStore();

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    const timer = window.setTimeout(async () => {
      try {
        const page = await fetchCompanies({
          search: search.trim() || undefined,
          status: (status || undefined) as CompanyStatus | undefined,
        });
        setItems(page.items);
        setTotal(page.total);
        setError(null);
      } catch (cause) {
        setError(errorMessage(cause));
      }
    }, 250);
    return () => window.clearTimeout(timer);
  }, [search, status]);

  const serviceLabel = (key: string) =>
    Object.values(catalog?.service_types ?? {})
      .flat()
      .find((item) => item.key === key)?.label ?? key;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Компании</h1>
          <p className="mt-1 text-sm text-muted">
            Карточки компаний. Утверждённая карточка становится источником фактов для сайта.
          </p>
        </div>
        <Link to="/companies/new">
          <Button variant="primary">Новая компания</Button>
        </Link>
      </header>

      <div className="flex flex-wrap gap-3">
        <div className="w-full sm:w-72">
          <TextInput value={search} onChange={setSearch} placeholder="Поиск по бренду" />
        </div>
        <div className="w-48">
          <Select
            value={status}
            onChange={setStatus}
            options={[
              { value: "", label: "Все статусы" },
              { value: "draft", label: "Черновики" },
              { value: "approved", label: "Утверждённые" },
            ]}
          />
        </div>
      </div>

      {error && <Notice tone="error">{error}</Notice>}

      {items && items.length === 0 && !error && (
        <div className="rounded-lg border border-dashed border-line bg-surface px-6 py-12 text-center">
          <p className="font-medium">{search || status ? "Ничего не найдено" : "Компаний пока нет"}</p>
          <p className="mt-1 text-sm text-muted">
            Сгенерируйте первую: параметры можно задать или оставить случайными.
          </p>
        </div>
      )}

      {items && items.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-line bg-surface">
          <table className="w-full min-w-[46rem] text-left text-sm">
            <thead className="border-b border-line text-xs text-muted">
              <tr>
                <th className="px-4 py-3 font-medium">Компания</th>
                <th className="px-4 py-3 font-medium">Город</th>
                <th className="px-4 py-3 font-medium">Сервис</th>
                <th className="px-4 py-3 font-medium">Масштаб</th>
                <th className="px-4 py-3 font-medium">Статус</th>
                <th className="px-4 py-3 text-right font-medium">Изменена</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-b border-line last:border-0 hover:bg-sunken">
                  <td className="px-4 py-3">
                    <Link to={`/companies/${item.id}`} className="font-medium hover:text-accent">
                      {item.brand_name}
                    </Link>
                    <p className="text-xs text-muted">{item.legal_name}</p>
                  </td>
                  <td className="px-4 py-3">{item.city}</td>
                  <td className="px-4 py-3 text-muted">{serviceLabel(item.service_type)}</td>
                  <td className="px-4 py-3">{SCALE_LABELS[item.scale]}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={item.status} />
                    <span className="ml-2 text-xs text-faint">ревизия {item.revision}</span>
                  </td>
                  <td className="px-4 py-3 text-right text-muted">{formatDateTime(item.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="border-t border-line px-4 py-2 text-xs text-muted">Всего: {total}</p>
        </div>
      )}
    </div>
  );
}
