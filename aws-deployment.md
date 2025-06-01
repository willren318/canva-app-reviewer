# AWS Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the Canva App Reviewer to AWS using Docker containers, ECS, and supporting services.

## Architecture

```
Internet Gateway
       │
   Load Balancer (ALB)
       │
   ┌───┴───┐
   │  ECS  │
   │Cluster│
   └───┬───┘
       │
┌──────┼──────┐
│ Frontend    │ Backend │
│ (Next.js)   │(FastAPI)│
│   :3000     │  :8000  │
└─────────────┴─────────┘
       │
   RDS/S3 (optional)
```

## Prerequisites

1. **AWS CLI configured** with appropriate permissions
2. **Docker** installed locally
3. **Claude API Key** from Anthropic
4. **Domain name** (optional, for custom domain)

## Deployment Options

### Option 1: ECS with Fargate (Recommended)

#### 1. Create ECR Repositories

```bash
# Create repositories for both services
aws ecr create-repository --repository-name canva-app-reviewer/frontend
aws ecr create-repository --repository-name canva-app-reviewer/backend

# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
```

#### 2. Build and Push Images

```bash
# Build backend image
cd backend
docker build -t canva-app-reviewer/backend .
docker tag canva-app-reviewer/backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/canva-app-reviewer/backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/canva-app-reviewer/backend:latest

# Build frontend image
cd ../frontend
docker build -t canva-app-reviewer/frontend .
docker tag canva-app-reviewer/frontend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/canva-app-reviewer/frontend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/canva-app-reviewer/frontend:latest
```

#### 3. Create ECS Task Definition

Create `ecs-task-definition.json`:

```json
{
  "family": "canva-app-reviewer",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::<account-id>:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::<account-id>:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/canva-app-reviewer/backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        },
        {
          "name": "LOG_LEVEL",
          "value": "INFO"
        }
      ],
      "secrets": [
        {
          "name": "CLAUDE_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<account-id>:secret:claude-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/canva-app-reviewer",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "backend"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    },
    {
      "name": "frontend",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/canva-app-reviewer/frontend:latest",
      "portMappings": [
        {
          "containerPort": 3000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "NODE_ENV",
          "value": "production"
        },
        {
          "name": "NEXT_PUBLIC_API_URL",
          "value": "http://localhost:8000"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/canva-app-reviewer",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "frontend"
        }
      },
      "dependsOn": [
        {
          "containerName": "backend",
          "condition": "HEALTHY"
        }
      ]
    }
  ]
}
```

#### 4. Create ECS Service

```bash
# Register task definition
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# Create ECS cluster
aws ecs create-cluster --cluster-name canva-app-reviewer

# Create service
aws ecs create-service \
  --cluster canva-app-reviewer \
  --service-name canva-app-reviewer-service \
  --task-definition canva-app-reviewer \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345,subnet-67890],securityGroups=[sg-12345],assignPublicIp=ENABLED}" \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:<account-id>:targetgroup/canva-app-reviewer/1234567890,containerName=frontend,containerPort=3000
```

### Option 2: EC2 with SSH Deployment (Simple & Direct)

This method provides full control and is perfect for development, staging, or small production deployments.

#### Step 1: Create SSH Key Pair

```bash
# Generate SSH key pair locally
ssh-keygen -t rsa -b 4096 -f ~/.ssh/canva-app-reviewer-key -C "canva-app-reviewer-deployment"

# Set correct permissions
chmod 600 ~/.ssh/canva-app-reviewer-key
chmod 644 ~/.ssh/canva-app-reviewer-key.pub

# Display public key (copy this for AWS)
cat ~/.ssh/canva-app-reviewer-key.pub
```

#### Step 2: Launch EC2 Instance via AWS Console

**2.1. Create Security Group**

1. **Navigate to EC2 Dashboard**
   - Log into AWS Console: https://console.aws.amazon.com
   - Search for "EC2" in the top search bar
   - Click on "EC2" to open the EC2 Dashboard

2. **Create Security Group**
   - In the left sidebar, click **"Security Groups"** under "Network & Security"
   - Click **"Create security group"** button
   - Fill in the details:
     - **Security group name**: `canva-app-reviewer-sg`
     - **Description**: `Security group for Canva App Reviewer`
     - **VPC**: Select your default VPC (or preferred VPC)

3. **Add Inbound Rules**
   - In the "Inbound rules" section, click **"Add rule"** for each of the following:
   
   | Type | Protocol | Port Range | Source | Description |
   |------|----------|------------|--------|-------------|
   | SSH | TCP | 22 | 0.0.0.0/0 | SSH access |
   | HTTP | TCP | 80 | 0.0.0.0/0 | HTTP traffic |
   | HTTPS | TCP | 443 | 0.0.0.0/0 | HTTPS traffic |
   | Custom TCP | TCP | 3000 | 0.0.0.0/0 | Frontend (temporary) |
   | Custom TCP | TCP | 8000 | 0.0.0.0/0 | Backend (temporary) |

   - Click **"Create security group"**

