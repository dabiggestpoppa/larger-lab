# XHAAK Phase 3: Hetzner VM Implementation Steps

This document provides detailed implementation steps for deploying XHAAK Phase 3: Genesis Rebirth on Hetzner VM infrastructure, with special attention to the Cerebus Dialectic Brain Mode system integration and addressing known deployment challenges.

## 1. Hetzner Account Setup and CLI Configuration

### 1.1 Account Setup
1. Create a Hetzner Cloud account at https://accounts.hetzner.com/signUp
2. Verify email and set up payment method
3. Create a new project named "XHAAK-Phase3"

### 1.2 API Token Generation
1. Navigate to "Security" > "API Tokens"
2. Create a new token with "Read & Write" permissions
3. Save the token securely (it will only be shown once)

### 1.3 Hetzner CLI Installation and Authentication
```bash
# Install Hetzner CLI
curl -fsSL https://github.com/hetznercloud/cli/releases/latest/download/hcloud-linux-amd64.tar.gz | tar -xzC /usr/local/bin hcloud

# Configure authentication (addressing known authentication issues)
mkdir -p ~/.config/hcloud/
echo "token: YOUR_API_TOKEN" > ~/.config/hcloud/cli.toml
chmod 600 ~/.config/hcloud/cli.toml

# Verify authentication
hcloud server list
```

**Note:** If experiencing authentication issues with Hetzner CLI, try these alternatives:
- Use environment variable: `export HCLOUD_TOKEN=YOUR_API_TOKEN`
- Use direct API calls with curl:
  ```bash
  curl -H "Authorization: Bearer YOUR_API_TOKEN" \
       -H "Content-Type: application/json" \
       https://api.hetzner.cloud/v1/servers
  ```

## 2. Server Provisioning

### 2.1 Create SSH Key
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "xhaak-deployment"

# Add SSH key to Hetzner
hcloud ssh-key create --name xhaak-key --public-key-from-file ~/.ssh/id_ed25519.pub
```

### 2.2 Provision Primary Node (CCX33)
```bash
hcloud server create \
  --name xhaak-primary \
  --type ccx33 \
  --image ubuntu-22.04 \
  --ssh-key xhaak-key \
  --location fsn1 \
  --label "purpose=xhaak-primary"
```

### 2.3 Provision Secondary Nodes (CX32)
```bash
# Agent Node 1 (Browser Ritual Agent)
hcloud server create \
  --name xhaak-agent1 \
  --type cx32 \
  --image ubuntu-22.04 \
  --ssh-key xhaak-key \
  --location fsn1 \
  --label "purpose=xhaak-browser-agent"

# Agent Node 2 (Specialized Agents)
hcloud server create \
  --name xhaak-agent2 \
  --type cx32 \
  --image ubuntu-22.04 \
  --ssh-key xhaak-key \
  --location fsn1 \
  --label "purpose=xhaak-specialized-agents"
```

### 2.4 Create and Configure Network
```bash
# Create private network
hcloud network create --name xhaak-network --ip-range 10.0.0.0/16

# Create subnet
hcloud network add-subnet xhaak-network --network-zone eu-central --type server --ip-range 10.0.0.0/24

# Attach servers to network
hcloud server attach-to-network xhaak-primary --network xhaak-network --ip 10.0.0.2
hcloud server attach-to-network xhaak-agent1 --network xhaak-network --ip 10.0.0.3
hcloud server attach-to-network xhaak-agent2 --network xhaak-network --ip 10.0.0.4
```

### 2.5 Configure Firewall
```bash
# Create firewall
hcloud firewall create --name xhaak-firewall

