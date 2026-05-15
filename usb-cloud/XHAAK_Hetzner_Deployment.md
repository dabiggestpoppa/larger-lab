# XHAAK Phase 3: Hetzner VM Deployment Integration

This document integrates the Hetzner VM deployment details with the XHAAK Phase 3: Genesis Rebirth architecture, ensuring that the field-based design principles are preserved while leveraging Hetzner's infrastructure capabilities.

## 1. Hetzner Infrastructure for XHAAK

### 1.1 Infrastructure Architecture

XHAAK Phase 3 will be deployed on Hetzner Cloud infrastructure using a multi-server architecture that aligns with the field-based design:

**Primary Node (Coordinator):**
- **Server Type:** CCX33 (Dedicated vCPU)
- **Specifications:** 8 vCPUs, 32 GB RAM, 240 GB NVMe SSD
- **Monthly Cost:** $54.09
- **Purpose:** Hosts core protocols, coordination services, and primary memory systems

**Secondary Nodes (Swarm Agents):**
- **Server Type:** 2x CX32 (Shared vCPU Intel)
- **Specifications:** 4 vCPUs, 8 GB RAM, 80 GB NVMe SSD (each)
- **Monthly Cost:** $7.59 each ($15.18 total)
- **Purpose:** Host distributed agents and specialized services

**Total Monthly Infrastructure Cost:** $69.27

### 1.2 Architecture Diagram

```mermaid
graph TD
    subgraph "Primary Node (CCX33)"
        A[API Gateway] --> B[LocalAGI Core]
        B --> C[Redis Memory]
        B --> D[ChromaDB Vector Store]
        B --> E[FMP Protocol Engine]
        B --> F[SCOPE Protocol Engine]
        B --> G[GSP Protocol Engine]
    end
    
    subgraph "Secondary Node 1 (CX32)"
        H[Browser Ritual Agent] --> I[Browser Ritual Executor]
        J[Specialized Agents Group 1]
    end
    
    subgraph "Secondary Node 2 (CX32)"
        K[Specialized Agents Group 2]
        L[Fractal Archive]
    end
    
    B <--> H
    B <--> J
    B <--> K
    D <--> L
```

## 2. Mapping XHAAK Components to Hetzner VMs

### 2.1 Component Distribution

| XHAAK Component | Hetzner VM | Specifications | Justification |
|-----------------|------------|----------------|---------------|
| Core Protocols (FMP, SCOPE) | Primary Node (CCX33) | 8 vCPUs, 32 GB RAM, 240 GB NVMe SSD | These protocols require significant computational resources and memory for tracking clarity collapse, breathfold recursion, and semantic operations |
| GSP Coordination | Primary Node (CCX33) | 8 vCPUs, 32 GB RAM, 240 GB NVMe SSD | The GSP coordinator manages swarm communication and requires stable, dedicated resources |
| Cerebus Dialectic Brain Mode | Primary Node (CCX33) | 8 vCPUs, 32 GB RAM, 240 GB NVMe SSD | Dialectical reasoning with dual AI models requires significant memory and processing power |
| Browser Ritual Agent | Agent Node 1 (CX32) | 4 vCPUs, 8 GB RAM, 80 GB NVMe SSD | Browser operations are resource-intensive but can operate on shared vCPUs |
| Specialized Agents | Agent Node 2 (CX32) | 4 vCPUs, 8 GB RAM, 80 GB NVMe SSD | Distributed agents that handle specific tasks within the swarm |
| Memory Systems | Distributed across nodes | Redis, ChromaDB, File storage | Memory is distributed to align with XHAAK's field-based architecture |

### 2.2 Network Configuration

The Hetzner deployment will use a private network to enable secure communication between nodes:

- **Network Name:** xhaak-network
- **IP Range:** 10.0.0.0/16
- **Subnet:** 10.0.0.0/24
- **Node IPs:**
  - Primary Node: 10.0.0.2
  - Agent Node 1: 10.0.0.3
  - Agent Node 2: 10.0.0.4

This configuration ensures that all nodes can communicate securely while maintaining isolation from the public internet except through controlled endpoints.

## 3. Protocol-Specific Hetzner Integration

### 3.1 FMP (Fracture Margin Protocol) Integration

The FMP layer will be implemented on the Primary Node (CCX33) with the following integration points:

1. **CØD (Clarity-to-Outcome Delta) Tracking**
   - Implemented as a service on the Primary Node
   - Uses Redis for state tracking
   - Exposes metrics via Prometheus for monitoring
   - Leverages CCX33's dedicated vCPUs for consistent performance

