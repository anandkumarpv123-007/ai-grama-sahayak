"use client";

export type ConnectivityStatus = "online" | "offline" | "backend_unreachable";

export interface ConnectivityState {
  status: ConnectivityStatus;
  isBrowserOnline: boolean;
  isBackendReachable: boolean;
  lastChecked: string;
}

type ConnectivityListener = (state: ConnectivityState) => void;

const listeners: Set<ConnectivityListener> = new Set();

let currentState: ConnectivityState = {
  status: typeof navigator !== "undefined" && navigator.onLine ? "online" : "offline",
  isBrowserOnline: typeof navigator !== "undefined" ? navigator.onLine : true,
  isBackendReachable: true,
  lastChecked: new Date().toISOString(),
};

/**
 * Checks backend reachability via /api/health with a 3-second timeout.
 */
export async function probeBackendHealth(apiBaseUrl: string = "http://127.0.0.1:8000"): Promise<boolean> {
  if (typeof navigator !== "undefined" && !navigator.onLine) {
    updateState({
      status: "offline",
      isBrowserOnline: false,
      isBackendReachable: false,
      lastChecked: new Date().toISOString(),
    });
    return false;
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000);

    const res = await fetch(`${apiBaseUrl}/api/health`, {
      method: "GET",
      cache: "no-store",
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    const reachable = res.ok;
    updateState({
      status: reachable ? "online" : "backend_unreachable",
      isBrowserOnline: true,
      isBackendReachable: reachable,
      lastChecked: new Date().toISOString(),
    });
    return reachable;
  } catch {
    updateState({
      status: "backend_unreachable",
      isBrowserOnline: typeof navigator !== "undefined" ? navigator.onLine : true,
      isBackendReachable: false,
      lastChecked: new Date().toISOString(),
    });
    return false;
  }
}

function updateState(newState: ConnectivityState) {
  currentState = newState;
  listeners.forEach((listener) => {
    try {
      listener(currentState);
    } catch {
      // ignore listener errors
    }
  });
}

export function getConnectivityState(): ConnectivityState {
  return currentState;
}

export function subscribeConnectivity(listener: ConnectivityListener): () => void {
  listeners.add(listener);

  // Trigger immediate callback with current state
  listener(currentState);

  // Set up window event listeners once
  if (typeof window !== "undefined") {
    const handleOnline = () => {
      probeBackendHealth();
    };

    const handleOffline = () => {
      updateState({
        status: "offline",
        isBrowserOnline: false,
        isBackendReachable: false,
        lastChecked: new Date().toISOString(),
      });
    };

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      listeners.delete(listener);
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }

  return () => {
    listeners.delete(listener);
  };
}