# Add rules
hcloud firewall add-rule xhaak-firewall --direction in --protocol tcp --port 22 --source-ips 0.0.0.0/0
hcloud firewall add-rule xhaak-firewall --direction in --protocol tcp --port 80 --source-ips 0.0.0.0/0
hcloud firewall add-rule xhaak-firewall --direction in --protocol tcp --port 443 --source-ips 0.0.0.0/0
hcloud firewall add-rule xhaak-firewall --direction in --protocol udp --port 5353 --source-ips 10.0.0.0/16
hcloud firewall add-rule xhaak-firewall --direction in --protocol tcp --port 8000-8100 --source-ips 10.0.0.0/16

# Apply firewall to servers
hcloud firewall apply-to-resource xhaak-firewall --type server --server xhaak-primary
hcloud firewall apply-to-resource xhaak-firewall --type server --server xhaak-agent1
hcloud firewall apply-to-resource xhaak-firewall --type server --server xhaak-agent2
```

## 3. Base System Configuration

### 3.1 Primary Node Setup
```bash
# Connect to server (replace with actual IP)
ssh root@$(hcloud server ip xhaak-primary)

# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y python3-pip python3-venv git nginx certbot python3-certbot-nginx redis-server build-essential supervisor

# Configure hostname and hosts
echo "xhaak-primary" > /etc/hostname
echo "127.0.0.1 localhost" > /etc/hosts
echo "10.0.0.2 xhaak-primary" >> /etc/hosts
echo "10.0.0.3 xhaak-agent1" >> /etc/hosts
echo "10.0.0.4 xhaak-agent2" >> /etc/hosts

# Create XHAAK user
useradd -m -s /bin/bash xhaak
usermod -aG sudo xhaak
echo "xhaak ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/xhaak

# Set up Python environment
su - xhaak
mkdir -p ~/xhaak
cd ~/xhaak
python3 -m venv venv
echo 'source ~/xhaak/venv/bin/activate' >> ~/.bashrc
source ~/xhaak/venv/bin/activate
```

### 3.2 Secondary Nodes Setup
```bash
# Connect to Agent Node 1
ssh root@$(hcloud server ip xhaak-agent1)

# Update system and install dependencies
apt update && apt upgrade -y
apt install -y python3-pip python3-venv git build-essential supervisor

# Configure hostname and hosts
echo "xhaak-agent1" > /etc/hostname
echo "127.0.0.1 localhost" > /etc/hosts
echo "10.0.0.2 xhaak-primary" >> /etc/hosts
echo "10.0.0.3 xhaak-agent1" >> /etc/hosts
echo "10.0.0.4 xhaak-agent2" >> /etc/hosts

# Create XHAAK user
useradd -m -s /bin/bash xhaak
usermod -aG sudo xhaak
echo "xhaak ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/xhaak

# Set up Python environment
su - xhaak
mkdir -p ~/xhaak
cd ~/xhaak
python3 -m venv venv
echo 'source ~/xhaak/venv/bin/activate' >> ~/.bashrc
source ~/xhaak/venv/bin/activate

# Repeat for Agent Node 2 (with appropriate hostname changes)
```

## 4. XHAAK Core Installation

### 4.1 Primary Node Installation
```bash
# Connect as xhaak user
su - xhaak
cd ~/xhaak
source venv/bin/activate

# Clone repository
git clone https://github.com/your-repo/xhaak.git
cd xhaak

# Install dependencies
pip install -r requirements.txt
pip install localagi langgraph pydantic graphiti cognee mem0 memary

# Create data directories
mkdir -p data/chromadb
mkdir -p data/redis
mkdir -p data/archive
mkdir -p config
```

### 4.2 Configure LocalAGI
```bash
cat > ~/xhaak/config/localagi.yaml << EOF
system:
  name: "XHAAK Phase 3"
  version: "3.0.0"
  data_dir: "/home/xhaak/xhaak/data"

agents:
  discovery:
    enabled: true
    method: "zeroconf"
    network: "10.0.0.0/16"
  
  memory:
    primary: "redis"
    vector: "chromadb"
    redis_url: "redis://localhost:6379/0"
    chromadb_path: "/home/xhaak/xhaak/data/chromadb"

