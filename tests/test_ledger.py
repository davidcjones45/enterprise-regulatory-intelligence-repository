from pathlib import Path

import pytest

from erir.ledger import connect, initialize, load_records, reconstruct_obligation
from erir.models import load_json


ROOT = Path(__file__).resolve().parents[1]


def test_ledger_load_and_reconstruct(tmp_path):
    database = tmp_path / "test.db"
    initialize(database, ROOT / "sql" / "schema.sql")
    records = [load_json(path) for path in sorted((ROOT / "examples" / "valid").glob("*.json"))]

    with connect(database) as connection:
        assert load_records(connection, records) == len(records)
        result = reconstruct_obligation(connection, "OBL-FTC-001")
        assert len(result) == 1
        assert result[0]["source_json"] is not None
        assert "CTL-CLAIMS-001" in result[0]["controls"]


def test_ledger_is_append_only(tmp_path):
    database = tmp_path / "test.db"
    initialize(database, ROOT / "sql" / "schema.sql")
    records = [load_json(ROOT / "examples" / "valid" / "obligation.json")]

    with connect(database) as connection:
        load_records(connection, records)
        with pytest.raises(Exception):
            connection.execute("DELETE FROM ledger_event")
