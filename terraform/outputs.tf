output "lambda_function_arn" {
  description = "The ARN of the deployed Lambda Function"
  value       = aws_lambda_function.cost_optimizer.arn
}

output "eventbridge_rule_arn" {
  description = "The ARN of the EventBridge cron schedule"
  value       = aws_cloudwatch_event_rule.daily_schedule.arn
}
