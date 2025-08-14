import React from "react";
import ReactDOM from "react-dom/client";
import Analysis from "./pages/Analysis";
import Portfolio from "./pages/Portfolio";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Analysis />
    <Portfolio />
  </React.StrictMode>
);