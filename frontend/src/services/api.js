/**
 * Smart Fence - Frontend API Service
 * Handles communication with FastAPI backend REST endpoints.
 */

const BASE_URL = ''; // Relative URL handled by Vite proxy to backend

export async function fetchDashboardStats() {
  const res = await fetch(`${BASE_URL}/api/dashboard/stats`);
  if (!res.ok) throw new Error(`HTTP error ${res.status}`);
  return await res.json();
}

export async function fetchRecentDetections(limit = 15) {
  const res = await fetch(`${BASE_URL}/api/detections/recent?limit=${limit}`);
  if (!res.ok) throw new Error(`HTTP error ${res.status}`);
  return await res.json();
}

export async function fetchAlerts(limit = 25) {
  const res = await fetch(`${BASE_URL}/api/alerts?limit=${limit}`);
  if (!res.ok) throw new Error(`HTTP error ${res.status}`);
  return await res.json();
}

export async function acknowledgeAlert(alertId) {
  const res = await fetch(`${BASE_URL}/api/alerts/${alertId}/ack`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ acknowledged: true, status: 'ACKNOWLEDGED' })
  });
  if (!res.ok) throw new Error(`HTTP error ${res.status}`);
  return await res.json();
}

export async function fetchAnalytics() {
  const res = await fetch(`${BASE_URL}/api/dashboard/analytics`);
  if (!res.ok) throw new Error(`HTTP error ${res.status}`);
  return await res.json();
}

export async function fetchSystemStatus() {
  const res = await fetch(`${BASE_URL}/api/system/status`);
  if (!res.ok) throw new Error(`HTTP error ${res.status}`);
  return await res.json();
}

export async function fetchZones() {
  const res = await fetch(`${BASE_URL}/api/zones`);
  if (!res.ok) throw new Error(`HTTP error ${res.status}`);
  return await res.json();
}

export async function triggerIoTTest() {
  const res = await fetch(`${BASE_URL}/api/system/iot/trigger-test`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error(`HTTP error ${res.status}`);
  return await res.json();
}
