# Welcome to your CDK TypeScript project

This is a blank project for CDK development with TypeScript.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

## Useful commands

* `npm run build`   compile typescript to js
* `npm run watch`   watch for changes and compile
* `npm run test`    perform the jest unit tests
* `npx cdk deploy`  deploy this stack to your default AWS account/region
* `npx cdk diff`    compare deployed stack with current state
* `npx cdk synth`   emits the synthesized CloudFormation template

## Deploy mode image to AWS ECR

* `docker build --platform linux/amd64 -t linear-regression-model-image .`
* `aws ecr get-login-password --region us-east-1 --profile lazar-private | docker login --username AWS --password-stdin 607282882839.dkr.ecr.us-east-1.amazonaws.com`
* `aws ecr create-repository --repository-name linear-regression-model-repo --region us-east-1 --profile lazar-private`
* `docker tag linear-regression-model-image:latest 607282882839.dkr.ecr.us-east-1.amazonaws.com/linear-regression-model-repo:latest`
* `docker push 607282882839.dkr.ecr.us-east-1.amazonaws.com/linear-regression-model-repo:latest`
