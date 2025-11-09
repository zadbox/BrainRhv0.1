import { AlertCircle } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import type { APIError } from '../../api/types';

interface ErrorBannerProps {
  error: APIError | Error | string;
  className?: string;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({ error, className }) => {
  let code = 'ERROR';
  let message = 'Une erreur est survenue';
  let details: unknown = null;

  if (typeof error === 'string') {
    message = error;
  } else if ('code' in error && 'message' in error) {
    // APIError
    code = error.code;
    message = error.message;
    details = error.details;
  } else if (error instanceof Error) {
    message = error.message;
  }

  const hasDetails = details !== null && details !== undefined;

  return (
    <Alert variant="destructive" className={className}>
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>
        {code !== 'ERROR' && <span className="font-mono text-xs mr-2">[{code}]</span>}
        Erreur
      </AlertTitle>
      <AlertDescription>
        <p>{message}</p>
        {hasDetails && (
          <pre className="mt-2 text-xs overflow-auto max-h-40 bg-destructive/10 p-2 rounded">
            {JSON.stringify(details, null, 2)}
          </pre>
        )}
      </AlertDescription>
    </Alert>
  );
};
