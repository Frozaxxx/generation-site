import type { ReactNode } from "react";

import { ROLE_LABELS, type Person } from "@/entities/company";
import { Button, Panel, TextArea, TextInput } from "@/shared/ui";

import type { ProfileDraft } from "../model/use-profile-draft";
import { BoundArea, BoundNumber, BoundText, StringList, TitledList } from "./inputs";

export const SECTIONS = [
  { id: "brand", title: "Бренд" },
  { id: "contacts", title: "Контакты" },
  { id: "history", title: "История" },
  { id: "audience", title: "Аудитория" },
  { id: "product", title: "Продукт" },
  { id: "team", title: "Команда" },
  { id: "faq", title: "FAQ" },
] as const;

interface SectionProps {
  form: ProfileDraft;
}

function BrandSection({ form }: SectionProps) {
  const brand = form.draft.brand;
  return (
    <Panel id="brand" title="Бренд">
      <div className="grid gap-4 sm:grid-cols-2">
        <BoundText form={form} path="brand.name" label="Бренд" value={brand.name} />
        <BoundText form={form} path="brand.legal_form" label="Правовая форма" value={brand.legal_form} />
        <BoundText
          form={form}
          path="brand.legal_name"
          label="Юридическое лицо"
          value={brand.legal_name}
          hint="Должно содержать бренд и заканчиваться правовой формой"
        />
        <BoundText form={form} path="brand.domain" label="Домен" value={brand.domain} />
      </div>
      <div className="mt-4">
        <BoundText form={form} path="brand.tagline" label="Слоган" value={brand.tagline} />
      </div>
    </Panel>
  );
}

function ContactsSection({ form }: SectionProps) {
  const contacts = form.draft.contacts;
  const address = contacts.address;
  return (
    <Panel id="contacts" title="Контакты">
      <div className="grid gap-4 sm:grid-cols-[1fr_8rem_8rem]">
        <BoundText form={form} path="contacts.address.street" label="Улица" value={address.street} />
        <BoundText form={form} path="contacts.address.house_number" label="Дом" value={address.house_number} />
        <BoundText form={form} path="contacts.address.postal_code" label="Индекс" value={address.postal_code} />
      </div>
      <div className="mt-4 grid gap-4 sm:grid-cols-3">
        <BoundText
          form={form}
          path="contacts.address.city"
          label="Город"
          value={address.city}
          hint="Телефон и индекс проверяются по городу"
        />
        <BoundText form={form} path="contacts.address.district" label="Район" value={address.district} />
        <BoundText form={form} path="contacts.address.state" label="Земля" value={address.state} />
      </div>
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <BoundText form={form} path="contacts.phone" label="Телефон (E.164)" value={contacts.phone} />
        <BoundText
          form={form}
          path="contacts.phone_display"
          label="Телефон на сайте"
          value={contacts.phone_display}
        />
        <BoundText form={form} path="contacts.email" label="Почта" value={contacts.email} />
        <BoundText form={form} path="contacts.office_hours" label="Часы работы" value={contacts.office_hours} />
      </div>
    </Panel>
  );
}

