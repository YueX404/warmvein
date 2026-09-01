/** Mock-first switch. Set VITE_USE_MOCK=0 to hit the real FastAPI backend. */
export const useMock = import.meta.env.VITE_USE_MOCK !== "0";
