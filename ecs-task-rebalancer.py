#!/usr/bin/python
# Rebalance ECS Tasks on all available cluster instances
# 2022-02-11 updates for Python 3.9 runtimes

"""// Copyright 2017,2022 Amazon.com, Inc. or its affiliates.
   // All Rights Reserved.
   // SPDX-License-Identifier: MIT-0"""

import os

import boto3
import botocore

# Initialize ecs client
ecs = boto3.client("ecs")

# Cluster name is passed in from a exported CloudFormation value
cluster_name = os.environ["ECSClusterName"]


def lambda_handler(event, context):
    """A short Lambda function that will force a redeploy to rebalance your
    ECS cluster."""

    # Return all services deployed in the cluster
    def get_cluster_services():
        is_truncated = "True"
        next_token = ""
        all_services = []

        while "True" == is_truncated:
            if "" == next_token:
                response = ecs.list_services(cluster=cluster_name)
            else:
                response = ecs.list_services(cluster=cluster_name, nextToken=next_token)

            if "nextToken" in response:
                next_token = response["nextToken"]
            else:
                is_truncated = "False"

            services = response["serviceArns"]
            for service in services:
                all_services.append(service)

        return all_services

    # Rebalance ECS tasks of all services deployed in the cluster
    def rebalance_tasks():
        all_services = get_cluster_services()
        for service in all_services:
            print("Rebalancing tasks for service: " + service)
            response = ecs.update_service(
                cluster=cluster_name, service=service, forceNewDeployment=True
            )
