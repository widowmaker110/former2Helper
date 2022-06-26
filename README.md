# former2Helper

[former2](https://github.com/iann0036/former2) is a great tool for point-and-click migration of AWS resources. They have an operating [website](https://former2.com/) you can use or you can run locally via code in the github mentioned above. The only issue I ran into with the project is the Lambda code location wouldn't authenticate correctly when I took the raw CloudFormation output and created a new CloudFormation stack. 

CLOUDFORMATION FORMAT ONLY

Used Pytrhon 3.10 when developing this.

# Setup

    pip install -r requirements.txt

Following the same steps as Former2, you'll need Access and Secret Key from an IAM user. Read-only to the Lambda functions will suffice. You will need write permissions to a S3 bucket if you're migrating Lambdas. 

You *may* need to run the configure command in your terminal before running. More info [here](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-quickstart.html)

    aws configure


# Process

1. Get all Lambda function resource names
2. Query AWS account Lambda resource by name
3. Get signed URL pointing to Zip file of Lambda code
4. Download Lambdas as Zips locally
5. Upload Lambdas to S3 bucket
6. Convert YAML file to JSON using [cfn-flip](https://github.com/awslabs/aws-cfn-template-flip)
7. Update CloudFormation S3 locations to ZipFile location found in step 5
8. Remove Function name from all Lambda resources. (This is optional. I'm doing this so I can remake the same resources in the same region and they would be named dynamically.)
9. Flip the JSON back into YAML and save to file **formation_updated.yml** in the same directory as main.py

# License
MIT - free code to help the community.
