#!/usr/bin/env python3
"""
检查 sources/sources.json 中启用的数据源的可用性，生成 reports/source-health.json。
Python 3.11+, 仅使用标准库。
"""
from __future__ import annotations
import json
import logging
import os
import time
import urllib.request
import urllib.error
from typing import Any, Dict, List
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

LOG = logging.getLogger("check_sources")
LOG.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
LOG.addHandler(handler)

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))


def load_sources(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("sources", [])


def probe_source(source: Dict[str, Any]) -> Dict[str, Any]:
    key = source.get("key")
    name = source.get("name")
    url = source.get("api")
    timeout = float(source.get("timeout", 10))
    result: Dict[str, Any] = {
        "key": key,
        "name": name,
        "url": url,
        "http_status": None,
        "response_time_ms": None,
        "content_type": None,
        "valid": False,
        "status": "offline",
        "error": None,
    }

    headers = {"User-Agent": "tvbox-checker/1.0 (+https://github.com/)"}

    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        start = time.monotonic()
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = (time.monotonic() - start) * 1000.0
            result["http_status"] = resp.getcode()
            result["response_time_ms"] = int(elapsed)
            content_type = resp.headers.get("Content-Type", "")
            result["content_type"] = content_type
            body = resp.read(64 * 1024)  # 读取最多 64KB（避免大规模采集）
            # 尝试解析 JSON
            try:
                decoded = body.decode("utf-8", errors="replace")
                json.loads(decoded)
                result["valid"] = True
                result["status"] = "online"
            except Exception:
                # 不是 JSON，尝试 XML
                try:
                    ET.fromstring(body)
                    result["valid"] = True
                    result["status"] = "online"
                except Exception:
                    result["valid"] = False
                    result["status"] = "invalid"
    except urllib.error.HTTPError as e:
        result["http_status"] = e.code
        result["error"] = f"HTTPError: {e.reason}"
        result["status"] = "offline" if e.code >= 400 else "invalid"
    except urllib.error.URLError as e:
        result["error"] = f"URLError: {e.reason}"
        # 可能是超时或网络问题
        if isinstance(e.reason, TimeoutError) or "timed out" in str(e.reason):
            result["status"] = "timeout"
        else:
            result["status"] = "offline"
    except Exception as e:
        result["error"] = f"Exception: {e}"
        result["status"] = "offline"

    return result


def main() -> int:
    sources_path = os.path.join(REPO_ROOT, "sources", "sources.json")
    reports_dir = os.path.join(REPO_ROOT, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    try:
        sources = load_sources(sources_path)
    except Exception as e:
        LOG.error("无法读取 sources.json: %s", e)
        return 2

    reports: List[Dict[str, Any]] = []
    for src in sources:
        try:
            if not src.get("enabled", False):
                LOG.info("跳过未启用的数据源: %s", src.get("key"))
                continue
            LOG.info("检测数据源: %s (%s)", src.get("key"), src.get("api"))
            r = probe_source(src)
            reports.append(r)
        except Exception as e:
            LOG.exception("检测数据源时发生未捕获异常: %s", e)
            reports.append({
                "key": src.get("key"),
                "name": src.get("name"),
                "url": src.get("api"),
                "http_status": None,
                "response_time_ms": None,
                "content_type": None,
                "valid": False,
                "status": "offline",
                "error": f"unexpected: {e}"
            })
            continue

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": reports
    }
    out_path = os.path.join(reports_dir, "source-health.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    LOG.info("已写入健康报告: %s", out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
