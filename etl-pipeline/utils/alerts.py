"""
alerts.py
---------
Very small alerting layer. If ALERT_WEBHOOK_URL is configured (Slack/Teams
incoming webhook), a failure message is POSTed there. Otherwise the alert
is simply logged at CRITICAL level so it stands out in the log file and
in any log-monitoring tool (e.g. CloudWatch, ELK) watching this pipeline.

This is intentionally dependency-light (uses `requests`, already a
pipeline dependency) so it works out of the box.
"""

import requests
import config


def send_alert(logger, subject: str, message: str) -> None:
    full_message = f"[ETL ALERT] {subject}: {message}"
    logger.critical(full_message)

    if config.ALERT_WEBHOOK_URL:
        try:
            requests.post(
                config.ALERT_WEBHOOK_URL,
                json={"text": full_message},
                timeout=5,
            )
            logger.info("Alert successfully sent to webhook.")
        except requests.RequestException as exc:
            logger.error(f"Failed to deliver alert to webhook: {exc}")
    else:
        logger.warning(
            "ALERT_WEBHOOK_URL not configured — alert was only written to the log file. "
            "Set ALERT_WEBHOOK_URL (Slack/Teams) in your environment for live notifications."
        )
