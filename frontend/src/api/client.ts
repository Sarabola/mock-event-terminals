import type {
  AuthResponse,
  BatchSendResponse,
  BatchTarget,
  Device,
  DeviceSettings,
  ImageFile,
  NetworkSettings,
  PhotoScope,
  SendJob,
  User
} from "../types/domain";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api";
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
  const isFormData = init?.body instanceof FormData;
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
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
  changePassword: (email: string, password: string) =>
    request<User>("/auth/password", { method: "PUT", body: JSON.stringify({ email, password }) }),
  getNetwork: () => request<NetworkSettings>("/settings/network"),
  updateNetwork: (data: NetworkSettings) =>
    request<NetworkSettings>("/settings/network", { method: "PUT", body: JSON.stringify(data) }),
  getDevices: () => request<Device[]>("/devices"),
  updateDeviceSettings: (deviceName: string, data: DeviceSettings) =>
    request<Device>(`/devices/${deviceName}/settings`, { method: "PUT", body: JSON.stringify(data) }),
  getImages: (scope: PhotoScope = "all") => request<ImageFile[]>(`/images?scope=${scope}`),
  refreshImages: (scope: PhotoScope = "all") =>
    request<ImageFile[]>(`/images/refresh?scope=${scope}`, { method: "POST" }),
  updateImages: (images: Record<string, boolean>, scope: PhotoScope = "all") =>
    request<ImageFile[]>(`/images?scope=${scope}`, { method: "PUT", body: JSON.stringify({ images }) }),
  uploadImage: (file: File, scope: PhotoScope = "all") => {
    const formData = new FormData();
    formData.append("file", file);
    return request<ImageFile[]>(`/images/upload?scope=${scope}`, { method: "POST", body: formData });
  },
  deleteImage: (imageName: string, scope: PhotoScope = "all") =>
    request<ImageFile[]>(`/images/${encodeURIComponent(imageName)}?scope=${scope}`, { method: "DELETE" }),
  renameImage: (imageName: string, newName: string, scope: PhotoScope = "all") =>
    request<ImageFile[]>(`/images/${encodeURIComponent(imageName)}/rename?scope=${scope}`, {
      method: "PUT",
      body: JSON.stringify({ new_name: newName })
    }),
  imageUrl: (imageName: string) =>
    `${API_BASE}/images/${encodeURIComponent(imageName)}/content?token=${encodeURIComponent(getStoredToken() ?? "")}`,
  startSending: (deviceName: string, repeatEnabled = false, repeatMinutes: number | null = null) =>
    request<SendJob>(`/devices/${deviceName}/send`, {
      method: "POST",
      body: JSON.stringify({ repeat_enabled: repeatEnabled, repeat_minutes: repeatMinutes })
    }),
  startBatchSending: (targets: BatchTarget[], repeatEnabled = false, repeatMinutes: number | null = null) =>
    request<BatchSendResponse>("/devices/send", {
      method: "POST",
      body: JSON.stringify({
        targets: targets.map(({ id: _id, ...target }) => target),
        repeat_enabled: repeatEnabled,
        repeat_minutes: repeatMinutes
      })
    }),
  getSendJob: (jobId: number) => request<SendJob>(`/send-jobs/${jobId}`),
  stopSending: (jobId: number) => request<SendJob>(`/send-jobs/${jobId}/stop`, { method: "POST" }),
  sendCardEvent: (deviceName: string, cardNumber: string) =>
    request<{ status_code: number }>(`/devices/${deviceName}/card-event`, {
      method: "POST",
      body: JSON.stringify({ card_number: cardNumber })
    })
};