protocols:
  fmp:
    enabled: true
  scope:
    enabled: true
  gsp:
    enabled: true
EOF
```

### 4.3 Configure Redis
```bash
# Create Redis configuration
sudo tee /etc/redis/redis.conf > /dev/null << EOF
bind 0.0.0.0
protected-mode yes
port 6379
dir /var/lib/redis
maxmemory 12gb
maxmemory-policy allkeys-lru
appendonly yes
appendfsync everysec
EOF

# Restart Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

### 4.4 Configure ChromaDB
```bash
# Create ChromaDB configuration
mkdir -p ~/xhaak/config/chromadb
cat > ~/xhaak/config/chromadb/chroma.yaml << EOF
chroma_server_host: localhost
chroma_server_http_port: 8000
persist_directory: /home/xhaak/xhaak/data/chromadb
allow_reset: true
anonymized_telemetry: false
EOF
```

## 5. Cerebus Dialectic Brain Mode Implementation

### 5.1 Install AI Model Dependencies
```bash
# Install dependencies for AI model integration
pip install openrouter-py deepseek-ai transformers torch accelerate

# Create model configuration directory
mkdir -p ~/xhaak/config/models
```

### 5.2 Configure Dialectic Brain Mode
```bash
# Create configuration for Cerebus Dialectic Brain Mode
cat > ~/xhaak/config/cerebus.yaml << EOF
system:
  name: "Cerebus Dialectic Brain Mode"
  version: "1.0.0"

models:
  primary_reasoner:
    provider: "openrouter"
    model_id: "deepseek/deepseek-chat-v3-0324"
    api_key: "${OPENROUTER_API_KEY}"
    temperature: 0.7
    max_tokens: 4096
  
  devils_advocate:
    provider: "openrouter"
    model_id: "deepseek/deepseek-r1-zero:free"
    api_key: "${OPENROUTER_API_KEY}"
    temperature: 0.9
    max_tokens: 4096

dialectic:
  max_iterations: 5
  convergence_threshold: 0.85
  synthesis_method: "weighted_merge"
EOF
```

### 5.3 Create SystemD Services for Cerebus

