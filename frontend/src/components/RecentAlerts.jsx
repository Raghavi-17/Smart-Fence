import React from 'react';
import { AlertTriangle, CheckCircle, Clock, Shield } from 'lucide-react';
import { acknowledgeAlert } from '../services/api';

export default function RecentAlerts({ alerts = [], onAlertUpdated }) {
  const handleAcknowledge = async (id) => {
    try {
      await acknowledgeAlert(id);
      if (onAlertUpdated) onAlertUpdated();
    } catch (err) {
      alert(`Failed to acknowledge alert: ${err.message}`);
    }
  };

  const formatDirection = (dir) => {
    if (!dir) return 'Unknown';
    switch (dir) {
      case 'TOWARDS_FENCE': return 'Towards Fence';
      case 'AWAY_FROM_FENCE': return 'Away from Fence';
      case 'STATIONARY': return 'Stationary';
      default: return dir;
    }
  };

  return (
    <div className="dashboard-card">
      <div className="card-header">
        <span className="card-title">
          <AlertTriangle size={18} color="#ef4444" />
          INCIDENT & ALERT AUDIT LOG
        </span>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          {alerts.length} Total Incidents Logged
        </span>
      </div>

      <div className="card-body" style={{ padding: 0 }}>
        <div className="table-container">
          <table className="soc-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Object</th>
                <th>Risk Level</th>
                <th>Movement</th>
                <th>Zone</th>
                <th>Incident Reason</th>
                <th>Timestamp</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {alerts.length === 0 ? (
                <tr>
                  <td colSpan={9} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    No security alerts recorded yet. Perimeter is secure.
                  </td>
                </tr>
              ) : (
                alerts.map((alert) => {
                  const timeStr = new Date(alert.timestamp).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                  });

                  return (
                    <tr key={alert.id}>
                      <td className="mono" style={{ color: 'var(--text-dim)' }}>
                        #{alert.id}
                      </td>
                      <td style={{ fontWeight: 600, textTransform: 'capitalize' }}>
                        {alert.object_type} (#{alert.tracking_id})
                      </td>
                      <td>
                        <span className={`risk-badge ${alert.risk_level}`}>
                          {alert.risk_level}
                        </span>
                      </td>
                      <td style={{ color: alert.direction === 'TOWARDS_FENCE' ? '#f97316' : 'var(--text-muted)' }}>
                        {formatDirection(alert.direction)}
                      </td>
                      <td>
                        <span style={{ fontWeight: 600 }}>{alert.zone}</span>
                      </td>
                      <td style={{ maxWidth: '320px', fontSize: '0.8rem', color: '#cbd5e1' }}>
                        {alert.message}
                      </td>
                      <td className="mono" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {timeStr}
                      </td>
                      <td>
                        <span
                          style={{
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            color: alert.acknowledged ? '#10b981' : '#f59e0b',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px'
                          }}
                        >
                          {alert.acknowledged ? 'ACKNOWLEDGED' : 'ACTIVE'}
                        </span>
                      </td>
                      <td>
                        {!alert.acknowledged && (
                          <button
                            onClick={() => handleAcknowledge(alert.id)}
                            className="btn btn-secondary"
                            style={{ fontSize: '0.72rem', padding: '0.25rem 0.6rem' }}
                          >
                            <CheckCircle size={12} /> Ack
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
