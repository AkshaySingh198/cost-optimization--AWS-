import boto3
from datetime import datetime, timezone


def check_old_snapshots(dry_run=True):
    ec2 = boto3.client("ec2")
    findings = []
    response = ec2.describe_snapshots(OwnerIds=['self'])

    instances_response = ec2.describe_instances(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
    )
    active_instance_ids = set()

    for reservation in instances_response['Reservations']:
        for instance in reservation['Instances']:
            active_instance_ids.add(instance['InstanceId'])

    for snapshots in response['Snapshots']:
        snapshot_id = snapshots.get('SnapshotId')
        volume_id = snapshots.get('VolumeId')
        size_gb = snapshots.get('VolumeSize', 0)

        # Protect snapshots tagged 'do-not-delete'
        tags_dict = {t['Key']: t['Value'] for t in snapshots.get('Tags', [])}
        if 'do-not-delete' in tags_dict:
            continue

        age = (datetime.now(timezone.utc) - snapshots['StartTime']).days
        estimated_cost = round(size_gb * 0.05, 2)
        should_flag = False
        reason = ""

        if not volume_id and age > 30:
            should_flag = True
            reason = f"No associated volume and older than 30 days ({age} days)"
        elif volume_id:
            try:
                volume_response = ec2.describe_volumes(VolumeIds=[volume_id])
                if not volume_response['Volumes'][0]['Attachments'] and age > 30:
                    should_flag = True
                    reason = f"Parent volume {volume_id} is unattached and snapshot is {age} days old"
            except ec2.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'InvalidVolume.NotFound' and age > 30:
                    should_flag = True
                    reason = f"Parent volume {volume_id} no longer exists and snapshot is {age} days old"

        if should_flag:
            if not dry_run:
                ec2.delete_snapshot(SnapshotId=snapshot_id)
                action_taken = "deleted"
                print(f"Deleted EBS snapshot {snapshot_id}: {reason}")
            else:
                action_taken = "dry-run (no changes made)"

            findings.append({
                "resource_id": snapshot_id,
                "resource_type": "EBS Snapshot",
                "size_gb": size_gb,
                "age_days": age,
                "estimated_monthly_cost": estimated_cost,
                "reason": reason,
                "action": action_taken
            })

    return findings


def check_unattached_volumes(dry_run=True):
    ec2 = boto3.client("ec2")
    findings = []
    response = ec2.describe_volumes(
        Filters=[{'Name': 'status', 'Values': ['available']}]
    )

    today = str(datetime.now(timezone.utc).date())

    for volume in response['Volumes']:
        volume_id = volume.get('VolumeId')
        size_gb = volume.get('Size', 0)
        volume_type = volume.get('VolumeType', 'gp3')
        create_time = volume.get('CreateTime')

        # Protect volumes tagged 'do-not-delete'
        tags_dict = {t['Key']: t['Value'] for t in volume.get('Tags', [])}
        if 'do-not-delete' in tags_dict:
            continue

        age_days = (datetime.now(timezone.utc) - create_time).days if create_time else 0

        # Price per GB-month: ~$0.10 for gp2, ~$0.08 for gp3/default
        rate = 0.10 if volume_type == 'gp2' else 0.08
        estimated_cost = round(size_gb * rate, 2)

        if dry_run:
            ec2.create_tags(
                Resources=[volume_id],
                Tags=[{'Key': 'flagged-for-review', 'Value': today}]
            )
            action_taken = f"dry-run (tagged flagged-for-review: {today})"
        else:
            # Always create a backup snapshot before deleting the volume
            ec2.create_snapshot(
                VolumeId=volume_id,
                Description=f"Backup of {volume_id} before cost optimization deletion"
            )
            ec2.delete_volume(VolumeId=volume_id)
            action_taken = "snapshotted and deleted"

        findings.append({
            "resource_id": volume_id,
            "resource_type": "EBS Volume",
            "volume_type": volume_type,
            "size_gb": size_gb,
            "age_days": age_days,
            "estimated_monthly_cost": estimated_cost,
            "action": action_taken
        })

    return findings
