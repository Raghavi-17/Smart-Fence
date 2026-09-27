import React from 'react';
import { Server, Camera, Brain, Database, Cpu, CheckCircle2, AlertCircle, Wrench } from 'lucide-react';
import { triggerIoTTest } from '../services/api';

export default function SystemDiagnostics({ systemStatus, onRefresh }) {
  if (!systemStatus) return null;

  const components = [
    {
      name: 'Vision Sensor (Webcam)',
      key: 'camera',
      icon: Camera,
      data: systemStatus.camera,
      okValues: ['ONLINE']
    },
    {
      name: 'YOLOv8 & Tracking Engine',
      key: 'ai_model',
      icon: Brain,
      data: systemStatus.ai_model,
      okValues: ['READY', 'ONLINE']
    },
    {
      name: 'FastAPI Backend Engine',
      key: 'backend',
      icon: Server,
      data: systemStatus.backend,
      okValues: ['ONLINE']
    },
    {
      name: 'SQLite Relational Database',
      key: 'database',
      icon: Database,
      data: systemStatus.database,
      okValues: ['CONNECTED']
    },
    {
      name: 'ESP32 Microcontroller Actuator',
      key: 'esp32',
      icon: Cpu,
      data: systemStatus.esp32,
      okValues: ['CONNECTED']
    }
  ];

  const handleTestTrigger = async () => {
    try {
      await triggerIoTTest();
      alert('Diagnostic signal broadcast to ESP32 / Virtual Controller.');
      if (onRefresh) onRefresh();
    } catch (err) {
      alert(`IoT Test Failed: ${err.message}`);
    }
  };

  return (
    <div className="dashboard-card">
      <div className="card-header">
        <span className="card-title">
          <Wrench size={18} color="#3b82f6" />
          SYSTEM HEALTH & SUBSYSTEM DIAGNOSTICS
        </span>
        <button onClick={handleTestTrigger} className="btn btn-secondary">
          <Cpu size={14} /> Trigger Hardware Self-Test
        </button>
      </div>

      <div className="card-body">
        <div className="diagnostics-grid">
          {components.map((c) => {
            const Icon = c.icon;
            const statusStr = c.data?.status || 'UNKNOWN';
            const isOk = c.okValues.includes(statusStr.toUpperCase());

            return (
              <div key={c.key} className="diag-card">
                <div className="diag-header">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                    <Icon size={20} color={isOk ? '#10b981' : '#ef4444'} />
                    <span className="diag-title">{c.name}</span>
                  </div>
                  <span
                    className="status-pill"
                    style={{
                      borderColor: isOk ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)',
                      color: isOk ? 'var(--risk-safe)' : 'var(--risk-critical)'
                    }}
                  >
                    {isOk ? <CheckCircle2 size={12} /> : <AlertCircle size={12} />}
                    {statusStr}
                  </span>
                </div>

                <div className="diag-details">
                  {c.data?.details || 'Operating nominally.'}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
