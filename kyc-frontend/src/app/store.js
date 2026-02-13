import { create } from "zustand";
import { persist } from "zustand/middleware";

export const useKycStore = create(
  persist(
    (set) => ({
      user: null,
      ocrData: null,
      similarity: null,
      kycStatus: null,

      setUser: (user) => set({ user }),
      setOcrData: (data) => set({ ocrData: data }),
      setSimilarity: (score) => set({ similarity: score }),
      setKycStatus: (status) => set({ kycStatus: status }),

      logout: () =>
        set({
          user: null,
          ocrData: null,
          similarity: null,
          kycStatus: null,
        }),
    }),
    {
      name: "kyc-storage", // saved in localStorage
    },
  ),
);
