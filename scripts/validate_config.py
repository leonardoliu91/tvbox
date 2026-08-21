#!/usr/bin/env python3
"""
验证 tvbox.json 合法性并执行规则检查。
如果验证失败，程序以非 0 退出。
"""
from __future__ import annotations
import json
import logging
import os
import sys
from typing import Any, Dict, List, Set

LOG = logging.getLogger("validate_config")
LOG.setLevel(logging.INFO)
LOG.addHandler(logging.StreamHandler())

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))

def load_tvbox(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def validate(tv: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    if "spider" not in tv:
        errs.append("缺少 top-level 字段: spider")
    if "sites" not in tv:
        errs.append("缺少 top-level 字段: sites")
    else:
        if not isinstance(tv["sites"], list):
            errs.append("sites 必须是数组")
        else:
            keys: Set[str] = set()
            apis: Set[str] = set()
            for i, s in enumerate(tv["sites"]):
                prefix = f"sites[{i}]"
                if not isinstance(s, dict):
                    errs.append(f"{prefix} 必须为对象")
                    continue
                for field in ("key", "name", "type", "api"):
                    if field not in s:
                        errs.append(f"{prefix} 缺少字段: {field}")
                key = s.get("key")
                api = s.get("api")
                if key in keys:
                    errs.append(f"重复 key: {key}")
                else:
                    keys.add(key)
                if api in apis:
                    errs.append(f"重复 api: {api}")
                else:
                    apis.add(api)
                if isinstance(api, str) and not api.lower().startswith("https://"):
                    errs.append(f"{prefix}.api 必须为 HTTPS: {api}")
                if s.get("enabled", None) is False:
                    errs.append(f"{prefix} 包含 enabled=false（不允许）")
    return errs

def main() -> int:
    tvbox_path = os.path.join(REPO_ROOT, "tvbox.json")
    try:
        tv = load_tvbox(tvbox_path)
    except json.JSONDecodeError as e:
        LOG.error("tvbox.json 不是合法 JSON: %s", e)
        return 2
    except Exception as e:
        LOG.error("读取 tvbox.json 失败: %s", e)
        return 2

    errs = validate(tv)
    if errs:
        LOG.error("验证失败，共 %d 个错误：", len(errs))
        for e in errs:
            LOG.error(" - %s", e)
        return 3

    LOG.info("验证通过：tvbox.json 合法且满足规则")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
