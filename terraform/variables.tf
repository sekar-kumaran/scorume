variable "aws_region" {
  description = "AWS Region to deploy Scorume into"
  type        = string
  default     = "ap-south-1"
}

variable "instance_type" {
  description = "EC2 Instance type (2 vCPU, 4GB RAM recommended for local NLP inference)"
  type        = string
  default     = "t3.medium"
}

variable "app_name" {
  description = "Application name for tagging and resource naming"
  type        = string
  default     = "scorume"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}

variable "repo_url" {
  description = "Public GitHub repository URL"
  type        = string
  default     = "https://github.com/sekar-kumaran/scorume.git"
}

variable "root_volume_size" {
  description = "Root EBS storage volume size in GB"
  type        = number
  default     = 30
}
