#!/usr/bin/env python3
import json
import os
import unittest
from typing import Any, Dict, List

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))

class ConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        with open(os.path.join(REPO_ROOT, "tvbox.json"), "r", encoding="utf-8") as f:
            self.tv = json.load(f)
        with open(os.path.join(REPO_ROOT, "sources", "sources.json"), "r", encoding="utf-8") as f:
            self.sources = json.load(f).get("sources", [])

    def test_json_parseable(self):
        self.assertIsInstance(self.tv, dict)

    def test_sites_is_list(self):
        self.assertIn("sites", self.tv)
        self.assertIsInstance(self.tv["sites"], list)

    def test_keys_unique(self):
        keys = [s["key"] for s in self.tv["sites"]]
        self.assertEqual(len(keys), len(set(keys)), "site.key 存在重复")

    def test_apis_unique(self):
        apis = [s["api"] for s in self.tv["sites"]]
        self.assertEqual(len(apis), len(set(apis)), "site.api 存在重复")

    def test_apis_https(self):
        for s in self.tv["sites"]:
            self.assertTrue(s["api"].lower().startswith("https://"), f"{s['key']} api 非 HTTPS")

    def test_disabled_not_included(self):
        disabled_keys = {src["key"] for src in self.sources if not src.get("enabled", False)}
        for s in self.tv["sites"]:
            self.assertNotIn(s["key"], disabled_keys)

    def test_priority_sorted(self):
        priorities = [s.get("priority", 0) for s in self.tv["sites"]]
        self.assertEqual(priorities, sorted(priorities, reverse=True), "sites 未按 priority 降序排序")

    def test_required_fields_present(self):
        for s in self.tv["sites"]:
            for f in ("key", "name", "type", "api"):
                self.assertIn(f, s, f"{s.get('key')} 缺少 {f}")

if __name__ == "__main__":
    unittest.main()
