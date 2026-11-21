output "ec2_instance_id" {
  description = "The ID of the EC2 instance"
  value       = aws_instance.scorume_app.id
}

output "ec2_public_ip" {
  description = "Public IP address of the deployed Scorume server"
  value       = aws_instance.scorume_app.public_ip
}

output "ec2_public_dns" {
  description = "Public DNS of the EC2 instance"
  value       = aws_instance.scorume_app.public_dns
}

output "application_url" {
  description = "Direct HTTP URL to access the Scorume (evaluation engine) web dashboard"
  value       = "http://${aws_instance.scorume_app.public_ip}"
}

output "frontend_vite_url" {
  description = "Direct Vite port URL"
  value       = "http://${aws_instance.scorume_app.public_ip}:5173"
}

output "backend_api_docs" {
  description = "FastAPI Swagger interactive API documentation URL"
  value       = "http://${aws_instance.scorume_app.public_ip}/docs"
}

output "backend_health_url" {
  description = "FastAPI System Health check URL"
  value       = "http://${aws_instance.scorume_app.public_ip}/health"
}

output "ssh_command" {
  description = "Command to SSH into the instance using the generated key"
  value       = "ssh -i terraform/scorume-key.pem ubuntu@${aws_instance.scorume_app.public_ip}"
}
