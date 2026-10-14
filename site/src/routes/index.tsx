import { createFileRoute, Link } from '@tanstack/react-router';
import { ArrowRight, ArrowUpRight, CalendarDays, CheckCheck, Files, Rss, Sparkles, Clock3, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { PageIntro } from '@/components/veille/shell';
import { ThemeChart, ReliabilityChart, TimelineChart } from '@/components/veille/charts';
import { StatusBadge } from '@/components/veille/badge';
import { articles, sources, updatedAt, formatDate, themeName, downloadCsv, pageHead } from '@/lib/veille';

export const Route = createFileRoute('/')({
  head: () =>
    pageHead(
      'Accueil',
      'Consultez les tendances, les sources et la fiabilité du corpus de veille sur l’intelligence artificielle et la cybersécurité.'
    ),
  component: Home,
});

function Home() {
  const evaluated = articles.filter(a => a.score !== null).length;
  // Les articles les plus pertinents / notoires
  const watched = [...articles]
    .sort((a, b) => b.notability - a.notability || (b.score ?? 0) - (a.score ?? 0))
    .slice(0, 3);

  const stats = [
    {
      label: 'Articles collectés',
      value: articles.length,
      icon: Files,
      detail: 'Dans le corpus de veille',
      tone: 'blue',
    },
    {
      label: 'Sources suivies',
      value: sources.length,
      icon: Rss,
      detail: 'Flux RSS & presse spécialisée',
      tone: 'cyan',
    },
    {
      label: 'Articles évalués',
      value: evaluated,
      icon: CheckCheck,
      detail: `${Math.round((evaluated / (articles.length || 1)) * 100)} % du corpus analysé`,
      tone: 'green',
    },
    {
      label: 'Dernière mise à jour',
      value: updatedAt || 'En direct',
      icon: CalendarDays,
      detail: 'Collecte et analyse automatiques',
      tone: 'neutral',
    },
  ];

  return (
    <main className="page-container">
      <PageIntro
        section="ACCUEIL"
        title="Vue d’ensemble"
        description="L’essentiel de notre veille sur l’intelligence artificielle et la cybersécurité."
      >
        <span className="live-indicator">
          <span />
          Veille en cours
        </span>
        <Button variant="outline" onClick={() => downloadCsv()}>
          <Download />
          Exporter CSV
        </Button>
      </PageIntro>

      <section className="stats-grid" aria-label="Statistiques du corpus">
        {stats.map(s => (
          <div className="stat-card" key={s.label}>
            <div className="stat-top">
              <span>{s.label}</span>
              <span className={`stat-icon ${s.tone}`}>
                <s.icon size={17} />
              </span>
            </div>
            <strong className={typeof s.value === 'string' ? 'stat-date' : ''}>
              {s.value}
            </strong>
            <p>{s.detail}</p>
          </div>
        ))}
      </section>

      <div className="section-heading">
        <h2>Explorer les tendances</h2>
        <span>
          {articles.length} articles <span className="notice-separator">·</span> 5 sous-thèmes
        </span>
      </div>

      <div className="charts-grid">
        <ThemeChart />
        <ReliabilityChart />
        <TimelineChart />
      </div>

      <section className="watch-section">
        <div className="section-heading">
          <div className="inline-flex items-center gap-2">
            <Sparkles size={18} className="text-primary" />
            <h2>Articles à surveiller</h2>
            <span className="count-label">{watched.length}</span>
          </div>
          <Button asChild variant="link" className="px-0">
            <Link to="/veille">
              Toute la veille
              <ArrowRight />
            </Link>
          </Button>
        </div>
        <p className="section-description">
          Les signaux majeurs qui se distinguent par leur score de qualité et de notabilité.
        </p>

        <div className="watch-grid">
          {watched.map(a => (
            <article key={a.id} className="watch-card">
              <div className="watch-top">
                <span className="theme-tag">
                  {a.theme && a.theme !== '—' ? (
                    <>
                      {a.theme} <span>· {themeName(a.theme)}</span>
                    </>
                  ) : (
                    'À classer'
                  )}
                </span>
                <span className="notability" title="Score CRAAP / 11">
                  <Sparkles size={12} />
                  {a.score !== null ? `${a.score}/11` : `${a.notability}/100`}
                </span>
              </div>
              <a
                className="article-title"
                href={a.url}
                target="_blank"
                rel="noreferrer"
              >
                {a.title}
                <ArrowUpRight size={16} />
              </a>
              <div className="watch-source">
                <span>{a.source}</span>
                <span>{a.language}</span>
              </div>
              <div className="watch-bottom">
                <StatusBadge value={a.reliability} />
                <span>
                  <Clock3 size={12} />
                  {formatDate(a.date)}
                </span>
              </div>
            </article>
          ))}
        </div>
      </section>

      <div className="bottom-summary">
        <span>
          <span className="status-dot bg-series-2" />
          Dernière mise à jour : {updatedAt}
        </span>
        <span>Collecte · Classification IA · Évaluation CRAAP</span>
      </div>
    </main>
  );
}
