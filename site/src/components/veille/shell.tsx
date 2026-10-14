import { Link } from '@tanstack/react-router';
import { ShieldCheck } from 'lucide-react';

export function SiteHeader() {
  return (
    <header className="site-header">
      <div className="header-inner">
        <Link to="/" className="brand">
          <span className="brand-icon">
            <ShieldCheck size={23} />
          </span>
          <span>
            Veille IA <span className="text-muted-foreground">&</span> Cybersécurité
            <span className="brand-caption">OBSERVATOIRE DE VEILLE</span>
          </span>
        </Link>
        <nav aria-label="Navigation principale">
          <Link
            to="/"
            activeOptions={{ exact: true }}
            activeProps={{ className: 'nav-link active' }}
            className="nav-link"
          >
            Accueil
          </Link>
          <Link
            to="/veille"
            activeProps={{ className: 'nav-link active' }}
            className="nav-link"
          >
            Veille
          </Link>
          <Link
            to="/rapport"
            activeProps={{ className: 'nav-link active' }}
            className="nav-link"
          >
            Rapport
          </Link>
        </nav>
      </div>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="footer-bottom">
        <span>
          Veille IA &amp; Cybersécurité <span className="footer-divider">/</span> Observatoire
        </span>
        <span className="text-xs text-muted-foreground">
          Données synchronisées en continu
        </span>
      </div>
    </footer>
  );
}

export function PageIntro({
  section,
  title,
  description,
  children,
}: {
  section: string;
  title: string;
  description: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="page-intro">
      <div className="min-w-0">
        <div className="eyebrow">
          ESPACE DE VEILLE <span>/</span> {section}
        </div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {children && <div className="intro-actions">{children}</div>}
    </div>
  );
}
