import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import { App } from "@/App";
import { AppProvider } from "@/context/AppContext";
import "@/index.css";

if (typeof document !== "undefined") {
  const storedTheme = window.localStorage.getItem("visionpass-theme");
  const theme = storedTheme === "light" ? "light" : "dark";
  document.documentElement.classList.toggle("dark", theme === "dark");
  document.documentElement.dataset.theme = theme;
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <AppProvider>
        <App />
      </AppProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
