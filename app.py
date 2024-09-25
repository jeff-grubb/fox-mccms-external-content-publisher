#!/usr/bin/env python3
import os

import aws_cdk as cdk

from fox_mccms_external_content_publisher.fox_mccms_external_content_publisher_stack import FoxMccmsExternalContentPublisherStack

app = cdk.App()

FoxMccmsExternalContentPublisherStack(app,"FoxMccmsExternalContentPublisherStack")

app.synth()
