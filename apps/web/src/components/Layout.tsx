import { Outlet } from "react-router-dom";
import NavBar from "./NavBar";

export default function Layout() {
  return (
    <div className="app-layout">
      <header>
        <NavBar />
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  );
}