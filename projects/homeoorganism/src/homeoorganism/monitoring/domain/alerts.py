"""Alert helpers."""

from homeoorganism.monitoring.domain.enums import AlertLevel


ALERT_PRIORITY = {
    AlertLevel.INFO: 0,
    AlertLevel.WARN: 1,
    AlertLevel.CRITICAL: 2,
}
