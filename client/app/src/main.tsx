/**
 * Application entry — arch §G stack (Vite + React + TypeScript).
 * Mounts providers (Query + Session) around the router; imports the single
 * global stylesheet (tokens + Tailwind + §30.10 reduced-motion).
 */
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import { AppProviders } from "@/providers/AppProviders";
import { AppRouter } from "@/router";
import "@/styles/global.css";

const rootElement = document.getElementById("root");
if (!rootElement) throw new Error("Root element #root not found");

createRoot(rootElement).render(
  <StrictMode>
    <AppProviders>
      <BrowserRouter>
        <AppRouter />
      </BrowserRouter>
    </AppProviders>
  </StrictMode>,
);
