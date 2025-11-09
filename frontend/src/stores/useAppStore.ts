import { create } from 'zustand';

interface AppState {
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebar: () => void;
}

export const useAppStore = create<AppState>((set) => {
  // Load sidebar state from localStorage
  const storedCollapsed = localStorage.getItem('sidebar-collapsed');
  const initialCollapsed = storedCollapsed ? JSON.parse(storedCollapsed) : false;

  return {
    sidebarCollapsed: initialCollapsed,
    setSidebarCollapsed: (collapsed) => {
      set({ sidebarCollapsed: collapsed });
      localStorage.setItem('sidebar-collapsed', JSON.stringify(collapsed));
    },
    toggleSidebar: () => {
      set((state) => {
        const newCollapsed = !state.sidebarCollapsed;
        localStorage.setItem('sidebar-collapsed', JSON.stringify(newCollapsed));
        return { sidebarCollapsed: newCollapsed };
      });
    },
  };
});
