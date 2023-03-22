# This Software (Dioptra) is being made available as a public service by the
# National Institute of Standards and Technology (NIST), an Agency of the United
# States Department of Commerce. This software was developed in part by employees of
# NIST and in part by NIST contractors. Copyright in portions of this software that
# were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
# to Title 17 United States Code Section 105, works of NIST employees are not
# subject to copyright protection in the United States. However, NIST may hold
# international copyright in software created by its employees and domestic
# copyright (or licensing rights) in portions of software that were assigned or
# licensed to NIST. To the extent that NIST holds copyright in this software, it is
# being made available under the Creative Commons Attribution 4.0 International
# license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
# of the software developed or licensed by NIST.
#
# ACCESS THE FULL CC BY 4.0 LICENSE HERE:
# https://creativecommons.org/licenses/by/4.0/legalcode
from __future__ import annotations

import datetime
import uuid
from typing import Any, BinaryIO, Dict, List

import pytest
import structlog
from _pytest.monkeypatch import MonkeyPatch
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from freezegun import freeze_time
from structlog.stdlib import BoundLogger

from dioptra.restapi.job.routes import BASE_ROUTE as JOB_BASE_ROUTE
from dioptra.restapi.job.service import JobService
from dioptra.restapi.job.errors import JobDoesNotExistError, JobSubmissionError
from dioptra.restapi.models import Experiment, Job, JobForm
from dioptra.restapi.shared.s3.service import S3Service

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pytest.fixture
def experiment() -> Experiment:
    return Experiment(
        experiment_id=1,
        created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        name="mnist",
    )


@pytest.fixture
def job_form_request(workflow_tar_gz: BinaryIO) -> Dict[str, Any]:
    return {
        "experiment_name": "mnist",
        "queue": "tensorflow_cpu",
        "timeout": "12h",
        "entry_point": "main",
        "entry_point_kwargs": "-P var1=testing",
        "workflow": (workflow_tar_gz, "workflows.tar.gz"),
    }