```bash
# Create service for API Gateway
sudo tee /etc/systemd/system/xhaak-api-gateway.service > /dev/null << EOF
[Unit]
Description=XHAAK API Gateway
After=network.target
Wants=redis-server.service

[Service]
User=xhaak
WorkingDirectory=/home/xhaak/xhaak
ExecStart=/home/xhaak/xhaak/venv/bin/python -m xhaak.services.api_gateway
Environment="OPENROUTER_API_KEY=${OPENROUTER_API_KEY}"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create service for Prompt Router
sudo tee /etc/systemd/system/xhaak-prompt-router.service > /dev/null << EOF
[Unit]
Description=XHAAK Prompt Router
After=network.target xhaak-api-gateway.service
Wants=redis-server.service

[Service]
User=xhaak
WorkingDirectory=/home/xhaak/xhaak
ExecStart=/home/xhaak/xhaak/venv/bin/python -m xhaak.services.prompt_router
Environment="OPENROUTER_API_KEY=${OPENROUTER_API_KEY}"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create service for Memory Core
sudo tee /etc/systemd/system/xhaak-memory-core.service > /dev/null << EOF
[Unit]
Description=XHAAK Memory Core
After=network.target
Wants=redis-server.service

[Service]
User=xhaak
WorkingDirectory=/home/xhaak/xhaak
ExecStart=/home/xhaak/xhaak/venv/bin/python -m xhaak.services.memory_core
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create service for Meta-Cognitive Layer
sudo tee /etc/systemd/system/xhaak-metacognitive.service > /dev/null << EOF
[Unit]
Description=XHAAK Meta-Cognitive Layer
After=network.target xhaak-memory-core.service
Wants=redis-server.service

[Service]
User=xhaak
WorkingDirectory=/home/xhaak/xhaak
ExecStart=/home/xhaak/xhaak/venv/bin/python -m xhaak.services.metacognitive
Environment="OPENROUTER_API_KEY=${OPENROUTER_API_KEY}"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create service for DEP Interface
sudo tee /etc/systemd/system/xhaak-dep-interface.service > /dev/null << EOF
[Unit]
Description=XHAAK DEP Interface
After=network.target xhaak-api-gateway.service
Wants=redis-server.service

[Service]
User=xhaak
WorkingDirectory=/home/xhaak/xhaak
ExecStart=/home/xhaak/xhaak/venv/bin/python -m xhaak.services.dep_interface
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create service for Fractal Archive
sudo tee /etc/systemd/system/xhaak-fractal-archive.service > /dev/null << EOF
[Unit]
Description=XHAAK Fractal Archive
After=network.target xhaak-memory-core.service
Wants=redis-server.service

[Service]
User=xhaak
WorkingDirectory=/home/xhaak/xhaak
ExecStart=/home/xhaak/xhaak/venv/bin/python -m xhaak.services.fractal_archive
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create service for Task Queue
sudo tee /etc/systemd/system/xhaak-task-queue.service > /dev/null << EOF
[Unit]
Description=XHAAK Task Queue
After=network.target xhaak-api-gateway.service
Wants=redis-server.service

[Service]
User=xhaak
WorkingDirectory=/home/xhaak/xhaak
ExecStart=/home/xhaak/xhaak/venv/bin/python -m xhaak.services.task_queue
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable services
sudo systemctl daemon-reload
sudo systemctl enable xhaak-api-gateway.service
sudo systemctl enable xhaak-prompt-router.service
sudo systemctl enable xhaak-memory-core.service
sudo systemctl enable xhaak-metacognitive.service
sudo systemctl enable xhaak-dep-interface.service
sudo systemctl enable xhaak-fractal-archive.service
sudo systemctl enable xhaak-task-queue.service
```

## 6. Browser Ritual Agent Setup (Agent Node 1)

### 6.1 Install Browser Dependencies
```bash
# Connect to Agent Node 1
ssh root@$(hcloud server ip xhaak-agent1)
su - xhaak
cd ~/xhaak
source venv/bin/activate

# Install browser dependencies
sudo apt install -y chromium-browser xvfb
pip install selenium webdriver-manager playwright

# Install Playwright browsers
playwright install chromium
```

### 6.2 Configure Browser Ritual Agent
```bash
# Create configuration directory
mkdir -p ~/xhaak/config

# Create Browser Ritual Agent configuration
cat > ~/xhaak/config/browser_agent.yaml << EOF
system:
  name: "XHAAK Browser Ritual Agent"
  version: "1.0.0"
  primary_node: "10.0.0.2"

browser:
  type: "playwright"
  headless: true
  browser: "chromium"
  timeout: 30000
  user_agent: "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

rituals:
  schema_path: "/home/xhaak/xhaak/config/ritual_schemas"
  results_path: "/home/xhaak/xhaak/data/ritual_results"

gsp:
  enabled: true
  discovery_method: "zeroconf"
  network: "10.0.0.0/16"
EOF

# Create ritual schemas directory
mkdir -p ~/xhaak/config/ritual_schemas
mkdir -p ~/xhaak/data/ritual_results
```

### 6.3 Create Browser Ritual Agent Service
```bash
# Create service file
sudo tee /etc/systemd/system/xhaak-browser-agent.service > /dev/null << EOF
[Unit]
Description=XHAAK Browser Ritual Agent
After=network.target

[Service]
User=xhaak
WorkingDirectory=/home/xhaak/xhaak
ExecStart=/home/xhaak/xhaak/venv/bin/python -m xhaak.browser.agent --config /home/xhaak/xhaak/config/browser_agent.yaml
Environment="DISPLAY=:99"
ExecStartPre=/usr/bin/Xvfb :99 -screen 0 1920x1080x24 -ac
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable xhaak-browser-agent.service
```

