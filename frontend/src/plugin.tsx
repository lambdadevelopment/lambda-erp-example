// Frontend overrides, registered before bootstrap(). Everything here is a public
// seam exported by the core library — no core files are forked.
import {
  configureApiBase,
  configureBranding,
  registerComponent,
  registerNavItem,
} from "@lambda-development/erp-core";
import { AcmeDashboard } from "./dashboard";

// Point at the backend. Same-origin "/api" is the default; override per env.
configureApiBase(import.meta.env.VITE_API_BASE ?? "/api");

// Rebrand: product name (document title + sidebar fallback) + a new brand hue.
// Tokens are HSL channel triplets, matching the format in the core styles.css.
configureBranding({
  appName: "Acme ERP",
  tokens: { "--brand": "265 80% 60%" },
});

// Swap the dashboard (the "/" index route) for our own component.
registerComponent("Dashboard", AcmeDashboard);

// Add a sidebar link under the existing "Reports" group.
registerNavItem("Reports", { label: "Acme KPIs", path: "/reports/analytics" });
