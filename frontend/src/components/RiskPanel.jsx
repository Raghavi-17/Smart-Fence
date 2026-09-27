import React from 'react';
import { Volume2, VolumeX, Lightbulb, Shield, ShieldCheck, ShieldAlert, AlertOctagon, Flame } from 'lucide-react';
import { triggerIoTTest } from '../services/api';

export default function RiskPanel({ currentRisk, riskReason, iotStatus }) {
  const risk = (currentRisk || 'SAFE').toUpperCase();

  const getRiskIcon = () => {
    switch (risk) {
      case 'CRITICAL':
        return <AlertOctagon size={48} color="#ef4444" />;
      case 'HIGH':
        return <ShieldAlert size={48} color="#f97316" />;
      case 'WARNING':
        return <Flame size={48} color="#f59e0b" />;
      default:
        return <ShieldCheck size={48} color="#10b981" />;
    }
  };

  const handleTestIoT = async () => {
    try {
      await triggerIoTTest();
      alert('IoT Diagnostic Trigger Sent to ESP32 / Virtual Controller.');
    } catch (err) {
      alert(`Error triggering IoT test: ${err.message}`);
    }
  };

  const buzzerActive = iotStatus?.buzzer || risk === 'HIGH' || risk === 'CRITICAL';
  const ledActive = iotStatus?.led || risk === 'WARNING' || risk === 'HIGH' || risk === 'CRITICAL';

  return (
    <div className="dashboard-card">
      <div className="card-header">
        <span className="card-title">
          <Shield size={18} color="#3b82f6" />
          PERIMETER THREAT ASSESSMENT
        </span>
        <button onClick={handleTestIoT} className="btn btn-secondary" style={{ fontSize: '0.75rem', padding: '0.3rem 0.65rem' }}>
          Test IoT Alert
        </button>
      </div>

      <div className="card-body">
        <div className="risk-gauge-container">
          {/* Main Risk Gauge Banner */}
          <div className={`risk-level-banner ${risk}`}>
            <div style={{ marginBottom: '0.5rem' }}>
              {getRiskIcon()}
            </div>
            <div className="risk-title">CURRENT EVALUATED RISK</div>
            <div className={`risk-state-text ${risk}`}>
              {risk} {risk !== 'SAFE' && 'RISK'}
            </div>
            <div className="risk-reason-box">
              {riskReason || 'Perimeter secure. No approaching threats.'}
            </div>
          </div>

          {/* IoT Warning Actuators Status */}
          <div className="hw-indicators-grid">
            {/* Buzzer Status */}
            <div className={`hw-card ${buzzerActive ? 'active' : ''}`}>
              <div className="hw-card-icon" style={{ color: buzzerActive ? '#ef4444' : 'var(--text-muted)' }}>
                {buzzerActive ? <Volume2 size={20} /> : <VolumeX size={20} />}
              </div>
              <div>
                <div className="hw-name">Acoustic Buzzer</div>
                <div className="hw-state" style={{ color: buzzerActive ? '#ef4444' : 'var(--text-muted)' }}>
                  {buzzerActive ? 'SOUNDING [ON]' : 'MUTED [IDLE]'}
                </div>
              </div>
            </div>

            {/* LED Status */}
            <div className={`hw-card ${ledActive ? 'active' : ''}`}>
              <div className="hw-card-icon" style={{ color: ledActive ? '#f97316' : 'var(--text-muted)' }}>
                <Lightbulb size={20} />
              </div>
              <div>
                <div className="hw-name">Visual Warning LED</div>
                <div className="hw-state" style={{ color: ledActive ? '#f97316' : 'var(--text-muted)' }}>
                  {ledActive ? 'FLASHING [ON]' : 'OFF [IDLE]'}
                </div>
              </div>
            </div>
          </div>

          {/* Explanation Callout */}
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: '1.4', background: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: '8px' }}>
            <strong>Intelligent Rule Engine:</strong> Alerts evaluate Object Category (Human vs Animal) + Persistent Track + Directional Velocity vector + Boundary Zone proximity.
          </div>
        </div>
      </div>
    </div>
  );
}
