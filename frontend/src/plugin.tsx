// Frontend overrides, registered before bootstrap(). Everything here is a public
// seam exported by the core library — no core files are forked.
import {
  configureApiBase,
  configureBranding,
  registerComponent,
  registerNavItem,
  registerRoute,
} from "@lambda-development/erp-core";
import { AcmeDashboard } from "./dashboard";
import { AcmeKpis } from "./kpis";

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

// Add a page of our own and a sidebar link to it under the existing "Reports"
// group. Give every added link its own path: the personal menu layout tells
// entries apart by path, so reusing a core page's path would tie the two together.
registerRoute({ path: "acme/kpis", element: <AcmeKpis /> });
registerNavItem("Reports", { label: "Acme KPIs", path: "/acme/kpis" });
