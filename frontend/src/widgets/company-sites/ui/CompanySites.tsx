import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import type { Company } from "@/entities/company";
import { fetchCompanySites, SiteVersionRow, type SiteVersion } from "@/entities/site";
import { BuildSiteForm } from "@/features/build-site";
import { errorMessage } from "@/shared/api";
import { Notice } from "@/shared/ui";

function disabledReason(company: Company, dirty: boolean): string | null {
  if (dirty) return "Сохраните правки карточки.";
  if (company.status !== "approved") return "Сайт собирается из утверждённой карточки.";
  const withoutPhoto = company.profile.team.filter((person) => !person.photo).length;
  if (withoutPhoto) return `Создайте фото для ${withoutPhoto} человек из команды.`;
  return null;
}

/** Сборка сайта и список его версий для карточки компании. */
export function CompanySites({ company, dirty }: { company: Company; dirty: boolean }) {
  const [sites, setSites] = useState<SiteVersion[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const load = useCallback(() => {
    fetchCompanySites(company.id)
      .then(setSites)
      .catch((cause) => setError(errorMessage(cause)));
  }, [company.id]);

  useEffect(load, [load, company.revision]);

  const onBuilt = useCallback(
    (siteId: string) => {
      load();
      navigate(`/sites/${siteId}`);
    },
    [load, navigate],
  );

  return (
    <div className="space-y-5">
      <BuildSiteForm
        companyId={company.id}
        disabledReason={disabledReason(company, dirty)}
        onBuilt={onBuilt}
      />
      {error && <Notice tone="error">{error}</Notice>}
      {sites && sites.length > 0 && (
        <div className="space-y-2 border-t border-line pt-4">
          <p className="text-sm font-medium">Версии сайта</p>
          {sites.map((site) => (
            <SiteVersionRow key={site.id} site={site} />
          ))}
        </div>
      )}
    </div>
  );
}
