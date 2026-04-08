import os

from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    CfnOutput,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_s3 as s3,
)
import platform as _platform
from aws_cdk import aws_ecr_assets as ecr_assets
from constructs import Construct


class QrCodeStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket = s3.Bucket(
            self,
            "QrCodeBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False,
            ),
            object_ownership=s3.ObjectOwnership.BUCKET_OWNER_PREFERRED,
        )

        bucket.add_to_resource_policy(_create_public_read_policy(bucket))

        docker_dir = os.path.dirname(__file__) or "."

        is_arm = _platform.machine() == "arm64"
        arch = _lambda.Architecture.ARM_64 if is_arm else _lambda.Architecture.X86_64
        docker_platform = ecr_assets.Platform.LINUX_ARM64 if is_arm else ecr_assets.Platform.LINUX_AMD64

        fn = _lambda.DockerImageFunction(
            self,
            "QrCodeFunction",
            code=_lambda.DockerImageCode.from_image_asset(
                docker_dir, platform=docker_platform
            ),
            architecture=arch,
            memory_size=512,
            timeout=Duration.seconds(30),
            environment={
                "QR_S3_BUCKET": bucket.bucket_name,
            },
        )

        bucket.grant_put(fn)

        api = apigw.LambdaRestApi(
            self,
            "QrCodeApi",
            handler=fn,
            binary_media_types=["multipart/form-data"],
        )

        CfnOutput(self, "ApiUrl", value=api.url)
        CfnOutput(self, "BucketName", value=bucket.bucket_name)


def _create_public_read_policy(bucket):
    import aws_cdk.aws_iam as iam

    return iam.PolicyStatement(
        actions=["s3:GetObject"],
        resources=[bucket.arn_for_objects("*")],
        principals=[iam.AnyPrincipal()],
    )
