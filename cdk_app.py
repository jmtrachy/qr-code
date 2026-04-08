#!/usr/bin/env python3
import os

import aws_cdk as cdk

from qr_code_stack import QrCodeStack

app = cdk.App()
QrCodeStack(
    app,
    "QrCodeStack",
    env=cdk.Environment(
        account=os.environ["CDK_DEFAULT_ACCOUNT"],
        region=os.environ["CDK_DEFAULT_REGION"],
    ),
)
app.synth()
