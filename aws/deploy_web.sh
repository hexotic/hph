#!/bin/bash

# Deploy a static website

WEB_DIR=../web

function print_usage
{
  echo
  echo Usage:
  echo $0 "[-u|--url] [-t BUCKET]"
  echo '  ' Deploy a static web site
  echo
  echo "    -u | --url URL  Deploy a static web site using URL as the HTTP API url"
  echo "    -t BUCKET       Remove the bucket BUCKET and all its files"
  echo
}

function create_bucket_and_upload
{
  BUCKET_ID=$(dd if=/dev/random bs=8 count=1 2>/dev/null | od -An -tx1 | tr -d ' \t\n')
  BUCKET_NAME=bkt-web-${BUCKET_ID}

  sed "s/BUCKET_NAME/$BUCKET_NAME/g" policy_s3.json > policy_tmp.json

  aws s3api create-bucket --bucket $BUCKET_NAME --acl public-read --region us-east-1
  aws s3 website s3://$BUCKET_NAME --index-document index.html --error-document error.html --region us-east-1
  aws s3api put-bucket-policy --bucket $BUCKET_NAME --policy file://policy_tmp.json
  aws s3 cp $WEB_DIR s3://$BUCKET_NAME --recursive

  rm -f policy_tmp.json

  echo $BUCKET_NAME > .web_bucket__$BUCKET_NAME
  echo Website URL: http://${BUCKET_NAME}.s3-website-us-east-1.amazonaws.com
}

function remove_bucket
{
  BUCKET_NAME=$1
  echo Removing Bucket $BUCKET_NAME

  aws s3 rm s3://${BUCKET_NAME} --recursive
  aws s3 rb s3://${BUCKET_NAME} --force

  rm -f .web_bucket__${BUCKET_NAME}
}

while [[ $# -gt 0 ]]; do
  key="$1"

  case $key in
    -u|--url)
      URL="$2"
      shift
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

if [ -z "$URL" -a -z "$BUCKET" ]; then
  echo Requires at least an argument or argument unknown
  print_usage
fi

if [ ! -z "$BUCKET" ]; then
  remove_bucket $BUCKET
fi

if [ ! -z "$URL" ]; then

  # Replace URL
  sed -i.bak  "s|__POST_URL__|$URL|g" $WEB_DIR/index.html
  mv $WEB_DIR/index.html.bak .

  # Create bucket and upload files
  create_bucket_and_upload

  # Restore initial file
  mv index.html.bak $WEB_DIR/index.html

fi