## 7. Specialized Agents Setup (Agent Node 2)

### 7.1 Configure Specialized Agents
```bash
# Connect to Agent Node 2
ssh root@$(hcloud server ip xhaak-agent2)
su - xhaak
cd ~/xhaak
source venv/bin/activate

# Create configuration directory
mkdir -p ~/xhaak/config
mkdir -p ~/xhaak/data/archive

# Create Specialized Agents configuration
cat > ~/xhaak/config/specialized_agents.yaml << EOF
system:
  name: "XHAAK Specialized Agents"
  version: "1.0.0"
  primary_node: "10.0.0.2"

agents:
  fractal_archive:
    enabled: true
    path: "/home/xhaak/xhaak/data/archive"
  
  specialized_group:
    enabled: true
    agents:
      - name: "science_agent"
        type: "domain_specialist"
        domain: "science"
      - name: "creative_agent"
        type: "domain_specialist"
        domain: "creative"
      - name: "logic_agent"
        type: "domain_specialist"
        domain: "logic"

gsp:
  enabled: true
  discovery_method: "zeroconf"
  network: "10.0.0.0/16"
EOF
```

### 7.2 Create Specialized Agents Service
```bash
# Create service file
sudo tee /etc/systemd/system/xhaak-specialized-agents.service > /dev/null << EOF
[Unit]
Description=XHAAK Specialized Agents
After=network.target

[Service]
User=xhaak
WorkingDirectory=/home/xhaak/xhaak
ExecStart=/home/xhaak/xhaak/venv/bin/python -m xhaak.agents.specialized --config /home/xhaak/xhaak/config/specialized_agents.yaml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable xhaak-specialized-agents.service
```

## 8. CLI Tool Installation

### 8.1 Install xhaakctl on Primary Node
```bash
# Connect to Primary Node
ssh root@$(hcloud server ip xhaak-primary)
su - xhaak
cd ~/xhaak
source venv/bin/activate

# Install CLI tool
cd xhaak
pip install -e .

# Create configuration directory
mkdir -p ~/.xhaak

# Create CLI configuration
cat > ~/.xhaak/config.yaml << EOF
primary_node: "http://xhaak-primary:8000"
agent_nodes:
  - "http://xhaak-agent1:8000"
  - "http://xhaak-agent2:8000"
EOF
```

### 8.2 Create xhaakctl Bash Completion
```bash
# Generate bash completion script
xhaakctl completion bash > ~/.xhaak/xhaakctl-completion.bash

# Add to bashrc
echo 'source ~/.xhaak/xhaakctl-completion.bash' >> ~/.bashrc
```

## 9. Nginx Configuration for API Gateway

### 9.1 Configure Nginx on Primary Node
```bash
# Create Nginx configuration
sudo tee /etc/nginx/sites-available/xhaak-api.conf > /dev/null << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/xhaak-api.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 9.2 Set Up SSL with Let's Encrypt (Optional)
```bash
# If you have a domain pointed to your server
sudo certbot --nginx -d your-domain.com
```

## 10. Starting Services

### 10.1 Start Primary Node Services
```bash
# Start services in order
sudo systemctl start xhaak-api-gateway
sudo systemctl start xhaak-memory-core
sudo systemctl start xhaak-prompt-router
sudo systemctl start xhaak-metacognitive
sudo systemctl start xhaak-dep-interface
sudo systemctl start xhaak-fractal-archive
sudo systemctl start xhaak-task-queue

# Check status
sudo systemctl status xhaak-*
```

### 10.2 Start Agent Node Services
```bash
# On Agent Node 1
sudo systemctl start xhaak-browser-agent
sudo systemctl status xhaak-browser-agent