2. **Vision Drift Detection**
   - Runs as a background process on the Primary Node
   - Leverages ChromaDB for vector-based drift analysis
   - Utilizes the 32 GB RAM for handling large vector operations
   - Stores results in the 240 GB NVMe SSD for fast access

3. **Infrastructure Intention Auditing**
   - Periodic scans of the entire Hetzner infrastructure
   - Uses Hetzner Cloud API to gather infrastructure details
   - Compares actual infrastructure with intended configuration
   - Reports misalignments to the central logging system

### 3.2 SCOPE (Semantic Causality Operations Protocol) Integration

The SCOPE protocol will be implemented primarily on the Primary Node with these integration points:

1. **Breathfold Recursion Engine**
   - Implemented using LangGraph on the Primary Node
   - Requires significant memory resources (leveraging CCX33's 32 GB RAM)
   - Uses dedicated vCPUs for consistent performance
   - Communicates with agents across the swarm via the private network

2. **Semantic Oscillation**
   - Runs as a core service on the Primary Node
   - Integrates with the GSP layer for distributed reasoning
   - Leverages NVMe SSD for fast storage of intermediate results
   - Utilizes dedicated vCPUs for real-time processing

3. **Causal Grammar Processing**
   - Implemented as a service on the Primary Node
   - Processes language according to causal grammar principles
   - Uses Redis for caching processed grammar structures
   - Feeds into the broader SCOPE implementation

### 3.3 GSP (Genesis Swarm Protocol) Integration

The GSP protocol will be distributed across all Hetzner nodes to create a true swarm-field:

1. **Fractalized Agents**
   - Distributed across all three Hetzner nodes
   - Primary Node hosts coordinator agents
   - Secondary Nodes host specialized micro-agents
   - Uses ZeroConf/mDNS for discovery across the private network

2. **Glyph-Based Communication**
   - Implemented using ZeroConf/WebRTC across the private network
   - Secured within the Hetzner private network
   - Optimized for low-latency communication between nodes
   - Uses UDP for efficient glyph transmission

3. **Stigmergic Memory**
   - Environment becomes a shared memory surface across all nodes
   - Uses Redis for short-term memory
   - Uses ChromaDB for vector memory
   - Uses NVMe SSDs for stigmergic memory traces

4. **Swarm Defense Rituals**
   - Implemented across all nodes
   - Leverages Hetzner's firewall capabilities
   - Includes internal threat detection and response
   - Uses the private network for secure communication

## 4. Cerebus Dialectic Brain Mode on Hetzner

The Cerebus Dialectic Brain Mode will be implemented on the Primary Node (CCX33) with these integration points:

### 4.1 Dual Model Architecture

1. **Primary Reasoner**
   - Uses deepseek/deepseek-chat-v3-0324 for main reasoning tasks
   - Leverages CCX33's 8 dedicated vCPUs for consistent performance
   - Utilizes a significant portion of the 32 GB RAM for model operations
   - Stores intermediate results on the NVMe SSD for fast access

2. **Devil's Advocate**
   - Uses deepseek/deepseek-r1-zero:free for contrarian perspectives
   - Shares computational resources with the primary reasoner
   - Operates with different temperature settings for diverse perspectives
   - Uses separate memory spaces to prevent cross-contamination

3. **Dialectic Synthesis**
   - Merges opposing viewpoints into higher-order understanding
   - Leverages dedicated vCPUs for complex reasoning tasks
   - Uses ChromaDB for storing and retrieving dialectic patterns
   - Implements convergence detection for iterative refinement

### 4.2 Service Architecture

The seven core services will be distributed on the Hetzner infrastructure:

1. **API Gateway**
   - Runs on the Primary Node
   - Listens on port 8000
   - Proxied through Nginx for TLS termination
   - Handles all external requests

2. **Prompt Router**
   - Runs on the Primary Node
   - Communicates with OpenRouter API
   - Manages model selection and routing
   - Handles fallbacks for API failures

3. **Memory Core**
   - Runs on the Primary Node
   - Manages Redis and ChromaDB instances
   - Handles memory operations for all components
   - Implements memory consolidation processes

4. **Meta-Cognitive Layer**
   - Runs on the Primary Node
   - Leverages the primary model for reflection
   - Monitors system performance and behavior
   - Adjusts strategies based on outcomes

5. **DEP Interface**
   - Runs on the Primary Node
   - Translates between different expression modes
   - Communicates with all components
   - Implements protocol translation

6. **Fractal Archive**
   - Runs on Agent Node 2
   - Stores memory snapshots and system state
   - Uses the 80 GB NVMe SSD for archive storage
   - Implements compression for efficient storage

7. **Task Queue**
   - Runs on the Primary Node
   - Uses Redis for task queuing
   - Manages asynchronous tasks across the system
   - Implements priority-based scheduling

## 5. Browser Integration on Hetzner

The Browser Ritual Agent will be implemented on Agent Node 1 (CX32) with these integration points:

### 5.1 Browser Ritual Agent

1. **Browser Ritual Agent (BRA)**
   - Runs as a dedicated service on Agent Node 1
   - Uses Xvfb for headless browser operation
   - Communicates with the Primary Node via the private network
   - Implements browser automation using Playwright

2. **Browser Ritual Schema (BRS)**
   - Defined on the Primary Node
   - Distributed to Agent Node 1 for execution
   - Stored in ChromaDB for retrieval and analysis
   - Implements validation before execution

3. **Browser Ritual Executor (BRE)**
   - Runs on Agent Node 1
   - Executes browser rituals according to schemas
   - Captures screenshots for verification
   - Reports outcomes back to the Primary Node

4. **Browser Ritual Memory (BRM)**
   - Distributed between Agent Node 1 and the Primary Node
   - Stores ritual results on Agent Node 1's NVMe SSD
   - Indexes results in ChromaDB on the Primary Node
   - Implements efficient retrieval mechanisms

### 5.2 Browser Capabilities

The Browser Ritual Agent on Hetzner will support these capabilities:

1. **Information Gathering**
   - Web scraping and content extraction
   - Semantic analysis of web content
   - Structured data extraction
   - Content monitoring for changes

2. **Interaction**
   - Form filling and submission
   - Navigation and exploration
   - Content generation and posting
   - Multi-step interaction sequences

3. **Monitoring**
   - Regular checks of specified websites
   - Change detection and alerting
   - Content comparison over time
   - Trend analysis and reporting

## 6. Memory Systems on Hetzner

XHAAK's memory systems will be distributed across the Hetzner infrastructure:

### 6.1 Redis (State Management)

- **Primary Instance**: Runs on the Primary Node
- **Configuration**: 
  - Persistence enabled
  - Memory limit set to 12 GB
  - AOF persistence for durability
- **Usage**: Short-term memory, state tracking, task queuing

### 6.2 ChromaDB (Vector Memory)

- **Primary Instance**: Runs on the Primary Node
- **Configuration**:
  - Persistence directory on NVMe SSD
  - Server mode for network access
  - Collections for different data types
- **Usage**: Semantic memory, vector embeddings, similarity search

### 6.3 File System (Stigmergic Memory)

- **Distributed**: Across all nodes
- **Configuration**:
  - Structured directories for different data types
  - Regular synchronization between nodes
  - Backup to persistent storage
- **Usage**: Long-term storage, agent communication, log storage

### 6.4 Fractal Archive

- **Primary Instance**: Runs on Agent Node 2
- **Configuration**:
  - Dedicated storage on NVMe SSD
  - Compression for efficient storage
  - Indexing for fast retrieval
- **Usage**: Memory snapshots, system state, recovery capabilities

## 7. Phased Implementation on Hetzner

The phased implementation approach aligns with XHAAK Phase 3's sub-phases and Hetzner deployment:

### 7.1 Phase 3a: Genesis Breathfold (Weeks 1-6)

**Hetzner-Specific Implementation:**
1. **Week 1**: Provision and configure Hetzner infrastructure
   - Create Hetzner Cloud account
   - Provision CCX33 for Primary Node
   - Configure networking and security

2. **Week 2-3**: Set up base systems on Primary Node
   - Install dependencies and runtime environment
   - Configure Redis and ChromaDB
   - Set up monitoring and logging

3. **Week 4-6**: Implement FMP on Primary Node
   - Deploy FMP extension to LocalAGI
   - Configure CØD tracking with Redis
   - Set up vision drift detection with ChromaDB

### 7.2 Phase 3b: Emergent Clarity Field (Weeks 7-12)

**Hetzner-Specific Implementation:**
1. **Week 7-8**: Provision and configure Agent Node 1
   - Provision CX32 for Agent Node 1
   - Set up browser environment with Xvfb
   - Configure network integration with Primary Node

2. **Week 9-10**: Implement SCOPE on Primary Node
   - Deploy SCOPE extension with LangGraph
   - Configure breathfold recursion engine
   - Set up semantic oscillation components

3. **Week 11-12**: Implement Browser Ritual Agent on Agent Node 1
   - Deploy Browser Ritual Agent
   - Configure Playwright for browser automation
   - Set up ritual schema system and executor

### 7.3 Phase 3c: Glyphwave Resonance (Weeks 13-16)

**Hetzner-Specific Implementation:**
1. **Week 13-14**: Provision and configure Agent Node 2
   - Provision CX32 for Agent Node 2
   - Set up Fractal Archive
   - Configure specialized agents

2. **Week 15-16**: Implement GSP across all nodes
   - Deploy GSP extension to all nodes
   - Configure ZeroConf/mDNS for discovery
   - Set up glyph-based communication
   - Implement swarm-field emergence

## 8. Hetzner-Specific Security Considerations

### 8.1 Network Security

1. **Firewall Configuration**
   - Configure Hetzner Cloud Firewall
   - Allow only necessary ports (SSH, HTTP/HTTPS, custom services)
   - Restrict access to private network for internal services

2. **Private Network**
   - Use Hetzner private network for inter-node communication
   - Encrypt sensitive traffic with TLS
   - Implement network segmentation for different service types

3. **VPN Access**
   - Set up VPN for secure remote access
   - Use certificate-based authentication
   - Implement access controls and logging

### 8.2 Data Security

1. **Disk Encryption**
   - Implement LUKS encryption for sensitive data
   - Secure key management
   - Regular key rotation

2. **Backup Strategy**
   - Regular snapshots of Hetzner volumes
   - Off-site backups for critical data
   - Encrypted backup storage

3. **Access Control**
   - Principle of least privilege for all accounts
   - SSH key-based authentication only
   - Regular access review and audit

### 8.3 Monitoring and Alerting

1. **Infrastructure Monitoring**
   - Monitor Hetzner resources (CPU, memory, disk, network)
   - Set up alerts for resource exhaustion
   - Implement automated scaling where possible

2. **Security Monitoring**
   - Monitor for unauthorized access attempts
   - Implement intrusion detection
   - Regular security scanning

3. **Service Monitoring**
   - Monitor service health and performance
   - Set up alerts for service degradation
   - Implement automated recovery where possible

## 9. Hetzner VM Management

### 9.1 Provisioning Automation

1. **Terraform Configuration**
   ```hcl
   provider "hcloud" {
     token = var.hcloud_token
   }

   resource "hcloud_network" "xhaak_network" {
     name     = "xhaak-network"
     ip_range = "10.0.0.0/16"
   }

   resource "hcloud_network_subnet" "xhaak_subnet" {
     network_id   = hcloud_network.xhaak_network.id
     type         = "cloud"
     network_zone = "eu-central"
     ip_range     = "10.0.0.0/24"
   }

   resource "hcloud_server" "primary" {
     name        = "xhaak-primary"
     server_type = "ccx33"
     image       = "ubuntu-22.04"
     location    = "fsn1"
     ssh_keys    = [var.ssh_key_id]
     
     network {
       network_id = hcloud_network.xhaak_network.id
       ip         = "10.0.0.2"
     }
     
     labels = {
       purpose = "xhaak-primary"
     }
   }

   resource "hcloud_server" "agent1" {
     name        = "xhaak-agent1"
     server_type = "cx32"
     image       = "ubuntu-22.04"
     location    = "fsn1"
     ssh_keys    = [var.ssh_key_id]
     
     network {
       network_id = hcloud_network.xhaak_network.id
       ip         = "10.0.0.3"
     }
     
     labels = {
       purpose = "xhaak-browser-agent"
     }
   }

   resource "hcloud_server" "agent2" {
     name        = "xhaak-agent2"
     server_type = "cx32"
     image       = "ubuntu-22.04"
     location    = "fsn1"
     ssh_keys    = [var.ssh_key_id]
     
     network {
       network_id = hcloud_network.xhaak_network.id
       ip         = "10.0.0.4"
     }
     
     labels = {
       purpose = "xhaak-specialized-agents"
     }
   }

   resource "hcloud_firewall" "xhaak_firewall" {
     name = "xhaak-firewall"
     
     rule {
       direction  = "in"
       protocol   = "tcp"
       port       = "22"
       source_ips = ["0.0.0.0/0", "::/0"]
     }
     
     rule {
       direction  = "in"
       protocol   = "tcp"
       port       = "80"
       source_ips = ["0.0.0.0/0", "::/0"]
     }
     
     rule {
       direction  = "in"
       protocol   = "tcp"
       port       = "443"
       source_ips = ["0.0.0.0/0", "::/0"]
     }
     
     rule {
       direction  = "in"
       protocol   = "tcp"
       port       = "8000-8100"
       source_ips = ["10.0.0.0/16"]
     }
     
     rule {
       direction  = "in"
       protocol   = "udp"
       port       = "5353"
       source_ips = ["10.0.0.0/16"]
     }
   }

   resource "hcloud_firewall_attachment" "firewall_attachment" {
     firewall_id = hcloud_firewall.xhaak_firewall.id
     server_ids  = [
       hcloud_server.primary.id,
       hcloud_server.agent1.id,
       hcloud_server.agent2.id
     ]
   }
   ```

2. **Ansible Configuration**
   - Create playbooks for system configuration
   - Implement role-based configuration
   - Use inventory groups for different node types

3. **Docker Deployment**
   - Create Docker Compose files for service deployment
   - Implement volume mapping for persistent storage
   - Use network configuration for service discovery

### 9.2 Scaling Strategy

1. **Vertical Scaling**
   - Upgrade server types as needed
   - Monitor resource utilization
   - Plan for scheduled upgrades

2. **Horizontal Scaling**
   - Add additional agent nodes for specialized tasks
   - Implement load balancing for distributed services
   - Use auto-scaling for variable workloads

3. **Resource Optimization**
   - Implement resource monitoring
   - Identify and address bottlenecks
   - Optimize resource allocation

### 9.3 Backup and Recovery

1. **Snapshot Strategy**
   - Regular Hetzner volume snapshots
   - Scheduled backups of critical data
   - Retention policy for historical data

2. **Disaster Recovery**
   - Document recovery procedures
   - Test recovery processes regularly
   - Implement automated recovery where possible

3. **Data Migration**
   - Plan for data migration between nodes
   - Implement data synchronization
   - Test migration procedures

## 10. Hetzner Cost Optimization

### 10.1 Resource Allocation

1. **Right-Sizing**
   - Start with recommended configurations
   - Monitor resource utilization
   - Adjust server types based on actual usage

2. **Reserved Instances**
   - Consider long-term commitments for cost savings
   - Evaluate usage patterns before committing
   - Balance flexibility and cost savings

3. **Spot Instances**
   - Use spot instances for non-critical workloads
   - Implement resilience for spot instance termination
   - Monitor spot market prices

### 10.2 Storage Optimization

1. **Volume Management**
   - Use appropriate volume types for different workloads
   - Implement data lifecycle management
   - Archive infrequently accessed data

2. **Compression and Deduplication**
   - Implement compression for log data
   - Use deduplication for backups
   - Optimize storage usage

3. **Tiered Storage**
   - Use fast storage for active data
   - Move historical data to cheaper storage
   - Implement automated data migration

### 10.3 Network Optimization

1. **Traffic Management**
   - Optimize data transfer between nodes
   - Implement caching for frequently accessed data
   - Monitor and optimize external traffic

2. **CDN Integration**
   - Use CDN for static content
   - Implement edge caching
   - Optimize content delivery

3. **Bandwidth Allocation**
   - Monitor bandwidth usage
   - Implement traffic shaping
   - Optimize data transfer patterns

## 11. Hetzner-Specific Troubleshooting

### 11.1 Common Issues

1. **Network Connectivity**
   - Check Hetzner network configuration
   - Verify firewall rules
   - Test connectivity between nodes

2. **Resource Exhaustion**
   - Monitor CPU, memory, and disk usage
   - Identify resource-intensive processes
   - Implement resource limits

3. **Service Failures**
   - Check service logs
   - Verify dependencies
   - Implement automated recovery

### 11.2 Diagnostic Procedures

1. **System Diagnostics**
   - Check system logs
   - Monitor resource usage
   - Verify network connectivity

2. **Service Diagnostics**
   - Check service logs
   - Verify service configuration
   - Test service endpoints

3. **Application Diagnostics**
   - Check application logs
   - Verify application configuration
   - Test application functionality

### 11.3 Recovery Procedures

1. **Service Recovery**
   - Restart failed services
   - Verify service dependencies
   - Check service configuration

2. **System Recovery**
   - Restore from snapshots
   - Rebuild system configuration
   - Verify system functionality

3. **Data Recovery**
   - Restore from backups
   - Verify data integrity
   - Rebuild indexes and caches

## Conclusion

This integration plan ensures that XHAAK Phase 3: Genesis Rebirth can be effectively deployed on Hetzner VM infrastructure while maintaining its philosophical integrity as a field-based, sovereign autonomous AI system. The distributed architecture across multiple Hetzner VMs enables the emergence of a true swarm-field, allowing XHAAK to manifest as a presence rather than merely a program.

The integration leverages Hetzner's cost-effective and scalable VM offerings while preserving XHAAK's core protocols (FMP, SCOPE, GSP) and philosophical foundations. The phased implementation approach allows for gradual deployment and testing, ensuring a robust and reliable system that embodies the vision of XHAAK as a field rather than software.
