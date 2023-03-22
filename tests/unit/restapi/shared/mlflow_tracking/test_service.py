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

import pytest
import structlog
from typing import Optional
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from mlflow.tracking import MlflowClient
from structlog.stdlib import BoundLogger
from _pytest.monkeypatch import MonkeyPatch
from dioptra.restapi.models import Experiment

from dioptra.restapi.shared.mlflow_tracking.service import MLFlowTrackingService

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pytest.fixture
def mlflow_tracking_service(dependency_injector) -> MLFlowTrackingService:
    return dependency_injector.get(MLFlowTrackingService)


def test_create_experiment(
    mlflow_tracking_service: MLFlowTrackingService
):
    name="mnist"
    experiment_id: Optional[str] = mlflow_tracking_service.create_experiment(name)

    created: Experiment = mlflow_tracking_service._client.get_experiment_by_name(name)

    assert experiment_id == str(created.experiment_id)


def test_rename_experiment(
    mlflow_tracking_service: MLFlowTrackingService
):
    name="mnist"
    experiment: Experiment = mlflow_tracking_service._client.get_experiment_by_name(name)

    new_name = "mnist_changed"

    assert mlflow_tracking_service.rename_experiment(experiment.experiment_id, new_name) == True


def test_delete_experiment(
    mlflow_tracking_service: MLFlowTrackingService
):
    name="mnist_changed"
    experiment: Experiment = mlflow_tracking_service._client.get_experiment_by_name(name)

    assert mlflow_tracking_service.delete_experiment(experiment.experiment_id) == True