import { useCallback, useEffect, useMemo, useState } from "react";

import { saveProfile, type Company, type CompanyProfile, type Issue } from "@/entities/company";
import { ApiError, errorMessage } from "@/shared/api";

import { setIn } from "../lib/path";

interface SchemaError {
  path: string;
  message: string;
}

export interface ProfileDraft {
  draft: CompanyProfile;
  dirty: boolean;
  saving: boolean;
  error: string | null;
  set: (path: string, value: unknown) => void;
  reset: () => void;
  save: () => Promise<void>;
  /** Сообщение для поля: ошибка схемы при сохранении или проблема из проверок. */
  issueFor: (path: string) => string | undefined;
}

export function useProfileDraft(company: Company, onSaved: (company: Company) => void): ProfileDraft {
  const [draft, setDraft] = useState<CompanyProfile>(company.profile);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [schemaErrors, setSchemaErrors] = useState<SchemaError[]>([]);

  useEffect(() => {
    setDraft(company.profile);
  }, [company]);

  const dirty = useMemo(
    () => JSON.stringify(draft) !== JSON.stringify(company.profile),
    [draft, company.profile],
  );

  const set = useCallback((path: string, value: unknown) => {
    setDraft((current) => setIn(current, path, value));
  }, []);

  const reset = useCallback(() => {
    setDraft(company.profile);
    setSchemaErrors([]);
    setError(null);
  }, [company.profile]);

  const save = useCallback(async () => {
    setSaving(true);
    setError(null);
    try {
      const saved = await saveProfile(company.id, draft, company.revision);
      setSchemaErrors([]);
      onSaved(saved);
    } catch (cause) {
      setError(errorMessage(cause));
      if (cause instanceof ApiError && Array.isArray(cause.details)) {
        setSchemaErrors(cause.details as SchemaError[]);
      }
    } finally {
      setSaving(false);
    }
  }, [company.id, company.revision, draft, onSaved]);

  const issueFor = useCallback(
    (path: string) => {
      const schema = schemaErrors.find((item) => item.path === path);
      if (schema) return schema.message;
      if (dirty) return undefined; // проверки относятся к сохранённой ревизии
      const issue = company.issues.find(
        (item: Issue) => item.severity === "error" && item.path === path,
      );
      return issue?.message;
    },
    [schemaErrors, company.issues, dirty],
  );

  return { draft, dirty, saving, error, set, reset, save, issueFor };
}
