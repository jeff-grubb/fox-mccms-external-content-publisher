import aws_cdk as core
import aws_cdk.assertions as assertions

from fox_mccms_external_content_publisher.fox_mccms_external_content_publisher_stack import FoxMccmsExternalContentPublisherStack

# example tests. To run these tests, uncomment this file along with the example
# resource in fox_mccms_external_content_publisher/fox_mccms_external_content_publisher_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = FoxMccmsExternalContentPublisherStack(app, "fox-mccms-external-content-publisher")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
