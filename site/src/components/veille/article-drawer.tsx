import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet';
import { StatusBadge } from '@/components/veille/badge';
import { Button } from '@/components/ui/button';
import { ExternalLink, Copy, Check, Sparkles, ShieldAlert, Newspaper, Calendar, Globe2, BookOpen } from 'lucide-react';
import { useState } from 'react';
import { type Article, formatDate, themeName, reference } from '@/lib/veille';

export function ArticleDrawer({
  article,
  open,
  onOpenChange,
}: {
  article: Article | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [copied, setCopied] = useState(false);

  if (!article) return null;

  async function handleCopy() {
    if (!article) return;
    try {
      await navigator.clipboard.writeText(reference(article));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
    }
  }

  const craap = article.craap;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-xl overflow-y-auto p-6 sm:p-8">
        <SheetHeader className="text-left space-y-3 pb-5 border-b">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <Globe2 size={14} className="text-primary" />
              {article.source}
            </span>
            <div className="flex items-center gap-2">
              <span className="text-xs px-2 py-0.5 rounded border font-semibold text-muted-foreground">
                {article.language}
              </span>
              <StatusBadge value={article.reliability} />
            </div>
          </div>

          <SheetTitle className="text-xl sm:text-2xl font-bold leading-snug tracking-tight font-display text-foreground">
            {article.title}
          </SheetTitle>

          <SheetDescription className="flex items-center gap-2 text-xs text-muted-foreground">
            <Calendar size={13} />
            Publié le {formatDate(article.date)}
          </SheetDescription>
        </SheetHeader>

        <div className="py-6 space-y-6">
          {/* Actions rapides */}
          <div className="flex flex-wrap items-center gap-2.5">
            <Button asChild size="sm" className="gap-2 text-xs">
              <a href={article.url} target="_blank" rel="noreferrer">
                Consulter la source originale <ExternalLink size={13} />
              </a>
            </Button>
            <Button variant="outline" size="sm" onClick={handleCopy} className="gap-2 text-xs">
              {copied ? <Check size={13} className="text-series-2" /> : <Copy size={13} />}
              {copied ? 'Référence copiée' : 'Copier la référence'}
            </Button>
          </div>

          {/* Résumé / Chapeau */}
          <div className="space-y-2 p-4 rounded-lg bg-muted/60 border">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
              <BookOpen size={14} className="text-primary" />
              Extrait & Résumé de l’article
            </div>
            <p className="text-sm leading-relaxed text-muted-foreground">
              {article.resume}
            </p>
          </div>

          {/* Grille d'évaluation CRAAP automatique */}
          <div className="space-y-4 p-5 rounded-lg border bg-card shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-sm font-bold tracking-tight text-foreground">
                  Évaluation de fiabilité CRAAP
                </h4>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Filtre d’entrée (Pertinence) + Score de rigueur (/8)
                </p>
              </div>
              <div className="text-right">
                <span className="text-2xl font-extrabold font-display text-primary">
                  {article.score ?? '—'}
                </span>
                <span className="text-xs text-muted-foreground font-semibold">/11</span>
              </div>
            </div>

            {craap ? (
              <div className="space-y-3 pt-2">
                {/* 1. Filtre d'entrée : Pertinence */}
                <div className="p-3 rounded-md bg-background border space-y-1.5">
                  <div className="flex items-center justify-between text-xs font-medium">
                    <span className="font-semibold text-foreground">
                      1. Filtre thématique (Pertinence)
                    </span>
                    <span className={craap.pertinence >= 2 ? 'text-series-2 font-bold' : 'text-danger font-bold'}>
                      {craap.pertinence} / 3 {craap.pertinence >= 2 ? '(Validé)' : '(Éliminatoire)'}
                    </span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${craap.pertinence >= 2 ? 'bg-series-2' : 'bg-danger'}`}
                      style={{ width: `${(craap.pertinence / 3) * 100}%` }}
                    />
                  </div>
                  <p className="text-[11px] text-muted-foreground pt-0.5">
                    Seuil minimum requis : 2 / 3 pour être retenu dans le corpus de veille.
                  </p>
                </div>

                {/* 2. Rigueur globale */}
                <div className="p-3 rounded-md bg-background border space-y-2">
                  <div className="flex items-center justify-between text-xs font-medium">
                    <span className="font-semibold text-foreground">
                      2. Rigueur méthodologique (4 critères)
                    </span>
                    <span className={craap.rigueur >= 5 ? 'text-series-2 font-bold' : 'text-warning font-bold'}>
                      {craap.rigueur} / 8 {craap.rigueur >= 5 ? '(Admis)' : '(Insuffisant)'}
                    </span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${craap.rigueur >= 5 ? 'bg-series-2' : 'bg-warning'}`}
                      style={{ width: `${(craap.rigueur / 8) * 100}%` }}
                    />
                  </div>

                  {/* Sous-critères sur 2 points chacun */}
                  <div className="grid grid-cols-2 gap-2 pt-2 text-xs">
                    <div className="flex items-center justify-between p-2 rounded bg-muted/40">
                      <span className="text-muted-foreground">Actualité :</span>
                      <strong className="font-medium text-foreground">{craap.actualite} / 2</strong>
                    </div>
                    <div className="flex items-center justify-between p-2 rounded bg-muted/40">
                      <span className="text-muted-foreground">Autorité :</span>
                      <strong className="font-medium text-foreground">{craap.autorite} / 2</strong>
                    </div>
                    <div className="flex items-center justify-between p-2 rounded bg-muted/40">
                      <span className="text-muted-foreground">Exactitude :</span>
                      <strong className="font-medium text-foreground">{craap.exactitude} / 2</strong>
                    </div>
                    <div className="flex items-center justify-between p-2 rounded bg-muted/40">
                      <span className="text-muted-foreground">Objectivité :</span>
                      <strong className="font-medium text-foreground">{craap.objectif} / 2</strong>
                    </div>
                  </div>
                </div>

                {article.justification_craap && (
                  <p className="text-xs text-muted-foreground pt-2 border-t border-border/50">
                    {article.justification_craap.replace(/\[(?:règles|IA gemini|IA groq)\]/gi, '').trim()}
                  </p>
                )}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground italic py-2">
                Évaluation automatique en attente pour cet article.
              </p>
            )}
          </div>

          {/* Sous-thème & Justification de classification */}
          <div className="space-y-3 p-4 rounded-lg border bg-card">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                Classification automatique
              </span>
              <span className="text-xs font-bold px-2.5 py-1 rounded bg-primary/10 text-primary">
                {article.theme ? `${article.theme} · ${themeName(article.theme)}` : 'À classer'}
              </span>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              {article.justification_theme}
            </p>
          </div>

          {/* Propagation médiatique & Reprises */}
          <div className="space-y-3 p-4 rounded-lg border bg-card">
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center gap-1.5 text-xs font-bold text-foreground">
                <Newspaper size={14} className="text-primary" />
                Écho médiatique & Reprises
              </span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-muted text-muted-foreground">
                {article.reprises} source{article.reprises > 1 ? 's' : ''} reprise{article.reprises > 1 ? 's' : ''}
              </span>
            </div>
            {article.reprises > 0 ? (
              <div className="space-y-2">
                <p className="text-xs text-muted-foreground">
                  Le même sujet a été couvert par d’autres éditeurs du corpus de veille :
                </p>
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {article.reprises_sources.map((src, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 text-[11px] px-2 py-1 rounded bg-muted/80 text-foreground border"
                    >
                      {src}
                    </span>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">
                Article exclusif ou non encore repris par d’autres sources suivies.
              </p>
            )}
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
