export type NetworkSettings = {
  host: string;
  port: number;
};

export type User = {
  id: number;
  email: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export type DeviceSettings = {
  device_id: string;
  delay_seconds: number;
  temperature_enabled: boolean;
  above_normal_temp: boolean;
  abnormal_temp: boolean;
  old_event: boolean;
  liveness_enabled: boolean;
  card_event: boolean;
  card_number: string;
};

export type Device = {
  name: string;
  title: string;
  supports_temperature: boolean;
  supports_card: boolean;
  supports_liveness: boolean;
  settings: DeviceSettings;
};

export type ImageFile = {
  name: string;
  selected: boolean;
  uploaded_by_user_id?: number | null;
  uploaded_by_me: boolean;
};

export type PhotoScope = "all" | "mine";

export type SendResult = {
  image_name: string;
  status_code: number;
  error?: string | null;
};

export type SendJob = {
  id: number;
  device_name: string;
  status: string;
  total: number;
  sent: number;
  progress: number;
  repeat_enabled: boolean;
  repeat_remaining_seconds?: number | null;
  target_name?: string | null;
  device_id?: string | null;
  results?: SendResult[];
};

export type BatchTarget = {
  id: string;
  name: string;
  device_name: string;
  settings: DeviceSettings;
};

export type BatchSendResponse = {
  jobs: SendJob[];
};
