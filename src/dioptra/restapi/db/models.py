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
from dataclasses import dataclass, field, fields
from typing import Any


@dataclass
class QueueLock(object):
    """The queue_locks table.

    Attributes:
        queue_id: An integer identifying a registered queue.
        created_on: The date and time the queue lock was created.
    """

    queue_id: int | None = field(default=None)
    created_on: datetime.datetime | None = field(default=None)


@dataclass
class Queue(object):
    """The queues table.

    Attributes:
        queue_id: An integer identifying a registered queue.
        created_on: The date and time the queue was created.
        last_modified: The date and time the queue was last modified.
        name: The name of the queue.
        is_deleted: A boolean that indicates if the queue record is deleted.
    """

    queue_id : int | None = field(default=None)
    created_on: datetime.datetime | None = field(default=None)
    last_modified: datetime.datetime | None = field(default=None)
    name: str = field(default=None)
    is_deleted: bool = field(default=None)

    def update(self, changes: dict[str, Any]):
        """Update the record.

        Args:
            changes: A dictionary containing record updates.
        """
        if set(changes.keys()) - {field.name for field in fields(self)}:
            raise ValueError("Invalid field name")

        self.last_modified = datetime.datetime.now()

        for key, val in changes.items():
            setattr(self, key, val)

        return self
