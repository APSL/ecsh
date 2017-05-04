#!/usr/bin/env python3

import ast
import sys
import shlex

from subprocess import check_call

import boto3
import click

import sh
from sh import ssh


ERROR_MESSAGE_SSH_BASTION = """
{}

Ssh to {} failed.

You can pass to --bastion the full ssh arguments with user / key file.

Is recommended to setup at YOUR machine the .ssh/config file to allow
ssh without password to {}
i.e.

    Host your-fantastic-host.aws.com
        user ec2-user
        IdentityFile ~/.ssh/your-fantastic-host.pem
"""

ERROR_MESSAGE_SSH_INSTANCE = """
{}

Ssh to {instance_address} from {bastion} failed.

Is needed to setup at bastion ({bastion}) the .ssh/config file to allow
ssh without password to {instance_address}.
i.e.

    Host {ip_wildcard_suggest} # Or some whildcard
        user ec2-user
        IdentityFile ~/.ssh/my-awesome-internal-instances.pem
"""


class AWSResource():

    def __init__(self):
        self.__ecs = boto3.client("ecs")
        self.__ec2 = boto3.client("ec2")

    def list(self, lfunc, lkwargs, kind, arns_key, name):
        resource_resp = getattr(self.__ecs, lfunc)(**lkwargs)

        if arns_key not in resource_resp:
            error = "No {} found, check your config / credentials".format(kind)
            raise ValueError(error)

        resources = [x.split("/")[1] for x in resource_resp[arns_key]]

        if name and name in resources:
            return name

        if name and name not in resources:
            error = "{} '{}' not found in this account, maybe on of {}?"
            raise ValueError(error.format(kind.capitalize(), name, resources))

        if not name and len(resources) == 1:
            name = resources[0]
            msg = "No {} specifided. Using '{}' as is the only one"
            print(msg.format(kind, name))
            return name

        msg = "\nNo {} specified, choose one:\n{}"
        name = click.prompt(msg.format(kind, resources), type=str)
        return name

    def describe(self, dfunc, dkwargs, kind, get_fields, name):
        resource_resp = getattr(self.__ecs, dfunc)(**dkwargs)

        resources = {}
        for field_name, get_field in get_fields.items():
            # FIXME do some error handling here
            resources[field_name] = get_field(resource_resp)

        if name and name in resources["name"]:
            resources["name"] = name
            return resources

        if name and name in resources["name"]:
            error = "{} '{}' not found, maybe on of {}?".format(
                kind.capitalize(),
                name,
                resources["name"],
            )
            raise ValueError(error)

        if not name and len(resources) == 1:
            name = resources["name"][0]
            msg = "No {} specifided. Using '{}' as is the only one"
            print(msg.format(kind, name))
            resources["name"] = name
            return resources

        msg = "\nNo {} specified, choose one:\n{}"
        name = click.prompt(msg.format(kind, resources["name"]), type=str)

        return self.describe(
            dfunc,
            dkwargs,
            kind,
            get_fields,
            name,
        )


def check_bastion_ssh_error(bastion):
    """
    " Check if there is any error sshing bastion
    "    @return error message if error
    "            None otherwise if success
    """

    test_text = "ecsh test"
    test_ssh_cmd = "echo '{}'".format(test_text)

    ssh_error = ""
    try:
        bastion_test = ssh(shlex.split(bastion), test_ssh_cmd).strip()
    except sh.ErrorReturnCode_2 as excep:
        ssh_error = excep.stderr.strip()
        bastion_test = None

    if bastion_test == test_text:
        return None

    return ERROR_MESSAGE_SSH_BASTION.format(ssh_error, bastion, bastion)


def check_instance_ssh_error(bastion, instance_address):
    """
    " Check if there is any error sshing instance from bastion
    "    @return error message if error
    "            None otherwise if success
    """

    test_text = "ecsh test"
    test_ssh_cmd = "echo '{}'".format(test_text)

    instance_test_cmd = "{} ssh {} {}".format(
        bastion,
        instance_address,
        test_ssh_cmd,
    )

    ssh_error = ""
    try:
        container_instance_test = ssh(shlex.split(instance_test_cmd)).strip()
    except sh.ErrorReturnCode_255 as excep:
        ssh_error = excep.stderr.strip()
        container_instance_test = None

    if container_instance_test == test_text:
        # Success!
        return None

    ip_wildcard_suggest = ".".join(instance_address.split(".")[:2]) + ".*"
    return ERROR_MESSAGE_SSH_INSTANCE.format(
        ssh_error,
        instance_address=instance_address,
        bastion=bastion,
        ip_wildcard_suggest=ip_wildcard_suggest,
    )


