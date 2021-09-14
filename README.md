# Hexadecimal Pattern Highlighter
This project implements a pattern highlighter for hexadecimal data.
It was originally designed to find common patterns in several network packets.

# Usage
```bash
./hph.py -f <filename>
```

## Input
It takes a file with hexadecimal data in ASCII, each line representing different data.<br>
Use `#` at the beginning of a line for comment. 

## Output
The script generates a output file with highlighted patterns called `output.html` in the same path the script is launched. <br>
The html contains a `CSS` file so be sure to be in the right directory structure so the browser can properly render the output file.<br>
Each colour represents the same set of lines where some patterns occur and not a pattern itself.

# Web/HTTP API
The project contains scripts used to deploy a HTTP API on AWS.
The directory `aws` contains scripts to deploy the necessary infrastructure for a HTTP API (API gateway and lambda function) and a static website which calls this API.<br>
The directory `web` contains files for a static website which uses the HTTP API deployed.<br>

#### deploy_lambda.sh
The scripts uses a combination of Cloudformation, SAM and CLI commands to deploy the serverless part. It outputs the HTTP API URL which needs to be fed to the script `deploy_web.sh`.

#### deploy_web.sh
The scripts deploys a static website in a S3 bucket.

### Deployment on AWS
```bash
$ aws configure
$ ...
$ cd aws
$ ./deploy_lambda.sh # you may need to confirm some inputs
$ # will output something like:
$ # https://XXXXXXXX.execute-api.REGION.amazonaws.com/hex
$ ./deploy_web.sh -u https://XXXXXXXX.execute-api.REGION.amazonaws.com/hex
```

