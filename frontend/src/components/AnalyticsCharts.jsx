import React from 'react';
import { BarChart3, PieChart, TrendingUp, Shield } from 'lucide-react';

export default function AnalyticsCharts({ analytics }) {
  if (!analytics) return null;

  const { risk_distribution = {}, object_distribution = {}, alerts_by_hour = [], detection_trend = [] } = analytics;

  // Compute total objects
  const totalObjects = (object_distribution.human || 0) + (object_distribution.animal || 0);
  const humanPct = totalObjects > 0 ? Math.round(((object_distribution.human || 0) / totalObjects) * 100) : 0;
  const animalPct = totalObjects > 0 ? Math.round(((object_distribution.animal || 0) / totalObjects) * 100) : 0;

  // Compute risk totals
  const totalRisks = Object.values(risk_distribution).reduce((a, b) => a + b, 0);

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
      {/* Chart 1: Object Distribution (Human vs Animal) */}
      <div className="dashboard-card">
        <div className="card-header">
          <span className="card-title">
            <PieChart size={18} color="#06b6d4" />
            HUMAN VS ANIMAL CLASSIFICATION
          </span>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {totalObjects} Ingested
          </span>
        </div>
        <div className="card-body">
          <div className="chart-bar-row">
            <div className="bar-item">
              <div className="bar-meta">
                <span>Human (Person)</span>
                <strong>{object_distribution.human || 0} ({humanPct}%)</strong>
              </div>
              <div className="bar-track">
                <div className="bar-fill" style={{ width: `${humanPct}%`, background: '#3b82f6' }}></div>
              </div>
            </div>

            <div className="bar-item">
              <div className="bar-meta">
                <span>Animal (Livestock/Wild)</span>
                <strong>{object_distribution.animal || 0} ({animalPct}%)</strong>
              </div>
              <div className="bar-track">
                <div className="bar-fill" style={{ width: `${animalPct}%`, background: '#10b981' }}></div>
              </div>
            </div>
          </div>

          <div style={{ marginTop: '1.5rem', padding: '0.75rem', background: 'var(--bg-secondary)', borderRadius: '8px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            AI filters false positives and classifies objects into Human vs Animal categories using COCO-trained weights.
          </div>
        </div>
      </div>

      {/* Chart 2: Threat & Risk Level Distribution */}
      <div className="dashboard-card">
        <div className="card-header">
          <span className="card-title">
            <BarChart3 size={18} color="#f59e0b" />
            RISK SEVERITY SPECTRUM
          </span>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {totalRisks} Recorded
          </span>
        </div>
        <div className="card-body">
          <div className="chart-bar-row">
            {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((lvl) => {
              const count = risk_distribution[lvl] || 0;
              const pct = totalRisks > 0 ? Math.round((count / totalRisks) * 100) : 0;
              const color = lvl === 'CRITICAL' ? '#ef4444' :
                            lvl === 'HIGH' ? '#f97316' :
                            lvl === 'MEDIUM' ? '#f59e0b' : '#10b981';

              return (
                <div key={lvl} className="bar-item">
                  <div className="bar-meta">
                    <span style={{ color }}>{lvl} Threat</span>
                    <strong>{count} ({pct}%)</strong>
                  </div>
                  <div className="bar-track">
                    <div className="bar-fill" style={{ width: `${pct}%`, background: color }}></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Chart 3: Activity Trends by Hour */}
      <div className="dashboard-card">
        <div className="card-header">
          <span className="card-title">
            <TrendingUp size={18} color="#10b981" />
            RECENT TEMPORAL ACTIVITY (LAST 6 HOURS)
          </span>
        </div>
        <div className="card-body">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', height: '140px', paddingTop: '1.5rem' }}>
            {detection_trend.map((pt, idx) => {
              const maxDet = Math.max(...detection_trend.map(d => d.detections), 1);
              const heightPct = Math.round((pt.detections / maxDet) * 100);

              return (
                <div key={idx} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem', flex: 1 }}>
                  <span style={{ fontSize: '0.75rem', color: '#fff', fontWeight: 700 }}>
                    {pt.detections}
                  </span>
                  <div style={{ width: '24px', height: `${Math.max(8, heightPct)}%`, background: 'linear-gradient(180deg, #3b82f6 0%, #1d4ed8 100%)', borderRadius: '4px 4px 0 0' }}></div>
                  <span className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                    {pt.hour}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
