import { Badge } from '../ui/badge';
import { AlertCircle, Clock, AlertTriangle } from 'lucide-react';
import type { Evidence, Flags } from '../../api/types';

interface EvidencePanelProps {
  evidences?: Evidence[];
  flags?: Flags;
  className?: string;
}

export const EvidencePanel: React.FC<EvidencePanelProps> = ({
  evidences,
  flags,
  className = ''
}) => {
  const hasEvidences = evidences && evidences.length > 0;
  const hasGaps = flags?.gappes && flags.gappes.length > 0;
  const hasOverlaps = flags?.overlaps && flags.overlaps.length > 0;
  const hasContent = hasEvidences || hasGaps || hasOverlaps;

  if (!hasContent) return null;

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Flags de vigilance - Trous et Chevauchements */}
      {(hasGaps || hasOverlaps) && (
        <div className="space-y-3">
          <p className="text-sm font-semibold flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-orange-600" />
            Drapeaux de vigilance:
          </p>

          {/* Trous (Gaps) */}
          {hasGaps && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
              <div className="flex items-start gap-2 mb-2">
                <Clock className="h-4 w-4 text-red-600 mt-0.5" />
                <span className="text-sm font-semibold text-red-800 dark:text-red-200">
                  Trous détectés ({flags.gappes!.length})
                </span>
              </div>
              <div className="space-y-2 ml-6">
                {flags.gappes!.map((gap, idx) => (
                  <div key={idx} className="text-sm">
                    <div className="flex items-start gap-2">
                      <Badge variant="destructive" className="text-xs">
                        {gap.duration_months} mois
                      </Badge>
                      <div>
                        <p className="text-red-700 dark:text-red-300">
                          {gap.period}
                        </p>
                        <p className="text-red-600 dark:text-red-400 text-xs mt-1">
                          Entre: {gap.between}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Chevauchements (Overlaps) */}
          {hasOverlaps && (
            <div className="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg p-3">
              <div className="flex items-start gap-2 mb-2">
                <AlertTriangle className="h-4 w-4 text-orange-600 mt-0.5" />
                <span className="text-sm font-semibold text-orange-800 dark:text-orange-200">
                  Chevauchements détectés ({flags.overlaps!.length})
                </span>
              </div>
              <div className="space-y-2 ml-6">
                {flags.overlaps!.map((overlap, idx) => (
                  <div key={idx} className="text-sm">
                    <div className="flex items-start gap-2">
                      <Badge
                        variant={overlap.same_company ? "outline" : "secondary"}
                        className="text-xs"
                      >
                        {overlap.overlap_days} jours
                      </Badge>
                      <div>
                        <p className="text-orange-700 dark:text-orange-300">
                          {overlap.overlap_period}
                          {overlap.same_company && (
                            <span className="ml-2 text-xs text-orange-600 dark:text-orange-400">
                              (même entreprise)
                            </span>
                          )}
                        </p>
                        <p className="text-orange-600 dark:text-orange-400 text-xs mt-1">
                          {overlap.experiences}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Evidences - Preuves justificatives */}
      {hasEvidences && (
        <div>
          <p className="text-sm font-semibold mb-2">Preuves justificatives:</p>
          <div className="space-y-1.5">
            {evidences!.map((evidence) => {
              // Icône selon le type
              const typeIcon = evidence.type === 'quote' ? '💬' :
                              evidence.type === 'section' ? '📄' :
                              evidence.type === 'json_path' ? '🔗' : '📌';

              // Couleur selon le type
              const typeColor = evidence.type === 'quote' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-200 border-blue-300' :
                               evidence.type === 'section' ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-200 border-green-300' :
                               'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200 border-gray-300';

              return (
                <div
                  key={evidence.id}
                  className={`flex items-start gap-2 p-2 rounded border ${typeColor} text-sm`}
                >
                  <span className="font-mono font-bold text-xs mt-0.5 min-w-[2rem]">
                    [{evidence.id}]
                  </span>
                  <div className="flex-1">
                    <span className="mr-2">{typeIcon}</span>
                    <span className="text-xs opacity-70 mr-2">({evidence.type})</span>
                    <span>{evidence.ref}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

