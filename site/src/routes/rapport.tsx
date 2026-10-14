import { createFileRoute } from '@tanstack/react-router';
import { Download, FileText, CalendarDays, ExternalLink, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { PageIntro } from '@/components/veille/shell';
import { pageHead } from '@/lib/veille';

export const Route = createFileRoute('/rapport')({
  head: () =>
    pageHead(
      'Rapport final',
      'Le rapport universitaire présente la méthode, l’analyse du corpus, les limites et les conclusions de la veille sur l’IA et la cybersécurité.'
    ),
  component: Report,
});

function Report() {
  const pdfUrl = `${import.meta.env.BASE_URL}rapport-veille.pdf`;

  return (
    <main className="page-container report-page">
      <PageIntro
        section="RAPPORT"
        title="Rapport de synthèse"
        description="Le livrable complet pour une lecture approfondie de notre veille sur l’IA et la cybersécurité."
      >
        <Button asChild variant="outline">
          <a href={pdfUrl} target="_blank" rel="noreferrer">
            <ExternalLink size={15} />
            Ouvrir en plein écran
          </a>
        </Button>
        <Button asChild>
          <a href={pdfUrl} download="rapport-veille.pdf">
            <Download size={15} />
            Télécharger le PDF
          </a>
        </Button>
      </PageIntro>

      <section className="report-section">
        <div className="report-document" aria-hidden="true">
          <div className="document-top">
            <span>VEILLE UNIVERSITAIRE</span>
            <FileText size={23} />
          </div>
          <div className="document-title">
            Intelligence artificielle
            <br />& cybersécurité
          </div>
          <div className="document-rule" />
          <p>Rapport de veille & Plan d’action</p>
          <div className="document-lines">
            <span />
            <span />
            <span />
            <span />
          </div>
          <div className="document-bottom">
            PROJET UNIVERSITAIRE<span>2026</span>
          </div>
          <span className="document-draft bg-primary text-primary-foreground font-bold">
            DOCUMENT DISPONIBLE
          </span>
        </div>

        <div className="report-content">
          <span className="report-status bg-series-2/15 text-series-2 font-semibold">
            <Sparkles size={14} />
            Rapport complet disponible
          </span>
          <h2>
            Synthèse du corpus
            <br />
            et analyse des tendances
          </h2>
          <p>
            Ce document détaille la démarche méthodologique de veille, les critères de sélection CRAAP, l’analyse approfondie des risques émergents et la classification thématique opérée par l’IA.
          </p>
          <div className="report-meta">
            <span>
              <FileText size={16} />
              Format PDF (Document officiel)
            </span>
            <span>
              <CalendarDays size={16} />
              Édition : Octobre 2026
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Button size="lg" asChild className="gap-2">
              <a href={pdfUrl} target="_blank" rel="noreferrer">
                <FileText size={16} />
                Lire le rapport PDF
              </a>
            </Button>
            <Button size="lg" variant="outline" asChild className="gap-2">
              <a href={pdfUrl} download="rapport-veille.pdf">
                <Download size={16} />
                Télécharger
              </a>
            </Button>
          </div>
        </div>
      </section>

      {/* Lecteur / intégration directe du PDF */}
      <section className="mt-8 rounded-xl border bg-card p-4 sm:p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b">
          <div>
            <h3 className="font-bold text-base text-foreground font-display">
              Aperçu direct du document
            </h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              Consultez le document directement ci-dessous ou ouvrez-le dans votre lecteur PDF.
            </p>
          </div>
          <Button variant="ghost" size="sm" asChild className="text-xs gap-1.5">
            <a href={pdfUrl} target="_blank" rel="noreferrer">
              Plein écran <ExternalLink size={13} />
            </a>
          </Button>
        </div>
        <div className="w-full h-[650px] mt-4 rounded-lg overflow-hidden border bg-muted/30">
          <iframe
            src={`${pdfUrl}#toolbar=1`}
            title="Rapport de veille IA et Cybersécurité"
            className="w-full h-full border-0"
          />
        </div>
      </section>

    </main>
  );
}
