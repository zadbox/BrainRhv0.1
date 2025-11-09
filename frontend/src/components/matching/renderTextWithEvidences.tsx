import React from 'react';
import { Badge } from '../ui/badge';
import type { Evidence } from '../../api/types';

export const renderTextWithEvidences = (
  text: string,
  evidences?: Evidence[]
): React.ReactNode => {
  if (!text || !evidences || evidences.length === 0) {
    return text;
  }

  const evidenceRegex = /\[E\d+\]/g;
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let partIndex = 0;

  while ((match = evidenceRegex.exec(text)) !== null) {
    const matchText = match[0];
    const matchIndex = match.index;

    if (matchIndex > lastIndex) {
      parts.push(
        <span key={`text-${partIndex++}`}>
          {text.slice(lastIndex, matchIndex)}
        </span>
      );
    }

    const evidenceId = matchText.slice(1, -1);
    const evidence = evidences.find((item) => item.id === evidenceId);

    if (evidence) {
      parts.push(
        <span key={`badge-wrapper-${evidenceId}-${matchIndex}`} className="relative inline-block group mx-1">
          <Badge
            variant="outline"
            className="cursor-help text-blue-600 border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20"
          >
            {matchText}
          </Badge>
          <span className="hidden group-hover:flex absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 text-sm text-white bg-gray-900 rounded-lg shadow-lg w-max max-w-xs flex-col">
            <span className="font-semibold">{evidence.type}:</span> {evidence.ref}
            <span className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900" />
          </span>
        </span>
      );
    } else {
      parts.push(
        <span key={`unknown-${partIndex++}`}>{matchText}</span>
      );
    }

    lastIndex = matchIndex + matchText.length;
  }

  if (lastIndex < text.length) {
    parts.push(
      <span key={`text-${partIndex++}`}>
        {text.slice(lastIndex)}
      </span>
    );
  }

  return <>{parts}</>;
};

