import os

from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    CfnOutput,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_route53_targets as route53_targets,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_ssm as ssm,
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

        table = dynamodb.Table(
            self,
            "QrCodeTable",
            partition_key=dynamodb.Attribute(
                name="id", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

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
                "QR_DYNAMO_TABLE": table.table_name,
                "CUSTOM_DOMAIN": "qrcode.jamestrachy.com",
                "URL_SHORTENER_URL": "https://l.jamestrachy.com",
            },
        )

        bucket.grant_put(fn)
        table.grant_read_write_data(fn)

        api = apigw.LambdaRestApi(
            self,
            "QrCodeApi",
            handler=fn,
            binary_media_types=["multipart/form-data"],
        )

        # Import shared platform resources via SSM (resolved at deploy time)
        zone_id = ssm.StringParameter.value_for_string_parameter(
            self, "/platform/hosted-zone-id"
        )
        zone_name = ssm.StringParameter.value_for_string_parameter(
            self, "/platform/hosted-zone-name"
        )
        cert_arn = ssm.StringParameter.value_for_string_parameter(
            self, "/platform/wildcard-cert-arn"
        )

        zone = route53.HostedZone.from_hosted_zone_attributes(
            self, "Zone",
            hosted_zone_id=zone_id,
            zone_name=zone_name,
        )

        cf_cert = acm.Certificate.from_certificate_arn(
            self, "WildcardCert", cert_arn
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