def get_docker_name(bastion, instance_address, task, container_name):
    docker_api_url = "http://localhost:51678/v1/tasks?taskarn={}".format(
        task,
    )

    docker_name_cmd = "{} ssh {} curl -s '{}'".format(
        bastion,
        instance_address,
        docker_api_url,
    )
    resp_json = ssh(shlex.split(docker_name_cmd)).strip()
    resp = ast.literal_eval(resp_json)

    containers = []
    if "Containers" not in resp or not resp["Containers"]:
        return containers

    for container in resp["Containers"]:
        if container["Name"] == container_name:
            containers.append(container["DockerName"])

    return containers


def get_arn_prefix(ecs):
    return ecs.list_clusters()["clusterArns"][0].split("/")[0].strip(":cluster")


def get_task_arn(ecs, task):
    return "{}:{}/{}".format(get_arn_prefix(ecs), "task", task)


@click.command()
@click.option("--cluster", help="ECS Cluster")
@click.option("--service", help="ECS Service")
@click.option("--task", default=None, help="ECS Task")
@click.option("--container", help="ECS Container name")
@click.option("--bastion", help="Bastion host to enter platform")
def ecsh(cluster, service, task, container, bastion):

    ecs = boto3.client("ecs")
    ec2 = boto3.client("ec2")

    resource = AWSResource()

    try:
        cluster = resource.list(
            lfunc="list_clusters",
            lkwargs={},
            kind="cluster",
            arns_key="clusterArns",
            name=cluster,
        )

        service = resource.list(
            lfunc="list_services",
            lkwargs={
                "cluster": cluster,
            },
            kind="service",
            arns_key="serviceArns",
            name=service,
        )

        task = resource.list(
            lfunc="list_tasks",
            lkwargs={
                "cluster": cluster,
                "serviceName": service,
            },
            kind="task",
            arns_key="taskArns",
            name=task,
        )

        container = resource.describe(
            dfunc="describe_tasks",
            dkwargs={
                "cluster": cluster,
                "tasks": [task],
            },
            kind="container",
            get_fields={
                "name": lambda d: [x["name"] for x in d["tasks"][0]["containers"]],
                "container": lambda d: d["tasks"][0]["containerInstanceArn"],
            },
            name=container,
        )
    except ValueError as excep:
        print(str(excep))
        sys.exit(1)

    instance_resp = ecs.describe_container_instances(
        cluster=cluster,
        containerInstances=[container["container"]],
    )
    container_name = container["name"]

    instance = instance_resp["containerInstances"][0]["ec2InstanceId"]

    instance_address = ec2.describe_instances(InstanceIds=[instance])\
        ["Reservations"][0]\
        ["Instances"][0]\
        ["NetworkInterfaces"][0]\
        ["PrivateIpAddress"]

    if not bastion:
        bastion = click.prompt("Bastion host", type=str)

    error = check_bastion_ssh_error(bastion)
    if error:
        print(error)
        sys.exit(1)

    error = check_instance_ssh_error(bastion, instance_address)
    if error:
        print(error)
        sys.exit(1)

    task_arn = get_task_arn(ecs, task)

    docker_name = get_docker_name(
        bastion,
        instance_address,
        task_arn,
        container_name,
    )

    if docker_name:
        docker_name = docker_name[0]
    else:
        print("No docker container name found inside {}".format(
                instance_address,
            )
        )
        exit(1)

    full_command = "ssh -t {} ssh -t {} docker exec -it {} sh".format(
        bastion,
        instance_address,
        docker_name,
    )
    print("Executing: \n\n\t{}\n\n".format(full_command))

    print("Entering {}/{}/{}/{}...".format(
        cluster,
        service,
        task,
        container_name,
        instance,
        )
         )
    check_call(shlex.split(full_command))


if __name__ == "__main__":
    ecsh()
