#!/usr/bin/env python
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

import os
from pathlib import Path

import click
import mlflow
import structlog
from prefect import Flow, Parameter
from prefect.utilities.logging import get_logger as get_prefect_logger
from structlog.stdlib import BoundLogger

from dioptra import pyplugs
from dioptra.sdk.utilities.contexts import plugin_dirs
from dioptra.sdk.utilities.logging import (
    StderrLogStream,
    StdoutLogStream,
    attach_stdout_stream_handler,
    clear_logger_handlers,
    configure_structlog,
    set_logging_level,
)

_PLUGINS_IMPORT_PATH: str = "dioptra_builtins"
_CUSTOM_PLUGINS_IMPORT_PATH: str = "dioptra_custom"

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@click.command()
@click.option(
    "--adv-tar-name",
    type=click.STRING,
    default="testing_adversarial_mi.tar.gz",
    help="Name to give to tarfile artifact containing model inversion predictions",
)
@click.option(
    "--adv-data-dir",
    type=click.STRING,
    default="adv_testing",
    help="Directory for saving model inversion predictions",
)
@click.option(
    "--model-name",
    type=click.STRING,
    help="Name of model to load from registry",
)
@click.option(
    "--model-version",
    type=click.STRING,
    help="Version of model to load from registry",
)
@click.option(
    "--batch-size",
    type=click.INT,
    help="Batch size to use when training a single epoch",
    default=32,
)
@click.option(
    "--classes",
    type=click.INT,
    help="Model Inversion Number of Classes",
    default=10,
)
@click.option(
    "--max-iter",
    type=click.INT,
    help="Model Inversion Max Iterations",
    default=10000,
)
@click.option(
    "--window-length",
    type=click.INT,
    help="Model Inversion Window Length",
    default=100,
)
@click.option(
    "--threshold",
    type=click.FLOAT,
    help="Model Inversion Threshold",
    default=0.99,
)
@click.option(
    "--learning-rate",
    type=click.FLOAT,
    help="Model Inversion Learning Rate",
    default=0.1,
)
@click.option(
    "--seed",
    type=click.INT,
    help="Set the entry point rng seed",
    default=-1,
)
def mi_attack(
    adv_tar_name,
    adv_data_dir,
    model_name,
    model_version,
    batch_size,
    classes,
    max_iter,
    window_length,
    threshold,
    learning_rate,
    seed,
):
    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="mi",
        adv_tar_name=adv_tar_name,
        adv_data_dir=adv_data_dir,
        model_name=model_name,
        model_version=model_version,
        batch_size=batch_size,
        classes=classes,
        max_iter=max_iter,
        window_length=window_length,
        threshold=threshold,
        learning_rate=learning_rate,
        seed=seed,
    )

    with mlflow.start_run() as active_run:  # noqa: F841
        flow: Flow = init_mi_flow()
        state = flow.run(
            parameters=dict(
                adv_tar_name=adv_tar_name,
                adv_data_dir=(Path.cwd() / adv_data_dir).resolve(),
                model_name=model_name,
                model_version=model_version,
                batch_size=batch_size,
                classes=classes,
                max_iter=max_iter,
                window_length=window_length,
                threshold=threshold,
                learning_rate=learning_rate,
                seed=seed,
            )
        )

    return state


def init_mi_flow() -> Flow:
    with Flow("Model Inversion") as flow:
        (
            adv_tar_name,
            adv_data_dir,
            model_name,
            model_version,
            batch_size,
            classes,
            max_iter,
            window_length,
            threshold,
            learning_rate,
            seed,
        ) = (
            Parameter("adv_tar_name"),
            Parameter("adv_data_dir"),
            Parameter("model_name"),
            Parameter("model_version"),
            Parameter("batch_size"),
            Parameter("classes"),
            Parameter("max_iter"),
            Parameter("window_length"),
            Parameter("threshold"),
            Parameter("learning_rate"),
            Parameter("seed"),
        )
        seed, rng = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.random", "rng", "init_rng", seed=seed
        )
        tensorflow_global_seed = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.random", "sample", "draw_random_integer", rng=rng
        )
        dataset_seed = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.random", "sample", "draw_random_integer", rng=rng
        )
        init_tensorflow_results = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.backend_configs",
            "tensorflow",
            "init_tensorflow",
            seed=tensorflow_global_seed,
        )
        make_directories_results = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "utils",
            "make_directories",
            dirs=[adv_data_dir],
        )

        log_mlflow_params_result = pyplugs.call_task(  # noqa: F841
            f"{_PLUGINS_IMPORT_PATH}.tracking",
            "mlflow",
            "log_parameters",
            parameters=dict(
                entry_point_seed=seed,
                tensorflow_global_seed=tensorflow_global_seed,
                dataset_seed=dataset_seed,
            ),
        )
        keras_classifier = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.registry",
            "art",
            "load_wrapped_tensorflow_keras_classifier",
            name=model_name,
            version=model_version,
            upstream_tasks=[init_tensorflow_results],
        )
        inferred = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.model_inversion",
            "modelinversion",
            "infer_model_inversion",
            keras_classifier=keras_classifier,
            adv_data_dir=adv_data_dir,
            batch_size=batch_size,
            classes=classes,
            max_iter=max_iter,
            window_length=window_length,
            threshold=threshold,
            learning_rate=learning_rate,
            upstream_tasks=[make_directories_results],
        )

        log_evasion_dataset_result = pyplugs.call_task(  # noqa: F841
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "mlflow",
            "upload_directory_as_tarball_artifact",
            source_dir=adv_data_dir,
            tarball_filename=adv_tar_name,
            upstream_tasks=[inferred],
        )

    return flow


if __name__ == "__main__":
    log_level: str = os.getenv("DIOPTRA_JOB_LOG_LEVEL", default="INFO")
    as_json: bool = True if os.getenv("DIOPTRA_JOB_LOG_AS_JSON") else False

    clear_logger_handlers(get_prefect_logger())
    attach_stdout_stream_handler(as_json)
    set_logging_level(log_level)
    configure_structlog()

    with plugin_dirs(), StdoutLogStream(as_json), StderrLogStream(as_json):
        _ = mi_attack()
