import React from 'react';
import { Users, PawPrint, AlertTriangle, Activity, Calendar, Radio } from 'lucide-react';

export default function StatsOverview({ stats }) {
  if (!stats) return null;

  const statItems = [
    {
      label: 'Total Detections',
      value: stats.total_detections,
      icon: Activity,
      color: '#3b82f6',
      sub: 'All targets tracked'
    },
    {
      label: 'Human Detections',
      value: stats.human_detections,
      icon: Users,
      color: '#06b6d4',
      sub: 'Class: Person'
    },
    {
      label: 'Animal Detections',
      value: stats.animal_detections,
      icon: PawPrint,
      color: '#10b981',
      sub: 'Livestock & Wildlife'
    },
    {
      label: 'High-Risk Alerts',
      value: stats.high_risk_alerts,
      icon: AlertTriangle,
      color: '#ef4444',
      sub: 'High & Critical threats'
    },
    {
      label: "Today's Alerts",
      value: stats.today_alerts,
      icon: Calendar,
      color: '#f59e0b',
      sub: 'Recorded since midnight'
    },
    {
      label: 'Active Threat Level',
      value: stats.current_system_risk || 'SAFE',
      icon: Radio,
      color: stats.current_system_risk === 'CRITICAL' ? '#ef4444' :
             stats.current_system_risk === 'HIGH' ? '#f97316' :
             stats.current_system_risk === 'WARNING' ? '#f59e0b' : '#10b981',
      sub: 'Perimeter Status'
    }
  ];

  return (
    <div className="stats-grid">
      {statItems.map((item, index) => {
        const Icon = item.icon;
        return (
          <div key={index} className="stat-card">
            <div className="stat-icon" style={{ color: item.color }}>
              <Icon size={22} />
            </div>
            <div className="stat-info">
              <span className="stat-label">{item.label}</span>
              <span className="stat-value" style={typeof item.value === 'string' ? { fontSize: '1.2rem', color: item.color } : {}}>
                {item.value}
              </span>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: '2px' }}>
                {item.sub}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
