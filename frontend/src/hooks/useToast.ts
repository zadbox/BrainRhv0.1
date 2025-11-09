import { useToastStore } from '../stores/useToastStore';

export const useToast = () => {
  const { addToast } = useToastStore();

  return {
    toast: (options: {
      title?: string;
      description?: string;
      type?: 'success' | 'error' | 'warning' | 'info';
      duration?: number;
    }) => addToast(options),

    success: (title: string, description?: string) =>
      addToast({ title, description, type: 'success' }),

    error: (title: string, description?: string) =>
      addToast({ title, description, type: 'error' }),

    warning: (title: string, description?: string) =>
      addToast({ title, description, type: 'warning' }),

    info: (title: string, description?: string) =>
      addToast({ title, description, type: 'info' }),
  };
};
