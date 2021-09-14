#!/bin/sh

# Deploy lambda function with API gateway using SAM

function print_usage
{
  echo
  echo Usage:
  echo $0 [-d] [-t BUCKET]
  echo "    Deploy a HTTP API"
  echo
  echo "    -d         deploy the HTTP API using a cloudformation/SAM template"
  echo "    -t BUCKET  tear down the cloudformation stack created using the S3 bucket BUCKET"
  echo
}

function deploy_lambda
{
  # Create deployement bucket
  BUCKET_ID=$(dd if=/dev/random bs=8 count=1 2>/dev/null | od -An -tx1 | tr -d ' \t\n')
  BUCKET_NAME=aws-sam-cli-managed-bucket-${BUCKET_ID}

  aws s3api create-bucket --bucket $BUCKET_NAME --region us-east-1
  echo $BUCKET_NAME > .sam_bucket__$BUCKET_NAME

  # Let manually confirm the deployment
  sam deploy --template-file template.yaml --stack-name sam-app --capabilities CAPABILITY_IAM  --s3-bucket $BUCKET_NAME

  API_URL=$(aws cloudformation describe-stacks --query Stacks[].Outputs[*].[OutputKey,OutputValue] --output text | grep APIendpoint | cut -f 2)
  echo Deployment bucket: $BUCKET_NAME
  echo Api URL: $API_URL
}

function tear_down
{
  BUCKET_NAME=$1

  # Delete deployment bucket. Delete objects, versions and markers
  aws s3api delete-objects --bucket ${BUCKET_NAME} --delete "$(aws s3api list-object-versions --bucket ${BUCKET_NAME} --output=json --query='{Objects: Versions[].{Key:Key,VersionId:VersionId}}')"

  aws s3 rb s3://${BUCKET_NAME} --force

  # Delete CloudFormation stack
  aws cloudformation delete-stack --stack-name sam-app

  rm -f .sam_bucket__$BUCKET_NAME
}

while [[ $# -gt 0 ]]; do
  key="$1"

  case $key in
    -d|--deploy)
      DEPLOY=1
      shift
      ;;

    -t|--teardown)
      BUCKET="$2"
      shift
      shift
      ;;
    *)
      shift
      ;;
  esac
done

if [ -z "$DEPLOY" -a -z "$BUCKET" ]; then
  echo Requires at least an argument or argument unknown
  print_usage
fi


if [ ! -z "$BUCKET" ]; then
    tear_down $BUCKET
    exit 0
fi

if [ ! -z "$DEPLOY" ]; then
  deploy_lambda
fi
