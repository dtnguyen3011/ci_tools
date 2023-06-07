import argparse
import subprocess
import json

def nonempty_str(value: str):
    if len(value) > 0:
        return value
    raise argparse.ArgumentTypeError('Must not be empty string')


def parse_args() -> argparse.Namespace:
    """Adds and parses command line arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-fu', '--file-url', required=True, type=nonempty_str,
                        help='Artifactory file url')
    parser.add_argument('-pk', '--property-key', required=True, type=nonempty_str,
                        help='Property key string. Ex: commitId')
    parser.add_argument('-v', '--value', required=True, type=nonempty_str,
                        help='Expected property value')
    parser.add_argument('-u', '--username', required=True, type=nonempty_str,
                        help='Username for access Artifactory Server')
    parser.add_argument('-p', '--password', required=True, type=nonempty_str,
                        help='Password for access Artifactory Server')

    return parser.parse_args()


def validate_artifactory_file_property(file_url: str, property_key: str, value: str, username: str, password: str):
    # Log input data
    print(f"Artifactory file url: {file_url}")
    print(f"Property key: {property_key}")
    print(f"Expected property value: {value}")

    # Read properties from artifactory file
    cmd = f'curl -u {username}:{password} -X GET {file_url}?properties'
    try:
        pipe = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        out, err = pipe.communicate()
        print(f'Error response: {err.decode("utf-8")}')
    except Exception as e:
        print(e)
        raise Exception(f"Could not find artifactory file: {file_url}")
    json_data = json.loads(out.decode("utf-8"))

    # Validate property value
    if 'errors' in json_data:
        print(f"ERROR: {json_data}")
        raise Exception(f"Could not find artifactory file: {file_url}")
    if 'properties' in json_data and property_key in json_data['properties']:
        if value not in json_data['properties'][property_key]:
            raise Exception(f'Mismatch "{property_key}" between artifactory and input value. Found value from artifactory: {", ".join(json_data["properties"][property_key])}. Expected value: {value}')
    else:
        raise Exception("Property is empty")
    print("Found value is the same with expected value.")

if __name__ == '__main__':
    args = parse_args()
    validate_artifactory_file_property(args.file_url, args.property_key, args.value, args.username, args.password)
