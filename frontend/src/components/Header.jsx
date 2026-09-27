import React, { useState, useEffect } from 'react';
import { ShieldAlert, Radio, Cpu, Clock, Bell } from 'lucide-react';

export default function Header({ systemOnline, esp32Status, activeAlertCount }) {
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const isEsp32Connected = esp32Status && esp32Status.toLowerCase().includes('connected');

  return (
    <header className="header-bar">
      <div className="logo-section">
        <div className="logo-icon-box">
          <ShieldAlert size={26} color="#ffffff" />
        </div>
        <div className="header-titles">
          <h1>
            SMART FENCE
            <span style={{ fontSize: '0.65rem', padding: '0.2rem 0.5rem', background: '#f97316', borderRadius: '4px', color: '#fff', verticalAlign: 'middle' }}>
              AI & IoT
            </span>
          </h1>
          <p>Intelligent Safety & Early-Warning Monitoring System</p>
        </div>
      </div>

      <div className="header-status-group">
        {/* Live Clock */}
        <div className="status-pill" style={{ color: 'var(--text-muted)' }}>
          <Clock size={14} />
          <span className="mono">{currentTime}</span>
        </div>

        {/* System Online / Offline */}
        <div className={`status-pill ${systemOnline ? 'online' : 'offline'}`}>
          <span className={`status-dot ${systemOnline ? 'green pulse' : 'red'}`}></span>
          <span>SYSTEM {systemOnline ? 'ONLINE' : 'OFFLINE'}</span>
        </div>

        {/* ESP32 Status */}
        <div className={`status-pill ${isEsp32Connected ? 'online' : 'offline'}`}>
          <Cpu size={14} />
          <span>ESP32: {esp32Status || 'CONNECTING...'}</span>
        </div>

        {/* Active Alerts Pill */}
        {activeAlertCount > 0 && (
          <div className="status-pill" style={{ borderColor: 'rgba(239, 68, 68, 0.4)', color: 'var(--risk-critical)' }}>
            <Bell size={14} />
            <span>{activeAlertCount} ACTIVE</span>
          </div>
        )}
      </div>
    </header>
  );
}
