terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "Scorume"
      Application = "EvaluationEngine"
      ManagedBy   = "Terraform"
      Environment = var.environment
    }
  }
}

# ==============================================================================
# Networking: Lookup Default VPC & Subnets in ap-south-1
# ==============================================================================
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# ==============================================================================
# Compute Image: Official Ubuntu 22.04 LTS (Jammy)
# ==============================================================================
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ==============================================================================
# Key Pair: Generate Automated SSH Key Pair
# ==============================================================================
resource "tls_private_key" "scorume_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "scorume_key" {
  key_name   = "${var.app_name}-key-${var.environment}"
  public_key = tls_private_key.scorume_key.public_key_openssh
}

resource "local_file" "private_key" {
  content         = tls_private_key.scorume_key.private_key_pem
  filename        = "${path.module}/scorume-key.pem"
  file_permission = "0600"
}

# ==============================================================================
# Security Group: Ingress for HTTP (80), Vite (5173), FastAPI (8000), SSH (22)
# ==============================================================================
resource "aws_security_group" "scorume_sg" {
  name        = "${var.app_name}-sg-${var.environment}"
  description = "Security group for Scorume (evaluation engine) web application"
  vpc_id      = data.aws_vpc.default.id

  # SSH
  ingress {
    description = "SSH access"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Standard HTTP (Nginx reverse proxy)
  ingress {
    description = "HTTP web traffic"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Standard HTTPS
  ingress {
    description = "HTTPS web traffic"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Direct Frontend Vite Access
  ingress {
    description = "Direct Frontend Vite port"
    from_port   = 5173
    to_port     = 5173
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Direct FastAPI Backend Access
  ingress {
    description = "Direct FastAPI Backend port"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Outbound traffic (allow all)
  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name = "${var.app_name}-sg"
  }
}

# ==============================================================================
# EC2 Instance: Host Scorume Docker Stack
# ==============================================================================
resource "aws_instance" "scorume_app" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  subnet_id                   = tolist(data.aws_subnets.default.ids)[0]
  vpc_security_group_ids      = [aws_security_group.scorume_sg.id]
  key_name                    = aws_key_pair.scorume_key.key_name
  associate_public_ip_address = true

  root_block_device {
    volume_size           = var.root_volume_size
    volume_type           = "gp3"
    delete_on_termination = true
    tags = {
      Name = "${var.app_name}-root-volume"
    }
  }

  user_data = <<-EOF
              #!/bin/bash
              set -e
              exec > >(tee -a /var/log/scorume-bootstrap.log) 2>&1
              echo "=== Starting Scorume Automated Bootstrap ==="

              # Configure 4GB Swap Space for smooth Free Tier execution
              if [ ! -f /swapfile ]; then
                echo "Configuring 4GB swapfile..."
                fallocate -l 4G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=4096
                chmod 600 /swapfile
                mkswap /swapfile
                swapon /swapfile
                echo '/swapfile none swap sw 0 0' >> /etc/fstab
              fi

              # 1. Update system packages
              apt-get update -y
              apt-get install -y ca-certificates curl gnupg lsb-release git nginx

              # 2. Install official Docker Engine & Docker Compose plugin
              install -m 0755 -d /etc/apt/keyrings
              curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
              chmod a+r /etc/apt/keyrings/docker.asc
              echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
              apt-get update -y
              apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

              systemctl enable docker
              systemctl start docker
              usermod -aG docker ubuntu

              # 3. Clone Repository
              mkdir -p /opt/scorume
              git clone ${var.repo_url} /opt/scorume
              cd /opt/scorume

              # Set environment variables for docker-compose
              cat <<EOT > /opt/scorume/.env
              COMPOSE_PROJECT_NAME=scorume
              POSTGRES_USER=postgres
              POSTGRES_PASSWORD=postgres
              POSTGRES_DB=scorume
              VITE_API_BASE_URL=
              VITE_API_PROXY_TARGET=http://backend:8000
              EOT

              # 4. Build and start containers
              docker compose up -d --build

              # 5. Configure Nginx Reverse Proxy on port 80
              cat <<'NGINX_CONF' > /etc/nginx/sites-available/scorume
              server {
                  listen 80 default_server;
                  listen [::]:80 default_server;

                  client_max_body_size 50M;

                  # Frontend UI
                  location / {
                      proxy_pass http://127.0.0.1:5173;
                      proxy_http_version 1.1;
                      proxy_set_header Upgrade $http_upgrade;
                      proxy_set_header Connection 'upgrade';
                      proxy_set_header Host $host;
                      proxy_cache_bypass $http_upgrade;
                  }

                  # Backend API
                  location /api/ {
                      proxy_pass http://127.0.0.1:8000/api/;
                      proxy_http_version 1.1;
                      proxy_set_header Host $host;
                      proxy_set_header X-Real-IP $remote_addr;
                      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                      proxy_set_header X-Forwarded-Proto $scheme;
                      proxy_read_timeout 300s;
                      proxy_connect_timeout 300s;
                  }

                  # Backend Health Check
                  location /health {
                      proxy_pass http://127.0.0.1:8000/health;
                  }

                  # Backend Swagger Docs
                  location /docs {
                      proxy_pass http://127.0.0.1:8000/docs;
                      proxy_set_header Host $host;
                  }
                  location /openapi.json {
                      proxy_pass http://127.0.0.1:8000/openapi.json;
                      proxy_set_header Host $host;
                  }
              }
              NGINX_CONF

              rm -f /etc/nginx/sites-enabled/default
              ln -sf /etc/nginx/sites-available/scorume /etc/nginx/sites-enabled/
              systemctl restart nginx

              echo "=== Scorume Bootstrap Completed Successfully ==="
              EOF

  tags = {
    Name = "${var.app_name}-server"
  }
}
