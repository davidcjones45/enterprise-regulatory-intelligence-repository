from pathlib import Path

from erir.ingestion import SourceIngestor


class FakeResponse:
    def __init__(self, content: bytes, content_type: str = "application/pdf"):
        self.content = content
        self.status = 200
        self.headers = self
        self.content_type = content_type

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return self.content

    def get_content_type(self):
        return self.content_type


def test_ingestion_stores_hashes_detects_changes_and_queues_work(tmp_path):
    content = [b"first version"]
    ingestor = SourceIngestor(tmp_path, opener=lambda _: FakeResponse(content[0]))
    source = {"id": "SRC-US-TEST", "official_url": "https://authority.example/source"}

    first = ingestor.ingest(source)
    second = ingestor.ingest(source)
    content[0] = b"revised version"
    third = ingestor.ingest(source)

    assert first["change_type"] == "new"
    assert second["change_type"] == "unchanged"
    assert third["change_type"] == "changed"
    assert Path(tmp_path / first["content_path"]).read_bytes() == b"first version"
    assert len(ingestor.extraction_tasks()) == 2
    assert all(task["status"] == "pending_human_review" for task in ingestor.extraction_tasks())


def test_machine_candidate_preserves_source_snapshot_provenance(tmp_path):
    ingestor = SourceIngestor(tmp_path, opener=lambda _: FakeResponse(b"source text"))
    snapshot = ingestor.ingest({"id": "SRC-US-TEST", "official_url": "https://authority.example/source"})

    candidate = ingestor.queue_machine_candidate(
        source_id="SRC-US-TEST",
        snapshot_sha256=snapshot["content_sha256"],
        candidate_text="A creditor must provide specific reasons.",
        pinpoint="Section 7",
        generator="demonstration-extractor/0.1",
    )

    assert candidate["status"] == "pending_human_review"
    assert candidate["provenance"]["snapshot_sha256"] == snapshot["content_sha256"]
    assert candidate["provenance"]["generator"] == "demonstration-extractor/0.1"
