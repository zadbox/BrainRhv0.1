import * as React from 'react';
import { X } from 'lucide-react';
import { cn } from '../../lib/utils';

export interface Toast {
  id: string;
  title?: string;
  description?: string;
  type?: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
}

interface ToastProps extends Toast {
  onClose: (id: string) => void;
}

const Toast: React.FC<ToastProps> = ({ id, title, description, type = 'info', onClose }) => {
  const typeStyles = {
    success: 'bg-success/10 border-success text-success',
    error: 'bg-destructive/10 border-destructive text-destructive',
    warning: 'bg-warning/10 border-[hsl(var(--warning))] text-[hsl(var(--warning))]',
    info: 'bg-primary/10 border-primary text-primary',
  };

  return (
    <div
      className={cn(
        'pointer-events-auto w-full max-w-sm overflow-hidden rounded-lg border-2 shadow-lg',
        'animate-in slide-in-from-right-full',
        typeStyles[type]
      )}
    >
      <div className="p-4">
        <div className="flex items-start gap-3">
          <div className="flex-1">
            {title && <p className="font-semibold">{title}</p>}
            {description && <p className="text-sm opacity-90 mt-1">{description}</p>}
          </div>
          <button
            onClick={() => onClose(id)}
            className="flex-shrink-0 rounded-md p-1 hover:bg-black/5 transition-colors"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export { Toast };
