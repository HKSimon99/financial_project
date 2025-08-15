import "./App.css";
import Analysis from "./pages/Analysis";
import Portfolio from "./pages/Portfolio";
import Company from "./pages/Company";
import { Routes, Route, Navigate } from "react-router-dom";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/analysis" replace />} />
      <Route path="/analysis" element={<Analysis />} />
      <Route path="/portfolio" element={<Portfolio />} />
      <Route path="/company/:symbol" element={<Company />} />
    </Routes>
  );
}