function HistorySection({ form }: SectionProps) {
  const history = form.draft.history;
  return (
    <Panel id="history" title="История">
      <div className="grid gap-4 sm:grid-cols-2">
        <BoundNumber form={form} path="history.founded_year" label="Год основания" value={history.founded_year} />
        <BoundNumber form={form} path="history.employees" label="Сотрудников" value={history.employees} />
      </div>
      <div className="mt-4 space-y-4">
        <BoundArea form={form} path="history.founding_story" label="История основания" value={history.founding_story} rows={7} />
        <BoundArea form={form} path="history.specialization" label="Специализация" value={history.specialization} rows={5} />
        <div className="space-y-3">
          <p className="text-sm font-medium">Этапы</p>
          {history.milestones.map((milestone, index) => {
            const path = `history.milestones[${index}]`;
            const error = form.issueFor(`${path}.year`);
            return (
              <div key={index} className="grid gap-2 rounded-md border border-line bg-sunken p-3 sm:grid-cols-[6rem_1fr]">
                <div>
                  <TextInput
                    type="number"
                    value={String(milestone.year)}
                    invalid={Boolean(error)}
                    onChange={(next) => form.set(`${path}.year`, Number(next))}
                  />
                  {error && <p className="mt-1 text-xs text-danger">{error}</p>}
                </div>
                <div className="space-y-2">
                  <TextInput value={milestone.title} onChange={(next) => form.set(`${path}.title`, next)} />
                  <TextArea rows={2} value={milestone.description} onChange={(next) => form.set(`${path}.description`, next)} />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </Panel>
  );
}

function AudienceSection({ form }: SectionProps) {
  const audience = form.draft.audience;
  return (
    <Panel id="audience" title="Аудитория">
      <div className="space-y-4">
        {audience.segments.map((segment, index) => (
          <div key={index} className="space-y-2 rounded-md border border-line bg-sunken p-3">
            <TextInput value={segment.name} onChange={(next) => form.set(`audience.segments[${index}].name`, next)} />
            <TextArea
              rows={2}
              value={segment.description}
              onChange={(next) => form.set(`audience.segments[${index}].description`, next)}
            />
          </div>
        ))}
        <BoundArea form={form} path="audience.client_problem" label="Проблема клиента" value={audience.client_problem} rows={5} />
      </div>
    </Panel>
  );
}

function ProductSection({ form }: SectionProps) {
  const product = form.draft.product;
  return (
    <Panel id="product" title="Продукт">
      <div className="space-y-5">
        <BoundText form={form} path="product.name" label="Название" value={product.name} />
        <BoundArea form={form} path="product.summary" label="Описание" value={product.summary} rows={6} />
        <StringList form={form} path="product.inputs" label="Входные данные" items={product.inputs} addLabel="Источник" />
        <TitledList form={form} path="product.process" label="Процесс работы" items={product.process} addLabel="Шаг" numbered />
        <StringList form={form} path="product.outputs" label="Результат" items={product.outputs} addLabel="Результат" />
        <StringList form={form} path="product.limitations" label="Ограничения" items={product.limitations} addLabel="Ограничение" />
        <TitledList form={form} path="product.benefits" label="Преимущества" items={product.benefits} addLabel="Преимущество" />
        <BoundArea form={form} path="product.delivery" label="Поставка" value={product.delivery} rows={3} />
      </div>
    </Panel>
  );
}

interface TeamSectionProps extends SectionProps {
  photoSlot: (person: Person) => ReactNode;
}

function TeamSection({ form, photoSlot }: TeamSectionProps) {
  return (
    <Panel id="team" title={`Команда (${form.draft.team.length})`}>
      <div className="space-y-6">
        {form.draft.team.map((person, index) => {
          const path = `team[${index}]`;
          return (
            <article key={person.id} className="grid gap-4 border-b border-line pb-6 last:border-0 last:pb-0 sm:grid-cols-[9rem_1fr]">
              <div>{photoSlot(person)}</div>
              <div className="space-y-3">
                <p className="text-xs text-muted">{ROLE_LABELS[person.role]}</p>
                <div className="grid gap-3 sm:grid-cols-[1fr_1fr_5rem]">
                  <BoundText form={form} path={`${path}.first_name`} label="Имя" value={person.first_name} />
                  <BoundText form={form} path={`${path}.last_name`} label="Фамилия" value={person.last_name} />
                  <BoundNumber form={form} path={`${path}.age`} label="Возраст" value={person.age} />
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <BoundText form={form} path={`${path}.position`} label="Должность" value={person.position} />
                  <BoundText form={form} path={`${path}.department`} label="Отдел" value={person.department} />
                </div>
                <BoundArea form={form} path={`${path}.bio`} label="Биография" value={person.bio} rows={4} />
                <StringList form={form} path={`${path}.experience`} label="Опыт" items={person.experience} addLabel="Место работы" />
                <BoundText form={form} path={`${path}.education`} label="Образование" value={person.education} />
              </div>
            </article>
          );
        })}
      </div>
    </Panel>
  );
}

function FaqSection({ form }: SectionProps) {
  const faq = form.draft.faq;
  const error = form.issueFor("faq");
  return (
    <Panel id="faq" title="FAQ">
      <div className="space-y-3">
        {faq.map((item, index) => (
          <div key={index} className="space-y-2 rounded-md border border-line bg-sunken p-3">
            <div className="flex gap-2">
              <div className="flex-1">
                <TextInput value={item.question} onChange={(next) => form.set(`faq[${index}].question`, next)} />
              </div>
              <Button variant="ghost" onClick={() => form.set("faq", faq.filter((_, i) => i !== index))}>
                Удалить
              </Button>
            </div>
            <TextArea rows={3} value={item.answer} onChange={(next) => form.set(`faq[${index}].answer`, next)} />
          </div>
        ))}
        {error && <p className="text-xs text-danger">{error}</p>}
        <Button variant="ghost" onClick={() => form.set("faq", [...faq, { question: "", answer: "" }])}>
          + Вопрос
        </Button>
      </div>
    </Panel>
  );
}

interface ProfileSectionsProps extends SectionProps {
  photoSlot: (person: Person) => ReactNode;
}

export function ProfileSections({ form, photoSlot }: ProfileSectionsProps) {
  return (
    <div className="space-y-5">
      <BrandSection form={form} />
      <ContactsSection form={form} />
      <HistorySection form={form} />
      <AudienceSection form={form} />
      <ProductSection form={form} />
      <TeamSection form={form} photoSlot={photoSlot} />
      <FaqSection form={form} />
    </div>
  );
}