# On Agent Node 2
sudo systemctl start xhaak-specialized-agents
sudo systemctl status xhaak-specialized-agents
```

## 11. Verification and Testing

### 11.1 Verify API Gateway
```bash
# Test API Gateway
curl http://localhost:8000/api/health

# Expected response: {"status":"ok","version":"3.0.0"}
```

### 11.2 Test GSP Communication
```bash
# List all agents
xhaakctl list-agents

# Scan mesh
xhaakctl scan-mesh

# Send test glyph
xhaakctl glyphcast "test_intent"
```

### 11.3 Test Cerebus Dialectic Brain Mode
```bash
# Send test dialectic query
curl -X POST http://localhost:8000/api/dialectic/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the benefits and drawbacks of artificial general intelligence?", "max_iterations": 3}'
```

### 11.4 Test Browser Ritual Agent
```bash
# Create test ritual
cat > ~/test-ritual.json << EOF
{
  "site_url": "https://example.com",
  "navigation_flow": [
    {
      "type": "wait",
      "duration": 2
    }
  ],
  "target_actions": [
    {
      "type": "scrape",
      "selector": "body"
    }
  ],
  "completion_conditions": {
    "element_exists": "body"
  }
}
EOF

# Send ritual to agent
curl -X POST http://localhost:8000/api/browser/ritual \
  -H "Content-Type: application/json" \
  -d @~/test-ritual.json
```

## 12. Troubleshooting Common Issues

### 12.1 Hetzner CLI Authentication Issues
If experiencing authentication issues with Hetzner CLI:
```bash
# Check if token is correctly set
cat ~/.config/hcloud/cli.toml

# Try using environment variable instead
export HCLOUD_TOKEN=YOUR_API_TOKEN
hcloud server list

# Verify API token permissions in Hetzner Cloud Console
```

### 12.2 Network Connectivity Issues
If nodes cannot communicate:
```bash
# Check network configuration
hcloud network list
hcloud network describe xhaak-network

# Verify firewall rules
hcloud firewall describe xhaak-firewall

# Test connectivity between nodes
ping 10.0.0.2  # From agent nodes
ping 10.0.0.3  # From primary node
```

### 12.3 Service Startup Issues
If services fail to start:
```bash
# Check service logs
sudo journalctl -u xhaak-api-gateway -n 100
sudo journalctl -u xhaak-memory-core -n 100

# Check for Python dependency issues
source ~/xhaak/venv/bin/activate
pip list | grep -E 'localagi|langgraph|pydantic|graphiti|cognee|mem0|memary'

# Verify file permissions
sudo chown -R xhaak:xhaak ~/xhaak
```

### 12.4 AI Model Integration Issues
If experiencing issues with AI models:
```bash
# Verify API keys are set
echo $OPENROUTER_API_KEY

# Test API access
curl -X POST https://openrouter.ai/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -d '{
    "model": "deepseek/deepseek-chat-v3-0324",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

## 13. Maintenance Procedures

### 13.1 Backup Configuration
```bash
# Create backup script
cat > ~/xhaak/scripts/backup.sh << EOF
#!/bin/bash

BACKUP_DIR="/home/xhaak/backups"
DATE=\$(date +%Y%m%d)

mkdir -p \$BACKUP_DIR

# Backup Redis
redis-cli save
sudo cp /var/lib/redis/dump.rdb \$BACKUP_DIR/redis_\$DATE.rdb

# Backup ChromaDB
tar -czf \$BACKUP_DIR/chromadb_\$DATE.tar.gz -C /home/xhaak/xhaak/data chromadb

# Backup Configuration
tar -czf \$BACKUP_DIR/config_\$DATE.tar.gz -C /home/xhaak/xhaak config

# Rotate backups (keep last 7 days)
find \$BACKUP_DIR -name "*.tar.gz" -type f -mtime +7 -delete
find \$BACKUP_DIR -name "*.rdb" -type f -mtime +7 -delete
EOF

chmod +x ~/xhaak/scripts/backup.sh

# Schedule daily backups
(crontab -l 2>/dev/null; echo "0 2 * * * /home/xhaak/xhaak/scripts/backup.sh") | crontab -
```

