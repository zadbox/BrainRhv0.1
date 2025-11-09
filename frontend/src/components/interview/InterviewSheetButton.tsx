import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ClipboardList } from 'lucide-react';
import { Button } from '../ui/button';
import { interviewSheetApi } from '../../api/interviewSheet';

interface InterviewSheetButtonProps {
  candidateId: string;
  jobId: string;
  matchingId: string;
  variant?: 'default' | 'outline' | 'ghost';
  size?: 'default' | 'sm' | 'lg' | 'icon';
  className?: string;
}

export function InterviewSheetButton({
  candidateId,
  jobId,
  matchingId,
  variant = 'default',
  size = 'sm',
  className = ''
}: InterviewSheetButtonProps) {
  const navigate = useNavigate();
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleClick = async () => {
    setIsGenerating(true);
    setError(null);

    try {
      const response = await interviewSheetApi.generateOrOpen({
        candidate_id: candidateId,
        job_id: jobId,
        matching_id: matchingId,
        interviewer_id: 'default'
      });

      navigate(`/interviews/${response.interview_sheet_id}`);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Échec de la génération de la fiche d\'entretien';
      setError(errorMessage);
      console.error('Error generating interview sheet:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <>
      <Button
        onClick={handleClick}
        disabled={isGenerating}
        variant={variant}
        size={size}
        className={className}
      >
        <ClipboardList className="mr-2 h-4 w-4" />
        {isGenerating ? 'Génération...' : 'Préparer entretien'}
      </Button>
      {error && (
        <p className="text-sm text-red-600 mt-1">{error}</p>
      )}
    </>
  );
}
