import "./plugin";                                  // register overrides BEFORE bootstrap
// Self-host Inter (family "Inter", the weights erp-core's fontFamily.sans expects).
// Without this the package asks for "Inter" but nothing loads it → system-ui fallback.
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";
import "@lambda-development/erp-core/styles.css";   // base tokens + Tailwind layers (our Tailwind processes them)
import "./brand.css";                               // our brand overrides, layered on top
import { bootstrap } from "@lambda-development/erp-core";

// bootstrap() builds the router (after registration) and mounts the app at #root.
bootstrap();
