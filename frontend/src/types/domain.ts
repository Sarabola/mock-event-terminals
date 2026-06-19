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
  temperature_enabled: boolean;
  above_normal_temp: boolean;
  abnormal_temp: boolean;
  old_event: boolean;
  card_event: boolean;
  card_number: string;
};

export type Device = {
  name: string;
  title: string;
  supports_temperature: boolean;
  supports_card: boolean;
  settings: DeviceSettings;
};

export type ImageFile = {
  name: string;
  selected: boolean;
};

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
  results?: SendResult[];
};
