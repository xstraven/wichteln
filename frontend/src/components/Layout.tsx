import { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";

type LayoutProps = {
  children: ReactNode;
};

const Layout = ({ children }: LayoutProps) => {
  const location = useLocation();

  return (
    <div className="app-wrapper">
      <header className="app-header">
        <div className="header-content">
          <Link to="/" className="brand">
            <span aria-hidden="true" className="brand-icon">
              🎄
            </span>
            <div className="brand-text">
              <span className="brand-title gold-accent">Wichteln</span>
              <span className="brand-subtitle">Secret Santa Magic ✨</span>
            </div>
          </Link>
          <nav className="nav-links" aria-label="Main navigation">
            <Link to="/create" className={location.pathname === "/create" ? "active" : ""}>
              Create Group
            </Link>
            <Link to="/reveal" className={location.pathname === "/reveal" ? "active" : ""}>
              Reveal Match
            </Link>
          </nav>
        </div>
      </header>
      <main className="app-main">{children}</main>
      <footer className="app-footer">
        <small>Made with ❤️, cocoa, and a dash of cinnamon.</small>
        <small className="imprint">Impressum – David Hinrichs, Reuterstr. 1, 12053 Berlin</small>
      </footer>
    </div>
  );
};

export default Layout;
