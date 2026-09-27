import React, { useState } from 'react';
import { Camera, RefreshCw, Download, Maximize2, Shield, Eye } from 'lucide-react';

export default function LiveMonitor({ streamUrl = '/api/video/feed' }) {
  const [streamKey, setStreamKey] = useState(Date.now());
  const [isFullscreen, setIsFullscreen] = useState(false);

  const handleRefresh = () => {
    setStreamKey(Date.now());
  };

  const handleSnapshot = () => {
    window.open('/api/video/snapshot', '_blank');
  };

  const toggleFullscreen = () => {
    const el = document.getElementById('camera-stream-container');
    if (!el) return;
    if (!document.fullscreenElement) {
      el.requestFullscreen().then(() => setIsFullscreen(true)).catch(err => console.error(err));
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false));
    }
  };

  return (
    <div className="dashboard-card">
      <div className="card-header">
        <span className="card-title">
          <Camera size={18} color="#06b6d4" />
          AI PERIMETER VIDEO SURVEILLANCE
        </span>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button onClick={handleSnapshot} className="btn btn-secondary" title="Capture Snapshot">
            <Download size={14} />
            Snapshot
          </button>
          <button onClick={handleRefresh} className="btn btn-secondary" title="Restart Stream Feed">
            <RefreshCw size={14} />
            Reconnect
          </button>
          <button onClick={toggleFullscreen} className="btn btn-secondary" title="Fullscreen">
            <Maximize2 size={14} />
          </button>
        </div>
      </div>

      <div className="card-body">
        <div id="camera-stream-container" className="video-wrapper">
          <img
            key={streamKey}
            src={`${streamUrl}?t=${streamKey}`}
            alt="Smart Fence AI Live Feed"
            className="video-element"
            onError={(e) => {
              e.target.style.display = 'none';
              const errBox = document.getElementById('stream-error-fallback');
              if (errBox) errBox.style.display = 'flex';
            }}
            onLoad={(e) => {
              e.target.style.display = 'block';
              const errBox = document.getElementById('stream-error-fallback');
              if (errBox) errBox.style.display = 'none';
            }}
          />

          <div
            id="stream-error-fallback"
            style={{
              display: 'none',
              position: 'absolute',
              inset: 0,
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              background: '#0a0e17',
              color: '#ef4444',
              gap: '0.75rem',
              textAlign: 'center',
              padding: '2rem'
            }}
          >
            <Camera size={44} color="#ef4444" />
            <h3 style={{ color: '#fff' }}>Connecting to Video Stream...</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Waiting for backend MJPEG feed at <code>/api/video/feed</code>. Click Reconnect to retry.
            </p>
            <button onClick={handleRefresh} className="btn btn-secondary">
              <RefreshCw size={14} /> Retry Connection
            </button>
          </div>

          <div className="video-overlay-badge">
            <span className="status-dot green pulse"></span>
            <span>LIVE INFERENCE & TRACKING ACTIVE</span>
          </div>
        </div>

        <div className="video-controls">
          <div style={{ display: 'flex', gap: '1rem', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            <span><strong style={{ color: '#10b981' }}>■</strong> Safe Zone</span>
            <span><strong style={{ color: '#f59e0b' }}>■</strong> Warning Zone</span>
            <span><strong style={{ color: '#ef4444' }}>■</strong> Danger Zone</span>
            <span><strong style={{ color: '#06b6d4' }}>---</strong> Simulated Fence</span>
          </div>

          <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>
            Engine: YOLOv8 + ByteTrack + Dynamic Risk Matrix
          </div>
        </div>
      </div>
    </div>
  );
}
