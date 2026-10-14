import rawData from '../data/articles.json';

export const themes = [
  { code: 'S1', name: 'IA offensive & Vecteurs d\u2019attaque', short: 'IA offensive', color: 'series-1' },
  { code: 'S2', name: 'IA d\u00e9fensive & D\u00e9tection SOC', short: 'IA d\u00e9fensive', color: 'series-2' },
  { code: 'S3', name: 'S\u00e9curit\u00e9 & Robustesse des mod\u00e8les', short: 'S\u00e9curit\u00e9 des mod\u00e8les', color: 'series-3' },
  { code: 'S4', name: 'Gouvernance, Normes & R\u00e9gulation', short: 'Gouvernance & \u00e9thique', color: 'series-4' },
  { code: 'S5', name: 'Menaces \u00e9mergentes & Agents autonomes', short: 'Menaces \u00e9mergentes', color: 'series-5' },
];

export type Reliability = 'Fiable' | '\u00c0 v\u00e9rifier' | '\u00c9cart\u00e9' | 'Non \u00e9valu\u00e9';

export type CraapScores = {
  pertinence: number; // /3 (seuil >= 2)
  actualite: number;  // /2
  autorite: number;   // /2
  exactitude: number; // /2
  objectif: number;   // /2
  rigueur: number;    // /8 (seuil >= 6)
  total: number;      // /11 (seuil >= 8)
};

export type Article = {
  id: number;
  date: string;
  title: string;
  source: string;
  language: 'EN' | 'FR';
  theme: string;
  craap: CraapScores | null;
  score: number | null; // Total sur 11
  reliability: Reliability;
  reprises: number;
  reprises_sources: string[];
  collection: string;
  url: string;
  notability: number;
  resume: string;
  justification_craap: string;
  justification_theme: string;
};

// -- Donn\u00e9es r\u00e9elles import\u00e9es depuis le JSON g\u00e9n\u00e9r\u00e9 par 09_export_site.py --
export const articles: Article[] = (rawData.articles as Article[]);

// Sources dynamiques : extraites des articles r\u00e9els (sans doublons, tri\u00e9es)
export const sources: string[] = [...new Set(articles.map(a => a.source))].filter(Boolean).sort();

export const updatedAt = rawData.updatedAt;

export const formatDate = (date: string) =>
  new Date(`${date}T12:00:00Z`).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC' });

export const themeName = (code: string) =>
  themes.find(t => t.code === code)?.name ?? '\u00c0 classer';

export type Filters = {
  query: string;
  source: string;
  language: string;
  theme: string;
  reliability: string;
  sort: string;
};

export const defaultFilters: Filters = {
  query: '',
  source: '',
  language: '',
  theme: '',
  reliability: '',
  sort: 'date',
};

export function filterArticles(rows: Article[], filters: Filters) {
  const query = filters.query.toLocaleLowerCase('fr').normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  return rows.filter(a =>
    (!query || `${a.title} ${a.source} ${themeName(a.theme)} ${a.resume}`.toLocaleLowerCase('fr').normalize('NFD').replace(/[\u0300-\u036f]/g, '').includes(query)) &&
    (!filters.source || a.source === filters.source) &&
    (!filters.language || a.language === filters.language) &&
    (!filters.theme || (filters.theme === 'unclassified' ? !a.theme : a.theme === filters.theme)) &&
    (!filters.reliability || a.reliability === filters.reliability)
  ).sort((a, b) =>
    filters.sort === 'source' ? a.source.localeCompare(b.source) :
    filters.sort === 'score' ? (b.score ?? -1) - (a.score ?? -1) :
    filters.sort === 'notability' ? b.notability - a.notability :
    b.date.localeCompare(a.date) || a.id - b.id
  );
}

export function publicCsv(rows: Article[]) {
  const escape = (value: unknown) => {
    let text = String(value ?? '');
    if (/^[=+@-]/.test(text)) text = `'${text}`;
    return `"${text.replaceAll('"', '""')}"`;
  };
  const header = ['date', 'titre', 'source', 'langue', 'sous_theme', 'pertinence_sur_3', 'rigueur_sur_8', 'score_CRAAP_sur_11', 'fiabilite', 'nb_sources_reprise', 'statut_collecte', 'url'];
  return '\uFEFF' + [
    header,
    ...rows.map(a => [
      a.date,
      a.title,
      a.source,
      a.language,
      a.theme,
      a.craap?.pertinence ?? '',
      a.craap?.rigueur ?? '',
      a.score ?? '',
      a.reliability,
      a.reprises,
      a.collection,
      a.url
    ])
  ].map(row => row.map(escape).join(';')).join('\r\n');
}

export function downloadCsv(rows: Article[] = articles) {
  const url = URL.createObjectURL(new Blob([publicCsv(rows)], { type: 'text/csv;charset=utf-8;' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'veille-ia-cybersecurite-public.csv';
  link.click();
  URL.revokeObjectURL(url);
}

export function reference(a: Article) {
  return `${a.source}. \u00ab ${a.title} \u00bb. ${formatDate(a.date)}. ${a.url}`;
}

export function pageHead(title: string, description: string) {
  return {
    meta: [
      { title: `${title} \u00b7 Veille IA & Cybers\u00e9curit\u00e9` },
      { name: 'description', content: description },
      { property: 'og:title', content: `${title} \u00b7 Veille IA & Cybers\u00e9curit\u00e9` },
      { property: 'og:description', content: description },
      { property: 'og:type', content: 'website' },
      { name: 'twitter:card', content: 'summary_large_image' },
    ],
  };
}
