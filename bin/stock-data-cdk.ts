#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { StockDataCdkStack } from '../lib/stock-data-cdk-stack';
 
const app = new cdk.App();

const props: cdk.StackProps = {
  env: {
    account: "607282882839",
    region: "us-east-1",
  },
};

new StockDataCdkStack(app, "StockDataStack", {
  ...props,
  lambdasMemory: 1024,
});