### 13.2 System Updates
```bash
# Create update script
cat > ~/xhaak/scripts/update.sh << EOF
#!/bin/bash

# Update system packages
sudo apt update && sudo apt upgrade -y

# Update XHAAK repository
cd ~/xhaak/xhaak
git pull

# Update Python dependencies
source ~/xhaak/venv/bin/activate
pip install -r requirements.txt --upgrade

# Restart services
sudo systemctl restart xhaak-*
EOF

chmod +x ~/xhaak/scripts/update.sh
```

## 14. Monitoring Setup

### 14.1 Install Prometheus and Grafana
```bash
# Install Prometheus
sudo apt install -y prometheus

# Configure Prometheus
sudo tee /etc/prometheus/prometheus.yml > /dev/null << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'xhaak'
    static_configs:
      - targets: ['localhost:8000', 'xhaak-agent1:8000', 'xhaak-agent2:8000']
EOF

sudo systemctl restart prometheus
sudo systemctl enable prometheus

# Install Grafana
sudo apt-get install -y apt-transport-https software-properties-common
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
sudo apt-get update
sudo apt-get install -y grafana

sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

### 14.2 Configure Grafana Dashboard
```bash
# Access Grafana at http://<primary-node-ip>:3000
# Default login: admin/admin
# Add Prometheus as a data source (http://localhost:9090)
# Import XHAAK dashboard template (if available)
```

## 15. Security Hardening

### 15.1 Secure SSH Access
```bash
# Edit SSH configuration
sudo nano /etc/ssh/sshd_config

# Make these changes:
# PermitRootLogin no
# PasswordAuthentication no
# PubkeyAuthentication yes

# Restart SSH
sudo systemctl restart sshd
```

### 15.2 Enable Automatic Security Updates
```bash
# Install unattended-upgrades
sudo apt install -y unattended-upgrades apt-listchanges

# Configure automatic updates
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 15.3 Set Up Fail2Ban
```bash
# Install Fail2Ban
sudo apt install -y fail2ban

# Create configuration
sudo tee /etc/fail2ban/jail.local > /dev/null << EOF
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 5
bantime = 3600
EOF

# Restart Fail2Ban
sudo systemctl restart fail2ban
sudo systemctl enable fail2ban
```

## 16. Final Verification

### 16.1 Complete System Test
```bash
# Check all services
sudo systemctl status xhaak-*

# Test API endpoints
curl http://localhost:8000/api/health
curl http://localhost:8000/api/agents/list
curl http://localhost:8000/api/protocols/status

# Test CLI tool
xhaakctl list-agents
xhaakctl scan-mesh
xhaakctl audit-cod
```

### 16.2 Verify Cerebus Dialectic Brain Mode
```bash
# Test dialectic reasoning
curl -X POST http://localhost:8000/api/dialectic/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the philosophical implications of artificial consciousness?",
    "max_iterations": 3
  }'
```

### 16.3 Verify Browser Ritual Agent
```bash
# Test browser ritual execution
curl -X POST http://localhost:8000/api/browser/ritual \
  -H "Content-Type: application/json" \
  -d '{
    "site_url": "https://example.com",
    "navigation_flow": [{"type": "wait", "duration": 2}],
    "target_actions": [{"type": "scrape", "selector": "body"}],
    "completion_conditions": {"element_exists": "body"}
  }'
```

This implementation guide provides detailed steps for deploying XHAAK Phase 3: Genesis Rebirth on Hetzner VM infrastructure, with special attention to the Cerebus Dialectic Brain Mode system integration. By following these steps, you can establish a distributed, field-based architecture that aligns with XHAAK's philosophical foundations while leveraging Hetzner's cost-effective and scalable VM offerings.
