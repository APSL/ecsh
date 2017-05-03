


** Not all features has been implemented yet! **


# Overview

With `ecsh` you can easy access with a shell into your ECS docker containers.

To enter the _container_ you will need a _bastion_ properly configured to access
all the _instances_ running the docker that handles the containers.

By the Elastic Container Service poit of view we will do:

            +--------------------------------------------------------------+
            |                                                              |
            | cluster                                                      |
            |                                                              |
            |  +--------------------------+  +--------------------------+  |
            |  |                          |  |                          |  |
            |  |  service                 |  |  service                 |  |
            |  |                          |  |                          |  |
            |  |  +--------------------+  |  |  +--------------------+  |  |
            |  |  |                    |  |  |  |                    |  |  |
            |  |  |  task              |  |  |  |  task              |  |  |
            |  |  |                    |  |  |  |                    |  |  |
    +-----+ |  |  |   +-------------+  |  |  |  |   +-------------+  |  |  |
    | you |---ssh---->|  container  |  |  |  |  |   |  container  |  |  |  |
    +-----+ |  |  |   +-------------+  |  |  |  |   +-------------+  |  |  |
            |  |  |                    |  |  |  |                    |  |  |
            |  |  +--------------------+  |  |  +--------------------+  |  |
            |  |                          |  |                          |  |
            |  +--------------------------+  +--------------------------+  |
            |                                                              |
            +--------------------------------------------------------------+

By the EC2 point of view you will do:

                ++======================================================++
                ||                                                      ||
                ||  Amazon Web Services - VPC                           ||
                ||                                                      ||
                ||                   +-------------------------------+  ||
                ||                   |                               |  ||
                ||                   |  EC2-Instance                 |  ||
    +-----+ ssh ||   +---------+ ssh |                               |  ||
    | you |-----||-->| bastion |---->|----+    +------------------+  |  ||
    +-----+     ||   +---------+     |    +--->| docker-container |  |  ||
                ||                   |         +------------------+  |  ||
                ||                   |                               |  ||
                ||                   |         +------------------+  |  ||
                ||                   |         | docker-container |  |  ||
                ||                   |         +------------------+  |  ||
                ||                   |                               |  ||
                ||                   +-------------------------------+  ||
                ||                                                      ||
                ++======================================================++


# Install

Install the package.

    pip install ecsh


## Configure IAM

Create user called `ecsh` with _programatic access_ and attach a custom policy
with thos permissions:

    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "Stmt1493373127000",
                "Effect": "Allow",
                "Action": [
                    "ec2:DescribeInstances",
                    "ecs:DescribeClusters",
                    "ecs:DescribeContainerInstances",
                    "ecs:DescribeServices",
                    "ecs:DescribeTaskDefinition",
                    "ecs:DescribeTasks",
                    "ecs:ListClusters",
                    "ecs:ListContainerInstances",
                    "ecs:ListServices",
                    "ecs:ListTaskDefinitions",
                    "ecs:ListTasks"
                ],
                "Resource": [
                    "*"
                ]
            }
        ]
    }

Then configure the programatic access at the computer you want to use `ecsh`

    aws configure

# Usage

    ecsh # And anything else :)

## Configure your .ecshcfg

By default ecsh will prompt for every option it need if not specified.

As many times you will use the same arguments, use the same bastion instance,
enter the same container etc. Is useful to create a .ecshcfg file in your project
or user home.

Ecsh will look for a .ecshcfg file in your current directory, if not found will
look for it on each parent directory until the root of the filesystem si reached.

So first (nearest) .ecshcfg found will be used.

The .ecshcfg is a yaml file where you can set defaul parameters or create
environments. All variables are optional.

    bastion: bastion.mydomain.com
    cluster: mycluster
    service: sales
    task: !latest!

    environments:
        myprod:
             container: web_front

        mydev:
            bastion: bastion.test.mydomain.com
            cluster: mydevcluster
            contaner: web_back


With those settings:

* If I type `ecsh` without arguments I'll enter using bastion.mydomain.com to
mycluster/sales/<last spawned task> and it will be prompet which container to use.

* If I type ecsh -e myprod I use all the default settings but the container won't
be prompted as web_front will be used.

* If I type ecsh -e mydev I'll inherit the sales service and task from the defaults
but the bastion, clustera and container will be overriden by the environment specific ones.

* If at some level there is one one choose (i.e. you only have one cluster) `ecsh`
won't prompt anything and will use it.

* If the tag !latest! is set to the task if there is more than one task running
the most recent one is used.


Remember that if you want you can override any parameter by invoking it with a `--`
in the cli.

    ecsh -e mydev --container web_varnish

Will use the service and task from the defaults, bastion and cluster from the
environment mydev and finally override the container from mydev with the
specified one in the cli.

If you want you can also set your AWS cretentials inside the .ecshcfg instead
of using the `aws cli` ones.
