import multiprocessing as mp
from typing import Any, Mapping, MutableMapping

import requests
import structlog

from dioptra.rq.tasks.run_task_engine import run_task_engine_task as real_run_task

# Which endpoint to poll
_POLL_URL = "http://localhost:5000/get"


# Web server endpoint poll interval, in seconds
_POLL_INTERVAL = 3


def _get_logger() -> Any:
    """
    Get a logger for this module.

    Returns:
        A logger object
    """
    return structlog.get_logger(__name__)


def run_task_engine_task(
    experiment_id: int,
    experiment_desc: Mapping[str, Any],
    global_parameters: MutableMapping[str, Any]
):
    """
    Run an experiment via the task engine.  This implementation runs it in a
    sub-process.  The parent process will poll an endpoint for a shutdown
    instruction which will cause us to stop the experiment early.

    Args:
        experiment_id: The ID of the experiment to use for this run
        experiment_desc: A declarative experiment description, as a mapping
        global_parameters: Global parameters for this run, as a mapping from
            parameter name to value
    """
    p = mp.Process(
        target=real_run_task,
        args=(experiment_id, experiment_desc, global_parameters)
    )

    p.start()

    _monitor_process(p)

    p.close()


def _monitor_process(p: mp.Process):
    """
    Watch the given child process while polling for a shutdown request.
    If shutdown is requested, shut down the child process early.

    This function blocks until the child process terminates.

    Args:
        p: The child process to watch
    """
    log = _get_logger()
    log.debug("Monitoring task engine process: %d", p.pid)

    while p.is_alive():
        should_stop = _should_stop()

        if should_stop:
            # Send a SIGTERM to attempt a graceful shutdown
            p.terminate()

            # Wait one poll interval to see if it stops.  If not, forcibly
            # kill it.
            p.join(_POLL_INTERVAL)

            # Docs describe checking .exitcode, not .is_alive().
            if p.exitcode is None:
                p.kill()
                p.join()

        else:
            # Wait until next poll
            p.join(_POLL_INTERVAL)


def _should_stop():
    """
    Determine whether the current experiment should be stopped.

    Returns:
        True if it should be stopped; False if not
    """
    log = _get_logger()

    resp = requests.get(_POLL_URL)
    if resp.ok:
        value = resp.json()

    else:
        log.warning(
            "Polling endpoint returned http status: %d",
            resp.status_code
        )
        value = False

    return value
