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
from typing import Any, Dict, List
from unittest import TestCase

import pytest
import structlog
from _pytest.monkeypatch import MonkeyPatch
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask.wrappers import Response
from freezegun import freeze_time
from structlog.stdlib import BoundLogger

from dioptra.restapi.experiment.routes import BASE_ROUTE as EXPERIMENT_BASE_ROUTE
from dioptra.restapi.experiment.service import ExperimentService
from dioptra.restapi.models import Experiment, ExperimentRegistrationForm
from dioptra.restapi.experiment.schema import ExperimentUpdateSchema
from dioptra.restapi.experiment.interface import ExperimentUpdateInterface
from dioptra.restapi.experiment.errors import ExperimentRegistrationError, ExperimentDoesNotExistError


LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pytest.fixture
def experiment_registration_request() -> Dict[str, Any]:
    return {"name": "mnist"}

def test_experiment_resource_get(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockgetall(self, *args, **kwargs) -> List[Experiment]:
        LOGGER.info("Mocking ExperimentService.get_all()")
        experiment: Experiment = Experiment(
            experiment_id=1,
            created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            name="mnist",
        )
        return [experiment]

    monkeypatch.setattr(ExperimentService, "get_all", mockgetall)

    with app.test_client() as client:
        response: List[Dict[str, Any]] = client.get(
            f"/api/{EXPERIMENT_BASE_ROUTE}/"
        ).get_json()

        expected: List[Dict[str, Any]] = [
            {
                "experimentId": 1,
                "createdOn": "2020-08-17T18:46:28.717559",
                "lastModified": "2020-08-17T18:46:28.717559",
                "name": "mnist",
            }
        ]

        assert response == expected


@freeze_time("2020-08-17T18:46:28.717559")
def test_experiment_resource_post(
    app: Flask,
    db: SQLAlchemy,
    experiment_registration_request: Dict[str, Any],
    monkeypatch: MonkeyPatch,
) -> None:
    def mockcreate(*args, **kwargs) -> Experiment:
        LOGGER.info("Mocking ExperimentService.create()")
        timestamp = datetime.datetime.now()
        return Experiment(
            experiment_id=1,
            created_on=timestamp,
            last_modified=timestamp,
            name="mnist",
        )

    monkeypatch.setattr(ExperimentService, "create", mockcreate)

    with app.test_client() as client:
        response: Dict[str, Any] = client.post(
            f"/api/{EXPERIMENT_BASE_ROUTE}/",
            content_type="multipart/form-data",
            data=experiment_registration_request,
            follow_redirects=True,
        ).get_json()
        LOGGER.info("Response received", response=response)

        expected: Dict[str, Any] = {
            "experimentId": 1,
            "createdOn": "2020-08-17T18:46:28.717559",
            "lastModified": "2020-08-17T18:46:28.717559",
            "name": "mnist",
        }

        assert response == expected


def test_experiment_resource_post_registration_error( app: Flask,
    db: SQLAlchemy,
    experiment_registration_request: Dict[str, Any],
    monkeypatch: MonkeyPatch,
) -> None:
    def mockvalidateonsubmit(*args, **kwargs) -> bool:
        LOGGER.info("Mocking ExperimentRegistrationForm.validate_on_submit())")
        return False

    monkeypatch.setattr(ExperimentRegistrationForm, "validate_on_submit", mockvalidateonsubmit)

    with app.test_client() as client:
        response: Dict[str, Any] = client.post(
            f"/api/{EXPERIMENT_BASE_ROUTE}/",
            content_type="multipart/form-data",
            data=experiment_registration_request,
            follow_redirects=True,
        )
        LOGGER.info("Response received", response=response)

        assert response._status_code == 400
        pytest.raises(ExperimentRegistrationError)


def test_experiment_id_resource_get(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockgetbyid(self, experiment_id: str, *args, **kwargs) -> Experiment:
        LOGGER.info("Mocking ExperimentService.get_by_id()")
        return Experiment(
            experiment_id=experiment_id,
            created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            name="mnist",
        )

    monkeypatch.setattr(ExperimentService, "get_by_id", mockgetbyid)
    experiment_id: int = 1

    with app.test_client() as client:
        response: Dict[str, Any] = client.get(
            f"/api/{EXPERIMENT_BASE_ROUTE}/{experiment_id}"
        ).get_json()

        expected: Dict[str, Any] = {
            "experimentId": 1,
            "createdOn": "2020-08-17T18:46:28.717559",
            "lastModified": "2020-08-17T18:46:28.717559",
            "name": "mnist",
        }

        assert response == expected


def test_experiment_id_resource_get_non_existing(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockgetbyid(self, experiment_id: str, *args, **kwargs) -> Experiment:
        LOGGER.info("Mocking ExperimentService.get_by_id()")
        return None

    monkeypatch.setattr(ExperimentService, "get_by_id", mockgetbyid)
    experiment_id: int = 1

    with app.test_client() as client:
        response = client.get(
            f"/api/{EXPERIMENT_BASE_ROUTE}/{experiment_id}"
        )

    assert response._status_code == 404
    pytest.raises(ExperimentDoesNotExistError)


def test_experiment_id_resource_delete(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockdeleteexpirement(self, experiment_id: str, *args, **kwargs) -> List[int]:
        LOGGER.info("Mocking ExperimentService.delete_experiment()")
        return [experiment_id]
    
    monkeypatch.setattr(ExperimentService, "delete_experiment", mockdeleteexpirement)
    experiment_id: int = 1
    
    with app.test_client() as client:
        response: Dict[str, Any] = client.delete(
            f"/api/{EXPERIMENT_BASE_ROUTE}/{experiment_id}"
        ).get_json()
        LOGGER.info("Response received", response=response)

        expected: Dict[str, Any] = {
            "status": "Success",
            "id": [experiment_id],
        }

        assert response == expected


def test_expirement_id_resource_put(
    app: Flask,
    monkeypatch: MonkeyPatch
) -> None:
    def mockgetbyid(self, experiment_id: str, *args, **kwargs) -> Experiment:
        LOGGER.info("Mocking ExperimentService.get_by_id()")
        return Experiment(
            experiment_id=experiment_id,
            created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            name="mnist",
        )
    monkeypatch.setattr(ExperimentService, "get_by_id", mockgetbyid)
    experiment_id: int = 1

    def mockrenameexpirement(self, experiment: Experiment, new_name: str, *args, **kwargs) -> List[int]:
        LOGGER.info("Mocking ExperimentService.rename_experiment()")
        experiment.name = new_name
        return experiment
    
    monkeypatch.setattr(ExperimentService, "rename_experiment", mockrenameexpirement)
    
    payload: Dict[str, Any] = {"name": "mnist_changed"}
    with app.test_client() as client:
        response: Dict[str, Any] = client.put(
            f"/api/{EXPERIMENT_BASE_ROUTE}/{experiment_id}",
            json=payload
        ).get_json()
        LOGGER.info("Response received", response=response)

        
        expected: Dict[str, Any] = {
            "experimentId": 1,
            "createdOn": "2020-08-17T18:46:28.717559",
            "lastModified": "2020-08-17T18:46:28.717559",
            "name": "mnist_changed",
        }
        

        assert response == expected


def test_experiment_name_resource_get(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockgetbyname(self, experiment_name: str, *args, **kwargs) -> Experiment:
        LOGGER.info("Mocking ExperimentService.get_by_name()")
        return Experiment(
            experiment_id=1,
            created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            name=experiment_name,
        )

    monkeypatch.setattr(ExperimentService, "get_by_name", mockgetbyname)
    experiment_name: str = "mnist"

    with app.test_client() as client:
        response: Dict[str, Any] = client.get(
            f"/api/{EXPERIMENT_BASE_ROUTE}/name/{experiment_name}"
        ).get_json()

        expected: Dict[str, Any] = {
            "experimentId": 1,
            "createdOn": "2020-08-17T18:46:28.717559",
            "lastModified": "2020-08-17T18:46:28.717559",
            "name": "mnist",
        }

        assert response == expected

    
def test_experiment_name_resource_get_non_existing(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockgetbyname(self, experiment_name: str, *args, **kwargs) -> Experiment:
        LOGGER.info("Mocking ExperimentService.get_by_name()")
        return None

    monkeypatch.setattr(ExperimentService, "get_by_name", mockgetbyname)
    experiment_name: str = "mnist"

    with app.test_client() as client:
        response = client.get(
            f"/api/{EXPERIMENT_BASE_ROUTE}/name/{experiment_name}"
        )

    assert response._status_code == 404
    pytest.raises(ExperimentDoesNotExistError)


def test_expirement_name_resource_put(
    app: Flask,
    monkeypatch: MonkeyPatch
) -> None:
    def mockgetbyname(self, experiment_name: str, *args, **kwargs) -> Experiment:
        LOGGER.info("Mocking ExperimentService.get_by_name()")
        return Experiment(
            experiment_id=1,
            created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            name=experiment_name,
        )

    monkeypatch.setattr(ExperimentService, "get_by_name", mockgetbyname)
    experiment_name: str = "mnist"

    def mockrenameexpirement(self, experiment: Experiment, new_name: str, *args, **kwargs) -> List[int]:
        LOGGER.info("Mocking ExperimentService.rename_experiment()")
        experiment.name = new_name
        return experiment
    
    monkeypatch.setattr(ExperimentService, "rename_experiment", mockrenameexpirement)
    
    payload: Dict[str, Any] = {"name": "mnist_changed"}
    with app.test_client() as client:
        response: Dict[str, Any] = client.put(
            f"/api/{EXPERIMENT_BASE_ROUTE}/name/{experiment_name}",
            json=payload
        ).get_json()
        LOGGER.info("Response received", response=response)

        
        expected: Dict[str, Any] = {
            "experimentId": 1,
            "createdOn": "2020-08-17T18:46:28.717559",
            "lastModified": "2020-08-17T18:46:28.717559",
            "name": "mnist_changed",
        }
        

        assert response == expected
    