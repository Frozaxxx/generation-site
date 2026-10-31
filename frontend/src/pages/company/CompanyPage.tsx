import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  approveCompany,
  companyExportUrl,
  deleteCompany,
  fetchCompany,
  photoUrl,
  regeneratePhoto,
  reviewCompany,
  SCALE_LABELS,
  StatusBadge,
  type Company,
  type Person,
} from "@/entities/company";
import { ProfileSections, SECTIONS, useProfileDraft } from "@/features/edit-company-profile";
import { errorMessage } from "@/shared/api";
import { formatDateTime, formatUsd } from "@/shared/lib";
import { Button, Notice, Panel } from "@/shared/ui";
import { IssuesPanel } from "@/widgets/company-issues";

function PhotoSlot({
  company,
  person,
  onUpdated,
}: {
  company: Company;
  person: Person;
  onUpdated: (company: Company) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function regenerate() {
    setBusy(true);
    setError(null);
    try {
      onUpdated(await regeneratePhoto(company.id, person.id));
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-2">
      {person.photo ? (
        <img
          src={photoUrl(company.id, person.photo.file, company.updated_at)}
          alt={person.photo.alt}
          className="aspect-[4/5] w-full rounded-md object-cover"
        />
      ) : (
        <div className="flex aspect-[4/5] w-full items-center justify-center rounded-md border border-dashed border-line bg-sunken px-3 text-center text-xs text-muted">
          Фото нет, без него сайт не собрать
        </div>
      )}
      <Button variant="ghost" busy={busy} onClick={regenerate} className="w-full">
        {person.photo ? "Новое фото" : "Создать фото"}
      </Button>
      {error && <p className="text-xs text-danger">{error}</p>}
    </div>
  );
}

function GenerationInfoList({ company }: { company: Company }) {
  const info = company.generation;
  if (!info) return null;
  const concept = Object.entries(info.concept).filter(([key]) => key !== "фон фото");
  return (
    <div className="space-y-3 text-sm">
      <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1">
        <dt className="text-muted">Модель</dt>
        <dd className="break-all">{info.model}</dd>
        <dt className="text-muted">Стоимость</dt>
        <dd>{formatUsd(info.cost_usd)}</dd>
        <dt className="text-muted">Запросов</dt>
        <dd>{info.requests}</dd>
        <dt className="text-muted">Время</dt>
        <dd>{Math.round(info.duration_seconds)} с</dd>
        <dt className="text-muted">Масштаб</dt>
        <dd>{SCALE_LABELS[company.params.scale]}</dd>
      </dl>
      {concept.length > 0 && (
        <details className="group">
          <summary className="cursor-pointer text-muted hover:text-ink">Концепт генерации</summary>
          <dl className="mt-2 space-y-2">
            {concept.map(([key, value]) => (
              <div key={key}>
                <dt className="text-xs text-muted">{key}</dt>
                <dd className="leading-snug">{value}</dd>
              </div>
            ))}
          </dl>
        </details>
      )}
      {info.warnings.length > 0 && (
        <ul className="space-y-1 text-xs text-warn">
          {info.warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function CompanyEditor({ company, onUpdated }: { company: Company; onUpdated: (c: Company) => void }) {
  const form = useProfileDraft(company, onUpdated);
  const navigate = useNavigate();
  const [action, setAction] = useState<"approve" | "review" | "delete" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const errors = company.issues.filter((issue) => issue.severity === "error").length;

  async function run(kind: "approve" | "review" | "delete") {
    if (kind === "delete" && !window.confirm(`Удалить ${company.profile.brand.name} вместе с фото?`)) {
      return;
    }
    setAction(kind);
    setError(null);
    try {
      if (kind === "approve") onUpdated(await approveCompany(company.id));
      if (kind === "review") onUpdated(await reviewCompany(company.id));
      if (kind === "delete") {
        await deleteCompany(company.id);
        navigate("/companies");
      }
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setAction(null);
    }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 pb-24">
      <header className="space-y-3">
        <Link to="/companies" className="text-sm text-muted hover:text-ink">
          Компании
        </Link>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold">{company.profile.brand.name}</h1>
            <p className="mt-1 text-sm text-muted">
              {company.profile.brand.legal_name}, {company.profile.contacts.address.city}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <a href={companyExportUrl(company.id)} download>
              <Button>Скачать JSON</Button>
            </a>
            <Button
              busy={action === "review"}
              disabled={form.dirty}
              onClick={() => run("review")}
              title="Платный запрос к модели"
            >
              Проверить смысл
            </Button>
          </div>
        </div>
      </header>

      {error && <Notice tone="error">{error}</Notice>}

      <div className="grid gap-6 lg:grid-cols-[1fr_20rem]">
        <ProfileSections
          form={form}
          photoSlot={(person) => <PhotoSlot company={company} person={person} onUpdated={onUpdated} />}
        />

        <aside className="space-y-5 lg:sticky lg:top-6 lg:self-start">
          <Panel>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <StatusBadge status={company.status} />
                <span className="text-xs text-muted">ревизия {company.revision}</span>
              </div>
              {company.status === "approved" ? (
                <p className="text-sm text-muted">
                  Утверждена {formatDateTime(company.approved_at)}. Любая правка вернёт карточку в
                  черновик, уже собранные сайты не изменятся.
                </p>
              ) : (
                <Button
                  variant="primary"
                  className="w-full"
                  busy={action === "approve"}
                  disabled={form.dirty || errors > 0}
                  onClick={() => run("approve")}
                >
                  Утвердить карточку
                </Button>
              )}
              {company.status !== "approved" && errors > 0 && !form.dirty && (
                <p className="text-xs text-muted">Сначала исправьте ошибки проверки.</p>
              )}
            </div>
          </Panel>

          <Panel title="Проверки">
            <IssuesPanel issues={company.issues} stale={form.dirty} />
          </Panel>

          <nav className="hidden rounded-lg border border-line bg-surface p-2 lg:block">
            {SECTIONS.map((section) => (
              <a key={section.id} href={`#${section.id}`} className="block rounded px-3 py-1.5 text-sm text-muted hover:bg-sunken hover:text-ink">
                {section.title}
              </a>
            ))}
          </nav>

          <Panel title="Генерация">
            <GenerationInfoList company={company} />
          </Panel>

          <Button variant="danger" className="w-full" busy={action === "delete"} onClick={() => run("delete")}>
            Удалить компанию
          </Button>
        </aside>
      </div>

      {form.dirty && (
        <div className="fixed inset-x-0 bottom-0 z-10 border-t border-line bg-surface/95 backdrop-blur">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-8">
            <p className="text-sm">
              Несохранённые правки. После сохранения ревизия станет {company.revision + 1}, карточка
              вернётся в черновик.
            </p>
            <div className="flex gap-2">
              <Button variant="ghost" onClick={form.reset}>
                Отменить
              </Button>
              <Button variant="primary" busy={form.saving} onClick={form.save}>
                Сохранить
              </Button>
            </div>
          </div>
          {form.error && <p className="mx-auto max-w-6xl px-4 pb-3 text-sm text-danger sm:px-8">{form.error}</p>}
        </div>
      )}
    </div>
  );
}

export function CompanyPage() {
  const { companyId = "" } = useParams();
  const [company, setCompany] = useState<Company | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCompany(companyId)
      .then(setCompany)
      .catch((cause) => setError(errorMessage(cause)));
  }, [companyId]);

  const onUpdated = useCallback((next: Company) => setCompany(next), []);

  if (error) return <Notice tone="error">{error}</Notice>;
  if (!company) return <p className="text-sm text-muted">Загружаю карточку…</p>;
  return <CompanyEditor company={company} onUpdated={onUpdated} />;
}
