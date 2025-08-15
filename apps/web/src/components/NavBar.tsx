import { useState } from "react";
import { Link } from "react-router-dom";
import "./NavBar.css";

export default function NavBar() {
  const [open, setOpen] = useState(false);

  const toggle = () => setOpen((o) => !o);
  const close = () => setOpen(false);

  return (
    <nav className="navbar">
      <div className="brand">Finance</div>
      <button className="nav-toggle" aria-label="Toggle navigation" onClick={toggle}>
        ☰
      </button>
      <ul className={`nav-links ${open ? "open" : ""}`}>
        <li>
          <Link to="/analysis" onClick={close}>Analysis</Link>
        </li>
        <li>
          <Link to="/portfolio" onClick={close}>Portfolio</Link>
        </li>
        <li>
          <Link to="/company" onClick={close}>Company</Link>
        </li>
      </ul>
    </nav>
  );
}