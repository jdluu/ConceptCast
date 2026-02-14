import { create } from 'zustand';
import { NavId } from '../../components/layout/DashboardLayout';

interface NavState {
    currentNav: NavId;
    setCurrentNav: (nav: NavId) => void;
}

export const useNavStore = create<NavState>((set) => ({
    currentNav: 'new-project',
    setCurrentNav: (nav) => set({ currentNav: nav }),
}));
