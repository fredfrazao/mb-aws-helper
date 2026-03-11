"""Discovery logic for ASGs and EC2 instances."""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Optional

from aws_helper.aws.auth import get_client
from aws_helper.aws.cache import get_or_set
from aws_helper.utils.common import casefold_contains, chunked
from aws_helper.utils.logging_utils import LOG

AsgFilter = Optional[Callable[[Dict[str, Any]], bool]]


def get_asgs(
    env: str,
    service: str,
    region: str,
    asg_filter: AsgFilter = None,
) -> List[Dict[str, Any]]:
    def _load() -> List[Dict[str, Any]]:
        client = get_client(env, service, "autoscaling", region)
        paginator = client.get_paginator("describe_auto_scaling_groups")
        results: List[Dict[str, Any]] = []
        for page in paginator.paginate():
            for asg in page.get("AutoScalingGroups", []):
                if asg_filter and not asg_filter(asg):
                    continue
                results.append(asg)
        LOG.debug("Discovered %d ASGs for service=%s env=%s", len(results), service, env)
        return results

    cache_key = ("asgs", env, service, region, getattr(asg_filter, "__name__", repr(asg_filter)))
    return get_or_set(cache_key, _load)


def summarize_asg(asg: Dict[str, Any]) -> Dict[str, Any]:
    name = asg.get("AutoScalingGroupName", "-")
    launch_template = asg.get("LaunchTemplate")
    mixed_policy = asg.get("MixedInstancesPolicy")

    lt_name = "-"
    lt_version = "-"
    uses_mixed_policy = False

    if launch_template:
        lt_name = launch_template.get("LaunchTemplateName", "-")
        lt_version = launch_template.get("Version", "-")
    elif mixed_policy:
        uses_mixed_policy = True
        lt_spec = mixed_policy.get("LaunchTemplate", {}).get("LaunchTemplateSpecification", {})
        lt_name = lt_spec.get("LaunchTemplateName", "-")
        lt_version = lt_spec.get("Version", "-")

    return {
        "asg": name,
        "min": asg.get("MinSize", "-"),
        "max": asg.get("MaxSize", "-"),
        "desired": asg.get("DesiredCapacity", "-"),
        "instances": len(asg.get("Instances", [])),
        "lt_name": lt_name,
        "lt_version": lt_version,
        "mixed_policy": uses_mixed_policy,
    }


def get_instance_details(
    env: str,
    service: str,
    region: str,
    instance_ids: List[str],
) -> Dict[str, Dict[str, Any]]:
    if not instance_ids:
        return {}

    def _load() -> Dict[str, Dict[str, Any]]:
        ec2_client = get_client(env, service, "ec2", region)
        instance_info: Dict[str, Dict[str, Any]] = {}
        for batch in chunked(instance_ids, 200):
            LOG.debug("Fetching EC2 details for %d instances", len(batch))
            response = ec2_client.describe_instances(InstanceIds=batch)
            for reservation in response.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    instance_id = instance["InstanceId"]
                    launch_time = instance.get("LaunchTime")
                    launch_template = instance.get("LaunchTemplate", {}) or {}
                    instance_info[instance_id] = {
                        "state": instance.get("State", {}).get("Name", "-"),
                        "az": instance.get("Placement", {}).get("AvailabilityZone", "-"),
                        "private_ip": instance.get("PrivateIpAddress", "-"),
                        "instance_type": instance.get("InstanceType", "-"),
                        "image_id": instance.get("ImageId", "-"),
                        "launch_time": launch_time,
                        "launch_time_str": launch_time.strftime("%Y-%m-%d %H:%M:%S %Z") if launch_time else "-",
                        "lt_name": launch_template.get("LaunchTemplateName", "-"),
                        "lt_version": launch_template.get("Version", "-"),
                    }
        return instance_info

    cache_key = ("instance_details", env, service, region, tuple(sorted(instance_ids)))
    return get_or_set(cache_key, _load)


def discover_asg_instances(
    env: str,
    service: str,
    region: str,
    asg_filter: AsgFilter = None,
    instance_state: Optional[str] = None,
    name_match: Optional[str] = None,
    asg_match: Optional[str] = None,
    sort_order: str = "asc",
) -> List[Dict[str, Any]]:
    asgs = get_asgs(env, service, region, asg_filter=asg_filter)

    all_instance_ids: List[str] = []
    asg_instance_pairs: List[Dict[str, str]] = []

    for asg in asgs:
        asg_name = asg.get("AutoScalingGroupName", "")
        if not casefold_contains(asg_name, asg_match):
            continue

        for instance in asg.get("Instances", []):
            instance_id = instance["InstanceId"]
            all_instance_ids.append(instance_id)
            asg_instance_pairs.append({"asg": asg_name, "id": instance_id})

    details = get_instance_details(env, service, region, all_instance_ids)

    discovered: List[Dict[str, Any]] = []
    for item in asg_instance_pairs:
        info = details.get(item["id"], {})
        merged = {
            "asg": item["asg"],
            "id": item["id"],
            "state": info.get("state", "-"),
            "az": info.get("az", "-"),
            "private_ip": info.get("private_ip", "-"),
            "instance_type": info.get("instance_type", "-"),
            "image_id": info.get("image_id", "-"),
            "lt_name": info.get("lt_name", "-"),
            "lt_version": info.get("lt_version", "-"),
            "launch_time": info.get("launch_time"),
            "launch_time_str": info.get("launch_time_str", "-"),
        }

        if instance_state and merged["state"] != instance_state:
            continue

        if name_match:
            haystack = f"{merged['asg']} {merged['id']}"
            if not casefold_contains(haystack, name_match):
                continue

        discovered.append(merged)

    reverse = sort_order == "desc"
    discovered.sort(
        key=lambda value: (
            value["asg"],
            value["launch_time"].timestamp() if value["launch_time"] else 0,
            value["id"],
        ),
        reverse=reverse,
    )

    LOG.debug("Discovered %d instances after filtering", len(discovered))
    return discovered


def summarize_environment(
    env: str,
    service: str,
    region: str,
    asg_match: Optional[str] = None,
) -> Dict[str, Any]:
    asgs = get_asgs(
        env,
        service,
        region,
        asg_filter=lambda asg: casefold_contains(asg.get("AutoScalingGroupName", ""), asg_match),
    )
    instances = discover_asg_instances(env, service, region, asg_match=asg_match)

    role_counter: Counter[str] = Counter()
    az_counter: Counter[str] = Counter()
    type_counter: Counter[str] = Counter()
    image_counter: Counter[str] = Counter()

    for instance in instances:
        asg_name = instance["asg"]
        role = "unknown"
        for candidate in ("deploy-node", "rails-worker", "gitaly", "sidekiq", "frontend", "worker"):
            if candidate in asg_name:
                role = candidate
                break
        role_counter[role] += 1
        az_counter[instance["az"]] += 1
        type_counter[instance["instance_type"]] += 1
        image_counter[instance["image_id"]] += 1

    deploy_nodes = [inst for inst in instances if "deploy-node" in inst["asg"]]
    return {
        "service": service,
        "env": env,
        "region": region,
        "asgs": len(asgs),
        "instances": len(instances),
        "roles": dict(sorted(role_counter.items())),
        "availability_zones": dict(sorted(az_counter.items())),
        "instance_types": dict(sorted(type_counter.items())),
        "amis": dict(sorted(image_counter.items())),
        "deploy_nodes": len(deploy_nodes),
    }
