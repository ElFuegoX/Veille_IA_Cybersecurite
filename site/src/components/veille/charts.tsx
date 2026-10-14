import { articles, themes } from '@/lib/veille';
import { Info, TrendingUp } from 'lucide-react';

const reliabilityItems = [
  { name: 'Fiable', className: 'good', color: 'var(--series-2)' },
  { name: 'À vérifier', className: 'warning', color: 'var(--series-4)' },
  { name: 'Écarté', className: 'bad', color: 'var(--series-alert)' },
  { name: 'Non évalué', className: 'neutral', color: 'var(--series-neutral)' },
];

export function ThemeChart() {
  const themeItems = themes.map(t => ({
    label: t.short,
    fullLabel: t.name,
    code: t.code,
    color: t.color,
    count: articles.filter(a => a.theme === t.code).length,
  }));

  const unclassified = articles.filter(a => !a.theme || a.theme === '—').length;
  const total = articles.length || 1;
  const maxVal = Math.max(...themeItems.map(t => t.count), 1);

  return (
    <section className="chart-panel theme-panel">
      <div className="panel-heading">
        <div>
          <h2>Répartition par sous-thème</h2>
          <p>Axes thématiques du corpus de veille</p>
        </div>
        <span title="Sous-thèmes S1 à S5 classés par IA et règles">
          <Info size={16} />
        </span>
      </div>

      <div className="gauge-grid">
        {themeItems.map(t => {
          // Hauteur proportionnelle : strictement 0 si aucun article (pas de jauge préremplie)
          const pct = t.count === 0 ? 0 : Math.min(100, 3 + (t.count / maxVal) * 97);
          const share = Math.round((t.count / total) * 100);
          return (
            <div className="gauge-item" key={t.code} title={t.fullLabel}>
              <div className="gauge-track">
                {t.count > 0 && (
                  <div
                    className={`gauge-fill bg-${t.color}`}
                    style={{ height: `${pct}%` }}
                  />
                )}
              </div>
              <div className="gauge-value">{t.count}</div>
              <div className="gauge-code">{t.code}</div>
              <div className="gauge-label" title={t.fullLabel}>{t.label}</div>
              <div className="gauge-share">{share} %</div>
            </div>
          );
        })}
      </div>

      <div className="panel-note">
        <span className="status-dot bg-series-neutral" />{' '}
        {unclassified} article(s) en attente de classification
      </div>
    </section>
  );
}

export function ReliabilityChart() {
  const total = articles.length || 1;
  const items = reliabilityItems.map(t => ({
    ...t,
    count: articles.filter(a => a.reliability === t.name).length,
  }));

  // Circonférence d'un cercle r=63 : 2 * PI * 63 = 395.84
  const circumference = 395.84;
  let accumulated = 0;

  const slices = items
    .filter(t => t.count > 0)
    .map(t => {
      const length = (t.count / total) * circumference;
      const strokeDashoffset = -accumulated;
      accumulated += length;
      return {
        ...t,
        length,
        strokeDashoffset,
      };
    });

  const evaluatedCount = articles.filter(a => a.score !== null).length;

  return (
    <section className="chart-panel reliability-panel">
      <div className="panel-heading">
        <div>
          <h2>Fiabilité du corpus</h2>
          <p>Évaluation selon la grille CRAAP (Pertinence + Rigueur)</p>
        </div>
        <span className="tiny-label">SUR 11 POINTS</span>
      </div>

      <div className="reliability-content">
        <div className="donut-wrap">
          <svg viewBox="0 0 160 160" role="img" aria-label="Répartition de la fiabilité du corpus">
            {/* Anneau d'arrière-plan */}
            <circle
              cx="80"
              cy="80"
              r="63"
              fill="none"
              stroke="var(--muted)"
              strokeWidth="16"
            />
            {/* Segments colorés */}
            {slices.map(slice => (
              <circle
                key={slice.name}
                cx="80"
                cy="80"
                r="63"
                fill="none"
                stroke={slice.color}
                strokeWidth="16"
                strokeDasharray={`${Math.max(0.5, slice.length - 2)} ${circumference - Math.max(0.5, slice.length - 2)}`}
                strokeDashoffset={slice.strokeDashoffset}
                transform="rotate(-90 80 80)"
              />
            ))}
          </svg>
          <div className="donut-number">
            <strong>{evaluatedCount}</strong>
            <span>articles évalués</span>
          </div>
        </div>

        <div className="donut-legend">
          {items.map(t => (
            <div key={t.name}>
              <span className={`legend-dot ${t.className}`} />
              <span>{t.name}</span>
              <strong>{t.count}</strong>
              <small>{Math.round((t.count / total) * 100)} %</small>
            </div>
          ))}
        </div>
      </div>

      <div className="panel-note">
        <Info size={13} /> Seuil d’admission : Pertinence ≥ 2/3 et Rigueur ≥ 6/8 (Total ≥ 8/11).
      </div>
    </section>
  );
}

