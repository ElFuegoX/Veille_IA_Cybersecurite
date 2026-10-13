import { cn } from '@/lib/utils';
export function StatusBadge({ value }: { value: string }) {
  const style = value === 'Fiable' || value === 'Validé' || value === 'ok' ? 'status-good' : value === 'À vérifier' || value === 'En attente' ? 'status-warning' : value === 'Écarté' || value === 'echec_http' ? 'status-bad' : 'status-neutral';
  return <span className={cn('status-badge', style)}><span className="status-dot" />{value}</span>;
}
