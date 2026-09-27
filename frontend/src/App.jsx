import React, { useState, useEffect, useCallback } from 'react';
import { Camera, AlertTriangle, BarChart3, Wrench, Sliders, Shield } from 'lucide-react';

import Header from './components/Header';
import StatsOverview from './components/StatsOverview';
import LiveMonitor from './components/LiveMonitor';
import RiskPanel from './components/RiskPanel';
import RecentAlerts from './components/RecentAlerts';
import AnalyticsCharts from './components/AnalyticsCharts';
import SystemDiagnostics from './components/SystemDiagnostics';
import ZoneSettings from './components/ZoneSettings';

import {
  fetchDashboardStats,
  fetchAlerts,
  fetchAnalytics,
  fetchSystemStatus,
  fetchZones
} from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('live');
  const [stats, setStats] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [systemStatus, setSystemStatus] = useState(null);
  const [zones, setZones] = useState([]);
  const [systemOnline, setSystemOnline] = useState(true);

  // Data fetching routine
  const loadData = useCallback(async () => {
    try {
      const [sData, aData, anData, sysData, zData] = await Promise.all([
        fetchDashboardStats(),
        fetchAlerts(20),
        fetchAnalytics(),
        fetchSystemStatus(),
        fetchZones()
      ]);

      setStats(sData);
      setAlerts(aData);
      setAnalytics(anData);
      setSystemStatus(sysData);
      setZones(zData);
      setSystemOnline(true);
    } catch (err) {
      console.warn('Backend sync error:', err.message);
      setSystemOnline(false);
    }
  }, []);

  // Polling loop
  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 2500);
    return () => clearInterval(interval);
  }, [loadData]);

  // WebSocket connection for instant push updates
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/live`;
    let ws = null;

    try {
      ws = new WebSocket(wsUrl);
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'ALERT') {
            loadData(); // Immediately refresh dashboard upon real-time alert push
          }
        } catch (e) {
          // ignore keepalive pings
        }
      };
    } catch (e) {
      console.warn('WebSocket connection not initialized:', e);
    }

    return () => {
      if (ws) ws.close();
    };
  }, [loadData]);

  return (
    <div className="app-container">
      {/* Top Header */}
      <Header
        systemOnline={systemOnline}
        esp32Status={stats?.esp32_status || systemStatus?.esp32?.status}
        activeAlertCount={stats?.active_alerts || 0}
      />

      {/* Navigation Sub-Header */}
      <nav className="nav-tabs">
        <button
          className={`nav-tab-btn ${activeTab === 'live' ? 'active' : ''}`}
          onClick={() => setActiveTab('live')}
        >
          <Camera size={16} /> Live Operations
        </button>
        <button
          className={`nav-tab-btn ${activeTab === 'alerts' ? 'active' : ''}`}
          onClick={() => setActiveTab('alerts')}
        >
          <AlertTriangle size={16} /> Alert History ({alerts.length})
        </button>
        <button
          className={`nav-tab-btn ${activeTab === 'analytics' ? 'active' : ''}`}
          onClick={() => setActiveTab('analytics')}
        >
          <BarChart3 size={16} /> Analytics & Intelligence
        </button>
        <button
          className={`nav-tab-btn ${activeTab === 'diagnostics' ? 'active' : ''}`}
          onClick={() => setActiveTab('diagnostics')}
        >
          <Wrench size={16} /> Subsystem Health
        </button>
        <button
          className={`nav-tab-btn ${activeTab === 'zones' ? 'active' : ''}`}
          onClick={() => setActiveTab('zones')}
        >
          <Sliders size={16} /> Virtual Zones
        </button>
      </nav>

      {/* Main Body */}
      <main className="main-layout">
        {/* Quick Stats Overview */}
        <StatsOverview stats={stats} />

        {/* Tab 1: Live Operations */}
        {activeTab === 'live' && (
          <>
            <div className="monitor-grid">
              <LiveMonitor streamUrl="/api/video/feed" />
              <RiskPanel
                currentRisk={stats?.current_system_risk}
                riskReason={stats?.current_risk_reason}
                iotStatus={systemStatus?.esp32}
              />
            </div>
            <RecentAlerts alerts={alerts.slice(0, 10)} onAlertUpdated={loadData} />
          </>
        )}

        {/* Tab 2: Alert History */}
        {activeTab === 'alerts' && (
          <RecentAlerts alerts={alerts} onAlertUpdated={loadData} />
        )}

        {/* Tab 3: Analytics */}
        {activeTab === 'analytics' && (
          <AnalyticsCharts analytics={analytics} />
        )}

        {/* Tab 4: Subsystem Diagnostics */}
        {activeTab === 'diagnostics' && (
          <SystemDiagnostics systemStatus={systemStatus} onRefresh={loadData} />
        )}

        {/* Tab 5: Virtual Zones */}
        {activeTab === 'zones' && (
          <ZoneSettings zones={zones} />
        )}
      </main>
    </div>
  );
}
