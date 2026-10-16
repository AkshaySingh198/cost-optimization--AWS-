terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}
provider "aws" {
  region = var.aws_region
}
# lamda code to zip
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../src"
  output_path = "${path.module}/cost_optimizer.zip"
}
resource "aws_iam_role" "lambda_exec" {
  name = "aws-cost-optimizer-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}
resource "aws_iam_policy" "lambda_policy" {
  name        = "aws-cost-optimizer-policy"
  description = "Least privilege permissions for scanning cost waste and sending Slack alerts"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # CloudWatch Logging
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      # EC2 & EBS Detection + Remediation
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:DescribeVolumes",
          "ec2:DescribeSnapshots",
          "ec2:DescribeAddresses",
          "ec2:CreateTags",
          "ec2:CreateSnapshot",
          "ec2:DeleteSnapshot",
          "ec2:DeleteVolume"
        ]
        Resource = "*"
      },
      # CloudWatch CPU Metric Queries
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:GetMetricStatistics"
        ]
        Resource = "*"
      },
      # Resource Groups Tagging API
      {
        Effect = "Allow"
        Action = [
          "tag:GetResources"
        ]
        Resource = "*"
      },
      # SSM Parameter Store (Slack Webhook)
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter"
        ]
        Resource = "arn:aws:ssm:*:*:parameter/cost-optimizer/slack-webhook"
      }
    ]
  })
}
resource "aws_iam_role_policy_attachment" "lambda_attach" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

# 3. CloudWatch Log Group (7-Day Free Retention)

resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/aws-cost-optimizer"
  retention_in_days = 7
}

# 4. AWS Lambda Function

resource "aws_lambda_function" "cost_optimizer" {
  function_name    = "aws-cost-optimizer"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  role             = aws_iam_role.lambda_exec.arn
  handler          = "lamda.lambda_handler"
  runtime          = "python3.11"
  timeout          = var.lambda_timeout
  memory_size      = var.lambda_memory_size
  environment {
    variables = {
      DRY_RUN = "true"
    }
  }
  depends_on = [
    aws_iam_role_policy_attachment.lambda_attach,
    aws_cloudwatch_log_group.lambda_logs
  ]
}

# 5. Amazon EventBridge Scheduler (Daily Cron)

resource "aws_cloudwatch_event_rule" "daily_schedule" {
  name                = "cost-optimizer-daily-rule"
  description         = "Triggers AWS Cost Optimizer Lambda daily"
  schedule_expression = var.schedule_expression
}
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_schedule.name
  target_id = "CostOptimizerLambdaTarget"
  arn       = aws_lambda_function.cost_optimizer.arn
}
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cost_optimizer.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_schedule.arn
}