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

from typing import Any, BinaryIO, Dict, List, Optional

import pytest
import structlog
from _pytest.monkeypatch import MonkeyPatch
from flask import Flask
from structlog.stdlib import BoundLogger

from dioptra.restapi.models import TaskPlugin
from dioptra.restapi.shared.s3.service import S3Service
from dioptra.restapi.task_plugin.routes import BASE_ROUTE as TASK_PLUGIN_BASE_ROUTE
from dioptra.restapi.task_plugin.controller import (
    TaskPluginResource,
    TaskPluginBuiltinsCollectionResource,
    TaskPluginBuiltinCollectionNameResource,
    TaskPluginCustomCollectionResource,
    TaskPluginCustomCollectionNameResource
)
from dioptra.restapi.task_plugin.service import TaskPluginService


LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pytest.fixture
def task_plugin_upload_form_request(task_plugin_archive: BinaryIO) -> Dict[str, Any]:
    return {
        "task_plugin_name": "new_plugin_one",
        "collection": "dioptra_custom",
        "task_plugin_file": (task_plugin_archive, "task_plugin_new_package.tar.gz"),
    }

@pytest.fixture
def task_plugin_service(dependency_injector) -> TaskPluginService:
    return dependency_injector.get(TaskPluginService)


def test_task_plugin_resource_init_() -> None:
    task_plugin_service = TaskPluginService
    task_plugin_resource = TaskPluginResource(task_plugin_service=task_plugin_service)
    assert task_plugin_service == task_plugin_resource._task_plugin_service


