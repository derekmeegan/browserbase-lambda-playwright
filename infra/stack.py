from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    Duration,
    Size,
    aws_secretsmanager as secretsmanager,
    RemovalPolicy,
    CfnOutput
)
from aws_cdk.aws_ecr_assets import Platform
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

        job_table = dynamodb.Table(
            self, "JobStatusTable",
            partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            removal_policy=RemovalPolicy.DESTROY
        )

        scraper_execution_role = iam.Role(
            self, "ScraperLambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
            ]
        )
        browserbase_project_id_secret.grant_read(scraper_execution_role)
        browserbase_api_key_secret.grant_read(scraper_execution_role)
        job_table.grant_read_write_data(scraper_execution_role)

        getter_execution_role = iam.Role(
            self, "GetterLambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
            ]
        )
        job_table.grant_read_data(getter_execution_role)
        
        browserbase_lambda = lambda_.DockerImageFunction(
            self, "BrowserbaseLambda",
            code=lambda_.DockerImageCode.from_image_asset(
                "../lambdas/scraper",
                cmd=["scraper.lambda_handler"],
                platform=Platform.LINUX_ARM64
            ),
            architecture=lambda_.Architecture.ARM_64,
            role=scraper_execution_role,
            timeout=Duration.minutes(15),
            memory_size=512,
            ephemeral_storage_size=Size.gibibytes(1),
            environment={
                "BROWSERBASE_PROJECT_ID_ARN": browserbase_project_id_secret.secret_arn,
                "BROWSERBASE_API_KEY_SECRET_ARN": browserbase_api_key_secret.secret_arn,
                "JOB_STATUS_TABLE_NAME": job_table.table_name
            },
        )

        getter_lambda = lambda_.DockerImageFunction(
            self, "JobStatusGetterLambda",
            code=lambda_.DockerImageCode.from_image_asset(
                "../lambdas/getter",
                cmd=["getter.lambda_handler"],
                platform=Platform.LINUX_ARM64
            ),
            architecture=lambda_.Architecture.ARM_64,
            role=getter_execution_role,
            timeout=Duration.minutes(1),
            environment={
                "JOB_STATUS_TABLE_NAME": job_table.table_name,
            },
        )
        
        async_lambda_integration = apigateway.LambdaIntegration(
            browserbase_lambda,
            proxy=False,
            request_parameters={
                'integration.request.header.X-Amz-Invocation-Type': "'Event'"
            }
        )

        getter_lambda_integration = apigateway.LambdaIntegration(
            getter_lambda,
            proxy=True
        )

        api = apigateway.RestApi(
            self, "BrowserbaseAsyncApi",
            rest_api_name="Browserbase Async API",
            description="API to trigger Browserbase Lambda asynchronously",
            deploy_options=apigateway.StageOptions(
                stage_name="v1"
            )
        )

        scrape_request_model = api.add_model("ScrapeRequestModel",
            content_type="application/json",
            model_name="ScrapeRequestModel",
            schema=apigateway.JsonSchema(
                schema=apigateway.JsonSchemaVersion.DRAFT4,
                title="ScrapeRequest",
                type=apigateway.JsonSchemaType.OBJECT,
                required=["jobId", "url"],
                properties={
                    "jobId": apigateway.JsonSchema(
                        type=apigateway.JsonSchemaType.STRING,
                        description="Unique identifier for the scrape job provided by the caller"
                    ),
                    "url": apigateway.JsonSchema(
                        type=apigateway.JsonSchemaType.STRING,
                        format="uri",
                        description="The URL to scrape"
                    )
                }
            )
        )

        body_validator = api.add_request_validator("BodyValidator",
            request_validator_name="ValidateRequestBody",
            validate_request_body=True,
            validate_request_parameters=False
        )

        params_validator = api.add_request_validator("ParameterValidator",
            request_validator_name="ValidateRequestParameters",
            validate_request_body=False,
            validate_request_parameters=True
        )
        
        scrape_resource = api.root.add_resource("scrape")
        scrape_resource.add_method(
            "POST",
            async_lambda_integration,
            api_key_required=True,
            request_validator=body_validator,
            request_models={
                "application/json": scrape_request_model
            },
            method_responses=[
                apigateway.MethodResponse(status_code="202"),
                apigateway.MethodResponse(status_code="400")
            ]
        )

        job_resource = scrape_resource.add_resource("{jobId}")
        job_resource.add_method(
            "GET",
            getter_lambda_integration,
            api_key_required=True,
            request_validator=params_validator,
            request_parameters={
                'method.request.path.jobId': True
            },
            method_responses=[
                apigateway.MethodResponse(status_code="200"),
                apigateway.MethodResponse(status_code="404"),
                apigateway.MethodResponse(status_code="400"),
                apigateway.MethodResponse(status_code="500")
            ]
        )

        api_key = api.add_api_key("ServerlessScraperApiKey",
            api_key_name="serverless-scraper-api-key"
        )

        usage_plan = api.add_usage_plan("ServerlessScraperUsagePlan",
            name="ServerlessScraperBasic",
            throttle=apigateway.ThrottleSettings(
                rate_limit=5,
                burst_limit=2
            ),
            api_stages=[apigateway.UsagePlanPerApiStage(
                api=api,
                stage=api.deployment_stage
            )]
        )
        usage_plan.add_api_key(api_key)

        CfnOutput(
            self, "ApiEndpointUrl",
            value=f"{api.url}scrape",
            description="API Gateway Endpoint URL for POST /scrape"
        )
        CfnOutput(
            self, "ApiStatusEndpointBaseUrl",
            value=f"{api.url}scrape/",
            description="Base URL for GETting job status (append {jobId})"
        )
        CfnOutput(
            self, "ApiKeyId",
            value=api_key.key_id,
            description="API Key ID (use 'aws apigateway get-api-key --api-key <key-id> --include-value' to retrieve the key value)"
        )
        CfnOutput(
            self, "JobStatusTableName",
            value=job_table.table_name,
            description="DynamoDB table name for job status"
        )