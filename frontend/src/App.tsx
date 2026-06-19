import { useEffect, useMemo, useState } from "react";

import { api, getStoredToken, setStoredToken } from "./api/client";
import type { Device, DeviceSettings, ImageFile, NetworkSettings, PhotoScope, SendJob, User } from "./types/domain";

const emptyNetwork: NetworkSettings = { host: "localhost", port: 9091 };

function cloneSettings(settings: DeviceSettings): DeviceSettings {
  return { ...settings };
}

export default function App() {
  const [network, setNetwork] = useState<NetworkSettings>(emptyNetwork);
  const [networkDraft, setNetworkDraft] = useState<NetworkSettings>(emptyNetwork);
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDeviceName, setSelectedDeviceName] = useState<string>("");
  const [deviceDraft, setDeviceDraft] = useState<DeviceSettings | null>(null);
  const [images, setImages] = useState<ImageFile[]>([]);
  const [photoScope, setPhotoScope] = useState<PhotoScope>("all");
  const [sendJob, setSendJob] = useState<SendJob | null>(null);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [renameDrafts, setRenameDrafts] = useState<Record<string, string>>({});
  const [editingImageName, setEditingImageName] = useState<string | null>(null);
  const [notice, setNotice] = useState<string>("");
  const [error, setError] = useState<string>("");

  const selectedDevice = useMemo(
    () => devices.find((device) => device.name === selectedDeviceName) ?? null,
    [devices, selectedDeviceName]
  );

  useEffect(() => {
    void restoreSession();
  }, []);

  useEffect(() => {
    if (!selectedDevice) return;
    setDeviceDraft(cloneSettings(selectedDevice.settings));
  }, [selectedDevice]);

  useEffect(() => {
    if (!sendJob || ["completed", "failed"].includes(sendJob.status)) return;

    const timer = window.setInterval(async () => {
      try {
        const freshJob = await api.getSendJob(sendJob.id);
        setSendJob(freshJob);
      } catch (err) {
        setError(formatError(err));
      }
    }, 1000);

    return () => window.clearInterval(timer);
  }, [sendJob]);

  async function restoreSession() {
    if (!getStoredToken()) return;
    try {
      const user = await api.me();
      setCurrentUser(user);
      await loadInitialData();
    } catch {
      setStoredToken(null);
      setCurrentUser(null);
    }
  }

  async function submitAuth() {
    try {
      setError("");
      const response =
        authMode === "login"
          ? await api.login(authEmail, authPassword)
          : await api.register(authEmail, authPassword);
      setStoredToken(response.access_token);
      setCurrentUser(response.user);
      setNotice(authMode === "login" ? "Signed in" : "Account created");
      await loadInitialData();
    } catch (err) {
      setError(formatError(err));
    }
  }

  function logout() {
    setStoredToken(null);
    setCurrentUser(null);
    setDevices([]);
    setImages([]);
    setSendJob(null);
    setDeviceDraft(null);
    setSelectedDeviceName("");
  }

  async function loadInitialData() {
    try {
      setError("");
      const [networkData, devicesData, imagesData] = await Promise.all([
        api.getNetwork(),
        api.getDevices(),
        api.refreshImages(photoScope)
      ]);
      setNetwork(networkData);
      setNetworkDraft(networkData);
      setDevices(devicesData);
      setImages(imagesData);
      setRenameDrafts(Object.fromEntries(imagesData.map((image) => [image.name, image.name])));
      setSelectedDeviceName(devicesData[0]?.name ?? "");
    } catch (err) {
      setError(formatError(err));
      if (formatError(err).includes("401")) {
        logout();
      }
    }
  }

  async function saveNetwork() {
    try {
      const saved = await api.updateNetwork(networkDraft);
      setNetwork(saved);
      setNetworkDraft(saved);
      setNotice("Network settings saved");
    } catch (err) {
      setError(formatError(err));
    }
  }

  async function saveDeviceSettings() {
    if (!selectedDevice || !deviceDraft) return;
    try {
      const updated = await api.updateDeviceSettings(selectedDevice.name, deviceDraft);
      setDevices((current) => current.map((device) => (device.name === updated.name ? updated : device)));
      setNotice("Device settings saved");
    } catch (err) {
      setError(formatError(err));
    }
  }

  async function refreshImages() {
    try {
      const refreshed = await api.refreshImages(photoScope);
      setImages(refreshed);
      setRenameDrafts(Object.fromEntries(refreshed.map((image) => [image.name, image.name])));
      setNotice("Image list refreshed");
    } catch (err) {
      setError(formatError(err));
    }
  }

  async function saveImageSelection(nextImages = images) {
    try {
      const payload = Object.fromEntries(nextImages.map((image) => [image.name, image.selected]));
      const saved = await api.updateImages(payload, photoScope);
      setImages(saved);
      setRenameDrafts(Object.fromEntries(saved.map((image) => [image.name, image.name])));
      setNotice("Photo selection saved");
    } catch (err) {
      setError(formatError(err));
    }
  }

  async function startSending() {
    if (!selectedDevice || !deviceDraft) return;
    try {
      const updated = await api.updateDeviceSettings(selectedDevice.name, deviceDraft);
      setDevices((current) => current.map((device) => (device.name === updated.name ? updated : device)));
      const payload = Object.fromEntries(images.map((image) => [image.name, image.selected]));
      const savedImages = await api.updateImages(payload, photoScope);
      setImages(savedImages);
      setRenameDrafts(Object.fromEntries(savedImages.map((image) => [image.name, image.name])));
      const job = await api.startSending(selectedDevice.name);
      setSendJob(job);
      setNotice("Sending started");
    } catch (err) {
      setError(formatError(err));
    }
  }

  async function sendCardEvent() {
    if (!selectedDevice || !deviceDraft) return;
    try {
      const updated = await api.updateDeviceSettings(selectedDevice.name, deviceDraft);
      setDevices((current) => current.map((device) => (device.name === updated.name ? updated : device)));
      const response = await api.sendCardEvent(selectedDevice.name, deviceDraft.card_number);
      setNotice(`Card event status: ${response.status_code}`);
    } catch (err) {
      setError(formatError(err));
    }
  }

  function patchDeviceDraft(patch: Partial<DeviceSettings>) {
    setDeviceDraft((current) => (current ? { ...current, ...patch } : current));
  }

  function setTemperatureMode(mode: "normal" | "above" | "abnormal") {
    patchDeviceDraft({
      above_normal_temp: mode === "above",
      abnormal_temp: mode === "abnormal"
    });
  }

  function toggleImage(imageName: string, selected: boolean) {
    setImages((current) =>
      current.map((image) => (image.name === imageName ? { ...image, selected } : image))
    );
  }

  function setAllImagesSelected(selected: boolean) {
    setImages((current) => current.map((image) => ({ ...image, selected })));
  }

  async function changePhotoScope(scope: PhotoScope) {
    try {
      setPhotoScope(scope);
      const refreshed = await api.refreshImages(scope);
      setImages(refreshed);
      setRenameDrafts(Object.fromEntries(refreshed.map((image) => [image.name, image.name])));
      setEditingImageName(null);
    } catch (err) {
      setError(formatError(err));
    }
  }

  async function uploadPhoto(file: File | null) {
    if (!file) return;
    try {
      const updated = await api.uploadImage(file, photoScope);
      setImages(updated);
      setRenameDrafts(Object.fromEntries(updated.map((image) => [image.name, image.name])));
      setNotice("Photo uploaded");
    } catch (err) {
      setError(formatError(err));
    }
  }

  async function deletePhoto(imageName: string) {
    try {
      const updated = await api.deleteImage(imageName, photoScope);
      setImages(updated);
      setRenameDrafts(Object.fromEntries(updated.map((image) => [image.name, image.name])));
      setEditingImageName(null);
      setNotice("Photo deleted");
    } catch (err) {
      setError(formatError(err));
    }
  }

  async function renamePhoto(imageName: string) {
    const newName = renameDrafts[imageName]?.trim();
    if (!newName || newName === imageName) return;
    try {
      const updated = await api.renameImage(imageName, newName, photoScope);
      setImages(updated);
      setRenameDrafts(Object.fromEntries(updated.map((image) => [image.name, image.name])));
      setEditingImageName(null);
      setNotice("Photo renamed");
    } catch (err) {
      setError(formatError(err));
    }
  }

  const selectedCount = images.filter((image) => image.selected).length;
  const temperatureMode = deviceDraft?.above_normal_temp
    ? "above"
    : deviceDraft?.abnormal_temp
      ? "abnormal"
      : "normal";

  if (!currentUser) {
    return (
      <main className="auth-shell">
        <section className="auth-panel">
          <h1>Terminal Emulator</h1>
          <div className="auth-tabs">
            <button className={authMode === "login" ? "active" : ""} onClick={() => setAuthMode("login")}>
              Login
            </button>
            <button className={authMode === "register" ? "active" : ""} onClick={() => setAuthMode("register")}>
              Register
            </button>
          </div>
          <label>
            <span>Email</span>
            <input
              type="email"
              autoComplete="email"
              value={authEmail}
              onChange={(event) => setAuthEmail(event.target.value)}
            />
          </label>
          <label>
            <span>Password</span>
            <input
              type="password"
              autoComplete={authMode === "login" ? "current-password" : "new-password"}
              value={authPassword}
              onChange={(event) => setAuthPassword(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") void submitAuth();
              }}
            />
          </label>
          <button className="primary-action" onClick={submitAuth}>
            {authMode === "login" ? "Login" : "Create Account"}
          </button>
          {error && <div className="auth-error">{error}</div>}
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>Terminal Emulator</h1>
          <p>
            {currentUser.email} · Target: {network.host}:{network.port}
          </p>
        </div>
        <div className="topbar-actions">
          <button onClick={loadInitialData}>Reload</button>
          <button onClick={logout}>Logout</button>
        </div>
      </header>

      {(notice || error) && (
        <section className={`message ${error ? "message-error" : "message-ok"}`}>
          <span>{error || notice}</span>
          <button
            aria-label="Close message"
            onClick={() => {
              setNotice("");
              setError("");
            }}
          >
            x
          </button>
        </section>
      )}

      <section className="workspace">
        <aside className="device-list">
          <div className="section-heading">
            <h2>Devices</h2>
          </div>
          {devices.map((device) => (
            <button
              className={device.name === selectedDeviceName ? "device-button active" : "device-button"}
              key={device.name}
              onClick={() => setSelectedDeviceName(device.name)}
            >
              <span>{device.title}</span>
              <small>{device.settings.device_id || "No device ID"}</small>
            </button>
          ))}
        </aside>

        <section className="main-panels">
          <section className="panel">
            <div className="section-heading">
              <h2>Network Settings</h2>
              <button onClick={saveNetwork}>Save</button>
            </div>
            <div className="form-grid two-columns">
              <label>
                <span>Host</span>
                <input
                  value={networkDraft.host}
                  onChange={(event) => setNetworkDraft({ ...networkDraft, host: event.target.value })}
                />
              </label>
              <label>
                <span>Port</span>
                <input
                  type="number"
                  min={1}
                  max={65535}
                  value={networkDraft.port}
                  onChange={(event) => setNetworkDraft({ ...networkDraft, port: Number(event.target.value) })}
                />
              </label>
            </div>
          </section>

          <section className="panel">
            <div className="section-heading">
              <h2>{selectedDevice?.title ?? "Device Settings"}</h2>
              <button onClick={saveDeviceSettings} disabled={!selectedDevice || !deviceDraft}>
                Save
              </button>
            </div>

            {deviceDraft && selectedDevice && (
              <>
                <div className="form-grid">
                  <label>
                    <span>Device ID</span>
                    <input
                      value={deviceDraft.device_id}
                      onChange={(event) => patchDeviceDraft({ device_id: event.target.value })}
                    />
                  </label>
                </div>

                {selectedDevice.supports_temperature && (
                  <div className="settings-band">
                    <label className="check-row">
                      <input
                        type="checkbox"
                        checked={deviceDraft.temperature_enabled}
                        onChange={(event) => patchDeviceDraft({ temperature_enabled: event.target.checked })}
                      />
                      <span>Temperature detection</span>
                    </label>
                    <div className="segmented" aria-label="Temperature mode">
                      <button
                        className={temperatureMode === "normal" ? "active" : ""}
                        onClick={() => setTemperatureMode("normal")}
                        disabled={!deviceDraft.temperature_enabled}
                      >
                        Normal
                      </button>
                      <button
                        className={temperatureMode === "above" ? "active" : ""}
                        onClick={() => setTemperatureMode("above")}
                        disabled={!deviceDraft.temperature_enabled}
                      >
                        Above
                      </button>
                      <button
                        className={temperatureMode === "abnormal" ? "active" : ""}
                        onClick={() => setTemperatureMode("abnormal")}
                        disabled={!deviceDraft.temperature_enabled}
                      >
                        Abnormal
                      </button>
                    </div>
                    <label className="check-row">
                      <input
                        type="checkbox"
                        checked={deviceDraft.old_event}
                        onChange={(event) => patchDeviceDraft({ old_event: event.target.checked })}
                      />
                      <span>Old event date</span>
                    </label>
                    {selectedDevice.supports_liveness && (
                      <label className="check-row">
                        <input
                          type="checkbox"
                          checked={deviceDraft.liveness_enabled}
                          onChange={(event) => patchDeviceDraft({ liveness_enabled: event.target.checked })}
                        />
                        <span>Liveness event</span>
                      </label>
                    )}
                  </div>
                )}

                {selectedDevice.supports_card && (
                  <div className="settings-band compact">
                    <label className="check-row">
                      <input
                        type="checkbox"
                        checked={deviceDraft.card_event}
                        onChange={(event) => patchDeviceDraft({ card_event: event.target.checked })}
                      />
                      <span>Card event</span>
                    </label>
                    <div className="inline-form">
                      <input
                        value={deviceDraft.card_number}
                        onChange={(event) => patchDeviceDraft({ card_number: event.target.value })}
                      />
                      <button onClick={sendCardEvent}>Send Card</button>
                    </div>
                  </div>
                )}
              </>
            )}
          </section>

          <section className="panel photo-panel">
            <div className="section-heading">
              <h2>Photos</h2>
              <div className="toolbar">
                <label className="file-button">
                  <span>Upload</span>
                  <input
                    type="file"
                    accept=".jpg,.jpeg,.png,image/jpeg,image/png"
                    onChange={(event) => {
                      void uploadPhoto(event.target.files?.[0] ?? null);
                      event.currentTarget.value = "";
                    }}
                  />
                </label>
                <button onClick={refreshImages}>Refresh</button>
                <div className="photo-filter" aria-label="Photo filter">
                  <button
                    className={photoScope === "all" ? "active" : ""}
                    onClick={() => void changePhotoScope("all")}
                  >
                    All Photos
                  </button>
                  <button
                    className={photoScope === "mine" ? "active" : ""}
                    onClick={() => void changePhotoScope("mine")}
                  >
                    My Uploads
                  </button>
                </div>
                <button onClick={() => setAllImagesSelected(true)} disabled={images.length === 0}>
                  Select All
                </button>
                <button onClick={() => setAllImagesSelected(false)} disabled={selectedCount === 0}>
                  Clear
                </button>
                <button onClick={() => saveImageSelection()}>Save Selection</button>
              </div>
            </div>
            <div className="photo-summary">{selectedCount} selected</div>
            <div className="image-table">
              {images.length === 0 && <p className="empty">No images found in mounted images directory.</p>}
              {images.map((image) => (
                <div className="image-row" key={image.name}>
                  <label className="image-select">
                    <input
                      type="checkbox"
                      checked={image.selected}
                      onChange={(event) => toggleImage(image.name, event.target.checked)}
                    />
                    <img src={api.imageUrl(image.name)} alt={image.name} />
                  </label>
                  <div className="image-details">
                    {editingImageName === image.name ? (
                      <div className="rename-row">
                        <input
                          value={renameDrafts[image.name] ?? image.name}
                          autoFocus
                          onChange={(event) =>
                            setRenameDrafts((current) => ({ ...current, [image.name]: event.target.value }))
                          }
                          onKeyDown={(event) => {
                            if (event.key === "Enter") void renamePhoto(image.name);
                            if (event.key === "Escape") {
                              setRenameDrafts((current) => ({ ...current, [image.name]: image.name }));
                              setEditingImageName(null);
                            }
                          }}
                        />
                        <button onClick={() => renamePhoto(image.name)}>Save</button>
                        <button
                          onClick={() => {
                            setRenameDrafts((current) => ({ ...current, [image.name]: image.name }));
                            setEditingImageName(null);
                          }}
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <div className="image-view-row">
                        <span className="image-name" title={image.name}>
                          {image.name}
                        </span>
                        {image.uploaded_by_me && <span className="mine-badge">Mine</span>}
                        <button
                          className="compact-action"
                          onClick={() => {
                            setRenameDrafts((current) => ({ ...current, [image.name]: image.name }));
                            setEditingImageName(image.name);
                          }}
                        >
                          Edit
                        </button>
                        <button className="compact-action danger-action" onClick={() => deletePhoto(image.name)}>
                          Delete
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>
        </section>

        <aside className="send-panel">
          <div className="section-heading">
            <h2>Send Progress</h2>
          </div>
          <button className="primary-action" onClick={startSending} disabled={!selectedDevice}>
            Send Photos
          </button>
          <button className="secondary-action" onClick={startSending} disabled={!selectedDevice}>
            Repeat
          </button>

          <div className="progress-block">
            <div className="progress-meta">
              <span>{sendJob?.status ?? "idle"}</span>
              <span>{Math.round(sendJob?.progress ?? 0)}%</span>
            </div>
            <div className="progress-track">
              <div className="progress-fill" style={{ width: `${sendJob?.progress ?? 0}%` }} />
            </div>
            <p>
              {sendJob ? `${sendJob.sent}/${sendJob.total} photos processed` : `${selectedCount} photos ready`}
            </p>
          </div>

          <div className="result-list">
            {sendJob?.results?.map((result) => (
              <div className="result-row" key={`${result.image_name}-${result.status_code}-${result.error ?? ""}`}>
                <span>{result.image_name}</span>
                <strong className={result.status_code === 200 ? "ok" : "bad"}>{result.status_code}</strong>
              </div>
            ))}
          </div>
        </aside>
      </section>
    </main>
  );
}

function formatError(error: unknown): string {
  return error instanceof Error ? error.message : "Unexpected error";
}
