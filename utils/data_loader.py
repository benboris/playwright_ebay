"""
Data Loader - טעינת נתוני בדיקה מקובץ חיצוני (JSON / CSV / YAML).
תומך ב-Data-Driven Testing.
"""
import json
import csv
import os
import logging
from typing import Any, Dict, List

logger = logging.getLogger("DataLoader")


class DataLoader:
    """
    Loads test data from JSON, CSV, or YAML files.
    Provides typed accessors for common test-data structures.
    """

    def __init__(self, data_file: str = "data/test_data.json"):
        self.data_file = data_file
        self._data: Dict[str, Any] = {}
        self._load()

    # ─────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────

    def get_scenarios(self) -> List[Dict[str, Any]]:
        return self._data.get("test_scenarios", [])

    def get_credentials(self) -> Dict[str, str]:
        return self._data.get("credentials", {})

    def get_settings(self) -> Dict[str, Any]:
        return self._data.get("settings", {})

    def get_scenario_by_id(self, scenario_id: str) -> Dict[str, Any] | None:
        for s in self.get_scenarios():
            if s.get("scenario_id") == scenario_id:
                return s
        return None

    # ─────────────────────────────────────────────
    # Private loaders
    # ─────────────────────────────────────────────

    def _load(self) -> None:
        ext = os.path.splitext(self.data_file)[1].lower()
        loaders = {".json": self._load_json, ".csv": self._load_csv, ".yaml": self._load_yaml, ".yml": self._load_yaml}
        loader = loaders.get(ext)
        if loader is None:
            raise ValueError(f"Unsupported data file format: {ext}")
        self._data = loader()
        logger.info(f"Test data loaded from: {self.data_file}")

    def _load_json(self) -> Dict[str, Any]:
        with open(self.data_file, encoding="utf-8") as f:
            return json.load(f)

    def _load_csv(self) -> Dict[str, Any]:
        """CSV is expected to have one scenario per row."""
        scenarios = []
        with open(self.data_file, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # coerce numeric fields
                for key in ("max_price", "limit", "budget_per_item", "expected_max_total"):
                    if key in row:
                        row[key] = float(row[key]) if "." in row[key] else int(row[key])
                scenarios.append(row)
        return {"test_scenarios": scenarios, "credentials": {}, "settings": {}}

    def _load_yaml(self) -> Dict[str, Any]:
        try:
            import yaml
        except ImportError:
            raise ImportError("PyYAML is required for YAML support: pip install pyyaml")
        with open(self.data_file, encoding="utf-8") as f:
            return yaml.safe_load(f)
