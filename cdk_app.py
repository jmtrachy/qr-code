#!/usr/bin/env python3
import aws_cdk as cdk

from qr_code_stack import QrCodeStack

app = cdk.App()
QrCodeStack(app, "QrCodeStack")
app.synth()
