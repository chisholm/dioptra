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
from typing import List

import pytest
from _pytest.monkeypatch import MonkeyPatch
import structlog
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from freezegun import freeze_time
from structlog.stdlib import BoundLogger

from dioptra.restapi.experiment.errors import ExperimentAlreadyExistsError
from dioptra.restapi.experiment.service import ExperimentService
from dioptra.restapi.models import (
    Experiment,
    ExperimentRegistrationForm,
    ExperimentRegistrationFormData,
)
from dioptra.restapi.shared.mlflow_tracking.service import MLFlowTrackingService
import dioptra.restapi.experiment.schema

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pytest.fixture
def experiment_registration_form(app: Flask) -> ExperimentRegistrationForm:
    with app.test_request_context():
        form = ExperimentRegistrationForm(data={"name": "mnist"})

    return form


@pytest.fixture
def experiment_registration_form_data(app: Flask) -> ExperimentRegistrationFormData:
    return ExperimentRegistrationFormData(name="mnist")


@pytest.fixture
def experiment_service(dependency_injector) -> ExperimentService:
    return dependency_injector.get(ExperimentService)


@pytest.fixture
def mlflow_tracking_service(dependency_injector) -> MLFlowTrackingService:
    return dependency_injector.get(MLFlowTrackingService)


@freeze_time("2020-08-17T18:46:28.717559")
def test_create(
    db: SQLAlchemy,
    experiment_service: ExperimentService,
    experiment_registration_form_data: ExperimentRegistrationFormData,
    monkeypatch
):
    def mockcreatemlflowexperiment(self, experiment_name: str, *args, **kwargs) -> int:
        LOGGER.info(
            "Mocking ExperimentService.create_mlflow_experiment()",
            experiment_name=experiment_name,
            args=args,
            kwargs=kwargs,
        )
        return 1

    monkeypatch.setattr(
        ExperimentService, "create_mlflow_experiment", mockcreatemlflowexperiment
    )
    experiment: Experiment = experiment_service.create(
        experiment_registration_form_data=experiment_registration_form_data
    )

    assert experiment.experiment_id == 1
    assert experiment.name == "mnist"
    assert experiment.created_on == datetime.datetime(2020, 8, 17, 18, 46, 28, 717559)
    assert experiment.last_modified == datetime.datetime(
        2020, 8, 17, 18, 46, 28, 717559
    )

    with pytest.raises(ExperimentAlreadyExistsError):
        experiment_service.create(
            experiment_registration_form_data=experiment_registration_form_data
        )


def test_create_mlflow_experiment(
    experiment_service: ExperimentService,
    mlflow_tracking_service: MLFlowTrackingService
):
    name="mnist"
    
    experiment_id: int = experiment_service.create_mlflow_experiment(name)

    experiment: Experiment = mlflow_tracking_service._client.get_experiment_by_name(name)
    
    assert experiment_id == int(experiment.experiment_id)
    
    mlflow_tracking_service._client.delete_experiment(str(experiment_id))


@freeze_time("2020-08-17T18:46:28.717559")
def test_rename_experiment(
    db: SQLAlchemy, 
    experiment_service: ExperimentService,
    monkeypatch: MonkeyPatch
):
    def mockrenameexperiment(self, experiment_id: int, new_name: str, *args, **kwargs) -> Experiment:
        LOGGER.info("Mocking MlflowTrackingService.rename_experiment()")
        return True

    monkeypatch.setattr(MLFlowTrackingService, "rename_experiment", mockrenameexperiment)

    name="mnist"
    timestamp: datetime.datetime = datetime.datetime.now()
    new_experiment: Experiment = Experiment(
        name=name, created_on=timestamp, last_modified=timestamp
    )
    db.session.add(new_experiment)
    db.session.commit()


    new_name="mnist_changed"
    response: Experiment = experiment_service.rename_experiment(
        experiment=new_experiment,
        new_name=new_name
    )

    assert response.name == new_name


@freeze_time("2020-08-17T18:46:28.717559")
def test_delete_experiment(
    db: SQLAlchemy, 
    experiment_service: ExperimentService,
    monkeypatch: MonkeyPatch
):
    def mockdeleteexperiment(self, experiment_id: int, *args, **kwargs) -> Experiment:
        LOGGER.info("Mocking MlflowTrackingService.delete_experiment()")
        return True

    monkeypatch.setattr(MLFlowTrackingService, "delete_experiment", mockdeleteexperiment)

    name="mnist"
    timestamp: datetime.datetime = datetime.datetime.now()

    new_experiment: Experiment = Experiment(
        name=name, created_on=timestamp, last_modified=timestamp
    )
    db.session.add(new_experiment)
    db.session.commit()

    response: List = experiment_service.delete_experiment(
        experiment_id=new_experiment.experiment_id
    )

    assert response == [new_experiment.experiment_id]


@freeze_time("2020-08-17T18:46:28.717559")
def test_get_by_id(db: SQLAlchemy, experiment_service: ExperimentService):
    timestamp: datetime.datetime = datetime.datetime.now()

    new_experiment: Experiment = Experiment(
        name="mnist", created_on=timestamp, last_modified=timestamp
    )

    db.session.add(new_experiment)
    db.session.commit()

    experiment: Experiment = experiment_service.get_by_id(1)

    assert experiment == new_experiment


@freeze_time("2020-08-17T18:46:28.717559")
def test_get_by_name(db: SQLAlchemy, experiment_service: ExperimentService):
    timestamp: datetime.datetime = datetime.datetime.now()

    new_experiment: Experiment = Experiment(
        name="mnist", created_on=timestamp, last_modified=timestamp
    )

    db.session.add(new_experiment)
    db.session.commit()

    experiment: Experiment = experiment_service.get_by_name("mnist")

    assert experiment == new_experiment


@freeze_time("2020-08-17T18:46:28.717559")
def test_get_all(db: SQLAlchemy, experiment_service: ExperimentService):
    timestamp: datetime.datetime = datetime.datetime.now()

    new_experiment1: Experiment = Experiment(
        name="mnist", created_on=timestamp, last_modified=timestamp
    )
    new_experiment2: Experiment = Experiment(
        name="imagenet", created_on=timestamp, last_modified=timestamp
    )

    db.session.add(new_experiment1)
    db.session.add(new_experiment2)
    db.session.commit()

    results: List[Experiment] = experiment_service.get_all()

    assert len(results) == 2
    assert new_experiment1 in results and new_experiment2 in results
    assert new_experiment1.experiment_id == 1
    assert new_experiment2.experiment_id == 2


def test_extract_data_from_form(
    experiment_service: ExperimentService,
    experiment_registration_form: ExperimentRegistrationForm,
):
    experiment_registration_form_data: ExperimentRegistrationFormData = (
        experiment_service.extract_data_from_form(
            experiment_registration_form=experiment_registration_form
        )
    )

    assert experiment_registration_form_data["name"] == "mnist"
