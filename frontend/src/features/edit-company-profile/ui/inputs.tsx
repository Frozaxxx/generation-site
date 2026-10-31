import { Button, Field, TextArea, TextInput } from "@/shared/ui";

import type { ProfileDraft } from "../model/use-profile-draft";

interface BoundProps {
  form: ProfileDraft;
  path: string;
  label: string;
  value: string | number | null;
  hint?: string;
}

export function BoundText({ form, path, label, value, hint }: BoundProps) {
  const error = form.issueFor(path);
  return (
    <Field label={label} hint={hint} error={error}>
      <TextInput value={String(value ?? "")} invalid={Boolean(error)} onChange={(next) => form.set(path, next)} />
    </Field>
  );
}

export function BoundNumber({ form, path, label, value, hint }: BoundProps) {
  const error = form.issueFor(path);
  return (
    <Field label={label} hint={hint} error={error}>
      <TextInput
        type="number"
        value={String(value ?? "")}
        invalid={Boolean(error)}
        onChange={(next) => form.set(path, next === "" ? 0 : Number(next))}
      />
    </Field>
  );
}

export function BoundArea({ form, path, label, value, hint, rows }: BoundProps & { rows?: number }) {
  const error = form.issueFor(path);
  return (
    <Field label={label} hint={hint} error={error}>
      <TextArea value={String(value ?? "")} rows={rows} invalid={Boolean(error)} onChange={(next) => form.set(path, next)} />
    </Field>
  );
}

interface StringListProps {
  form: ProfileDraft;
  path: string;
  label: string;
  items: string[];
  addLabel: string;
}

/** Список строк: входные данные, ограничения, опыт. */
export function StringList({ form, path, label, items, addLabel }: StringListProps) {
  const error = form.issueFor(path);
  return (
    <div className="space-y-2">
      <p className="text-sm font-medium">{label}</p>
      {items.map((item, index) => (
        <div key={index} className="flex gap-2">
          <div className="flex-1">
            <TextInput value={item} onChange={(next) => form.set(`${path}[${index}]`, next)} />
          </div>
          <Button
            variant="ghost"
            aria-label="Удалить пункт"
            onClick={() => form.set(path, items.filter((_, i) => i !== index))}
          >
            Удалить
          </Button>
        </div>
      ))}
      {error && <p className="text-xs text-danger">{error}</p>}
      <Button variant="ghost" onClick={() => form.set(path, [...items, ""])}>
        + {addLabel}
      </Button>
    </div>
  );
}

interface TitledListProps {
  form: ProfileDraft;
  path: string;
  label: string;
  items: { title: string; description: string }[];
  addLabel: string;
  numbered?: boolean;
}

/** Список «заголовок + описание»: шаги процесса, преимущества. */
export function TitledList({ form, path, label, items, addLabel, numbered }: TitledListProps) {
  const error = form.issueFor(path);
  return (
    <div className="space-y-3">
      <p className="text-sm font-medium">{label}</p>
      {items.map((item, index) => (
        <div key={index} className="flex gap-3 rounded-md border border-line bg-sunken p-3">
          {numbered && <span className="pt-2 text-sm font-semibold text-muted">{index + 1}</span>}
          <div className="flex-1 space-y-2">
            <TextInput value={item.title} onChange={(next) => form.set(`${path}[${index}].title`, next)} />
            <TextArea
              rows={2}
              value={item.description}
              onChange={(next) => form.set(`${path}[${index}].description`, next)}
            />
          </div>
          <Button
            variant="ghost"
            aria-label="Удалить"
            onClick={() => form.set(path, items.filter((_, i) => i !== index))}
          >
            Удалить
          </Button>
        </div>
      ))}
      {error && <p className="text-xs text-danger">{error}</p>}
      <Button variant="ghost" onClick={() => form.set(path, [...items, { title: "", description: "" }])}>
        + {addLabel}
      </Button>
    </div>
  );
}
