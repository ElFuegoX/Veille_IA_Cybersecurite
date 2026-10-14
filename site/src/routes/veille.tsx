import { createFileRoute } from '@tanstack/react-router';
import { useState, useRef, useEffect } from 'react';
import {
  Search,
  Download,
  RotateCcw,
  ArrowDownWideNarrow,
  ExternalLink,
  Copy,
  Check,
  ChevronLeft,
  ChevronRight,
  FileSearch,
  SlidersHorizontal,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { PageIntro } from '@/components/veille/shell';
import { StatusBadge } from '@/components/veille/badge';
import { ArticleDrawer } from '@/components/veille/article-drawer';
import {
  articles,
  sources,
  themes,
  defaultFilters,
  filterArticles,
  downloadCsv,
  themeName,
  formatDate,
  reference,
  pageHead,
  type Article,
  type Filters,
} from '@/lib/veille';

export const Route = createFileRoute('/veille')({
  head: () =>
    pageHead(
      'Veille',
      'Explorez les articles du corpus : recherche instantanée, filtres par source et sous-thème, scores CRAAP sur 11 et export CSV public.'
    ),
  component: Explorer,
});

function ArticleActions({
  article,
  onOpenDrawer,
}: {
  article: Article;
  onOpenDrawer: (a: Article) => void;
}) {
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState(false);

  async function copy(e: React.MouseEvent) {
    e.stopPropagation();
    try {
      await navigator.clipboard.writeText(reference(article));
      setCopied(true);
      setError(false);
      setTimeout(() => setCopied(false), 2200);
    } catch {
      setError(true);
    }
  }

  return (
    <div className="article-actions" onClick={e => e.stopPropagation()}>
      <Button
        variant="ghost"
        size="icon"
        title="Détails & Évaluation CRAAP"
        aria-label={`Détails : ${article.title}`}
        onClick={() => onOpenDrawer(article)}
      >
        <SlidersHorizontal size={14} />
      </Button>
      <Button
        asChild
        variant="ghost"
        size="icon"
        title="Lire l’article original"
      >
        <a
          href={article.url}
          target="_blank"
          rel="noreferrer"
          aria-label={`Lire l’article : ${article.title}`}
        >
          <ExternalLink size={14} />
        </a>
      </Button>
      <Button
        variant="ghost"
        size="icon"
        onClick={copy}
        title={copied ? 'Référence copiée' : 'Copier la référence'}
        aria-label={`Copier la référence : ${article.title}`}
      >
        {copied ? <Check size={14} className="text-series-2" /> : <Copy size={14} />}
      </Button>
      {copied && <span className="sr-only" role="status">Référence copiée</span>}
      {error && <span className="copy-error" role="alert">Copie indisponible</span>}
    </div>
  );
}

function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <label className="filter-label">
      <span>{label}</span>
      <select value={value} onChange={e => onChange(e.target.value)} aria-label={label}>
        <option value="">
          {label === 'Source'
            ? 'Toutes les sources'
            : label === 'Langue'
            ? 'Toutes les langues'
            : label === 'Sous-thème'
            ? 'Tous les sous-thèmes'
            : 'Toutes les fiabilités'}
        </option>
        {options.map(o => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function Explorer() {
  const [filters, setFilters] = useState<Filters>(defaultFilters);
  const [page, setPage] = useState(1);
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Raccourci clavier universel "/" pour focus la recherche
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (
        e.key === '/' &&
        document.activeElement?.tagName !== 'INPUT' &&
        document.activeElement?.tagName !== 'TEXTAREA' &&
        document.activeElement?.tagName !== 'SELECT'
      ) {
        e.preventDefault();
        searchInputRef.current?.focus();
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const results = filterArticles(articles, filters);
  const pageSize = 12;
  const pages = Math.max(1, Math.ceil(results.length / pageSize));
  const rows = results.slice((page - 1) * pageSize, page * pageSize);
  const isFiltered = Object.entries(filters).some(([k, v]) => k !== 'sort' && v);

  function change(key: keyof Filters, value: string) {
    setFilters(f => ({ ...f, [key]: value }));
    setPage(1);
  }

  function handleSelectArticle(a: Article) {
    setSelectedArticle(a);
    setDrawerOpen(true);
  }

  return (
    <main className="page-container">
      <PageIntro
        section="VEILLE"
        title="Explorer la veille automatique"
        description="Corpus d’articles analysés, filtrés et évalués selon la grille CRAAP sur 11 points."
      >
        <Button onClick={() => downloadCsv(results)}>
          <Download /> Exporter CSV public
        </Button>
      </PageIntro>

      <div className="demo-notice">
        <span className="demo-dot" />
        Flux de veille automatisé
        <span className="notice-separator">·</span>
        <span>Cliquez sur une ligne pour ouvrir l’analyse détaillée CRAAP. Appuyez sur <kbd className="px-1.5 py-0.5 rounded border bg-card text-foreground font-mono text-[11px]">/</kbd> pour rechercher.</span>
      </div>

      <section className="filters-section" aria-label="Filtres des articles">
        <div className="search-box">
          <Search size={19} />
          <input
            ref={searchInputRef}
            aria-label="Rechercher un article"
            placeholder="Rechercher un mot-clé, un titre, une source… (raccourci : /)"
            value={filters.query}
            onChange={e => change('query', e.target.value)}
          />
          <div className="flex items-center gap-2">
            <kbd className="hidden sm:inline-block px-2 py-0.5 rounded border bg-muted/60 text-muted-foreground font-mono text-xs">
              /
            </kbd>
            <span>{results.length} articles</span>
          </div>
        </div>

        <div className="filters-grid">
          <FilterSelect
            label="Source"
            value={filters.source}
            onChange={v => change('source', v)}
            options={sources.map(s => ({ value: s, label: s }))}
          />
          <FilterSelect
            label="Langue"
            value={filters.language}
            onChange={v => change('language', v)}
            options={[
              { value: 'EN', label: 'Anglais (EN)' },
              { value: 'FR', label: 'Français (FR)' },
            ]}
          />
          <FilterSelect
            label="Sous-thème"
            value={filters.theme}
            onChange={v => change('theme', v)}
            options={[
              ...themes.map(t => ({ value: t.code, label: `${t.code} · ${t.short}` })),
              { value: 'unclassified', label: 'À classer' },
            ]}
          />
          <FilterSelect
            label="Fiabilité CRAAP"
            value={filters.reliability}
            onChange={v => change('reliability', v)}
            options={['Fiable', 'À vérifier', 'Écarté', 'Non évalué'].map(s => ({
              value: s,
              label: s,
            }))}
          />
          <Button
            variant="ghost"
            className="reset-button"
            onClick={() => {
              setFilters(defaultFilters);
              setPage(1);
            }}
          >
            <RotateCcw /> Réinitialiser les filtres
          </Button>
        </div>
      </section>

      <div className="results-toolbar">
        <p>
          <strong>{results.length}</strong> articles {isFiltered ? 'correspondants' : 'dans le corpus'}
        </p>
        <label className="sort-control">
          <ArrowDownWideNarrow size={16} />
          <span>Trier par</span>
          <select
            aria-label="Trier les articles"
            value={filters.sort}
            onChange={e => change('sort', e.target.value)}
          >
            <option value="date">Date récente</option>
            <option value="source">Source</option>
            <option value="score">Score CRAAP (/11)</option>
            <option value="notability">Notabilité</option>
          </select>
        </label>
      </div>

      <div className="article-table-wrap">
        <table className="article-table">
          <thead>
            <tr>
              <th>
                <Button variant="ghost" size="sm" onClick={() => change('sort', 'date')}>
                  Date ↓
                </Button>
              </th>
              <th>Article / source</th>
              <th>Langue</th>
              <th>Sous-thème</th>
              <th>
                <Button variant="ghost" size="sm" onClick={() => change('sort', 'score')}>
                  CRAAP ↓
                </Button>
              </th>
              <th>Fiabilité</th>
              <th title="Nombre de sources ayant repris le sujet">Reprises</th>
              <th className="text-right pr-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(a => (
              <tr
                key={a.id}
                onClick={() => handleSelectArticle(a)}
                className="cursor-pointer transition-colors hover:bg-muted/40"
              >
                <td className="date-cell">{formatDate(a.date)}</td>
                <td className="title-cell">
                  <span className="font-semibold text-foreground hover:text-primary transition-colors">
                    {a.title}
                  </span>
                  <div className="table-source">
                    <span>{a.source}</span>
                    <span className="collection-status" title="Statut de collecte">
                      {a.collection}
                    </span>
                  </div>
                </td>
                <td>
                  <span className="language-badge">{a.language}</span>
                </td>
                <td>
                  <span className="table-theme">{a.theme || 'À classer'}</span>
                  {a.theme && <span className="table-theme-name">{themeName(a.theme)}</span>}
                </td>
                <td className="score-cell">
                  {a.score === null ? (
                    <span className="text-muted-foreground">—</span>
                  ) : (
                    <>
                      <strong>{a.score}</strong>
                      <span>/11</span>
                    </>
                  )}
                </td>
                <td>
                  <StatusBadge value={a.reliability} />
                </td>
                <td className="reprises-cell">{a.reprises}</td>
                <td>
                  <ArticleActions article={a} onOpenDrawer={handleSelectArticle} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="mobile-articles">
          {rows.map(a => (
            <article
              key={a.id}
              className="mobile-article cursor-pointer"
              onClick={() => handleSelectArticle(a)}
            >
              <div className="mobile-article-top">
                <span>{formatDate(a.date)} · {a.language}</span>
                <StatusBadge value={a.reliability} />
              </div>
              <div className="article-title">{a.title}</div>
              <div className="table-source">
                <span>{a.source}</span>
                <span>{a.collection}</span>
              </div>
              <div className="mobile-article-details">
                <span>{a.theme ? `${a.theme} · ${themeName(a.theme)}` : 'À classer'}</span>
                <span>
                  CRAAP {a.score === null ? '—' : `${a.score}/11`} · {a.reprises} reprise{a.reprises > 1 ? 's' : ''}
                </span>
              </div>
              <div className="mobile-article-bottom">
                <Button size="sm" variant="outline" onClick={(e) => { e.stopPropagation(); handleSelectArticle(a); }}>
                  Voir l’évaluation
                </Button>
                <ArticleActions article={a} onOpenDrawer={handleSelectArticle} />
              </div>
            </article>
          ))}
        </div>

        {!rows.length && (
          <div className="empty-state">
            <FileSearch size={36} />
            <h2>Aucun article trouvé</h2>
            <p>Essayez un autre mot-clé ou élargissez les filtres.</p>
            <Button
              variant="outline"
              onClick={() => {
                setFilters(defaultFilters);
                setPage(1);
              }}
            >
              <RotateCcw /> Réinitialiser les filtres
            </Button>
          </div>
        )}
      </div>

      <div className="pagination">
        <span>
          {results.length
            ? `${(page - 1) * pageSize + 1}–${Math.min(page * pageSize, results.length)} sur ${results.length} articles`
            : '0 article'}
        </span>
        <div>
          <Button
            variant="outline"
            size="icon"
            aria-label="Page précédente"
            disabled={page <= 1}
            onClick={() => setPage(p => p - 1)}
          >
            <ChevronLeft />
          </Button>
          <span>
            Page {page} sur {pages}
          </span>
          <Button
            variant="outline"
            size="icon"
            aria-label="Page suivante"
            disabled={page >= pages}
            onClick={() => setPage(p => p + 1)}
          >
            <ChevronRight />
          </Button>
        </div>
      </div>

      <p className="data-caption">
        Grille CRAAP à double filtre : Pertinence thématique (sur 3, seuil ≥ 2) + Rigueur méthodologique (sur 8, seuil ≥ 5). Score total sur 11 points. Veille automatique sans intervention manuelle.
      </p>

      {/* Tiroir latéral d'analyse */}
      <ArticleDrawer
        article={selectedArticle}
        open={drawerOpen}
        onOpenChange={setDrawerOpen}
      />
    </main>
  );
}