def test_task_plugin_resource_get(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockgetall(self, *args, **kwargs) -> List[TaskPlugin]:
        LOGGER.info("Mocking TaskPluginService.get_all()")
        return [
            TaskPlugin("artifacts", "dioptra_builtins", ["__init__.py", "mlflow.py"]),
            TaskPlugin("attacks", "dioptra_builtins", ["__init__.py", "fgm.py"]),
            TaskPlugin(
                "new_plugin_one", "dioptra_custom", ["__init__.py", "plugin_one.py"]
            ),
            TaskPlugin(
                "new_plugin_two", "dioptra_custom", ["__init__.py", "plugin_two.py"]
            ),
        ]

    monkeypatch.setattr(TaskPluginService, "get_all", mockgetall)

    with app.test_client() as client:
        response: List[Dict[str, Any]] = client.get(
            f"/api/{TASK_PLUGIN_BASE_ROUTE}/"
        ).get_json()

        expected: List[Dict[str, Any]] = [
            {
                "taskPluginName": "artifacts",
                "collection": "dioptra_builtins",
                "modules": ["__init__.py", "mlflow.py"],
            },
            {
                "taskPluginName": "attacks",
                "collection": "dioptra_builtins",
                "modules": ["__init__.py", "fgm.py"],
            },
            {
                "taskPluginName": "new_plugin_one",
                "collection": "dioptra_custom",
                "modules": ["__init__.py", "plugin_one.py"],
            },
            {
                "taskPluginName": "new_plugin_two",
                "collection": "dioptra_custom",
                "modules": ["__init__.py", "plugin_two.py"],
            },
        ]

        assert response == expected


def test_task_plugin_resource_post(
    app: Flask,
    task_plugin_upload_form_request: Dict[str, Any],
    monkeypatch: MonkeyPatch,
) -> None:
    def mockcreate(*args, **kwargs) -> TaskPlugin:
        LOGGER.info("Mocking TaskPluginService.create()")
        return TaskPlugin(
            task_plugin_name="new_plugin_one",
            collection="custom",
            modules=["__init__.py", "plugin_module.py"],
        )

    def mockupload(fileobj, bucket, key, *args, **kwargs):
        LOGGER.info(
            "Mocking S3Service.upload()", fileobj=fileobj, bucket=bucket, key=key
        )
        return S3Service.as_uri(bucket=bucket, key=key)

    monkeypatch.setattr(TaskPluginService, "create", mockcreate)
    monkeypatch.setattr(S3Service, "upload", mockupload)

    with app.test_client() as client:
        response: Dict[str, Any] = client.post(
            f"/api/{TASK_PLUGIN_BASE_ROUTE}/",
            content_type="multipart/form-data",
            data=task_plugin_upload_form_request,
            follow_redirects=True,
        ).get_json()
        LOGGER.info("Response received", response=response)

        expected: Dict[str, Any] = {
            "taskPluginName": "new_plugin_one",
            "collection": "custom",
            "modules": ["__init__.py", "plugin_module.py"],
        }

        assert response == expected



def test_task_plugin_builtins_collection_resource_init_() -> None:
    task_plugin_service = TaskPluginService
    task_plugin_builtins_collection_resource = TaskPluginBuiltinsCollectionResource(task_plugin_service=task_plugin_service)
    assert task_plugin_service == task_plugin_builtins_collection_resource._task_plugin_service


def test_task_plugin_builtins_collection_resource_get(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockgetallincollection(self, *args, **kwargs) -> List[TaskPlugin]:
        LOGGER.info("Mocking TaskPluginService.get_all_in_collection()")
        return [
            TaskPlugin("artifacts", "dioptra_builtins", ["__init__.py", "mlflow.py"]),
            TaskPlugin("attacks", "dioptra_builtins", ["__init__.py", "fgm.py"]),
        ]

    monkeypatch.setattr(TaskPluginService, "get_all_in_collection", mockgetallincollection)

    with app.test_client() as client:
        response: List[Dict[str, Any]] = client.get(
            f"/api/{TASK_PLUGIN_BASE_ROUTE}/dioptra_builtins"
        ).get_json()

        expected: List[Dict[str, Any]] = [
            {
                "taskPluginName": "artifacts",
                "collection": "dioptra_builtins",
                "modules": ["__init__.py", "mlflow.py"],
            },
            {
                "taskPluginName": "attacks",
                "collection": "dioptra_builtins",
                "modules": ["__init__.py", "fgm.py"],
            },
        ]

        assert response == expected



def test_task_plugin_builtins_collection_name_resource_init_() -> None:
    task_plugin_service = TaskPluginService
    task_plugin_builtin_collection_name_resource = TaskPluginBuiltinCollectionNameResource(task_plugin_service=task_plugin_service)
    assert task_plugin_service == task_plugin_builtin_collection_name_resource._task_plugin_service


def test_task_plugin_builtin_collection_name_resource_get(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockgetbynameincollection(self, task_plugin_name: str, *args, **kwargs) -> Optional[TaskPlugin]:
        LOGGER.info("Mocking TaskPluginService.get_by_name_in_collection()")
        dioptra_builtins = [
            TaskPlugin("artifacts", "dioptra_builtins", ["__init__.py", "mlflow.py"]),
            TaskPlugin("attacks", "dioptra_builtins", ["__init__.py", "fgm.py"]),
        ]
        
        for task_plugin in dioptra_builtins:
            if task_plugin.task_plugin_name == task_plugin_name:
                return task_plugin
            
        return None

    monkeypatch.setattr(TaskPluginService, "get_by_name_in_collection", mockgetbynameincollection)

    task_plugin_name = "artifacts"

    with app.test_client() as client:
        response: List[Dict[str, Any]] = client.get(
            f"/api/{TASK_PLUGIN_BASE_ROUTE}/dioptra_builtins/{task_plugin_name}"
        ).get_json()

        expected: List[Dict[str, Any]] = {
                "taskPluginName": "artifacts",
                "collection": "dioptra_builtins",
                "modules": ["__init__.py", "mlflow.py"],
            }
        
        assert response == expected



def test_task_plugin_custom_collection_resource_init_() -> None:
    task_plugin_service = TaskPluginService
    task_plugin_custom_collection_resource = TaskPluginCustomCollectionResource(task_plugin_service=task_plugin_service)
    assert task_plugin_service == task_plugin_custom_collection_resource._task_plugin_service


def test_task_plugin_custom_collection_resource_get(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockgetallincollection(self, *args, **kwargs) -> List[TaskPlugin]:
        LOGGER.info("Mocking TaskPluginService.get_all_in_collection()")
        return [
            TaskPlugin(
                "new_plugin_one", "dioptra_custom", ["__init__.py", "plugin_one.py"]
            ),
            TaskPlugin(
                "new_plugin_two", "dioptra_custom", ["__init__.py", "plugin_two.py"]
            ),
        ]

    monkeypatch.setattr(TaskPluginService, "get_all_in_collection", mockgetallincollection)

    with app.test_client() as client:
        response: List[Dict[str, Any]] = client.get(
            f"/api/{TASK_PLUGIN_BASE_ROUTE}/dioptra_custom"
        ).get_json()

        expected: List[Dict[str, Any]] = [
            {
                "taskPluginName": "new_plugin_one",
                "collection": "dioptra_custom",
                "modules": ["__init__.py", "plugin_one.py"],
            },
            {
                "taskPluginName": "new_plugin_two",
                "collection": "dioptra_custom",
                "modules": ["__init__.py", "plugin_two.py"],
            },
        ]

        assert response == expected



def test_task_plugin_custom_collection_name_resource_init_() -> None:
    task_plugin_service = TaskPluginService
    task_plugin_custom_collection_name_resource = TaskPluginCustomCollectionNameResource(task_plugin_service=task_plugin_service)
    assert task_plugin_service == task_plugin_custom_collection_name_resource._task_plugin_service


def test_task_plugin_custom_collection_name_resource_get(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockgetbynameincollection(self, task_plugin_name: str, *args, **kwargs) -> List[TaskPlugin]:
        LOGGER.info("Mocking TaskPluginService.get_by_name_in_collection()")
        dioptra_custom = [
            TaskPlugin(
                "new_plugin_one", "dioptra_custom", ["__init__.py", "plugin_one.py"]
            ),
            TaskPlugin(
                "new_plugin_two", "dioptra_custom", ["__init__.py", "plugin_two.py"]
            ),
        ]
        
        for task_plugin in dioptra_custom:
            if task_plugin.task_plugin_name == task_plugin_name:
                return task_plugin
            
        return None

    monkeypatch.setattr(TaskPluginService, "get_by_name_in_collection", mockgetbynameincollection)

    task_plugin_name = "new_plugin_one"

    with app.test_client() as client:
        response: List[Dict[str, Any]] = client.get(
            f"/api/{TASK_PLUGIN_BASE_ROUTE}/dioptra_custom/{task_plugin_name}"
        ).get_json()

        expected: List[Dict[str, Any]] = {
            "taskPluginName": "new_plugin_one",
            "collection": "dioptra_custom",
            "modules": ["__init__.py", "plugin_one.py"],
        }
        
        assert response == expected


def test_task_plugin_custom_collection_name_resource_delete(app: Flask, monkeypatch: MonkeyPatch) -> None:
    def mockdelete(self, task_plugin_name: str, *args, **kwargs) -> List[TaskPlugin]:
        LOGGER.info("Mocking TaskPluginService.delete()")
        dioptra_custom = [
            TaskPlugin(
                "new_plugin_one", "dioptra_custom", ["__init__.py", "plugin_one.py"]
            ),
            TaskPlugin(
                "new_plugin_two", "dioptra_custom", ["__init__.py", "plugin_two.py"]
            ),
        ]
        
        for task_plugin in dioptra_custom:
            if task_plugin.task_plugin_name == task_plugin_name:
                return [task_plugin]
            
        return []

    monkeypatch.setattr(TaskPluginService, "delete", mockdelete)

    task_plugin_name = "new_plugin_two"

    with app.test_client() as client:
        response: List[Dict[str, Any]] = client.delete(
            f"/api/{TASK_PLUGIN_BASE_ROUTE}/dioptra_custom/{task_plugin_name}"
        ).get_json()

        expected: List[Dict[str, Any]] = {
                "status": "Success",
                "collection": "dioptra_custom",
                "taskPluginName": [task_plugin_name],
            }

        assert response == expected