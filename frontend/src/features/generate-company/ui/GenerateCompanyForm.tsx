import { useEffect, useMemo, useState, type FormEvent } from "react";

import { useCatalogStore } from "@/entities/catalog";
import { generateCompany, type CompanyScale } from "@/entities/company";
import type { Job } from "@/entities/job";
import { errorMessage } from "@/shared/api";
import { Button, Field, Notice, Select, TextInput } from "@/shared/ui";

const RANDOM = "";
const CUSTOM = "custom";

interface GenerateCompanyFormProps {
  onStarted: (job: Job) => void;
}

function priceHint(prompt: number | null, completion: number | null): string {
  if (prompt === null || completion === null) return "";
  return ` · $${prompt}/$${completion} за 1M`;
}

export function GenerateCompanyForm({ onStarted }: GenerateCompanyFormProps) {
  const { catalog, llm, error: catalogError, load } = useCatalogStore();

  const [brand, setBrand] = useState("");
  const [country, setCountry] = useState(RANDOM);
  const [direction, setDirection] = useState(RANDOM);
  const [serviceType, setServiceType] = useState(RANDOM);
  const [customDirection, setCustomDirection] = useState("");
  const [customService, setCustomService] = useState("");
  const [scale, setScale] = useState(RANDOM);
  const [model, setModel] = useState(RANDOM);
  const [withPhotos, setWithPhotos] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void load();
  }, [load]);

  const serviceTypes = useMemo(() => {
    if (!catalog) return [];
    if (direction === CUSTOM) return [];
    const keys = direction ? [direction] : Object.keys(catalog.service_types);
    return keys.flatMap((key) => catalog.service_types[key] ?? []);
  }, [catalog, direction]);

  if (catalogError) return <Notice tone="error">Справочник не загрузился: {catalogError}</Notice>;
  if (!catalog || !llm) return <p className="text-sm text-muted">Загружаю справочник…</p>;

  const random = (label: string) => ({ value: RANDOM, label: `Случайно${label}` });
  const custom = { value: CUSTOM, label: "Свой вариант…" };
  const directionIsCustom = direction === CUSTOM;
  const serviceIsCustom = directionIsCustom || serviceType === CUSTOM;
  const prices = new Map(llm.models.map((item) => [item.id, item]));

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const job = await generateCompany({
        brand_name: brand.trim() || null,
        country: country || null,
        direction: directionIsCustom ? null : direction || null,
        service_type: serviceIsCustom ? null : serviceType || null,
        custom_direction: directionIsCustom ? customDirection.trim() || null : null,
        custom_service: serviceIsCustom ? customService.trim() || null : null,
        scale: (scale || null) as CompanyScale | null,
        model: model || null,
        with_photos: withPhotos,
        budget_usd: null,
      });
      onStarted(job);
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-5">
      {!llm.configured && (
        <Notice tone="error">
          Не задан OPENROUTER_API_KEY в backend/.env. Генерация недоступна, библиотека работает.
        </Notice>
      )}

      <Field label="Название бренда" hint="Оставьте пустым, и модель придумает название сама">
        <TextInput value={brand} onChange={setBrand} placeholder="Например, Nordlicht Research" />
      </Field>

      <div className="grid gap-5 sm:grid-cols-2">
        <Field label="Страна">
          <Select
            value={country}
            onChange={setCountry}
            options={[
              random(""),
              ...catalog.countries.map((item) => ({ value: item.key, label: item.label })),
            ]}
          />
        </Field>
        <Field label="Масштаб">
          <Select
            value={scale}
            onChange={setScale}
            options={[
              random(""),
              ...catalog.scales.map((item) => ({
                value: item.key,
                label: `${item.label} (${item.description})`,
              })),
            ]}
          />
        </Field>
      </div>

      <Field label="Направление">
        <Select
          value={direction}
          onChange={(value) => {
            setDirection(value);
            setServiceType(RANDOM);
          }}
          options={[
            random(""),
            ...catalog.directions.map((item) => ({ value: item.key, label: item.label })),
            custom,
          ]}
        />
      </Field>

      {directionIsCustom && (
        <Field label="Своё направление" hint="Чем занимаются компании этого направления">
          <TextInput
            value={customDirection}
            onChange={setCustomDirection}
            placeholder="Например, ИИ для оценки рисков коммерческой недвижимости"
          />
        </Field>
      )}

      {!directionIsCustom && (
        <Field
          label="Тип B2B-сервиса"
          hint={serviceTypes.find((item) => item.key === serviceType)?.description ?? undefined}
        >
          <Select
            value={serviceType}
            onChange={setServiceType}
            options={[
              random(""),
              ...serviceTypes.map((item) => ({ value: item.key, label: item.label })),
              custom,
            ]}
          />
        </Field>
      )}

      {serviceIsCustom && (
        <Field
          label="Свой тип сервиса"
          hint="Что сервис делает для клиента. Если пусто, возьмём описание направления."
        >
          <TextInput
            value={customService}
            onChange={setCustomService}
            placeholder="Например, разбор отчётов о закупках государственных компаний"
          />
        </Field>
      )}

      <Field label="Модель OpenRouter" hint="Цены за 1M входных / выходных токенов">
        <Select
          value={model}
          onChange={setModel}
          options={[
            { value: RANDOM, label: `По умолчанию: ${catalog.default_model}` },
            ...catalog.models.map((item) => {
              const price = prices.get(item.key);
              return {
                value: item.key,
                label: `${item.label}${priceHint(price?.prompt_per_mtok ?? null, price?.completion_per_mtok ?? null)}`,
              };
            }),
          ]}
        />
      </Field>

      <label className="flex items-start gap-3 text-sm">
        <input
          type="checkbox"
          checked={withPhotos}
          onChange={(event) => setWithPhotos(event.target.checked)}
          className="mt-0.5 size-4 accent-[var(--color-accent)]"
        />
        <span>
          Фото команды
          <span className="block text-xs text-muted">
            {llm.image_model}, около $0.04 за фото. Без фото сайт собрать нельзя, но их можно
            создать позже в карточке.
          </span>
        </span>
      </label>

      {error && <Notice tone="error">{error}</Notice>}

      <div className="flex items-center gap-4">
        <Button
          type="submit"
          variant="primary"
          busy={busy}
          disabled={!llm.configured || (directionIsCustom && !customDirection.trim()) || (serviceType === CUSTOM && !customService.trim())}
        >
          Создать компанию
        </Button>
        <span className="text-xs text-muted">
          Лимит операции ${llm.operation_budget_usd.toFixed(2)}
        </span>
      </div>
    </form>
  );
}