def test_job_resource_get(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockgetall(self, *args, **kwargs) -> List[Job]:
        LOGGER.info("Mocking JobService.get_all()")
        job: Job = Job(
            job_id="4520511d-678b-4966-953e-af2d0edcea32",
            mlflow_run_id="a82982a795824afb926e646277eda152",
            experiment_id=1,
            queue_id=1,
            created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            timeout="12h",
            workflow_uri="s3://workflow/workflows.tar.gz",
            entry_point="main",
            depends_on=None,
            status="finished",
        )
        return [job]

    monkeypatch.setattr(JobService, "get_all", mockgetall)

    with app.test_client() as client:
        response: List[Dict[str, Any]] = client.get(
            f"/api/{JOB_BASE_ROUTE}/"
        ).get_json()

        expected: List[Dict[str, Any]] = [
            {
                "jobId": "4520511d-678b-4966-953e-af2d0edcea32",
                "mlflowRunId": "a82982a795824afb926e646277eda152",
                "experimentId": 1,
                "queueId": 1,
                "createdOn": "2020-08-17T18:46:28.717559",
                "lastModified": "2020-08-17T18:46:28.717559",
                "timeout": "12h",
                "workflowUri": "s3://workflow/workflows.tar.gz",
                "entryPoint": "main",
                "entryPointKwargs": None,
                "dependsOn": None,
                "status": "finished",
            }
        ]

        assert response == expected


@freeze_time("2020-08-17T18:46:28.717559")
def test_job_resource_post(
    app: Flask,
    db: SQLAlchemy,
    experiment: Experiment,
    job_form_request: Dict[str, Any],
    monkeypatch: MonkeyPatch,
) -> None:
    def mockuuid4() -> uuid.UUID:
        return uuid.UUID("3db40500-01b1-45a4-ae18-64e7d1bc7e9a")

    def mocksubmit(*args, **kwargs) -> Job:
        LOGGER.info("Mocking JobService.submit()")
        timestamp = datetime.datetime.now()
        return Job(
            job_id="4520511d-678b-4966-953e-af2d0edcea32",
            mlflow_run_id=None,
            experiment_id=1,
            queue_id=1,
            created_on=timestamp,
            last_modified=timestamp,
            timeout="12h",
            workflow_uri=(
                "s3://workflow/3db4050001b145a4ae1864e7d1bc7e9a/workflows.tar.gz"
            ),
            entry_point="main",
            entry_point_kwargs="-P var1=testing",
            depends_on=None,
            status="queued",
        )

    def mockupload(fileobj, bucket, key, *args, **kwargs):
        LOGGER.info(
            "Mocking S3Service.upload()", fileobj=fileobj, bucket=bucket, key=key
        )
        return S3Service.as_uri(bucket=bucket, key=key)

    monkeypatch.setattr(JobService, "submit", mocksubmit)
    monkeypatch.setattr(uuid, "uuid4", mockuuid4)
    monkeypatch.setattr(S3Service, "upload", mockupload)

    db.session.add(experiment)
    db.session.commit()

    with app.test_client() as client:
        response: Dict[str, Any] = client.post(
            f"/api/{JOB_BASE_ROUTE}/",
            content_type="multipart/form-data",
            data=job_form_request,
            follow_redirects=True,
        ).get_json()
        LOGGER.info("Response received", response=response)

        expected: Dict[str, Any] = {
            "jobId": "4520511d-678b-4966-953e-af2d0edcea32",
            "mlflowRunId": None,
            "experimentId": 1,
            "queueId": 1,
            "createdOn": "2020-08-17T18:46:28.717559",
            "lastModified": "2020-08-17T18:46:28.717559",
            "timeout": "12h",
            "workflowUri": (
                "s3://workflow/3db4050001b145a4ae1864e7d1bc7e9a/workflows.tar.gz"
            ),
            "entryPoint": "main",
            "entryPointKwargs": "-P var1=testing",
            "dependsOn": None,
            "status": "queued",
        }

        assert response == expected


def test_job_resource_post_job_submission_error(
    app: Flask,
    job_form_request: Dict[str, Any],
    monkeypatch: MonkeyPatch,
) -> None:
    def mockvalidateonsubmit(*args, **kwargs) -> bool:
        LOGGER.info("Mocking ExperimentRegistrationForm.validate_on_submit())")
        return False

    monkeypatch.setattr(JobForm, "validate_on_submit", mockvalidateonsubmit)

    with app.test_client() as client:
        response: Dict[str, Any] = client.post(
            f"/api/{JOB_BASE_ROUTE}/",
            content_type="multipart/form-data",
            data=job_form_request,
            follow_redirects=True,
        )
        LOGGER.info("Response received", response=response)

        assert response._status_code == 400
        pytest.raises(JobSubmissionError)


def test_job_id_resource_get(
    app: Flask,
    monkeypatch: MonkeyPatch,
) -> None:
    def mockgetbyid(self, job_id: str, *args, **kwargs) -> Job:
        LOGGER.info("Mocking JobService.get_by_id()")
        job: Job = Job(
            job_id=job_id,
            mlflow_run_id="a82982a795824afb926e646277eda152",
            experiment_id=1,
            queue_id=1,
            created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            timeout="12h",
            workflow_uri="s3://workflow/workflows.tar.gz",
            entry_point="main",
            depends_on=None,
            status="started",
        )
        return job

    monkeypatch.setattr(JobService, "get_by_id", mockgetbyid)
    job_id: str = "4520511d-678b-4966-953e-af2d0edcea32"

    with app.test_client() as client:
        response: Dict[str, Any] = client.get(
            f"/api/{JOB_BASE_ROUTE}/{job_id}"
        ).get_json()

        expected: Dict[str, Any] = {
            "jobId": "4520511d-678b-4966-953e-af2d0edcea32",
            "mlflowRunId": "a82982a795824afb926e646277eda152",
            "experimentId": 1,
            "queueId": 1,
            "createdOn": "2020-08-17T18:46:28.717559",
            "lastModified": "2020-08-17T18:46:28.717559",
            "timeout": "12h",
            "workflowUri": "s3://workflow/workflows.tar.gz",
            "entryPoint": "main",
            "entryPointKwargs": None,
            "dependsOn": None,
            "status": "started",
        }

        assert response == expected


def test_job_id_resource_get_non_existing(
    app: Flask,
    monkeypatch: MonkeyPatch,
) -> None:
    def mockgetbyid(self, job_id: str, *args, **kwargs) -> Job:
        LOGGER.info("Mocking JobService.get_by_id()")
        return None

    monkeypatch.setattr(JobService, "get_by_id", mockgetbyid)
    job_id: str = "4520511d-678b-4966-953e-af2d0edcea32"

    with app.test_client() as client:
        response: Dict[str, Any] = client.get(
            f"/api/{JOB_BASE_ROUTE}/{job_id}"
        )

        assert response._status_code == 404
        pytest.raises(JobDoesNotExistError)