"""
Smart Fence - Risk Assessment Engine Module
Evaluates multi-factor perimeter risk (Object Type, Confidence, Zone,
Movement Vector, Persistence) and applies debouncing to prevent alert spamming.
"""

import time
from typing import Dict, Any, Tuple
from ai.config import (
    RISK_LOW,
    RISK_MEDIUM,
    RISK_HIGH,
    RISK_CRITICAL,
    ZONE_SAFE,
    ZONE_WARNING,
    ZONE_DANGER,
    DIR_TOWARDS_FENCE,
    DIR_AWAY_FROM_FENCE,
    DIR_STATIONARY,
    ALERT_COOLDOWN_SECONDS,
    CRITICAL_DWELL_SECONDS
)
from ai.tracking import TrackedObject


class RiskAssessmentEngine:
    """
    Evaluates real-time threat level for tracked targets and determines
    whether an alert should be dispatched to IoT hardware and database.
    """
    def __init__(
        self,
        alert_cooldown_seconds: float = ALERT_COOLDOWN_SECONDS,
        critical_dwell_seconds: float = CRITICAL_DWELL_SECONDS
    ):
        self.cooldown_seconds = alert_cooldown_seconds
        self.critical_dwell_seconds = critical_dwell_seconds
        # Cooldown tracker: {track_id: (last_alert_time, last_alerted_risk)}
        self._alert_history: Dict[int, Tuple[float, str]] = {}

    def assess_risk(self, tracked_obj: TrackedObject) -> Dict[str, Any]:
        """
        Assesses the multi-factor risk for a tracked object.
        Returns a structured dictionary:
        {
            "risk_level": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
            "reason": str,
            "should_alert": bool,
            "iot_command": dict
        }
        """
        now = time.time()
        obj_type = tracked_obj.object_type  # "human" or "animal"
        zone = tracked_obj.current_zone
        direction = tracked_obj.direction

        # Track dwell time in danger zone
        if zone == ZONE_DANGER:
            if tracked_obj.danger_zone_entry_time is None:
                tracked_obj.danger_zone_entry_time = now
            tracked_obj.dwell_in_danger_zone = now - tracked_obj.danger_zone_entry_time
        else:
            tracked_obj.danger_zone_entry_time = None
            tracked_obj.dwell_in_danger_zone = 0.0

        risk_level = RISK_LOW
        reason = "Normal activity; no immediate threat."

        # Rule 1: CRITICAL Check (Sustained intrusion or rapid danger zone approach)
        if zone == ZONE_DANGER and tracked_obj.dwell_in_danger_zone >= self.critical_dwell_seconds:
            risk_level = RISK_CRITICAL
            reason = f"{obj_type.capitalize()} has lingered in DANGER ZONE for {tracked_obj.dwell_in_danger_zone:.1f}s near fence!"
        elif zone == ZONE_DANGER and direction == DIR_TOWARDS_FENCE:
            risk_level = RISK_CRITICAL
            reason = f"{obj_type.capitalize()} is actively advancing towards fence inside DANGER ZONE!"
        # Rule 2: HIGH Check
        elif zone == ZONE_DANGER:
            risk_level = RISK_HIGH
            reason = f"{obj_type.capitalize()} detected inside DANGER ZONE (Direction: {direction})."
        elif zone == ZONE_WARNING and direction == DIR_TOWARDS_FENCE:
            if obj_type == "human":
                risk_level = RISK_HIGH
                reason = "Human is moving toward the fence inside WARNING ZONE."
            else:
                risk_level = RISK_MEDIUM
                reason = f"{tracked_obj.class_name.capitalize()} moving toward fence inside WARNING ZONE."
        # Rule 3: MEDIUM Check
        elif zone == ZONE_WARNING:
            if direction == DIR_STATIONARY:
                risk_level = RISK_MEDIUM
                reason = f"{obj_type.capitalize()} is stationary inside WARNING ZONE."
            elif direction == DIR_AWAY_FROM_FENCE:
                risk_level = RISK_LOW
                reason = f"{obj_type.capitalize()} inside WARNING ZONE is moving away from the fence."
            else:
                risk_level = RISK_MEDIUM
                reason = f"{obj_type.capitalize()} detected in WARNING ZONE."
        # Rule 4: SAFE Zone
        else:
            if direction == DIR_TOWARDS_FENCE and obj_type == "human":
                risk_level = RISK_LOW
                reason = "Human in safe zone walking in direction of perimeter."
            else:
                risk_level = RISK_LOW
                reason = f"{obj_type.capitalize()} in SAFE ZONE (No threat)."

        # Update tracked object's risk state
        tracked_obj.risk_level = risk_level
        tracked_obj.risk_reason = reason

        # Debouncing Logic
        should_alert = False
        if risk_level in (RISK_MEDIUM, RISK_HIGH, RISK_CRITICAL):
            last_alert_record = self._alert_history.get(tracked_obj.track_id)
            if last_alert_record is None:
                # First time reaching alerting threshold
                should_alert = True
                self._alert_history[tracked_obj.track_id] = (now, risk_level)
            else:
                last_time, last_risk = last_alert_record
                # Re-alert if cooldown expired OR if risk escalated (e.g. MEDIUM -> HIGH or HIGH -> CRITICAL)
                risk_severity = {RISK_LOW: 0, RISK_MEDIUM: 1, RISK_HIGH: 2, RISK_CRITICAL: 3}
                escalated = risk_severity[risk_level] > risk_severity[last_risk]
                cooldown_elapsed = (now - last_time) >= self.cooldown_seconds

                if escalated or cooldown_elapsed:
                    should_alert = True
                    self._alert_history[tracked_obj.track_id] = (now, risk_level)

        # Formulate IoT command
        iot_command = {
            "risk": risk_level,
            "buzzer": risk_level in (RISK_HIGH, RISK_CRITICAL),
            "led": risk_level in (RISK_MEDIUM, RISK_HIGH, RISK_CRITICAL),
            "track_id": tracked_obj.track_id,
            "object_type": tracked_obj.object_type,
            "reason": reason
        }

        return {
            "risk_level": risk_level,
            "reason": reason,
            "should_alert": should_alert,
            "iot_command": iot_command
        }

    def reset_cooldown(self, track_id: int):
        """Manually clears cooldown state for a specific track ID."""
        if track_id in self._alert_history:
            del self._alert_history[track_id]
