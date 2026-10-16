import boto3


def check_tags():
    tag = boto3.client('resourcegroupstaggingapi')
    findings = []
    response = tag.get_resources(ResourceTypeFilters=[
        'ec2:instance',
        'ec2:volume',
        'ec2:snapshot'
    ])

    RequiredTag = {"Owner", "Environment", "Project"}

    for resource in response['ResourceTagMappingList']:
        resource_arn = resource.get('ResourceARN')
        resource_id = resource_arn.split('/')[-1]
        parts = resource_arn.split(':')
        res_type = parts[5].split('/')[0]

        tags_dict = {t['Key']: t['Value'] for t in resource.get('Tags', [])}

        missing = [t for t in RequiredTag if t not in tags_dict or not tags_dict[t].strip()]

        if len(missing) > 0:
            findings.append({
                "resource_id": resource_id,
                "Resource_ARN": resource_arn,
                "resource_type": res_type,
                "region": "us-east-1",
                "missing_tags": missing,
                "existed_tag": tags_dict
            })
    return findings