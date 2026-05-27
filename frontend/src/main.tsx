import "./plugin";                                  // register overrides BEFORE bootstrap
import "@lambda-development/erp-core/styles.css";   // base tokens + Tailwind layers (our Tailwind processes them)
import "./brand.css";                               // our brand overrides, layered on top
import { bootstrap } from "@lambda-development/erp-core";

// bootstrap() builds the router (after registration) and mounts the app at #root.
bootstrap();
