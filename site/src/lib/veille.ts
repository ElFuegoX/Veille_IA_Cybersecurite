export const sources = ['The Hacker News', 'BleepingComputer', 'MIT Technology Review', 'ANSSI', 'Dark Reading', 'SecurityWeek', 'Le Monde Informatique', 'Google Security Blog', 'Microsoft Security', 'CERT-FR'];
export const themes = [
  { code: 'S1', name: 'IA offensive', short: 'IA offensive', color: 'series-1' },
  { code: 'S2', name: 'IA défensive', short: 'IA défensive', color: 'series-2' },
  { code: 'S3', name: 'Sécurité des modèles', short: 'Sécurité des modèles', color: 'series-3' },
  { code: 'S4', name: 'Gouvernance & éthique', short: 'Gouvernance & éthique', color: 'series-4' },
  { code: 'S5', name: 'Menaces émergentes', short: 'Menaces émergentes', color: 'series-5' },
];
const titles = [
  'Les agents IA, nouvelle surface d’attaque pour les entreprises',
  'Detecting AI-powered phishing with machine learning',
  'Prompt injection: why enterprise copilots remain vulnerable',
  'L’ANSSI publie ses recommandations pour sécuriser l’IA générative',
  'How generative AI is reshaping the threat landscape',
  'Ransomware groups experiment with autonomous AI tools',
  'L’intelligence artificielle au service des équipes SOC',
  'Securing the software supply chain in the age of AI',
  'New research exposes vulnerabilities in large language models',
  'A practical framework for evaluating AI security risks',
  'Deepfake fraud: the next challenge for identity verification',
  'Adversarial attacks on machine learning systems',
  'Protecting sensitive data in enterprise AI deployments',
  'AI governance: translating policy into security controls',
  'AI-assisted malware analysis improves threat detection',
  'Model poisoning attacks target open-source AI ecosystems',
  'Zero trust architecture meets autonomous AI agents',
  'Red teaming generative AI: lessons from recent research',
  'Les enjeux de souveraineté et de confiance des modèles IA',
  'Cyber threat intelligence: extracting signals with AI',
];
export type Reliability = 'Fiable' | 'À vérifier' | 'Écarté' | 'Non évalué';
export type Article = { id: number; date: string; title: string; source: string; language: 'EN' | 'FR'; theme: string; score: number | null; reliability: Reliability; reprises: number; validation: 'Validé' | 'En attente' | 'Écarté'; collection: string; url: string; notability: number };
export const articles: Article[] = Array.from({ length: 201 }, (_, i) => {
  const date = new Date(Date.UTC(2026, 9, 13 - Math.floor(i / 3)));
  const score = i % 4 === 0 || i > 196 ? null : 22 + ((i * 17) % 29);
  const reliability: Reliability = score === null ? 'Non évalué' : score >= 38 ? 'Fiable' : score >= 28 ? 'À vérifier' : 'Écarté';
  const source = sources[i % 10] ?? 'The Hacker News';
  const title = titles[i % titles.length] ?? 'Analyse de sécurité IA';
  return { id: i + 1, date: date.toISOString().slice(0, 10), title: i < 20 ? title : `${title} — ${['recherche', 'analyse', 'retour d’expérience', 'mise à jour'][Math.floor(i / 20) % 4]} ${Math.floor(i / 20)}`, source, language: [0,3,6,8].includes(i % 20) ? 'FR' : 'EN', theme: i % 7 === 0 ? '' : `S${(i % 5) + 1}`, score, reliability, reprises: (i * 7) % 12, validation: score === null ? 'En attente' : reliability === 'Écarté' ? 'Écarté' : i % 3 === 0 ? 'En attente' : 'Validé', collection: ['ok', 'lien_redirection', 'echec_http', 'robots', 'vide', 'non traité'][i % 6] ?? 'ok', url: `https://${['thehackernews.com','www.bleepingcomputer.com','www.technologyreview.com','cyber.gouv.fr','www.darkreading.com','www.securityweek.com','www.lemondeinformatique.fr','security.googleblog.com','www.microsoft.com/en-us/security/blog','www.cert.ssi.gouv.fr'][i % 10]}/`, notability: (i * 13 + 29) % 100 };
});
export const updatedAt = '13 octobre 2026';
export const formatDate = (date: string) => new Date(`${date}T12:00:00Z`).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC' });
export const themeName = (code: string) => themes.find(t => t.code === code)?.name ?? 'À classer';
export type Filters = { query: string; source: string; language: string; theme: string; reliability: string; sort: string };
export const defaultFilters: Filters = { query: '', source: '', language: '', theme: '', reliability: '', sort: 'date' };
export function filterArticles(rows: Article[], filters: Filters) {
  const query = filters.query.toLocaleLowerCase('fr').normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  return rows.filter(a => (!query || `${a.title} ${a.source} ${themeName(a.theme)}`.toLocaleLowerCase('fr').normalize('NFD').replace(/[\u0300-\u036f]/g, '').includes(query)) && (!filters.source || a.source === filters.source) && (!filters.language || a.language === filters.language) && (!filters.theme || (filters.theme === 'unclassified' ? !a.theme : a.theme === filters.theme)) && (!filters.reliability || a.reliability === filters.reliability)).sort((a,b) => filters.sort === 'source' ? a.source.localeCompare(b.source) : filters.sort === 'score' ? (b.score ?? -1) - (a.score ?? -1) : filters.sort === 'notability' ? b.notability - a.notability : b.date.localeCompare(a.date) || a.id - b.id);
}
export function publicCsv(rows: Article[]) {
  const escape = (value: unknown) => { let text = String(value ?? ''); if (/^[=+@-]/.test(text)) text = `'${text}`; return `"${text.replaceAll('"', '""')}"`; };
  const header = ['date', 'titre', 'source', 'langue', 'sous_theme', 'score_CRAAP', 'fiabilite', 'nb_sources_reprise', 'validation', 'statut_collecte', 'url'];
  return '\uFEFF' + [header, ...rows.map(a => [a.date,a.title,a.source,a.language,a.theme,a.score,a.reliability,a.reprises,a.validation,a.collection,a.url])].map(row => row.map(escape).join(';')).join('\r\n');
}
export function downloadCsv(rows: Article[] = articles) {
  const url = URL.createObjectURL(new Blob([publicCsv(rows)], { type: 'text/csv;charset=utf-8;' }));
  const link = document.createElement('a'); link.href = url; link.download = 'veille-ia-cybersecurite-public.csv'; link.click(); URL.revokeObjectURL(url);
}
export function reference(a: Article) { return `${a.source}. « ${a.title} ». ${formatDate(a.date)}. ${a.url}`; }
export function pageHead(title: string, description: string) { return { meta: [{ title: `${title} · Veille IA & Cybersécurité` }, { name: 'description', content: description }, { property: 'og:title', content: `${title} · Veille IA & Cybersécurité` }, { property: 'og:description', content: description }, { property: 'og:type', content: 'website' }, { name: 'twitter:card', content: 'summary_large_image' }] }; }
