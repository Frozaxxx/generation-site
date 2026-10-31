import { create } from "zustand";

import { errorMessage, requestJson } from "@/shared/api";

import type { Catalog, LLMStatus } from "./types";

interface CatalogState {
  catalog: Catalog | null;
  llm: LLMStatus | null;
  error: string | null;
  load: () => Promise<void>;
}

/** Справочник и настройки модели почти не меняются: грузим один раз за сессию. */
export const useCatalogStore = create<CatalogState>((set, get) => ({
  catalog: null,
  llm: null,
  error: null,
  load: async () => {
    if (get().catalog) return;
    try {
      const [catalog, llm] = await Promise.all([
        requestJson<Catalog>("/catalog"),
        requestJson<LLMStatus>("/llm/status"),
      ]);
      set({ catalog, llm, error: null });
    } catch (cause) {
      set({ error: errorMessage(cause) });
    }
  },
}));