**2.2. Import SSH Key Pair**

1. **Navigate to Key Pairs**
   - In the left sidebar, click **"Key Pairs"** under "Network & Security"
   - Click **"Import key pair"** button

2. **Import Your Key**
   - **Name**: `canva-app-reviewer-key`
   - **Key pair file**: Click "Browse" and select your `canva-app-reviewer-key.pub` file
   - OR **Public key contents**: Copy and paste the contents of your `.pub` file
   - Click **"Import key pair"**

**2.3. Launch EC2 Instance**

1. **Start Instance Launch**
   - Go back to EC2 Dashboard
   - Click **"Launch instance"** button

2. **Configure Instance Details**
   
   **Step 1: Name and Tags**
   - **Name**: `canva-app-reviewer`
   - Add additional tags if needed (optional)

   **Step 2: Application and OS Images**
   - **AMI**: Select **"Amazon Linux 2023 AMI (HVM), SSD Volume Type"**
   - Architecture: **64-bit (x86)**

   **Step 3: Instance Type**
   - **Instance type**: `t3.medium` (2 vCPU, 4 GiB Memory)
   - For testing: `t3.small` or `t2.micro` (if eligible for free tier)

   **Step 4: Key Pair**
   - **Key pair name**: Select `canva-app-reviewer-key` (the one you imported)

   **Step 5: Network Settings**
   - Click **"Edit"** next to Network settings
   - **VPC**: Select your default VPC
   - **Subnet**: Select any available subnet (or leave as default)
   - **Auto-assign public IP**: **Enable**
   - **Firewall (security groups)**: Select **"Select existing security group"**
   - Choose `canva-app-reviewer-sg` from the dropdown

   **Step 6: Configure Storage**
   - **Root volume**: 
     - **Size**: `20 GiB` (minimum recommended)
     - **Volume type**: `gp3` (for better performance)
     - **Delete on termination**: ✅ Checked

   **Step 7: Advanced Details** (Optional)
   - Leave most settings as default
   - **User data** (optional): You can add the server setup script here to automate initial setup

3. **Review and Launch**
   - Review all settings in the **"Summary"** panel on the right
   - Click **"Launch instance"**

4. **Verify Instance Launch**
   - You'll see a success message with your instance ID
   - Click **"View all instances"** to see your new instance
   - Wait for **Instance State** to change from "Pending" to "Running"
   - Wait for **Status check** to show "2/2 checks passed"

**2.4. Get Instance Connection Details**

1. **Find Your Instance**
   - In the EC2 Dashboard, click **"Instances"** in the left sidebar
   - Find your `canva-app-reviewer` instance

2. **Get Public IP Address**
   - Select your instance by clicking the checkbox
   - In the details panel below, copy the **"Public IPv4 address"**
   - Save this IP address - you'll need it for SSH connection

3. **Test SSH Connection**
   ```bash
   # Replace YOUR_INSTANCE_IP with the actual IP address
   export INSTANCE_IP=YOUR_INSTANCE_IP
   echo "Instance IP: $INSTANCE_IP"
   
   # Test SSH connection (Amazon Linux uses ec2-user)
   ssh -i ~/.ssh/canva-app-reviewer-key ec2-user@$INSTANCE_IP
   ```

**2.5. Optional: Create Elastic IP (Recommended for Production)**

If you want a permanent IP address that won't change if you restart the instance:

1. **Allocate Elastic IP**
   - In EC2 Dashboard, click **"Elastic IPs"** under "Network & Security"
   - Click **"Allocate Elastic IP address"**
   - Click **"Allocate"**

2. **Associate with Instance**
   - Select the newly created Elastic IP
   - Click **"Actions"** → **"Associate Elastic IP address"**
   - **Resource type**: Instance
   - **Instance**: Select your `canva-app-reviewer` instance
   - Click **"Associate"**

3. **Update Your DNS/Domain**
   - Use the Elastic IP address for your domain's A record
   - This ensures your domain always points to the same IP

