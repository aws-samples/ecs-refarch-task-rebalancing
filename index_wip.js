exports.handler = (event, context, callback) => {

    var AWS = require('aws-sdk');
    //Initialize ECS
    var ecs = new AWS.ECS();

    //Get details about the ECS container instance from the event
    var containerInstanceArn = event.detail.containerInstanceArn;
    var agentConnected = event.detail.agentConnected;
    var ec2InstanceId = event.detail.ec2InstanceId;

    var params = {
       cluster: process.env.ECSClusterName,
       containerInstances: [
         containerInstanceArn
       ]
    };

    //Describe the container instance that caused the event.
    ecs.describeContainerInstances(params, function(err, data) {
        if (err) {
            console.log(err, err.stack); // an error occurred
        } else {
            //Get attributes of the container
           var containerInstance = data.containerInstances[0];
           var numberOfRunningTasks = containerInstance.runningTasksCount;
           var numberOfPendingTasks = containerInstance.pendingTasksCount;
           var version = containerInstance.version;

           if(numberOfRunningTasks === 0 && numberOfPendingTasks === 0 && agentConnected === true ) {


           //if(numberOfRunningTasks === 0 && numberOfPendingTasks === 0 && agentConnected === true && version === 3 && containerARNHandled.indexOf(containerInstanceArn) == -1 ) {
                   console.log("This could be a new ECS instance brought back into the cluster.");
                   console.log("Rebalance the tasks.");
                    // This example lists all of your registered task definition families.
                    //Note : Assuming only one, loop as needed for more families
                    //Get the registered task definition family

                   //DEBUG:Troubleshooting ServiceNotFoundException
                   console.log("Verify that Service exists");
                   var params = {
                       cluster: process.env.ECSClusterName,
                   };
                   ecs.listServices(params, function(err, data) {
                       
                   });
                   
                   console.log("List the task definitions.");
                   var params = {
                       familyPrefix: process.env.TaskDefinition
                   };
                   ecs.listTaskDefinitions(params, function(err, data) {

                       if (err) console.log(err, err.stack); // an error occurred
                       else   {
                           var taskDefinitionARNs = data.taskDefinitionArns;
                           var latestTaskDefinition = taskDefinitionARNs[taskDefinitionARNs.length -1 ];

                           var params = {
                              taskDefinition: latestTaskDefinition
                           };
                           ecs.describeTaskDefinition(params, function(err, data) {
                               if (err) console.log(err, err.stack); // an error occurred
                               else  {
                                    var params = {
                                      containerDefinitions: data.taskDefinition.containerDefinitions,
                                      family: data.taskDefinition.family,
                                      volumes: data.taskDefinition.volumes
                                    };

                                    ecs.registerTaskDefinition(params, function(err, data) {
                                       if (err) console.log(err, err.stack); // an error occurred
                                       else    {
                                           console.log("Registered task definition : ");
                                           console.log(data.taskDefinition);

                                           //Now update the service with the new revision of the task definition,
                                           //so tasks are rebalanced across all ECS instances

                                            var params = {
                                              service: process.env.ServiceName,
                                              taskDefinition: data.taskDefinition.taskDefinitionArn
                                            };
                                             ecs.updateService(params, function(err, data) {
                                               if (err) console.log(err, err.stack); // an error occurred
                                               else     console.log(data);           // successful response

                                             });

                                       }
                                    });
                               }
                           });
                       }

                 });

           }
        }
    });

    callback(null, 'Done with rebalancing ECS tasks');
}