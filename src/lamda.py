import json
from detection.EBS import check_old_snapshots, check_unattached_volumes
from detection.EIP import check_eip
from detection.EC2_IDLE import check_idle_ec2
from detection.TAG import check_tags
from notifier.slack import send_slack_report

def lambda_handler(event,context):
    dry_run = True
    if isinstance(event, dict) and 'dry_run' in event:
        dry_run = event['dry_run']
    
    snapshots= check_old_snapshots(dry_run=dry_run)
    eips= check_eip()
    volumes= check_unattached_volumes(dry_run=dry_run)
    idle_ec2 = check_idle_ec2()
    untagged = check_tags()

    cost_findings = snapshots + volumes + eips + idle_ec2
    total_savings = sum(item.get('estimated_monthly_cost', 0) for item in cost_findings)

    summary = {
        "dry_run": dry_run,
        "total_estimated_monthly_savings": round(total_savings, 2),
        "summary_counts": {
            "old_snapshots": len(snapshots),
            "unattached_volumes": len(volumes),
            "unassociated_eips": len(eips),
            "idle_ec2_instances": len(idle_ec2),
            "untagged_resources": len(untagged)
        },
        "findings": {
            "old_snapshots": snapshots,
            "unattached_volumes": volumes,
            "unassociated_eips": eips,
            "idle_ec2": idle_ec2,
            "untagged": untagged
        }
    }
    send_slack_report(summary)

    return {
        "statusCode": 200,
        "body": json.dumps(summary, default=str)
    }
        
    
    

    
