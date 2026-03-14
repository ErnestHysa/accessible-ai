import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, Website, Scan } from '@/types';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  setAuth: (tokens: { access_token: string; refresh_token: string }, user: User) => void;
  clearAuth: () => void;
  setUser: (user: User) => void;
}

interface WebsitesState {
  websites: Website[];
  selectedWebsite: Website | null;
  isLoading: boolean;
  setWebsites: (websites: Website[]) => void;
  addWebsite: (website: Website) => void;
  updateWebsite: (id: string, updates: Partial<Website>) => void;
  removeWebsite: (id: string) => void;
  setSelectedWebsite: (website: Website | null) => void;
  setLoading: (loading: boolean) => void;
}

interface ScansState {
  scans: Scan[];
  activeScan: Scan | null;
  isScanning: boolean;
  setScans: (scans: Scan[]) => void;
  addScan: (scan: Scan) => void;
  setActiveScan: (scan: Scan | null) => void;
  setScanning: (scanning: boolean) => void;
  updateScan: (id: string, updates: Partial<Scan>) => void;
}

interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  notifications: Array<{ id: string; message: string; type: 'success' | 'error' | 'info' }>;
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
  addNotification: (notification: Omit<{ id: string; message: string; type: 'success' | 'error' | 'info' }, 'id'>) => void;
  removeNotification: (id: string) => void;
}

// Auth store with persistence
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      setAuth: (tokens, user) =>
        set({
          accessToken: tokens.access_token,
          refreshToken: tokens.refresh_token,
          user,
          isAuthenticated: true,
        }),
      clearAuth: () =>
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        }),
      setUser: (user) => set({ user }),
    }),
    {
      name: 'accessible-ai-auth',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Websites store
export const useWebsiteStore = create<WebsitesState>((set) => ({
  websites: [],
  selectedWebsite: null,
  isLoading: false,
  setWebsites: (websites) => set({ websites }),
  addWebsite: (website) => set((state) => ({ websites: [...state.websites, website] })),
  updateWebsite: (id, updates) =>
    set((state) => ({
      websites: state.websites.map((w) => (w.id === id ? { ...w, ...updates } : w)),
      selectedWebsite:
        state.selectedWebsite?.id === id
          ? { ...state.selectedWebsite, ...updates }
          : state.selectedWebsite,
    })),
  removeWebsite: (id) =>
    set((state) => ({
      websites: state.websites.filter((w) => w.id !== id),
      selectedWebsite: state.selectedWebsite?.id === id ? null : state.selectedWebsite,
    })),
  setSelectedWebsite: (website) => set({ selectedWebsite: website }),
  setLoading: (isLoading) => set({ isLoading }),
}));

// Scans store
export const useScanStore = create<ScansState>((set) => ({
  scans: [],
  activeScan: null,
  isScanning: false,
  setScans: (scans) => set({ scans }),
  addScan: (scan) => set((state) => ({ scans: [scan, ...state.scans] })),
  setActiveScan: (scan) => set({ activeScan: scan }),
  setScanning: (isScanning) => set({ isScanning }),
  updateScan: (id, updates) =>
    set((state) => ({
      scans: state.scans.map((s) => (s.id === id ? { ...s, ...updates } : s)),
      activeScan: state.activeScan?.id === id ? { ...state.activeScan, ...updates } : state.activeScan,
    })),
}));

// UI store with persistence
export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      theme: 'light',
      notifications: [],
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setTheme: (theme) => set({ theme }),
      addNotification: (notification) =>
        set((state) => ({
          notifications: [
            ...state.notifications,
            { ...notification, id: Date.now().toString() },
          ],
        })),
      removeNotification: (id) =>
        set((state) => ({
          notifications: state.notifications.filter((n) => n.id !== id),
        })),
    }),
    {
      name: 'accessible-ai-ui',
      partialize: (state) => ({ theme: state.theme }),
    }
  )
);
