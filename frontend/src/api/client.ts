import type { AuthResponse, Device, DeviceSettings, ImageFile, NetworkSettings, SendJob, User } from "../types/domain";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";
const TOKEN_KEY = "mock-terminal-token";

export function getStoredToken(): string | null {
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string | null) {
  if (token) {
    window.localStorage.setItem(TOKEN_KEY, token);
  } else {
    window.localStorage.removeItem(TOKEN_KEY);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(getStoredToken() ? { Authorization: `Bearer ${getStoredToken()}` } : {}),
      ...(init?.headers ?? {})
    },
    ...init
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`HTTP ${response.status}: ${detail || response.statusText}`);
  }

  return response.json() as Promise<T>;
}

export const api = {
  register: (email: string, password: string) =>
    request<AuthResponse>("/auth/register", { method: "POST", body: JSON.stringify({ email, password }) }),
  login: (email: string, password: string) =>
    request<AuthResponse>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  me: () => request<User>("/auth/me"),
  getNetwork: () => request<NetworkSettings>("/settings/network"),
  updateNetwork: (data: NetworkSettings) =>
    request<NetworkSettings>("/settings/network", { method: "PUT", body: JSON.stringify(data) }),
  getDevices: () => request<Device[]>("/devices"),
  updateDeviceSettings: (deviceName: string, data: DeviceSettings) =>
    request<Device>(`/devices/${deviceName}/settings`, { method: "PUT", body: JSON.stringify(data) }),
  getImages: () => request<ImageFile[]>("/images"),
  refreshImages: () => request<ImageFile[]>("/images/refresh", { method: "POST" }),
  updateImages: (images: Record<string, boolean>) =>
    request<ImageFile[]>("/images", { method: "PUT", body: JSON.stringify({ images }) }),
  startSending: (deviceName: string) => request<SendJob>(`/devices/${deviceName}/send`, { method: "POST" }),
  getSendJob: (jobId: number) => request<SendJob>(`/send-jobs/${jobId}`),
  sendCardEvent: (deviceName: string, cardNumber: string) =>
    request<{ status_code: number }>(`/devices/${deviceName}/card-event`, {
      method: "POST",
      body: JSON.stringify({ card_number: cardNumber })
    })
};
