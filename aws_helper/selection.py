"""Shared selection helpers."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from aws_helper.utils.common import die


def choose_instance_interactively(instances: List[Dict[str, Any]], prompt: str) -> Dict[str, Any]:
    for idx, instance in enumerate(instances, start=1):
        print(
            "{idx}) {iid}   ({asg}) [{state}] {ip}".format(
                idx=idx,
                iid=instance["id"],
                asg=instance["asg"],
                state=instance.get("state", "-"),
                ip=instance.get("private_ip", "-"),
            )
        )

    print("")
    choice = input(prompt).strip()
    if not choice.isdigit():
        die("invalid choice")

    choice_number = int(choice)
    if choice_number < 1 or choice_number > len(instances):
        die("invalid choice")

    return instances[choice_number - 1]


def select_instance(
    instances: List[Dict[str, Any]],
    instance_id: Optional[str],
    title: str,
    prompt: str,
) -> Dict[str, Any]:
    if not instances:
        die("no instances available")

    if instance_id:
        matches = [instance for instance in instances if instance["id"] == instance_id]
        if not matches:
            die(f"instance-id {instance_id} not found in filtered results")
        return matches[0]

    if len(instances) == 1:
        return instances[0]

    print(title)
    return choose_instance_interactively(instances, prompt)
