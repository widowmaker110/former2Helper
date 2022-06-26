import boto3
import os
from dotenv import load_dotenv
import json
from cfn_flip import to_yaml, to_json

load_dotenv()

client = boto3.client(
    "lambda",
    aws_access_key_id=os.environ["aws_access_key_id"],
    aws_secret_access_key=os.environ["aws_secret_access_key"]
)


def get_function_code_url(function_name):
    response = client.get_function(
        FunctionName=function_name,
    )
    return response["Code"]["Location"]


def open_yml():
    f = open("formation.yml", "r")
    yaml_file = f.read()
    some_json = to_json(yaml_file)
    return json.loads(some_json)


def get_yml_function_names(yaml_json):
    function_names = []
    for item in yaml_json["Resources"].keys():
        if yaml_json["Resources"][item]["Type"] == "AWS::Lambda::Function":
            function_names.append(yaml_json["Resources"][item]["Properties"]["FunctionName"])
    return function_names


def update_s3_uri(yaml_json, function_codes):
    for item in yaml_json["Resources"].keys():
        if yaml_json["Resources"][item]["Type"] == "AWS::Lambda::Function":
            uri_code = function_codes[yaml_json["Resources"][item]["Properties"]["FunctionName"]]
            zip_file_update = {
                "ZipFile" : uri_code
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

# 3. Update URI locations
yaml_file = update_s3_uri(yaml_json, function_codes)

# 4. Remove Function Names to prevent duplicate errors
yaml_file = remove_function_names(yaml_file)

# 5. Put new CloudFormation
yaml_file = to_yaml(json.dumps(yaml_file, indent=4))
f = open("formation_updated.yml", "w")
f.write(yaml_file)
f.close()
