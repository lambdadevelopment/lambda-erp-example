// Custom dashboard, registered via registerComponent("Dashboard", …). The core
// resolves its index ("/") route through the component registry, so this renders
// in place of the core dashboard. Styled with the shared Tailwind tokens
// (bg-surface, text-fg, border-line, shadow-card) so it matches the app shell.
export function AcmeDashboard() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-fg">Acme ERP</h1>
      <p className="text-fg-muted">
        This dashboard comes from the example deployment — it replaces the core
        one via{" "}
        <code className="mx-0.5 rounded bg-surface-subtle px-1.5 py-0.5 text-sm">
          registerComponent("Dashboard", …)
        </code>
        .
      </p>
      <div className="rounded-lg border border-line bg-surface p-4 shadow-card">
        <p className="text-sm text-fg-muted">
          Drop your KPIs, charts, and shortcuts here. The brand colour, product
          name, and a sidebar link were also customized in{" "}
          <code className="text-xs">src/plugin.tsx</code>.
        </p>
      </div>
    </div>
  );
}
