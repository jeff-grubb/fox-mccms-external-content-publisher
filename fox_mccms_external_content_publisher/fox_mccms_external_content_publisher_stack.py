from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_sns as sns,
    aws_dynamodb as dynamodb,
    aws_pipes as pipes,
    custom_resources as cr
)
from constructs import Construct

class FoxMccmsExternalContentPublisherStack(Stack):

    environment_name = "dev"
    business_unit = "fs"
    et_sandbox_account_id = "851725335401"

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define the IAM role this pipe will run as
        role_name = "{env}-{bu}-fox-mccms-external-content-publisher-role".format(env=self.environment_name, bu=self.business_unit)
        pipe_role = iam.Role(
            self,
            role_name,
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("pipes.amazonaws.com"),
            )
        )

        # Define SNS topic
        topic_name = "{env}-{bu}-fox-mccms-external-content-publisher".format(env=self.environment_name, bu=self.business_unit)
        content_publisher_topic = sns.Topic(self, topic_name, display_name=topic_name, topic_name=topic_name)

        allow_sns_subscription_from_et = iam.PolicyStatement(
            sid="AllowSubscriptionFromET",
            actions=["sns:Subscribe"],
            principals=[iam.AccountPrincipal(self.et_sandbox_account_id)],
            resources=[content_publisher_topic.topic_arn]
        )

        default_sns_policy = iam.PolicyStatement(
            sid="DefaultTopicPolicy",
            actions=[
                "sns:Publish",
                "sns:RemovePermission",
                "sns:SetTopicAttributes",
                "sns:DeleteTopic",
                "sns:ListSubscriptionsByTopic",
                "sns:GetTopicAttributes",
                "sns:AddPermission",
                "sns:Subscribe"
            ],
            principals=[iam.AccountRootPrincipal()],
            resources=[content_publisher_topic.topic_arn]
        )

        default_sns_policy.add_condition("StringEquals", {"AWS:SourceOwner": "684424026845"})

        sns_topic_policy_document = iam.PolicyDocument(
            assign_sids=True,
            statements=[
                default_sns_policy,
                allow_sns_subscription_from_et
            ]
        )

        sns_topic_policy = sns.TopicPolicy(self, "sns_topic_policy",
                                       topics=[content_publisher_topic],
                                       policy_document=sns_topic_policy_document
                                       )

        # Because we didn't define the Dynamo table, let's cheat.
        # TODO - How do we import existing resources into CDK code?
        articles_arn = "arn:aws:dynamodb:us-east-1:684424026845:table/dev-fs-spark-v3-content/stream/2024-03-25T19:18:24.742"

        # Add publish permissions to pipe role
        # TODO - can I name this, so that in the role it shows up as a particular policy name?
        pipe_role.add_to_policy(iam.PolicyStatement(
            sid="publish",
            effect=iam.Effect.ALLOW,
            resources=[content_publisher_topic.topic_arn],
            actions=["sns:Publish"]
        ))

        # Add dynamo articles table permissions to pipe role
        pipe_role.add_to_policy(iam.PolicyStatement(
            sid="read",
            effect=iam.Effect.ALLOW,
            resources=[articles_arn],
            actions=["dynamodb:DescribeStream",
                     "dynamodb:GetRecords",
                     "dynamodb:GetShardIterator",
                     "dynamodb:ListStreams",
                     "dynamodb:BatchGetItem",
                     "dynamodb:GetItem"]
        ))


        # Create policy document for FS account to manage policy
        #content_publisher_topic_publish_from_pipe_policy_document = iam.PolicyDocument(
        #    assign_sids=True,
        #    statements=[

        #        )
        #    ]
        #)

        #topic_policy = sns.TopicPolicy(self, "allow_publish_from_pipe",
        #                               topics=[content_publisher_topic],
        #                               policy_document=content_publisher_topic_publish_from_pipe_policy_document
        #                               )

        # Create event bridge pipe - Articles Table -> SNS Topic

        cfn_pipe = pipes.CfnPipe(self, topic_name + "-pipe",
                                 role_arn=pipe_role.role_arn,
                                 name=topic_name + "-pipe",
                                 source=articles_arn,
                                 source_parameters=pipes.CfnPipe.PipeSourceParametersProperty(
                                     dynamo_db_stream_parameters=pipes.CfnPipe.PipeSourceDynamoDBStreamParametersProperty(
                                         starting_position='LATEST',
                                     )
                                 ),
                                 target=content_publisher_topic.topic_arn)
