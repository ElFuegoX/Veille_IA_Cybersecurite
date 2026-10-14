export const sources = [
  'The Hacker News', 'BleepingComputer', 'MIT Technology Review', 'ANSSI',
  'Dark Reading', 'SecurityWeek', 'Le Monde Informatique', 'Google Security Blog',
  'Microsoft Security', 'CERT-FR'
];

export const themes = [
  { code: 'S1', name: 'IA offensive & Vecteurs d’attaque', short: 'IA offensive', color: 'series-1' },
  { code: 'S2', name: 'IA défensive & Détection SOC', short: 'IA défensive', color: 'series-2' },
  { code: 'S3', name: 'Sécurité & Robustesse des modèles', short: 'Sécurité des modèles', color: 'series-3' },
  { code: 'S4', name: 'Gouvernance, Normes & Régulation', short: 'Gouvernance & éthique', color: 'series-4' },
  { code: 'S5', name: 'Menaces émergentes & Agents autonomes', short: 'Menaces émergentes', color: 'series-5' },
];

const titles = [
  'Les agents IA, nouvelle surface d’attaque pour les infrastructures critiques',
  'Detecting AI-powered spear-phishing with machine learning models',
  'Prompt injection & jailbreak: why enterprise copilots remain vulnerable',
  'L’ANSSI publie ses recommandations pour sécuriser l’adoption de l’IA générative',
  'How generative AI is reshaping the cyber threat landscape for SOC teams',
  'Ransomware groups experiment with autonomous AI tools for initial access',
  'L’intelligence artificielle au service de la détection et réponse aux incidents (XDR)',
  'Securing the AI software supply chain: open-source weights and poisoning',
  'New research exposes severe zero-day vulnerabilities in large language models',
  'A practical framework for evaluating cybersecurity risks of agentic workflows',
  'Deepfake fraud & synthetic audio: the next critical challenge for IAM verification',
  'Adversarial attacks on vision and language models in automated defenses',
  'Protecting sensitive enterprise data from exfiltration via AI assistant plugins',
  'EU AI Act compliance: translating security baselines into operational controls',
  'AI-assisted binary and malware analysis accelerates triage for threat intelligence',
  'Model poisoning attacks target HuggingFace and open-source model repositories',
  'Zero trust architecture applied to autonomous multi-agent systems',
  'Red teaming generative AI: methodology, guardrails and prompt fuzzing',
  'Les enjeux de souveraineté et de contrôle des modèles d’IA en environnement sensible',
  'Cyber threat intelligence: automated extraction of IoCs and TTPs with LLMs',
];

const excerpts = [
  'Des chercheurs en sécurité démontrent comment un agent IA connecté aux API d’une entreprise peut être détourné par prompt injection indirecte pour exfiltrer des bases de données.',
  'Analyse technique des mécanismes de détection comportementale appliqués aux flux de courriels générés par des modèles de langage avancés.',
  'Évaluation des garde-fous mis en place sur les assistants bureautiques d’entreprise et démonstration de contournements via encodage base64 et prompts imbriqués.',
  'Guide officiel de l’agence détaillant les bonnes pratiques de cloisonnement, d’audit des prompts et de gestion des accès pour les modèles déployés en interne.',
  'Rapport de renseignement sur les menaces observant une baisse des délais entre découverte de vulnérabilité et exploitation grâce aux assistants de code malveillants.',
  'Observation des premières souches de ransomwares intégrant des modules automatisés pour adapter leurs charges utiles aux défenses locales.',
];

export type Reliability = 'Fiable' | 'À vérifier' | 'Écarté' | 'Non évalué';

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

