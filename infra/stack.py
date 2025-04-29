from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_iam as iam,
    Duration,
    Size,
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct

class BrowserbaseLambdaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        browserbase_project_id_secret = secretsmanager.Secret.from_secret_name_v2(
            self,
            "BrowserbaseProjectId",
            "BrowserbaseLambda/BrowserbaseProjectId"
        )

        browserbase_api_key_secret = secretsmanager.Secret.from_secret_name_v2(
            self,
            "BrowserbaseApiKey",
            "BrowserbaseLambda/BrowserbaseApiKey"
        )

        lambda_execution_role = iam.Role(
            self, "BrowserbaseLambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
            ]
        )
        browserbase_project_id_secret.grant_read(lambda_execution_role)
        browserbase_api_key_secret.grant_read(lambda_execution_role)
        
        browserbase_lambda = lambda_.DockerImageFunction(
            self, "BrowserbaseLambda",
            code=lambda_.DockerImageCode.from_image_asset(
                "../src",
                cmd=["scraper.lambda_handler"],
                platform=Platform.LINUX_ARM64
            ),
            architecture=lambda_.Architecture.ARM_64,
            role=lambda_execution_role,
            timeout=Duration.minutes(15),
            memory_size=512,
            ephemeral_storage_size=Size.gibibytes(1),
            environment={
                "BROWSERBASE_PROJECT_ID_ARN": browserbase_project_id_secret.secret_arn,
                "BROWSERBASE_API_KEY_SECRET_ARN": browserbase_api_key_secret.secret_arn
            },
        )