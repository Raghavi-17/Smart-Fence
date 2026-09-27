import React from 'react';
import { Sliders, Shield, AlertTriangle, AlertOctagon, Check } from 'lucide-react';

export default function ZoneSettings({ zones = [] }) {
  const zoneDescriptions = {
    SAFE: 'Outer perimeter zone. Objects here represent normal background activity or distant movement.',
    WARNING: 'Intermediate zone approaching fence perimeter. Intrusion here escalates alert status and primes actuators.',
    DANGER: 'Critical safety buffer immediately adjacent to the simulated electric fence boundary. Triggers immediate Buzzer + LED alarm.'
  };

  return (
    <div className="dashboard-card">
      <div className="card-header">
        <span className="card-title">
          <Sliders size={18} color="#06b6d4" />
          VIRTUAL FENCE ZONE CONFIGURATIONS
        </span>
      </div>

      <div className="card-body">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.25rem' }}>
          {zones.map((zone) => {
            const zType = zone.zone_type.toUpperCase();
            const color = zType === 'DANGER' ? '#ef4444' : zType === 'WARNING' ? '#f59e0b' : '#10b981';
            const Icon = zType === 'DANGER' ? AlertOctagon : zType === 'WARNING' ? AlertTriangle : Shield;

            return (
              <div
                key={zone.id}
                style={{
                  background: 'var(--bg-secondary)',
                  border: `1px solid ${color}40`,
                  borderRadius: '10px',
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Icon size={18} color={color} />
                    <strong style={{ color }}>{zone.name}</strong>
                  </div>
                  <span className="status-pill online" style={{ borderColor: `${color}60`, color }}>
                    <Check size={12} /> ACTIVE
                  </span>
                </div>

                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
                  {zoneDescriptions[zType] || 'Perimeter monitoring zone.'}
                </p>

                <div style={{ marginTop: '0.5rem' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: '4px' }}>
                    Polygon Coordinates (X, Y)
                  </div>
                  <pre
                    className="mono"
                    style={{
                      background: 'var(--bg-primary)',
                      padding: '0.5rem',
                      borderRadius: '6px',
                      fontSize: '0.75rem',
                      color: '#94a3b8',
                      overflowX: 'auto'
                    }}
                  >
                    {JSON.stringify(zone.coordinates)}
                  </pre>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