export const articles: Article[] = Array.from({ length: 201 }, (_, i) => {
  const date = new Date(Date.UTC(2026, 9, 13 - Math.floor(i / 3)));
  const sourceIndex = i % 10;
  const source = sources[sourceIndex] ?? 'The Hacker News';
  const title = titles[i % titles.length] ?? 'Analyse de sécurité IA';
  const fullTitle = i < 20 ? title : `${title} — ${['recherche', 'analyse', 'rapport technique', 'bulletin d’alerte'][Math.floor(i / 20) % 4]} #${Math.floor(i / 20) + 1}`;
  const theme = i % 8 === 0 ? '' : `S${(i % 5) + 1}`;

  // Formule CRAAP selon vos règles :
  // pertinence sur 3 (>= 2 requis)
  // actualite /2, autorite /2, exactitude /2, objectif /2 (total rigueur sur 8, >= 6 requis)
  const isEvaluated = !(i % 5 === 0 && i > 150);

  let craap: CraapScores | null = null;
  let reliability: Reliability = 'Non évalué';

  if (isEvaluated) {
    // Calcul de pertinence /3
    const pertinence = i % 11 === 0 ? 1 : (i % 7 === 0 ? 2 : 3);
    const actualite = (i % 4 === 0) ? 1 : 2;
    const autorite = [0, 1, 3, 7, 8, 9].includes(sourceIndex) ? 2 : 1; // ANSSI, CERT, etc. ont 2
    const exactitude = (i % 6 === 0) ? 1 : 2;
    const objectif = (i % 5 === 0) ? 1 : 2;
    const rigueur = actualite + autorite + exactitude + objectif; // /8
    const total = pertinence + rigueur; // /11

    craap = { pertinence, actualite, autorite, exactitude, objectif, rigueur, total };

    // Application stricte des règles de filtrage :
    // 1. pertinence >= 2 requis
    // 2. rigueur >= 6 sur 8 requis
    if (pertinence < 2) {
      reliability = 'Écarté'; // Hors sujet ou pertinence insuffisante (< 2/3)
    } else if (rigueur < 6) {
      reliability = 'À vérifier'; // Pertinent mais rigueur insuffisante (< 6/8)
    } else {
      reliability = 'Fiable'; // Passe les 2 filtres (>=2/3 et >=6/8, donc >=8/11)
    }
  }

  const reprisesCount = (i * 7) % 9;
  const possibleSources = sources.filter(s => s !== source);
  const reprises_sources = Array.from({ length: Math.min(reprisesCount, 4) }, (_, idx) => possibleSources[(i + idx) % possibleSources.length] ?? 'CERT-FR');

  return {
    id: i + 1,
    date: date.toISOString().slice(0, 10),
    title: fullTitle,
    source,
    language: [0, 3, 6, 8, 9].includes(i % 10) ? 'FR' : 'EN',
    theme,
    craap,
    score: craap ? craap.total : null,
    reliability,
    reprises: reprisesCount,
    reprises_sources,
    collection: ['ok', 'lien_redirection', 'echec_http', 'robots', 'vide', 'non traité'][i % 6] ?? 'ok',
    url: `https://${['thehackernews.com','www.bleepingcomputer.com','www.technologyreview.com','cyber.gouv.fr','www.darkreading.com','www.securityweek.com','www.lemondeinformatique.fr','security.googleblog.com','www.microsoft.com/en-us/security/blog','www.cert.ssi.gouv.fr'][sourceIndex]}/`,
    notability: craap ? Math.min(100, Math.round(reprisesCount * 8 + craap.total * 4.5 + (craap.autorite === 2 ? 15 : 0))) : 20,
    resume: excerpts[i % excerpts.length] ?? 'Résumé technique de l’article extrait automatiquement.',
    justification_craap: craap && craap.pertinence < 2
      ? 'Pertinence insuffisante (< 2/3) : le sujet aborde l’IA sans lien direct avec la sécurité informatique.'
      : craap && craap.rigueur < 6
      ? 'Rigueur limitée (< 6/8) : source d’actualité grand public ou manque d’éléments techniques vérifiables.'
      : 'Plein cœur de cible avec haute autorité de la source et éléments techniques vérifiables.',
    justification_theme: theme
      ? `Article rattaché à ${theme} en raison des termes clés et concepts dominants identifiés dans le corps de texte.`
      : 'Thème en cours de qualification par le classifieur automatique.',
  };
});

export const updatedAt = '13 octobre 2026';

export const formatDate = (date: string) =>
  new Date(`${date}T12:00:00Z`).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC' });

export const themeName = (code: string) =>
  themes.find(t => t.code === code)?.name ?? 'À classer';

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
  return `${a.source}. « ${a.title} ». ${formatDate(a.date)}. ${a.url}`;
}

export function pageHead(title: string, description: string) {
  return {
    meta: [
      { title: `${title} · Veille IA & Cybersécurité` },
      { name: 'description', content: description },
      { property: 'og:title', content: `${title} · Veille IA & Cybersécurité` },
      { property: 'og:description', content: description },
      { property: 'og:type', content: 'website' },
      { name: 'twitter:card', content: 'summary_large_image' },
    ],
  };
}
