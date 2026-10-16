import boto3


def check_eip():
    ec2 = boto3.client("ec2")

    response = ec2.describe_addresses()
    findings = []
    for address in response['Addresses']:
        association_id = address.get('AssociationId')
        instance_id = address.get('InstanceId')
        networkFace_id = address.get('NetworkInterfaceId')
        public_ip = address.get('PublicIp')

        if not association_id:
            findings.append({
                "resource_id": address.get('AllocationId'),
                "public_ip": public_ip,
                "resource_type": "Elastic IP",
                "region": "us-west-2",
                "estimated_monthly_cost": 3.65
            })
        else:
            print("true")

    return findings
