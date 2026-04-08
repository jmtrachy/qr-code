import os

from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    CfnOutput,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_s3 as s3,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_route53_targets as route53_targets,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
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
                "CUSTOM_DOMAIN": "qrcode.jamestrachy.com",
            },
        )

        bucket.grant_put(fn)

        api = apigw.LambdaRestApi(
            self,
            "QrCodeApi",
            handler=fn,
            binary_media_types=["multipart/form-data"],
        )

        # Custom domain: qrcode.jamestrachy.com via CloudFront
        zone = route53.HostedZone.from_lookup(
            self, "Zone", domain_name="jamestrachy.com"
        )

        # CloudFront requires certificates in us-east-1
        cf_cert = acm.DnsValidatedCertificate(
            self,
            "CloudFrontCert",
            domain_name="qrcode.jamestrachy.com",
            hosted_zone=zone,
            region="us-east-1",
        )

        distribution = cloudfront.Distribution(
            self,
            "Distribution",
            domain_names=["qrcode.jamestrachy.com"],
            certificate=cf_cert,
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.HttpOrigin(
                    f"{api.rest_api_id}.execute-api.{self.region}.amazonaws.com",
                    origin_path=f"/{api.deployment_stage.stage_name}",
                ),
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
            ),
            additional_behaviors={
                "/qrs/*": cloudfront.BehaviorOptions(
                    origin=origins.S3Origin(bucket),
                    cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                ),
            },
        )

        route53.ARecord(
            self,
            "AliasRecord",
            zone=zone,
            record_name="qrcode",
            target=route53.RecordTarget.from_alias(
                route53_targets.CloudFrontTarget(distribution)
            ),
        )

        CfnOutput(self, "ApiUrl", value=api.url)
        CfnOutput(self, "CustomUrl", value="https://qrcode.jamestrachy.com")
        CfnOutput(self, "BucketName", value=bucket.bucket_name)


def _create_public_read_policy(bucket):
    import aws_cdk.aws_iam as iam

    return iam.PolicyStatement(
        actions=["s3:GetObject"],
        resources=[bucket.arn_for_objects("*")],
        principals=[iam.AnyPrincipal()],
    )
