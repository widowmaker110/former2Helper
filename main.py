import boto3
import os
from dotenv import load_dotenv
import json
from cfn_flip import to_yaml, to_json
import requests

load_dotenv()

directory = './zip_files/'
bucket = 'project-loading-amm'
remove_function_name = False

lambda_client = boto3.client(
    "lambda",
    aws_access_key_id=os.environ["aws_access_key_id"],
    aws_secret_access_key=os.environ["aws_secret_access_key"]
)

s3_client = boto3.resource(
    "s3",
    aws_access_key_id=os.environ["aws_access_key_id"],
    aws_secret_access_key=os.environ["aws_secret_access_key"]
)


def get_function_code_url(function_name):
    response = lambda_client.get_function(
        FunctionName=function_name,
    )
    return response["Code"]["Location"]


def download_url(url, save_path, chunk_size=128):
    r = requests.get(url, stream=True)
    with open(save_path, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            fd.write(chunk)


def clear_directory(directory):
    for file in os.listdir(directory):
        os.remove(os.path.join(directory, file))


def upload_file_to_s3(path, bucket_name, file_name):
    try:
        s3_client.meta.client.upload_file(path, bucket_name, file_name)
        return True
    except Exception as exp:
        print('exp: ', exp)
        return False


def open_yml():
    file = open("formation.yml", "r")
    yaml_file = file.read()
    some_json = to_json(yaml_file)
    return json.loads(some_json)


def get_yml_function_names(yaml_json):
    function_names = []
    for item in yaml_json["Resources"].keys():
        if yaml_json["Resources"][item]["Type"] == "AWS::Lambda::Function":
            function_names.append(yaml_json["Resources"][item]["Properties"]["FunctionName"])
    return function_names


def update_s3_uri(yaml_json):
    for item in yaml_json["Resources"].keys():
        if yaml_json["Resources"][item]["Type"] == "AWS::Lambda::Function":
            zip_file_update = {
                "S3Bucket": bucket,
                "S3Key": yaml_json["Resources"][item]["Properties"]["FunctionName"] + '.zip'
            }
            yaml_json["Resources"][item]["Properties"]["Code"] = zip_file_update
    return yaml_json


def remove_function_names(yaml_json):
    if "Resources" in yaml_json:
        for item in yaml_json["Resources"].keys():
            current_resource = yaml_json["Resources"][item]
            if "Type" in current_resource and current_resource["Type"] == "AWS::Lambda::Function":
                if "Properties" in current_resource and "FunctionName" in current_resource["Properties"]:
                    del current_resource["Properties"]["FunctionName"]
                    yaml_json["Resources"][item] = current_resource
    return yaml_json


# 1. Open YAML file
yaml_json = open_yml()

# 2. Get Lambda Function Names
function_names = get_yml_function_names(yaml_json)
function_codes = {}

for name in function_names:
    function_codes[name] = get_function_code_url(name)

# 3. Download zip files for each function
clear_directory(directory)
zip_files = []
for function_name in function_codes.keys():
    url = function_codes[function_name]
    download_url(url, directory + function_name + '.zip')
    zip_files.append(directory + function_name + '.zip')

# 4. Upload to S3
for zip_file in zip_files:
    upload_file_to_s3(zip_file, bucket, zip_file.replace(directory, ''))

# 5. Update Bucket locations
yaml_file = update_s3_uri(yaml_json, function_codes)

# 6. Remove Function Names to prevent duplicate errors
if remove_function_name:
    yaml_file = remove_function_names(yaml_file)

# 7. Create new CloudFormation
yaml_file = to_yaml(json.dumps(yaml_file, indent=4), clean_up=True)
f = open("formation_updated.yml", "w")
f.write(yaml_file)
f.close()
