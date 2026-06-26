#!/usr/bin/env python3
"""
Health monitor script for BA Jira Agent.

Checks the BA Jira Agent endpoint (HF Space or local) and reports health status
as JSON on stdout. Exits 0 for healthy, 1 for unhealthy.

Usage:
    python scripts/health_monitor.py                    # Check HF Space
    python scripts/health_monitor.py --local            # Check localhost:8503
    python scripts/health_monitor.py --url https://...  # Check custom URL
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from urllib import request, error

# ── Default URLs ───────────────────────────────────────────────────────────────
HF_SPACE_URL = "https://tshaik1990-ba-jira-agent.hf.space"
LOCAL_URL = "http://localhost:8503"


def check_health(url: str, timeout: int = 30) -> dict:
    """
    Perform a health check against the given URL.

    Args:
        url: Base URL of the app to check (e.g. https://... or http://localhost:...)
        timeout: Request timeout in seconds.

    Returns:
        dict with keys: status, latency_ms, timestamp.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    start = time.monotonic()

    try:
        req = request.Request(url, method="GET")
        with request.urlopen(req, timeout=timeout) as resp:
            latency_ms = round((time.monotonic() - start) * 1000, 1)
            status_code = resp.getcode()
            body = resp.read().decode("utf-8", errors="replace")

            if status_code != 200:
                return {
                    "status": "unhealthy",
                    "latency_ms": latency_ms,
                    "timestamp": timestamp,
                    "reason": f"HTTP {status_code}",
                }

            if "BA Jira Agent" not in body:
                return {
                    "status": "unhealthy",
                    "latency_ms": latency_ms,
                    "timestamp": timestamp,
                    "reason": "Page does not contain 'BA Jira Agent'",
                }

            return {
                "status": "healthy",
                "latency_ms": latency_ms,
                "timestamp": timestamp,
            }

    except error.HTTPError as e:
        latency_ms = round((time.monotonic() - start) * 1000, 1)
        return {
            "status": "unhealthy",
            "latency_ms": latency_ms,
            "timestamp": timestamp,
            "reason": f"HTTP {e.code}: {e.reason}",
        }
    except error.URLError as e:
        latency_ms = round((time.monotonic() - start) * 1000, 1)
        return {
            "status": "unhealthy",
            "latency_ms": latency_ms,
            "timestamp": timestamp,
            "reason": f"Connection failed: {e.reason}",
        }
    except Exception as e:
        latency_ms = round((time.monotonic() - start) * 1000, 1)
        return {
            "status": "unhealthy",
            "latency_ms": latency_ms,
            "timestamp": timestamp,
            "reason": str(e),
        }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Health check for BA Jira Agent"
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help=f"Check local dev server at {LOCAL_URL}",
    )
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="Check a custom URL (overrides --local and default)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)",
    )
    args = parser.parse_args()

    if args.url:
        url = args.url
    elif args.local:
        url = LOCAL_URL
    else:
        url = HF_SPACE_URL

    result = check_health(url, timeout=args.timeout)
    print(json.dumps(result, indent=2))

    if result["status"] == "healthy":
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