**AWS Console Alternative Commands Reference:**
```bash
# If you prefer CLI, here are the equivalent commands:

# Create security group
aws ec2 create-security-group \
  --group-name canva-app-reviewer-sg \
  --description "Security group for Canva App Reviewer" \
  --vpc-id vpc-xxxxxxxx

# Add security group rules (repeat for each port)
aws ec2 authorize-security-group-ingress \
  --group-name canva-app-reviewer-sg \
  --protocol tcp --port 22 --cidr 0.0.0.0/0

# Import SSH key
aws ec2 import-key-pair \
  --key-name canva-app-reviewer-key \
  --public-key-material fileb://~/.ssh/canva-app-reviewer-key.pub

# Launch instance
aws ec2 run-instances \
  --image-id ami-0230bd60aa48260c6 \
  --count 1 \
  --instance-type t3.medium \
  --key-name canva-app-reviewer-key \
  --security-group-ids sg-xxxxxxxxx \
  --subnet-id subnet-xxxxxxxxx \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=canva-app-reviewer}]' \
  --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":20,"VolumeType":"gp3"}}]'
```

#### Step 3: Connect to EC2 via SSH

```bash
# Get instance public IP
export INSTANCE_IP=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=canva-app-reviewer" "Name=instance-state-name,Values=running" \
  --query "Reservations[0].Instances[0].PublicIpAddress" \
  --output text)

echo "Instance IP: $INSTANCE_IP"

# Connect via SSH
ssh -i ~/.ssh/canva-app-reviewer-key ec2-user@$INSTANCE_IP

# Add to SSH config for easier access (optional)
cat >> ~/.ssh/config << EOF
Host canva-app-reviewer
    HostName $INSTANCE_IP
    User ec2-user
    IdentityFile ~/.ssh/canva-app-reviewer-key
    ServerAliveInterval 60
EOF

# Now you can connect with: ssh canva-app-reviewer
```

#### Step 4: Server Setup via SSH

Once connected to your EC2 instance:

```bash
# Update system (Amazon Linux uses yum)
sudo yum update -y

# Install required packages (curl-minimal is pre-installed and sufficient)
sudo yum install -y \
  git \
  docker \
  nginx \
  htop \
  unzip \
  python3 \
  python3-pip \
  wget

# Note: curl-minimal is already installed and sufficient for our needs
# No need to install full curl package which conflicts with system packages

# Install Node.js (using wget instead of curl to avoid conflicts)
wget -qO- https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo yum install -y nodejs

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user

# Install Docker Compose (using wget instead of curl)
sudo wget -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -O /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version
node --version
npm --version
curl --version  # curl-minimal is sufficient

# Logout and login again to apply docker group changes
exit
```

#### Step 5: Deploy Application via SSH

```bash
# Reconnect to EC2
ssh canva-app-reviewer

# Clone your repository
git clone https://github.com/your-username/canva-app-reviewer.git
cd canva-app-reviewer

# Create production environment file with your Claude API key
cat > .env << EOF
# Backend Environment Variables
CLAUDE_API_KEY={your-claude-api-key}
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE=10485760
SUPPORTED_FILE_TYPES=.js,.jsx,.tsx,.ts
LOG_LEVEL=INFO
ENVIRONMENT=production

# Frontend Environment Variables  
NODE_ENV=production
EOF

# Your existing docker-compose.yml is perfect! Just need to update the frontend API URL
# Update NEXT_PUBLIC_API_URL to use external IP for production
sed -i "s|NEXT_PUBLIC_API_URL=http://backend:8000|NEXT_PUBLIC_API_URL=http://$INSTANCE_IP:8000|g" docker-compose.yml

# Optional: Create nginx.conf if you want to use the nginx service
cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream frontend {
        server frontend:3000;
    }
    
    upstream backend {
        server backend:8000;
    }

    server {
        listen 80;
        server_name _;

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
        }

        # Backend API
        location /api/ {
            proxy_pass http://backend/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Backend docs
        location /docs {
            proxy_pass http://backend/docs;
        }

        # Health check
        location /health {
            proxy_pass http://backend/health;
        }
    }
}
EOF

# Build and start services using your existing docker-compose.yml
# Option 1: Without nginx (direct access to frontend:3000 and backend:8000)
docker-compose up --build -d backend frontend

# Option 2: With nginx reverse proxy (all traffic through port 80)
# docker-compose --profile production up --build -d

# Check service status
docker-compose ps
```

#### Step 6: Verify Deployment

```bash
# Check if services are running
docker ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:3000

# Test from external
curl http://$INSTANCE_IP/health
curl http://$INSTANCE_IP/

# Monitor system resources
htop
```

#### Step 7: SSL Setup (Optional but Recommended)

```bash
# Install Certbot for Let's Encrypt SSL (Amazon Linux)
sudo yum install -y certbot python3-certbot-nginx

# Alternative: Install Certbot via pip if yum version is not available
# sudo pip3 install certbot certbot-nginx

# Stop nginx temporarily
docker-compose -f docker-compose.prod.yml stop nginx

# Get SSL certificate (replace your-domain.com)
sudo certbot certonly --standalone -d your-domain.com
```

