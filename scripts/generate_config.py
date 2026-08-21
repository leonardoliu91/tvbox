#!/usr/bin/env python3
"""
根据 sources/sources.json 生成 tvbox.json，按 priority 降序。
仅将用户提供的启用源写入 sites。
"""
from __future__ import annotations
import json
import logging
import os
from typing import Any, Dict, List

LOG = logging.getLogger("generate_config")
LOG.setLevel(logging.INFO)
LOG.addHandler(logging.StreamHandler())

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))

def load_sources(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("sources", [])

def build_site_entry(src: Dict[str, Any]) -> Dict[str, Any]:
    # 只包含明确字段，不生成额外第三方信息
    return {
        "key": src["key"],
        "name": src.get("name", src["key"]),
        "type": src.get("type", 1),
        "api": src["api"],
        "quickSearch": src.get("quickSearch", 1),
        "searchable": src.get("searchable", 1),
        "filterable": src.get("filterable", 0),
        "priority": src.get("priority", 0),
        "timeout": src.get("timeout", 10)
    }

def main() -> int:
    sources_path = os.path.join(REPO_ROOT, "sources", "sources.json")
    tvbox_path = os.path.join(REPO_ROOT, "tvbox.json")
    try:
        sources = load_sources(sources_path)
    except Exception as e:
        LOG.error("读取 sources 失败: %s", e)
        return 2

    enabled = [s for s in sources if s.get("enabled", False)]
    enabled_sorted = sorted(enabled, key=lambda s: s.get("priority", 0), reverse=True)

    sites = [build_site_entry(s) for s in enabled_sorted]

    out = {
        "spider": "",
        "sites": sites,
        "parsers": [],
        "flags": [
            "youku",
            "qq",
            "iqiyi",
            "qiyi",
            "letv",
            "sohu",
            "tudou",
            "pptv",
            "mgtv",
            "wasu"
        ]
    }

    with open(tvbox_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    LOG.info("已生成 tvbox.json (%d sites)", len(sites))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
