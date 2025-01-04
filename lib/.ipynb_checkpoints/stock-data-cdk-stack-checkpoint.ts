import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { RetentionDays } from "aws-cdk-lib/aws-logs";
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as iam from "aws-cdk-lib/aws-iam";
import * as s3n from 'aws-cdk-lib/aws-s3-notifications';

export type StockDataStackProps = {
  lambdasMemory: number;
} & cdk.StackProps;

export class StockDataCdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: StockDataStackProps) {
    super(scope, id, props);

    const { lambdasMemory, env } = props;

    const bucket = new s3.Bucket(this, 'StockDataBucket', {
      bucketName: `stock-data-${env?.account}-${env?.region}`,
      removalPolicy: cdk.RemovalPolicy.RETAIN_ON_UPDATE_OR_DELETE,
    });

    const lambdaRole = new iam.Role(this, 'LambdaExecutionRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole')
      ]
    });

    const collectionAndProcessingLambda = new lambda.DockerImageFunction(
      this,
      'LambdaCollectionAndProcessing',
      {
        code: lambda.DockerImageCode.fromImageAsset("lambda/data_collection_and_processing"),
        environment: {
          S3_BUCKET: bucket.bucketName,
          POLYGON_API_KEY: 'ff_7GZKhJVWBtiLKz_MunrvJZI3zzvQR'
        },
        memorySize: lambdasMemory,
        logRetention: RetentionDays.ONE_WEEK,
        timeout: cdk.Duration.seconds(120),
        architecture: lambda.Architecture.ARM_64,
        role: lambdaRole
      }
    );

    const predictionLambda = new lambda.DockerImageFunction(
      this,
      'LambdaPrediction',
      {
        code: lambda.DockerImageCode.fromImageAsset("lambda/data_prediction"),
        environment: {
          BUCKET_NAME: bucket.bucketName,
        },
        memorySize: lambdasMemory,
        logRetention: RetentionDays.ONE_WEEK,
        timeout: cdk.Duration.seconds(120),
        architecture: lambda.Architecture.ARM_64,
        role: lambdaRole
      }
    );
    bucket.grantReadWrite(collectionAndProcessingLambda);
    bucket.grantReadWrite(predictionLambda);

    const sagemakerRole = new iam.Role(this, 'SageMakerExecutionRole', {
      assumedBy: new iam.ServicePrincipal('sagemaker.amazonaws.com'),
      description: 'Role for SageMaker to access S3 and run training jobs',
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonSageMakerFullAccess')
      ]
    });

    sagemakerRole.addToPolicy(new iam.PolicyStatement({
      actions: ['s3:GetObject', 's3:PutObject'],
      resources: [`arn:aws:s3:::${bucket.bucketName}/*`]
    }));

    const sagemakerLambda = new lambda.DockerImageFunction(
      this,
      'SageMakerTrainingLambda', 
      {
        code: lambda.DockerImageCode.fromImageAsset("lambda/sagemaker_training"),
        environment: {
          SAGEMAKER_ROLE_ARN: sagemakerRole.roleArn,
          SAGEMAKER_IMAGE_URI: '607282882839.dkr.ecr.us-east-1.amazonaws.com/linear-regression-model-repo:latest',
        },
        memorySize: lambdasMemory,
        logRetention: RetentionDays.ONE_WEEK,
        timeout: cdk.Duration.seconds(120),
        architecture: lambda.Architecture.ARM_64,
    });

    sagemakerLambda.addToRolePolicy(new iam.PolicyStatement({
      actions: [
        'sagemaker:CreateTrainingJob',
        'sagemaker:DescribeTrainingJob',
        's3:GetObject',
        's3:PutObject',
        'iam:PassRole',
      ],
      resources: ['*']
    }));

    bucket.addEventNotification(s3.EventType.OBJECT_CREATED_PUT, new s3n.LambdaDestination(sagemakerLambda), {
      prefix: 'training/processed/',
    });

    const stockDataApi = new apigateway.RestApi(this, 'StockDataApi', {
      restApiName: 'Stock Data Service',
      description: 'API Gateway for trigerring Collection and Processing Lambda function',
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: ['POST'],
      },
    });

    const predictionDataApi = new apigateway.RestApi(this, 'PredictionDataApi', {
      restApiName: 'Prediction Data Service',
      description: 'API Gateway for trigerring Prediction Lambda function',
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: ['POST'],
      },
    });
    
    const processingLambdaIntegration = new apigateway.LambdaIntegration(collectionAndProcessingLambda);
    const predictionLambdaIntegration = new apigateway.LambdaIntegration(predictionLambda);

    stockDataApi.root.addMethod('POST', processingLambdaIntegration);
    predictionDataApi.root.addMethod('POST', predictionLambdaIntegration);
  }
}
