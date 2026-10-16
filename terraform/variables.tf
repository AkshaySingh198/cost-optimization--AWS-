variable "aws_region" {
  description = "The AWS region to deploy resources to"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "schedule_expression" {
  description = "Cron or rate expression for EventBridge (e.g. daily at 8 AM UTC)"
  type        = string
  default     = "cron(0 8 * * ? *)"
}

variable "lambda_timeout" {
  description = "Timeout for the Lambda function in seconds"
  type        = number
  default     = 60
}

variable "lambda_memory_size" {
  description = "Memory size for the Lambda function in MB"
  type        = number
  default     = 128
}