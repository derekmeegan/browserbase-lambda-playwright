import os
from aws_cdk import App, Environment

from stack import BrowserbaseLambdaStack

app = App()

env = Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION"),
)

scraper_lambda = BrowserbaseLambdaStack(app, "BrowserbaseLambdaStack", env=env)

app.synth()
