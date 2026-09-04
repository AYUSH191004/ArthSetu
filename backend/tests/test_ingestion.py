from backend.app.db.models.business_entity import BusinessEntity
from backend.app.db.models.source_record import SourceRecord
from backend.app.services import ingestion


class TestParseCsv:
    def test_maps_aliased_headers(self):
        raw = (
            b"Registration No,Firm Name,PAN No,GST,Registered Address,Pincode,Owner\n"
            b'L-1,Punjab Steel,ABCDE1234F,03ABCDE1234F1Z5,"Focal Point, Ludhiana",141001,R Singh\n'
        )
        rows = ingestion.parse_csv(raw)
        assert len(rows) == 1
        row = rows[0]
        assert row["external_id"] == "L-1"
        assert row["name"] == "Punjab Steel"
        assert row["pan"] == "ABCDE1234F"
        assert row["gstin"] == "03ABCDE1234F1Z5"
        assert row["pin"] == "141001"
        assert row["_extra"] == {"Owner": "R Singh"}

    def test_handles_bom_and_blank_input(self):
        assert ingestion.parse_csv(b"") == []
        rows = ingestion.parse_csv("﻿name\nAcme\n".encode())
        assert rows[0]["name"] == "Acme"


class TestIngestRows:
    def _rows(self, *records):
        return [
            {"external_id": r.get("id", ""), "name": r["name"],
             "pan": r.get("pan", ""), "gstin": r.get("gstin", ""),
             "address": r.get("address", ""), "pin": r.get("pin", ""),
             "_extra": {}}
            for r in records
        ]

    def test_creates_records_and_runs_matching(self, db, seed):
        report = ingestion.ingest_rows(
            db, "LABOUR",
            self._rows(
                {"id": "X-1", "name": "Acme Steel Works", "pan": "ABCDE1234F",
                 "address": "Plot 42 Focal Point Ludhiana", "pin": "141001"},
                {"id": "X-2", "name": "Falcon Freight", "pan": "FLCN9999K"},
            ),
            process=True,
        )
        assert report.rows_read == 2
        assert report.created == 2
        assert report.matching is not None
        # Acme row has an exact PAN + name -> auto link; Falcon has no match -> new.
        assert report.matching.auto_link == 1
        assert report.matching.new_entity == 1

    def test_skips_duplicate_external_ids(self, db, seed):
        rows = self._rows({"id": "DUP-1", "name": "Beta Traders"})
        first = ingestion.ingest_rows(db, "LABOUR", rows, process=False)
        second = ingestion.ingest_rows(db, "LABOUR", list(rows), process=False)
        assert first.created == 1
        assert second.created == 0
        assert second.skipped_duplicates == 1

    def test_missing_name_is_a_row_error_not_a_crash(self, db, seed):
        report = ingestion.ingest_rows(
            db, "LABOUR",
            self._rows({"id": "OK", "name": "Valid Co"}, {"id": "BAD", "name": ""}),
            process=False,
        )
        assert report.created == 1
        assert len(report.errors) == 1
        assert report.errors[0].row == 2

    def test_unknown_source_system_raises(self, db, seed):
        import pytest

        with pytest.raises(ValueError):
            ingestion.ingest_rows(db, "NOPE", self._rows({"name": "X"}), process=False)

    def test_auto_external_id_dedupes_identical_rows(self, db, seed):
        rows = self._rows({"name": "Zephyr Logistics", "pin": "143001"})
        ingestion.ingest_rows(db, "LABOUR", rows, process=False)
        again = ingestion.ingest_rows(db, "LABOUR", list(rows), process=False)
        assert again.skipped_duplicates == 1


class TestProcessPending:
    def test_processes_only_unresolved_records(self, db, seed):
        # add a raw record with no link / review
        sr = SourceRecord(
            source_system_id=(
                db.query(SourceRecord.source_system_id).first()[0]
            ),
            external_id="pending-1",
            raw_payload={}, normalized_payload={},
            extracted_name="Acme Steel Works",
            extracted_pan="ABCDE1234F",
        )
        db.add(sr)
        db.commit()

        assert ingestion.pending_count(db) == 1
        result = ingestion.process_pending(db)
        assert result["processed"] == 1
        assert result["auto_link"] == 1
        assert ingestion.pending_count(db) == 0


class TestIngestApi:
    def test_source_systems_listing_needs_auth(self, client, seed, token):
        assert client.get("/api/v1/ingest/source-systems").status_code == 401
        ok = client.get("/api/v1/ingest/source-systems", headers=token("viewer"))
        assert ok.status_code == 200
        assert ok.json()[0]["code"] == "LABOUR"

    def test_csv_upload_is_admin_only(self, client, seed, token):
        files = {"file": ("d.csv", b"name\nAcme Co\n", "text/csv")}
        data = {"source_system_code": "LABOUR"}
        assert (
            client.post("/api/v1/ingest/csv", files=files, data=data,
                        headers=token("reviewer")).status_code
            == 403
        )
        resp = client.post(
            "/api/v1/ingest/csv", files=files, data=data, headers=token("admin")
        )
        assert resp.status_code == 200
        assert resp.json()["created"] == 1

    def test_template_download(self, client, seed, token):
        resp = client.get("/api/v1/ingest/template", headers=token("viewer"))
        assert resp.status_code == 200
        assert resp.text.startswith("external_id,name,pan")

    def test_records_endpoint_creates_and_matches(self, client, seed, token):
        resp = client.post(
            "/api/v1/ingest/records",
            headers=token("admin"),
            json={
                "source_system_code": "LABOUR",
                "process": True,
                "records": [
                    {"name": "Acme Steel Works", "pan": "ABCDE1234F"},
                ],
            },
        )
        assert resp.status_code == 200
        assert resp.json()["matching"]["auto_link"] == 1
        # the linked business gained a record
        prof = client.get(
            "/api/v1/business/UBID000001", headers=token("viewer")
        ).json()
        assert prof["linked_records_count"] >= 2