## SSH Management & Maintenance

### Daily Operations

```bash
# Connect to server
ssh canva-app-reviewer

# Check application status
cd ~/canva-app-reviewer
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs --tail=100 -f backend
docker-compose -f docker-compose.prod.yml logs --tail=100 -f frontend

# Update application
git pull origin main
docker-compose -f docker-compose.prod.yml up --build -d

# Restart services
docker-compose -f docker-compose.prod.yml restart backend
docker-compose -f docker-compose.prod.yml restart frontend

# Clean up Docker resources
docker system prune -f
docker image prune -f
```

### Monitoring via SSH

```bash
# System monitoring
htop                    # Interactive process viewer
df -h                  # Disk usage
free -h                # Memory usage
iostat 1 5             # I/O statistics
netstat -tulpn         # Network connections

# Application monitoring
docker stats           # Container resource usage
docker-compose -f docker-compose.prod.yml logs --tail=100 backend
docker-compose -f docker-compose.prod.yml logs --tail=100 frontend

# Check specific endpoints
curl -s http://localhost:8000/health | jq
curl -s http://localhost:3000/api/health | jq
```

### Backup via SSH

```bash
# Create backup directory
mkdir -p ~/backups/$(date +%Y%m%d)

# Backup application data
tar -czf ~/backups/$(date +%Y%m%d)/uploads.tar.gz uploads/
tar -czf ~/backups/$(date +%Y%m%d)/debug_screenshots.tar.gz debug_screenshots/

# Backup configuration
cp .env ~/backups/$(date +%Y%m%d)/
cp docker-compose.prod.yml ~/backups/$(date +%Y%m%d)/
cp nginx.conf ~/backups/$(date +%Y%m%d)/

# Automated backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="$HOME/backups/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Creating backup in $BACKUP_DIR..."
tar -czf "$BACKUP_DIR/app-data.tar.gz" uploads/ debug_screenshots/
cp .env docker-compose.prod.yml nginx.conf "$BACKUP_DIR/"

# Keep only last 7 days of backups
find $HOME/backups -type d -mtime +7 -exec rm -rf {} +

echo "Backup completed: $BACKUP_DIR"
EOF

chmod +x backup.sh

# Schedule daily backups
crontab -e
# Add: 0 2 * * * /home/ec2-user/canva-app-reviewer/backup.sh
```

### Security Best Practices for SSH

```bash
# 1. Disable password authentication (SSH keys only)
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# 2. Change default SSH port (optional)
sudo sed -i 's/#Port 22/Port 2222/' /etc/ssh/sshd_config
sudo systemctl restart sshd
# Update security group to allow port 2222 instead of 22

# 3. Install fail2ban for intrusion prevention (Amazon Linux)
sudo yum install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# 4. Setup firewall (Amazon Linux uses firewalld)
sudo systemctl start firewalld
sudo systemctl enable firewalld
sudo firewall-cmd --permanent --add-port=22/tcp      # SSH
sudo firewall-cmd --permanent --add-port=80/tcp      # HTTP
sudo firewall-cmd --permanent --add-port=443/tcp     # HTTPS
sudo firewall-cmd --reload

# 5. Automatic security updates (Amazon Linux)
sudo yum install -y yum-cron
sudo systemctl enable yum-cron
sudo systemctl start yum-cron
```

### Troubleshooting SSH Deployment

#### Connection Issues
```bash
# Test SSH connectivity
ssh -v -i ~/.ssh/canva-app-reviewer-key ec2-user@$INSTANCE_IP

# Check security group rules
aws ec2 describe-security-groups --group-names canva-app-reviewer-sg

# Verify instance is running
aws ec2 describe-instances --filters "Name=tag:Name,Values=canva-app-reviewer"
```

#### Application Issues
```bash
# Check Docker daemon
sudo systemctl status docker

# Check container logs
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs frontend

# Check ports
sudo netstat -tulpn | grep -E ':(3000|8000|80|443)'

# Check disk space
df -h

# Check memory usage
free -h

# Restart services
docker-compose -f docker-compose.prod.yml restart
```

#### Performance Issues
```bash
# Monitor real-time resource usage
htop

# Check I/O wait times
iostat -x 1

# Monitor Docker containers
docker stats

# Check for high-memory processes
ps aux --sort=-%mem | head -10

# Check for high-CPU processes
ps aux --sort=-%cpu | head -10
```

## Environment Variables

### Backend
- `CLAUDE_API_KEY`: Your Anthropic Claude API key
- `UPLOAD_DIR`: Directory for file uploads (default: /app/uploads)
- `MAX_FILE_SIZE`: Maximum file size in bytes (default: 10485760)
- `