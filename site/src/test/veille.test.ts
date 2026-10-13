import { describe, it, expect } from 'vitest';
import { articles, sources, publicCsv, filterArticles, defaultFilters } from '@/lib/veille';
describe('Corpus public de démonstration',()=>{
 it('contient les 201 articles demandés',()=>expect(articles).toHaveLength(201));
 it('suit les 10 sources demandées',()=>{expect(sources).toHaveLength(10);expect(new Set(articles.map(a=>a.source)).size).toBe(10);});
 it('contient une majorité d’articles anglais',()=>expect(articles.filter(a=>a.language==='EN').length).toBeGreaterThan(articles.filter(a=>a.language==='FR').length));
 it('conserve les scores CRAAP manquants non évalués',()=>{const rows=articles.filter(a=>a.score===null);expect(rows.length).toBeGreaterThan(0);expect(rows.every(a=>a.reliability==='Non évalué')).toBe(true);});
 it('conserve des sous-thèmes à classer',()=>expect(articles.filter(a=>a.theme==='').length).toBeGreaterThan(0));
 it('inclut les six statuts de collecte demandés',()=>expect([...new Set(articles.map(a=>a.collection))].sort()).toEqual(['ok','lien_redirection','echec_http','robots','vide','non traité'].sort()));
 it('combine les filtres de langue et de fiabilité',()=>{const rows=filterArticles(articles,{...defaultFilters,language:'FR',reliability:'Fiable'});expect(rows.length).toBeGreaterThan(0);expect(rows.every(a=>a.language==='FR'&&a.reliability==='Fiable')).toBe(true);});
 it('trie les scores CRAAP en conservant les valeurs vides en dernier',()=>{const rows=filterArticles(articles,{...defaultFilters,sort:'score'});expect(rows[0]?.score).toBe(50);expect(rows.at(-1)?.score).toBeNull();});
 it('exporte uniquement les champs publics sans texte intégral',()=>{const csv=publicCsv(articles);expect(csv.split('\r\n')).toHaveLength(202);expect(csv.split('\r\n')[0]).toBe('\uFEFF"date";"titre";"source";"langue";"sous_theme";"score_CRAAP";"fiabilite";"nb_sources_reprise";"validation";"statut_collecte";"url"');});
});
