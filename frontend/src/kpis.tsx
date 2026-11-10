// A page of the example's own, added with registerRoute (src/plugin.tsx) and
// linked from the sidebar with registerNavItem. Same Tailwind tokens as the shell.
export function AcmeKpis() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-fg">Acme KPIs</h1>
      <div className="rounded-lg border border-line bg-surface p-4 shadow-card">
        <p className="text-sm text-fg-muted">
          A page that only this deployment has. It has its own path
          (<code className="text-xs">/acme/kpis</code>), so it can be hidden or
          moved in the personal menu layout independently of the core's pages.
        </p>
      </div>
    </div>
  );
}
