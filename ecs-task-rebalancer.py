#!/usr/bin/python
##Rebalance ECS Tasks on all available cluster instances

"""// Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
   // SPDX-License-Identifier: MIT-0"""

import boto3
import botocore
import os

#Initialize ecs client
ecs = boto3.client('ecs');

#Cluster name is passed in from a exported CloudFormation value
cluster_name=os.environ['ECSClusterName']

def lambda_handler(event, context):

    #Return all services deployed in the cluster
    def get_cluster_services():
        isTruncated = "True"
        nextToken = ""
        all_services = []

        while ("True" == isTruncated):
            if "" == nextToken:
                response = ecs.list_services(
                    cluster=cluster_name
                )
            else:
                response = ecs.list_services(
                    cluster=cluster_name,
                    nextToken=nextToken
                )

            if  response.has_key("nextToken"):
                nextToken = response["nextToken"]
            else:
                isTruncated = "False"

            services = response["serviceArns"]
            for service in services:
                all_services.append(service)

        return all_services

    #Rebalance ECS tasks of all services deployed in the cluster
    def rebalance_tasks():
        all_services = get_cluster_services()

        #For each service, figure out the taskDefinition, register a new version
        #and update the service -- This sequence will rebalance the tasks on all
        #available and connected instances
        response = ecs.describe_services(
            cluster=cluster_name,
            services=all_services
        )

        described_services = response["services"]
        for service in described_services:

            print ("service : ", service)

            #Get information about the task definition of the service
            task_definition = service["taskDefinition"];

            response = ecs.describe_task_definition(
                taskDefinition=task_definition
            )

            taskDefinitionDescription = response["taskDefinition"]

            containerDefinitions = taskDefinitionDescription["containerDefinitions"]
            volumes = taskDefinitionDescription["volumes"]
            family = taskDefinitionDescription["family"]

            print ("containerDefinitions : ", containerDefinitions)
            print ("volumes : ", volumes)
            print ("family : ", family)

            #Register a new version of the task_definition
            response = ecs.register_task_definition(
                family=family,
                containerDefinitions=containerDefinitions,
                volumes= volumes
            )

            newTaskDefinitionArn = response["taskDefinition"]["taskDefinitionArn"]
            print "New task definition arn : " , newTaskDefinitionArn

            response = ecs.update_service(
                cluster=cluster_name,
                service=service["serviceArn"],
                taskDefinition=newTaskDefinitionArn
            )

            print ("Updated the service ", service, "with new task definition")

    ###############################################

    ##Get details about the ECS container instance from the event
    event_detail = event["detail"]
    containerInstanceArn = event_detail["containerInstanceArn"]
    agentConnected = event_detail["agentConnected"]
    ec2InstanceId = event_detail["ec2InstanceId"]

    ##Describe the container instance that caused the event.
    response = ecs.describe_container_instances(
        cluster=cluster_name,
        containerInstances=[containerInstanceArn]
    )

    containerInstances = response["containerInstances"]
    print "Number of container instances", len(containerInstances)
    if(len(containerInstances) != 0):
        containerInstance = containerInstances[0]
        numberOfRunningTasks = containerInstance["runningTasksCount"]
        numberOfPendingTasks = containerInstance["pendingTasksCount"]
        version = containerInstance["version"]

        if numberOfRunningTasks == 0 and numberOfPendingTasks == 0 and agentConnected == True:
            print ("Rebalancing the tasks due to the event.")
            rebalance_tasks()
        else :
            print ("Event does not warrant task rebalancing.")