export function TimelineChart() {
  // Récupérer et trier les dates réelles présentes dans les articles
  const dates = [...new Set(articles.map(a => a.date).filter(Boolean))].sort();

  // Garder les 7 à 10 jours les plus récents (ou tous si moins de 10)
  const recentDates = dates.slice(-9);

  // Compter les articles par date
  const counts = recentDates.map(d => articles.filter(a => a.date === d).length);
  const maxCount = Math.max(...counts, 10);

  // Formater les dates pour l'axe X (ex: "12 oct.")
  const labels = recentDates.map(d => {
    try {
      return new Date(`${d}T12:00:00Z`).toLocaleDateString('fr-FR', {
        day: 'numeric',
        month: 'short',
        timeZone: 'UTC',
      });
    } catch {
      return d;
    }
  });

  const width = 1000;
  const height = 150;
  const paddingLeft = 50;
  const paddingRight = 40;
  const chartWidth = width - paddingLeft - paddingRight;
  const stepX = recentDates.length > 1 ? chartWidth / (recentDates.length - 1) : chartWidth;

  const points = counts
    .map((n, i) => {
      const x = paddingLeft + i * stepX;
      const y = height - (n / maxCount) * 110 - 20;
      return `${x},${y}`;
    })
    .join(' ');

  const areaPoints = `${paddingLeft},${height - 15} ${points} ${paddingLeft + (counts.length - 1) * stepX},${height - 15}`;

  return (
    <section className="chart-panel timeline-panel">
      <div className="panel-heading">
        <div>
          <h2>Rythme des publications</h2>
          <p>Articles collectés par date récente de publication</p>
        </div>
        <span className="period-label">
          {labels[0] || 'Début'} — {labels.at(-1) || 'Aujourd’hui'}
        </span>
      </div>

      <div className="timeline-chart">
        <svg viewBox={`0 0 ${width} 185`} role="img" aria-label="Rythme récent des publications">
          {/* Lignes horizontales de repère */}
          {[0, Math.round(maxCount * 0.5), maxCount].map((n, i) => {
            const y = height - (n / maxCount) * 110 - 20;
            return (
              <g key={i}>
                <line
                  x1={paddingLeft}
                  x2={width - paddingRight}
                  y1={y}
                  y2={y}
                  stroke="var(--border)"
                  strokeDasharray="3 5"
                />
                <text x="10" y={y + 4} fill="var(--muted-foreground)" fontSize="11">
                  {n}
                </text>
              </g>
            );
          })}

          {/* Aire et courbe */}
          {points && (
            <>
              <polygon points={areaPoints} fill="var(--chart-area)" />
              <polyline
                points={points}
                fill="none"
                stroke="var(--primary)"
                strokeWidth="2.5"
                strokeLinejoin="round"
              />
            </>
          )}

          {/* Points */}
          {counts.map((n, i) => {
            const cx = paddingLeft + i * stepX;
            const cy = height - (n / maxCount) * 110 - 20;
            return (
              <circle
                key={i}
                cx={cx}
                cy={cy}
                r="4"
                fill="var(--card)"
                stroke="var(--primary)"
                strokeWidth="2"
                aria-label={`${n} articles le ${labels[i]}`}
              />
            );
          })}

          {/* Libellés de dates */}
          {labels.map((s, i) => {
            const x = paddingLeft + i * stepX;
            return (
              <text
                key={i}
                x={x}
                y="175"
                textAnchor="middle"
                fill="var(--muted-foreground)"
                fontSize="11"
              >
                {s}
              </text>
            );
          })}
        </svg>
      </div>

      <div className="panel-note">
        <TrendingUp size={14} />
        <span>Collecte continue, mise à jour à chaque exécution du pipeline.</span>
      </div>
    </section>
  );
}
