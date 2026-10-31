import { useEffect, useState } from "react";

import { JobProgress, useJob, type Job } from "@/entities/job";
import { buildSite, fetchThemes, type SiteLanguage, type SiteTheme } from "@/entities/site";
import { errorMessage } from "@/shared/api";
import { Button, Notice } from "@/shared/ui";

import { SITE_STAGE_LABELS } from "../config/stages";

interface BuildSiteFormProps {
  companyId: string;
  disabledReason: string | null;
  onBuilt: (siteId: string) => void;
}

export function BuildSiteForm({ companyId, disabledReason, onBuilt }: BuildSiteFormProps) {
  const [themes, setThemes] = useState<SiteTheme[]>([]);
  const [language, setLanguage] = useState<SiteLanguage>("ru");
  const [theme, setTheme] = useState("kontor");
  const [accent, setAccent] = useState<string | null>(null);
  const [reuse, setReuse] = useState(true);
  const [started, setStarted] = useState<Job | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { job } = useJob(started);

  useEffect(() => {
    fetchThemes()
      .then(setThemes)
      .catch((cause) => setError(errorMessage(cause)));
  }, []);

  useEffect(() => {
    if (job?.status === "succeeded" && job.result_id) {
      onBuilt(job.result_id);
      setStarted(null);
    }
  }, [job, onBuilt]);

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      setStarted(
        await buildSite(companyId, { language, theme, accent, reuse_texts: reuse, model: null }),
      );
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  }

  if (job && job.status !== "succeeded") {
    return (
      <div className="space-y-3">
        <JobProgress job={job} labels={SITE_STAGE_LABELS} />
        {job.status === "failed" && job.error && (
          <>
            <Notice tone="error">{job.error.message}</Notice>
            <Button onClick={() => setStarted(null)}>Назад к настройкам</Button>
          </>
        )}
      </div>
    );
  }

  const current = themes.find((item) => item.key === theme);

  return (
    <div className="space-y-4">
      <div className="space-y-1.5">
        <p className="text-sm font-medium">Язык</p>
        <div className="grid grid-cols-2 gap-2">
          {(["ru", "de"] as const).map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => setLanguage(value)}
              className={`rounded-md border px-3 py-2 text-sm ${
                language === value ? "border-accent bg-accent-soft font-medium" : "border-line"
              }`}
            >
              {value === "ru" ? "Русский" : "Немецкий"}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-1.5">
        <p className="text-sm font-medium">Оформление</p>
        <div className="grid grid-cols-2 gap-2">
          {themes.map((item) => (
            <button
              key={item.key}
              type="button"
              onClick={() => setTheme(item.key)}
              title={item.description}
              className={`flex items-center gap-2 rounded-md border px-2.5 py-2 text-left text-sm ${
                theme === item.key ? "border-accent bg-accent-soft font-medium" : "border-line"
              }`}
            >
              <span
                className="flex size-6 shrink-0 items-center justify-center rounded border border-line"
                style={{ background: item.background }}
              >
                <span className="size-3 rounded-sm" style={{ background: accent ?? item.accent }} />
              </span>
              {item.name}
            </button>
          ))}
        </div>
        {current && <p className="text-xs text-muted">{current.description}</p>}
      </div>

      <label className="flex items-center justify-between gap-3 text-sm">
        <span>Свой акцентный цвет</span>
        <span className="flex items-center gap-2">
          <input
            type="color"
            value={accent ?? current?.accent ?? "#2f5d8a"}
            onChange={(event) => setAccent(event.target.value)}
            className="h-8 w-10 cursor-pointer rounded border border-line bg-surface"
          />
          {accent && (
            <button type="button" className="text-xs text-muted hover:text-ink" onClick={() => setAccent(null)}>
              Сбросить
            </button>
          )}
        </span>
      </label>

      <label className="flex items-start gap-2 text-sm">
        <input
          type="checkbox"
          checked={reuse}
          onChange={(event) => setReuse(event.target.checked)}
          className="mt-0.5 size-4 accent-[var(--color-accent)]"
        />
        <span>
          Взять тексты прошлой версии
          <span className="block text-xs text-muted">
            Если сайт этой ревизии на этом языке уже собирали, тексты возьмутся бесплатно, а
            поменяется только оформление
          </span>
        </span>
      </label>

      {error && <Notice tone="error">{error}</Notice>}
      {disabledReason && <p className="text-xs text-muted">{disabledReason}</p>}

      <Button
        variant="primary"
        className="w-full"
        busy={busy}
        disabled={Boolean(disabledReason)}
        onClick={submit}
      >
        Собрать сайт
      </Button>
    </div>
  );
}
