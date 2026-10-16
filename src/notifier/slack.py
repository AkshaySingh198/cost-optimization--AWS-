import json
import urllib.request
import boto3


def get_webhook_url(parameter_name="/cost-optimizer/slack-webhook"):
    """Fetch the encrypted Slack Webhook URL from AWS SSM Parameter Store."""
    ssm = boto3.client("ssm")
    response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
    return response["Parameter"]["Value"]


def send_slack_report(summary, webhook_url=None):
    """Format and send the cost optimization summary to Slack via Block Kit."""
    if not webhook_url:
        webhook_url = get_webhook_url()

    dry_run = summary.get("dry_run", True)
    total_savings = summary.get("total_estimated_monthly_savings", 0.0)
    counts = summary.get("summary_counts", {})

    mode_text = "DRY RUN (No changes made)" if dry_run else "REMEDIATION ACTIVE"
    total_findings = sum(counts.values())

    if total_findings == 0:
        # Clean message when there is no waste in the account
        message_blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "✅ AWS Cost Optimization: All Clear",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Status:* `{mode_text}`\n"
                        f"*Result:* No idle or unattached resources found. Your AWS environment is fully optimized!"
                    )
                }
            }
        ]
    else:
        # Detailed report when waste is detected
        message_blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "💰 AWS Cost Optimization Summary",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Status:* `{mode_text}`\n*Total Estimated Monthly Savings:* *${total_savings:,.2f}*"
                }
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"• *Unattached EBS Volumes:* {counts.get('unattached_volumes', 0)}\n"
                        f"• *Old EBS Snapshots:* {counts.get('old_snapshots', 0)}\n"
                        f"• *Unassociated Elastic IPs:* {counts.get('unassociated_eips', 0)}\n"
                        f"• *Idle EC2 Instances:* {counts.get('idle_ec2_instances', 0)}\n"
                        f"• *Untagged Resources:* {counts.get('untagged_resources', 0)}"
                    )
                }
            }
        ]

    payload = {"blocks": message_blocks}
    req = urllib.request.Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(req) as response:
        return response.status