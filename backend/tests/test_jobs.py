from backend.app.db.enums import JobStatusEnum, JobTypeEnum
from backend.app.services import job_runner


class TestJobRunnerSync:
    """conftest sets JOBS_SYNC=1, so submit_job() runs the job inline —
    its result is available the instant it returns."""

    def test_status_run_all_job_recomputes_every_entity(self, db, seed):
        job = job_runner.submit_job(db, JobTypeEnum.STATUS_RUN_ALL, payload={})
        assert job.status == JobStatusEnum.SUCCEEDED
        assert job.result["processed"] == 2
        assert job.result["failed"] == 0
        assert job.started_at is not None
        assert job.finished_at is not None

    def test_process_pending_job_matches_unresolved_records(self, db, seed):
        from backend.app.db.models.source_record import SourceRecord

        sr = SourceRecord(
            source_system_id=db.query(SourceRecord.source_system_id).first()[0],
            external_id="pending-job-1",
            raw_payload={}, normalized_payload={},
            extracted_name="Acme Steel Works",
            extracted_pan="ABCDE1234F",
        )
        db.add(sr)
        db.commit()

        job = job_runner.submit_job(db, JobTypeEnum.PROCESS_PENDING, payload={"limit": 100})
        assert job.status == JobStatusEnum.SUCCEEDED
        assert job.result["processed"] == 1
        assert job.result["auto_link"] == 1

    def test_csv_match_job_scores_given_ids(self, db, seed):
        job = job_runner.submit_job(
            db, JobTypeEnum.CSV_MATCH,
            payload={"source_record_ids": [str(seed["sr_new_id"])]},
        )
        assert job.status == JobStatusEnum.SUCCEEDED
        assert job.result["new_entity"] + job.result["review"] + job.result["auto_link"] == 1

    def test_handler_exception_marks_job_failed(self, db, seed):
        job = job_runner.submit_job(
            db, JobTypeEnum.PROCESS_PENDING, payload={"limit": "not-a-number"}
        )
        assert job.status == JobStatusEnum.FAILED
        assert job.error
        assert job.finished_at is not None


class TestJobsApi:
    def test_run_all_status_queues_and_completes(self, client, seed, token):
        resp = client.post("/api/v1/status/run-all", headers=token("admin"))
        assert resp.status_code == 202
        body = resp.json()
        assert body["job_type"] == "status_run_all"
        assert body["status"] == "succeeded"  # sync mode

        listed = client.get("/api/v1/jobs", headers=token("admin"))
        assert listed.status_code == 200
        assert listed.json()["total"] >= 1

        one = client.get(f"/api/v1/jobs/{body['id']}", headers=token("admin"))
        assert one.status_code == 200
        assert one.json()["result"]["processed"] == 2

    def test_reviewer_cannot_trigger_or_view_jobs(self, client, seed, token):
        assert (
            client.post("/api/v1/status/run-all", headers=token("reviewer")).status_code
            == 403
        )
        assert client.get("/api/v1/jobs", headers=token("reviewer")).status_code == 403

    def test_process_pending_endpoint_queues_a_job(self, client, seed, token):
        resp = client.post("/api/v1/ingest/process-pending", headers=token("admin"))
        assert resp.status_code == 202
        assert resp.json()["job_type"] == "process_pending"

    def test_unknown_job_id_is_404(self, client, seed, token):
        resp = client.get(
            "/api/v1/jobs/00000000-0000-0000-0000-000000000000",
            headers=token("admin"),
        )
        assert resp.status_code == 404

    def test_csv_upload_queues_matching_job_and_backfills_report(self, client, seed, token):
        files = {"file": ("d.csv", b"name,pan\nAcme Steel Works,ABCDE1234F\n", "text/csv")}
        data = {"source_system_code": "LABOUR", "process": "true"}
        resp = client.post(
            "/api/v1/ingest/csv", files=files, data=data, headers=token("admin")
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["created"] == 1
        assert body["job_id"] is not None
        # sync mode: the job finished before the response was built
        assert body["matching"]["auto_link"] == 1
