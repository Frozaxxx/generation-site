import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { JobProgress, useJob, type Job } from "@/entities/job";
import { COMPANY_STAGE_LABELS, GenerateCompanyForm } from "@/features/generate-company";
import { Button, Notice, Panel } from "@/shared/ui";

export function NewCompanyPage() {
  const [started, setStarted] = useState<Job | null>(null);
  const { job, error } = useJob(started);
  const navigate = useNavigate();

  useEffect(() => {
    if (job?.status === "succeeded" && job.result_id) {
      const timer = window.setTimeout(() => navigate(`/companies/${job.result_id}`), 800);
      return () => window.clearTimeout(timer);
    }
    return undefined;
  }, [job, navigate]);

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <header>
        <Link to="/companies" className="text-sm text-muted hover:text-ink">
          Компании
        </Link>
        <h1 className="mt-1 text-2xl font-semibold">Новая компания</h1>
        <p className="mt-1 text-sm text-muted">
          Любое поле можно оставить случайным. Город, адрес, телефон и состав команды выбираются из
          каталога, тексты пишет модель.
        </p>
      </header>

      {!job && (
        <Panel>
          <GenerateCompanyForm onStarted={setStarted} />
        </Panel>
      )}

      {job && (
        <Panel title="Генерация">
          <JobProgress job={job} labels={COMPANY_STAGE_LABELS} />
          {error && <div className="mt-4"><Notice tone="error">Нет связи с сервером: {error}</Notice></div>}
          {job.status === "failed" && job.error && (
            <div className="mt-4 space-y-3">
              <Notice tone="error">{job.error.message}</Notice>
              <Button onClick={() => setStarted(null)}>Изменить параметры</Button>
            </div>
          )}
          {job.status === "succeeded" && (
            <p className="mt-4 text-sm text-accent-strong">Компания создана, открываю карточку.</p>
          )}
        </Panel>
      )}
    </div>
  );
}
