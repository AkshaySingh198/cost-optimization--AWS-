import boto3
from datetime import timezone, datetime, timedelta


def check_idle_ec2():
    days = 7
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=days)
    ec2 = boto3.client('ec2')
    cloudWatch = boto3.client('cloudwatch')

    response = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    findings = []

    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance.get('InstanceId')
            instance_type = instance.get('InstanceType')
            launch_time = instance.get('LaunchTime')

            if not (datetime.now(timezone.utc) - launch_time).total_seconds() < 3600:
                watchResponse = cloudWatch.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='CPUUtilization',
                    Dimensions=[
                        {'Name': 'InstanceId', 'Value': instance_id}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,
                    Statistics=['Average']
                )
                mean = 0
                i = 0
                if not watchResponse['Datapoints']:
                    continue
                for datapoint in watchResponse['Datapoints']:
                    if not datapoint:
                        return None
                    avg = datapoint.get('Average')
                    mean = mean + avg
                    i += 1

                mean = mean / i
                if mean < 5.0:
                    findings.append({
                        "resource_id": instance_id,
                        "instance_type": instance_type,
                        "average_cpu": round(mean, 2),
                        "resource_type": "EC2 Instance"
                    })

    return findings
