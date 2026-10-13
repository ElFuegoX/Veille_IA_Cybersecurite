import { Link } from '@tanstack/react-router';
import { ShieldCheck, ArrowUpRight, FlaskConical } from 'lucide-react';
export function SiteHeader() {
  return <header className="site-header"><div className="header-inner"><Link to="/" className="brand"><span className="brand-icon"><ShieldCheck size={23}/></span><span>Veille IA <span className="text-muted-foreground">&</span> Cybersécurité<span className="brand-caption">OBSERVATOIRE UNIVERSITAIRE</span></span></Link><nav aria-label="Navigation principale"><Link to="/" activeOptions={{ exact: true }} activeProps={{ className: 'nav-link active' }} className="nav-link">Accueil</Link><Link to="/veille" activeProps={{ className: 'nav-link active' }} className="nav-link">Veille</Link><Link to="/rapport" activeProps={{ className: 'nav-link active' }} className="nav-link">Rapport</Link></nav></div></header>;
}
export function SiteFooter() {
  return <footer className="site-footer"><div className="footer-method"><FlaskConical size={17} className="shrink-0 text-muted-foreground"/><p>Les articles proviennent de flux RSS et de sources manuelles. Les scores CRAAP, sous-thèmes et validations sont ajoutés progressivement. Le texte complet des articles n’est pas publié.</p></div><div className="footer-bottom"><span>Veille IA & Cybersécurité <span className="footer-divider">/</span> Projet universitaire</span><span className="inline-flex items-center gap-2">Corpus de démonstration <ArrowUpRight size={13}/></span></div></footer>;
}
export function PageIntro({ section, title, description, children }: { section: string; title: string; description: string; children?: React.ReactNode }) {
  return <div className="page-intro"><div className="min-w-0"><div className="eyebrow">ESPACE DE VEILLE <span>/</span> {section}</div><h1>{title}</h1><p>{description}</p></div>{children && <div className="intro-actions">{children}</div>}</div>;
}
