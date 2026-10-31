import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

const links = [
  { to: "/companies", label: "Компании", end: true },
  { to: "/companies/new", label: "Новая компания", end: true },
  { to: "/sites", label: "Сайты", end: false },
];

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[13rem_1fr]">
      <aside className="border-b border-line bg-surface lg:sticky lg:top-0 lg:h-screen lg:border-r lg:border-b-0">
        <div className="flex items-center gap-4 px-5 py-4 lg:flex-col lg:items-stretch lg:gap-6 lg:py-6">
          <a href="/companies" className="flex items-center gap-2 text-sm font-semibold">
            <img src="/favicon.svg" alt="" className="size-6" />
            Generation Site
          </a>
          <nav className="flex gap-1 lg:flex-col">
            {links.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.end}
                className={({ isActive }) =>
                  `rounded-md px-3 py-2 text-sm ${
                    isActive ? "bg-accent-soft font-medium text-accent-strong" : "text-muted hover:bg-sunken hover:text-ink"
                  }`
                }
              >
                {link.label}
              </NavLink>
            ))}
          </nav>
        </div>
        <p className="hidden px-5 text-xs leading-relaxed text-faint lg:block">
          Компании и люди вымышленные. Телефоны из блоков для медиапроизводств.
        </p>
      </aside>
      <main className="min-w-0 px-4 py-6 sm:px-8 lg:py-8">{children}</main>
    </div>
  );
}
