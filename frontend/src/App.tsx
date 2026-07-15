import { useEffect, useMemo, useState } from "react";

import { api, getStoredToken, setStoredToken } from "./api/client";
import type { BatchTarget, Device, DeviceSettings, ImageFile, NetworkSettings, PhotoScope, SendJob, User } from "./types/domain";

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
  const [activeTab, setActiveTab] = useState<"single" | "batch">("single");
  const [batchTargets, setBatchTargets] = useState<BatchTarget[]>([]);
  const [batchJobs, setBatchJobs] = useState<SendJob[]>([]);
  const [repeatEnabled, setRepeatEnabled] = useState(false);
  const [repeatMinutes, setRepeatMinutes] = useState(5);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [passwordPanelOpen, setPasswordPanelOpen] = useState(false);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
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
    if (!sendJob || ["completed", "failed", "cancelled"].includes(sendJob.status)) return;

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

  useEffect(() => {
    if (!batchJobs.some((job) => !["completed", "failed", "cancelled"].includes(job.status))) return;
    const timer = window.setInterval(async () => {
      try {
        const freshJobs = await Promise.all(batchJobs.map((job) => api.getSendJob(job.id)));
        setBatchJobs(freshJobs);
      } catch (err) {
        setError(formatError(err));
      }
    }, 1000);
    return () => window.clearInterval(timer);
  }, [batchJobs]);

  useEffect(() => {
    if (sendJob && ["completed", "failed", "cancelled"].includes(sendJob.status)) {
      setRepeatEnabled(false);
    }
  }, [sendJob?.status]);

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
    setBatchJobs([]);
    setBatchTargets([]);
    setDeviceDraft(null);
    setSelectedDeviceName("");
    setPasswordPanelOpen(false);
    setNewPassword("");
    setConfirmPassword("");
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
      setBatchTargets((current) => current.filter((target) => devicesData.some((device) => device.name === target.device_name)));
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

  function cancelPasswordChange() {
    setPasswordPanelOpen(false);
    setNewPassword("");
    setConfirmPassword("");
    setError("");
  }

  async function changePassword() {
    if (!authEmail || !newPassword) return;
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    try {
      setError("");
      await api.changePassword(authEmail, newPassword);
      cancelPasswordChange();
      setAuthMode("login");
      setAuthPassword("");
      setNotice("Password changed");
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
      const job = await api.startSending(
        selectedDevice.name,
        repeatEnabled,
        repeatEnabled ? repeatMinutes : null
      );
      setSendJob(job);
      setNotice("Sending started");
    } catch (err) {
      setError(formatError(err));
    }
  }

  async function stopSending() {
    if (!sendJob) return;
    try {
      const job = await api.stopSending(sendJob.id);
      setSendJob(job);
      setNotice("Stop requested — the current photo request will finish first");
    } catch (err) {
      setError(formatError(err));
    }
  }

  function addBatchTarget() {
    const device = devices[0];
    if (!device) return;
    setBatchTargets((current) => [
      ...current,
      {
        id: crypto.randomUUID(),
        name: `Terminal ${current.length + 1}`,
        device_name: device.name,
        settings: cloneSettings(device.settings)
      }
    ]);
  }

  function patchBatchTarget(id: string, patch: Partial<BatchTarget>) {
    setBatchTargets((current) => current.map((target) => (target.id === id ? { ...target, ...patch } : target)));
  }

  function patchBatchTargetSettings(id: string, patch: Partial<DeviceSettings>) {
    setBatchTargets((current) =>
      current.map((target) => (target.id === id ? { ...target, settings: { ...target.settings, ...patch } } : target))
    );
  }

  function setBatchTargetModel(id: string, deviceName: string) {
    const device = devices.find((item) => item.name === deviceName);
    if (!device) return;
    setBatchTargets((current) =>
      current.map((target) =>
        target.id === id ? { ...target, device_name: deviceName, settings: cloneSettings(device.settings) } : target
      )
    );
  }

  async function startBatchSending() {
    if (batchTargets.length === 0) return;
    try {
      setError("");
      const payload = Object.fromEntries(images.map((image) => [image.name, image.selected]));
      const savedImages = await api.updateImages(payload, photoScope);
      setImages(savedImages);
      const response = await api.startBatchSending(batchTargets, repeatEnabled, repeatEnabled ? repeatMinutes : null);
      setBatchJobs(response.jobs);
      setNotice(`${response.jobs.length} terminal jobs started in parallel`);
    } catch (err) {
      setError(formatError(err));
    }
  }

  async function stopBatchSending() {
    const activeJobs = batchJobs.filter((job) => !["completed", "failed", "cancelled"].includes(job.status));
    if (activeJobs.length === 0) return;
    try {
      const stoppedJobs = await Promise.all(activeJobs.map((job) => api.stopSending(job.id)));
      setBatchJobs((current) =>
        current.map((job) => stoppedJobs.find((stopped) => stopped.id === job.id) ?? job)
      );
      setNotice("Stop requested for all terminal jobs");
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

  function setDelaySeconds(value: number) {
    patchDeviceDraft({ delay_seconds: Math.min(3600, Math.max(0, Number.isFinite(value) ? value : 0)) });
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
          {passwordPanelOpen ? (
            <>
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
                <span>New password</span>
                <input
                  type="password"
                  autoComplete="new-password"
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                />
              </label>
              <label>
                <span>Confirm password</span>
                <input
                  type="password"
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") void changePassword();
                    if (event.key === "Escape") cancelPasswordChange();
                  }}
                />
              </label>
              <div className="auth-actions">
                <button
                  className="primary-action"
                  onClick={changePassword}
                  disabled={!authEmail || !newPassword || !confirmPassword}
                >
                  Save
                </button>
                <button onClick={cancelPasswordChange}>Cancel</button>
              </div>
            </>
          ) : (
            <>
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
              <button
                onClick={() => {
                  setError("");
                  setNotice("");
                  setPasswordPanelOpen(true);
                  setNewPassword("");
                  setConfirmPassword("");
                }}
              >
                Change Password
              </button>
            </>
          )}
          {error && <div className="auth-error">{error}</div>}
          {notice && <div className="auth-notice">{notice}</div>}
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

      <nav className="view-tabs" aria-label="Sending mode">
        <button className={activeTab === "single" ? "active" : ""} onClick={() => setActiveTab("single")}>
          Single terminal
        </button>
        <button className={activeTab === "batch" ? "active" : ""} onClick={() => setActiveTab("batch")}>
          Multi-send
        </button>
      </nav>

      {activeTab === "single" ? (
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
          {sendJob && !["completed", "failed", "cancelled"].includes(sendJob.status) && (
            <button className="secondary-action" onClick={stopSending}>Stop sending</button>
          )}
          <div className="repeat-control">
            <label>
              <span>Delay between sending, seconds</span>
              <input
                type="number"
                min={0}
                max={3600}
                step={0.1}
                value={deviceDraft?.delay_seconds ?? 3.1}
                disabled={!deviceDraft}
                onChange={(event) => {
                  setDelaySeconds(Number(event.target.value));
                }}
              />
            </label>
            <button className="secondary-action" onClick={saveDeviceSettings} disabled={!selectedDevice || !deviceDraft}>
              Save delay and settings
            </button>
            <label className="check-row">
              <input
                type="checkbox"
                checked={repeatEnabled}
                onChange={(event) => setRepeatEnabled(event.target.checked)}
              />
              <span>Repeat sending</span>
            </label>
            {repeatEnabled && (
              <label>
                <span>Minutes</span>
                <input
                  type="number"
                  min={1}
                  max={1440}
                  step={1}
                  value={repeatMinutes}
                  onChange={(event) => setRepeatMinutes(Math.max(1, Number(event.target.value) || 1))}
                />
              </label>
            )}
          </div>

          <div className="progress-block">
            <div className="progress-meta">
              <span>{sendJob?.status ?? "idle"}</span>
              <span>
                {sendJob?.repeat_enabled && sendJob.repeat_remaining_seconds != null
                  ? `${Math.ceil(sendJob.repeat_remaining_seconds / 60)} min left`
                  : `${Math.round(sendJob?.progress ?? 0)}%`}
              </span>
            </div>
            <div className="progress-track">
              <div className="progress-fill" style={{ width: `${sendJob?.progress ?? 0}%` }} />
            </div>
            <p>
              {sendJob
                ? sendJob.repeat_enabled
                  ? `${sendJob.sent} photos processed`
                  : `${sendJob.sent}/${sendJob.total} photos processed`
                : `${selectedCount} photos ready`}
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
      ) : (
        <section className="batch-workspace">
          <section className="panel batch-target-panel">
            <div className="section-heading">
              <div>
                <h2>Terminal instances</h2>
                <p className="section-description">Each instance receives the selected photos independently and in parallel.</p>
              </div>
              <button onClick={addBatchTarget} disabled={devices.length === 0}>Add terminal</button>
            </div>
            {batchTargets.length === 0 && <p className="empty">Add one or more terminal instances to prepare a multi-send.</p>}
            <div className="batch-target-list">
              {batchTargets.map((target, index) => {
                const targetDevice = devices.find((device) => device.name === target.device_name);
                return (
                  <article className="batch-target" key={target.id}>
                    <div className="batch-target-heading">
                      <strong>#{index + 1}</strong>
                      <button className="compact-action danger-action" onClick={() => setBatchTargets((current) => current.filter((item) => item.id !== target.id))}>Remove</button>
                    </div>
                    <div className="form-grid two-columns">
                      <label><span>Terminal name</span><input value={target.name} onChange={(event) => patchBatchTarget(target.id, { name: event.target.value })} /></label>
                      <label><span>Model</span><select value={target.device_name} onChange={(event) => setBatchTargetModel(target.id, event.target.value)}>{devices.map((device) => <option key={device.name} value={device.name}>{device.title}</option>)}</select></label>
                      <label><span>Device ID</span><input value={target.settings.device_id} onChange={(event) => patchBatchTargetSettings(target.id, { device_id: event.target.value })} /></label>
                      <label><span>Delay, seconds</span><input type="number" min={0} max={3600} step={0.1} value={target.settings.delay_seconds} onChange={(event) => patchBatchTargetSettings(target.id, { delay_seconds: Math.max(0, Number(event.target.value) || 0) })} /></label>
                    </div>
                    {targetDevice?.supports_temperature && <div className="batch-options">
                      <label className="check-row"><input type="checkbox" checked={target.settings.temperature_enabled} onChange={(event) => patchBatchTargetSettings(target.id, { temperature_enabled: event.target.checked })} /><span>Temperature detection</span></label>
                      <label className="check-row"><input type="checkbox" checked={target.settings.above_normal_temp} disabled={!target.settings.temperature_enabled} onChange={(event) => patchBatchTargetSettings(target.id, { above_normal_temp: event.target.checked, abnormal_temp: event.target.checked ? false : target.settings.abnormal_temp })} /><span>Above normal temperature</span></label>
                      <label className="check-row"><input type="checkbox" checked={target.settings.abnormal_temp} disabled={!target.settings.temperature_enabled} onChange={(event) => patchBatchTargetSettings(target.id, { abnormal_temp: event.target.checked, above_normal_temp: event.target.checked ? false : target.settings.above_normal_temp })} /><span>Abnormal temperature</span></label>
                      <label className="check-row"><input type="checkbox" checked={target.settings.old_event} onChange={(event) => patchBatchTargetSettings(target.id, { old_event: event.target.checked })} /><span>Old event date</span></label>
                      {targetDevice.supports_liveness && <label className="check-row"><input type="checkbox" checked={target.settings.liveness_enabled} onChange={(event) => patchBatchTargetSettings(target.id, { liveness_enabled: event.target.checked })} /><span>Liveness event</span></label>}
                    </div>}
                  </article>
                );
              })}
            </div>
          </section>

          <section className="panel batch-send-panel">
            <div className="section-heading"><h2>Batch send</h2></div>
            <p className="photo-summary">{selectedCount} selected photos × {batchTargets.length} terminals</p>
            <div className="batch-photo-list">
              {images.map((image) => <label className="check-row" key={image.name}><input type="checkbox" checked={image.selected} onChange={(event) => toggleImage(image.name, event.target.checked)} /><span>{image.name}</span></label>)}
            </div>
            <div className="repeat-control">
              <label className="check-row"><input type="checkbox" checked={repeatEnabled} onChange={(event) => setRepeatEnabled(event.target.checked)} /><span>Repeat sending</span></label>
              {repeatEnabled && <label><span>Minutes</span><input type="number" min={1} max={1440} value={repeatMinutes} onChange={(event) => setRepeatMinutes(Math.max(1, Number(event.target.value) || 1))} /></label>}
            </div>
            <button className="primary-action" onClick={startBatchSending} disabled={batchTargets.length === 0 || selectedCount === 0}>Send to all terminals</button>
            {batchJobs.some((job) => !["completed", "failed", "cancelled"].includes(job.status)) && <button className="secondary-action" onClick={stopBatchSending}>Stop all sending</button>}
            <div className="batch-progress-list">
              {batchJobs.map((job) => <div className="batch-job" key={job.id}>
                <div className="progress-meta"><span>{job.target_name ?? job.device_name}{job.device_id ? ` · ${job.device_id}` : ""}</span><span>{job.status} · {Math.round(job.progress)}%</span></div>
                <div className="progress-track"><div className="progress-fill" style={{ width: `${job.progress}%` }} /></div>
                <small>{job.repeat_enabled ? `${job.sent} photos processed` : `${job.sent}/${job.total} photos processed`}</small>
              </div>)}
            </div>
          </section>
        </section>
      )}
    </main>
  );
}

function formatError(error: unknown): string {
  return error instanceof Error ? error.message : "Unexpected error";
}
