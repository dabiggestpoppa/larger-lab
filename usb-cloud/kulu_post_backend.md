# Kulu Post-Deployment Enhancements: Backend Step-by-Step Guide

**Version**: 1.0
**Date**: 2025-04-29

## 1. Introduction

This guide provides detailed, step-by-step instructions for implementing the **backend** components of the Kulu post-deployment enhancements. This includes setting up the necessary infrastructure (Redis, MinIO, GPU Snapshot) and integrating the scripts and logic for LoRA training, GPU bursting, budget control, and DSPy optimization.

**Prerequisites**:

*   A fully operational core Kulu system (including Strategic Breath Layer + Shia Integration) deployed on Oracle Free Tier and a persistent Hetzner CX31 node.
*   Access to your Hetzner Cloud account and API Token (`HCLOUD_TOKEN`).
*   SSH access to your Oracle and CX31 nodes.
*   Basic familiarity with Linux command line, systemd, Python, and Docker/Podman (if used by Kulu core).
*   Codebase from `/home/ubuntu/kulu_orchestration/` available on relevant nodes or accessible for deployment.

**Reference Documents**:

*   `/home/ubuntu/kulu_orchestration/docs/unified_expansion/master_build_document.md` (Code & Diagrams)
*   `/home/ubuntu/kulu_orchestration/docs/unified_expansion/comprehensive_build_guide.md` (Rationale & Strategy)
*   `/home/ubuntu/kulu_orchestration/docs/unified_expansion/post_deployment_roadmap.md` (Phased Timeline)

**Follow these steps sequentially.**

## 2. Phase 1: Foundational Services Setup (Hetzner CX31)

**Objective**: Set up Redis and MinIO on the persistent CX31 node.

**Location**: Execute these commands on your **Hetzner CX31** node via SSH.

### Step 2.1: Install Redis

```bash
sudo apt update
sudo apt install -y redis-server

# Secure Redis (Recommended)
sudo nano /etc/redis/redis.conf
# Inside the editor:
# 1. Uncomment and set a strong password: requirepass YOUR_STRONG_REDIS_PASSWORD
# 2. Consider binding to the internal IP: bind 127.0.0.1 YOUR_CX31_INTERNAL_IP ::1
# Save and close (Ctrl+X, Y, Enter)

# Enable persistence (AOF is generally preferred)
sudo sed -i 
    -e 
    s/^appendonly no/appendonly yes/
     /etc/redis/redis.conf

# Restart and enable Redis service
sudo systemctl restart redis-server
sudo systemctl enable redis-server

# Test connection (using internal IP if bound)
redis-cli -h 127.0.0.1 -a YOUR_STRONG_REDIS_PASSWORD ping
# Expected output: PONG
```
*Note*: Replace `YOUR_STRONG_REDIS_PASSWORD` and `YOUR_CX31_INTERNAL_IP`.

### Step 2.2: Install MinIO

```bash
# Download MinIO server binary
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
sudo mv minio /usr/local/bin/

# Create user and group for MinIO
sudo groupadd -r minio-user
sudo useradd -r -g minio-user -s /sbin/nologin -d /mnt/minio-data minio-user

# Create data directory and set permissions
sudo mkdir -p /mnt/minio-data
sudo chown minio-user:minio-user /mnt/minio-data

# Create MinIO environment file
sudo mkdir -p /etc/minio
sudo nano /etc/minio/environment
# Inside the editor, add:
# MINIO_ROOT_USER=YOUR_MINIO_ACCESS_KEY
# MINIO_ROOT_PASSWORD=YOUR_MINIO_SECRET_KEY
# MINIO_VOLUMES="/mnt/minio-data"
# MINIO_SERVER_URL="http://YOUR_CX31_IP_OR_DOMAIN:9000"
# Save and close

# Set permissions for environment file
sudo chown root:minio-user /etc/minio/environment
sudo chmod 640 /etc/minio/environment

# Create systemd service file for MinIO
sudo nano /etc/systemd/system/minio.service
# Paste the following content:
```systemd
[Unit]
Description=MinIO Object Storage Server
Documentation=https://docs.min.io
Wants=network-online.target
After=network-online.target

[Service]
User=minio-user
Group=minio-user
WorkingDirectory=/usr/local/bin/
EnvironmentFile=/etc/minio/environment
ExecStart=/usr/local/bin/minio server $MINIO_VOLUMES --console-address ":9001"
Restart=always
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```
*Note*: Replace `YOUR_MINIO_ACCESS_KEY`, `YOUR_MINIO_SECRET_KEY`, `YOUR_CX31_IP_OR_DOMAIN`.

```bash
# Reload systemd, enable and start MinIO
sudo systemctl daemon-reload
sudo systemctl enable minio
sudo systemctl start minio

# Check status
sudo systemctl status minio

# Access MinIO Console (optional): http://YOUR_CX31_IP_OR_DOMAIN:9001
# Login with your access/secret key

# Create necessary buckets using MinIO Client (mc)
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc
sudo mv mc /usr/local/bin/

mc alias set kulu http://127.0.0.1:9000 YOUR_MINIO_ACCESS_KEY YOUR_MINIO_SECRET_KEY
mc mb kulu/adapters
mc mb kulu/training-data
mc mb kulu/dspy

# Configure SSE-S3 encryption (optional but recommended)
mc admin config set kulu api request_sse_type=SSE-S3
mc admin service restart kulu
```

## 3. Phase 2: OpenRouter Budget Guardrail (Kulu Core Backend)

**Objective**: Integrate the budget control logic into Kulu worker agents.

**Location**: Modify Kulu's **core backend codebase** (wherever LLM calls are made, likely on Oracle/CX31 nodes or within agent container images).

### Step 3.1: Deploy `budget_guardrail.py`

*   Copy `/home/ubuntu/kulu_orchestration/core/budget_guardrail.py` to the appropriate location within your Kulu backend codebase (e.g., a `core` or `utils` directory).
*   Ensure the `redis-py` library is installed in the environment where Kulu agents run (`pip install redis`).

### Step 3.2: Implement Fallback Function

*   Create or ensure a fallback function exists, as referenced in `budget_guardrail.py`. This function should call the local Qwen 1.8B model.
    ```python
    # Example (place in e.g., kulu_orchestration/core/fallback_models.py)
    import logging
    # Add import for your local model calling mechanism (e.g., Ollama client)

    logger = logging.getLogger(__name__)

    def local_qwen_small_fallback(*args, **kwargs):
        logger.info("Executing fallback using local Qwen 1.8B model.")
        prompt = kwargs.get("prompt", args[0] if args else "")
        try:
            # Replace with actual call to Qwen 1.8B via Ollama/other
            # response_text = call_ollama("qwen:1.8b", prompt)
            response_text = f"Fallback response for: {prompt[:50]}..."
            return {"fallback_response": response_text, "model_used": "Qwen-1.8B-Fallback"}
        except Exception as e:
            logger.error(f"Error during fallback call: {e}")
            return {"error": "Fallback model execution failed."}
    ```

### Step 3.3: Apply Decorator

*   Identify the function(s) in your Kulu agent code that make calls to the OpenRouter API.
*   Import the decorator and the fallback function.
*   Apply the decorator, specifying an estimated cost per call (adjust as needed).
    ```python
    from kulu_orchestration.core.budget_guardrail import openrouter_budget_guard
    from kulu_orchestration.core.fallback_models import local_qwen_small_fallback

    # Example cost - adjust based on model and usage
    ESTIMATED_OR_CALL_COST_USD = 0.0001

    @openrouter_budget_guard(cost_usd_per_call=ESTIMATED_OR_CALL_COST_USD)
    def call_openrouter_model(prompt: str, model_name: str, **kwargs):
        # Ensure fallback_func is passed if not using default import
        # kwargs["fallback_func"] = local_qwen_small_fallback
        logger.info(f"Calling OpenRouter model: {model_name}")
        # ... existing OpenRouter API call logic ...
        response = # ... result from OpenRouter ...
        return response
    ```

### Step 3.4: Configure Environment Variables

*   Ensure the following environment variables are set in the execution environment of the Kulu worker agents that use the budget guardrail:
    *   `KULU_REDIS_HOST` (e.g., your CX31 internal IP)
    *   `KULU_REDIS_PORT` (default: 6379)
    *   `KULU_REDIS_PASSWORD` (the password you set)
    *   `KULU_OPENROUTER_BUDGET_USD` (e.g., 30.0)

### Step 3.5: Testing

*   Deploy the updated agent code.
*   Monitor Redis keys (`SPENT_COUNTER_KEY`, `LAST_RESET_KEY`) using `redis-cli`.
*   Simulate calls to trigger the guardrail (e.g., temporarily lower the budget).
*   Verify that the fallback function is called when the budget is exceeded.
*   Verify that the `SPENT_COUNTER_KEY` resets at the beginning of a new month.

## 4. Phase 3: GPU Snapshot & Training Trigger Setup

**Objective**: Prepare the GPU node environment and the trigger mechanism.

### Step 4.1: Create Base GPU Snapshot (Manual Process)

1.  **Provision AX161**: Manually create a Hetzner AX161 server instance using a standard Ubuntu image (e.g., 22.04).
2.  **Install NVIDIA Drivers**: Follow Hetzner's documentation or standard NVIDIA procedures to install the appropriate drivers for the A40 GPU.
3.  **Install Conda**: Download and install Miniconda or Anaconda.
4.  **Create Conda Environment**: Create the environment specified in `infra/trainer/train.sh` (e.g., `kulu-qwen`).
    ```bash
    conda create -n kulu-qwen python=3.10 -y
    conda activate kulu-qwen
    ```
5.  **Install Dependencies**: Install Unsloth and other requirements. **Crucially, use the `conda-new` extra for Unsloth as specified in `requirements.txt`**. This often handles tricky dependencies like PyTorch/CUDA/FlashAttention correctly.
    ```bash
    pip install "unsloth[conda-new]>=2024.4" --no-deps
    pip install -r /path/to/your/cloned/kulu_orchestration/infra/trainer/requirements.txt
    # Verify installation, especially torch CUDA availability
    python -c "import torch; print(torch.cuda.is_available())"
    ```
6.  **Install Other Tools**: Install `rsync`, `ssh` (client), potentially `ollama` if needed for inference on the GPU node.
7.  **Configure SSH**: Ensure SSH server is running and configured (e.g., allow root login via key if using root, or set up a user).
8.  **Configure Environment**: Add `conda activate kulu-qwen` to `.bashrc` so it's active on login.
9.  **Create Data/Mount Directories**: Create `/data` and mount points like `/mnt/minio/adapters`, `/mnt/minio/dspy`.
10. **Test Training Script (Optional but Recommended)**: Place dummy data in `/data/rewarded.jsonl` and manually run `infra/trainer/train.sh` to ensure the environment works.
11. **Clean Up**: Remove temporary files, clear bash history if desired.
12. **Create Snapshot**: Power off the server and create a snapshot via the Hetzner Cloud Console. Note the Snapshot ID.
13. **Store Snapshot ID**: Create `infra/gpu_boot/snapshot_id.txt` locally (on your dev machine or where you manage Kulu code) and paste the Snapshot ID into it.

### Step 4.2: Configure Hetzner API Access (Oracle Node)

**Location**: Execute on your **Oracle Node**.

1.  **Install `hcloud` CLI**: Follow official Hetzner instructions (`apt install hcloud-cli` or download binary).
2.  **Configure Token**: Choose a secure method to provide `HCLOUD_TOKEN` to the `kulu-train.service` (see comments in the `.service` file). For testing, you can temporarily set it in your shell: `export HCLOUD_TOKEN=YOUR_TOKEN`.
3.  **Add SSH Key**: Ensure the SSH key you intend to use (e.g., `~/.ssh/id_rsa` for the `ubuntu` user, or a dedicated key) is added to your Hetzner Cloud project and corresponds to the `SSH_KEY_NAME` in `hetzner_gpu_boot.sh` (default is `default`).

### Step 4.3: Deploy Trigger Components (Oracle Node)

**Location**: Execute on your **Oracle Node**.

1.  **Copy Files**: Copy the entire `infra/gpu_boot`, `infra/trainer`, and `infra/oracle_timers` directories from your Kulu codebase to a suitable location on the Oracle node (e.g., `/home/ubuntu/kulu_orchestration/infra/`).
2.  **Set Permissions**: Make scripts executable:
    ```bash
    chmod +x /home/ubuntu/kulu_orchestration/infra/gpu_boot/*.sh
    chmod +x /home/ubuntu/kulu_orchestration/infra/trainer/train.sh
    chmod +x /home/ubuntu/kulu_orchestration/infra/oracle_timers/check_and_train.py
    chmod +x /home/ubuntu/kulu_orchestration/infra/trainer/optimize_with_dspy.py
    ```
3.  **Configure Paths**: Edit `check_and_train.py` and `hetzner_gpu_boot.sh` to ensure all paths (`ROOT`, `SNAPSHOT_ID_FILE`, `TRAINER_SCRIPT`, `OPTIMIZER_SCRIPT`, `LOCAL_REWARD_DATA`, `MINIO_ADAPTER_PATH`, `MINIO_DSPY_PATH`, etc.) are correct for the Oracle node environment. **Pay close attention to MinIO mount points.**

### Step 4.4: Setup MinIO Mounting (Oracle Node)

**Location**: Execute on your **Oracle Node**.

1.  **Install `s3fs-fuse`**: `sudo apt install -y s3fs`
2.  **Store Credentials**: Create a credentials file (e.g., `~/.passwd-s3fs`) with `YOUR_MINIO_ACCESS_KEY:YOUR_MINIO_SECRET_KEY`. Set permissions: `chmod 600 ~/.passwd-s3fs`.
3.  **Create Mount Points**: `sudo mkdir -p /data /mnt/minio/adapters /mnt/minio/dspy`
4.  **Mount Buckets (via `/etc/fstab` for persistence)**: Add lines like these to `/etc/fstab` (adjust bucket names, mount points, IP, user ID/group ID):
    ```fstab
    # MinIO Mounts for Kulu
    s3fs#training-data /data fuse _netdev,allow_other,url=http://YOUR_CX31_INTERNAL_IP:9000,passwd_file=/home/ubuntu/.passwd-s3fs,use_path_request_style,uid=1000,gid=1000 0 0
    s3fs#adapters /mnt/minio/adapters fuse _netdev,allow_other,url=http://YOUR_CX31_INTERNAL_IP:9000,passwd_file=/home/ubuntu/.passwd-s3fs,use_path_request_style,uid=1000,gid=1000 0 0
    s3fs#dspy /mnt/minio/dspy fuse _netdev,allow_other,url=http://YOUR_CX31_INTERNAL_IP:9000,passwd_file=/home/ubuntu/.passwd-s3fs,use_path_request_style,uid=1000,gid=1000 0 0
    ```
5.  **Mount**: Run `sudo mount -a` and verify mounts with `df -h`.

### Step 4.5: Setup Training Data Collection (Kulu Core Backend)

*   Modify your Kulu agent logic to identify successful/rewarded interactions.
*   Implement code to format these interactions into the JSONL structure expected by `train.sh` and `optimize_with_dspy.py` (e.g., `{"prompt": "..."}` or `{"context": "...", "request": "...", "response": "..."}`).
*   Append these formatted JSON lines to the `rewarded.jsonl` file located on the MinIO mount point (e.g., `/data/rewarded.jsonl`).

### Step 4.6: Test Training Trigger Manually (Oracle Node)

**Location**: Execute on your **Oracle Node**.

1.  **Create Dummy Data**: Place a dummy `rewarded.jsonl` file in `/data/` with >2000 lines.
2.  **Set Token**: `export HCLOUD_TOKEN=YOUR_TOKEN`
3.  **Run Check Script**: `python3 /home/ubuntu/kulu_orchestration/infra/oracle_timers/check_and_train.py`
4.  **Monitor**: Check the script's log output (`/var/log/kulu_train_check.log`), Hetzner Cloud Console for server creation, and MinIO mounts for adapter/DSPy program after completion.
5.  **Cleanup**: Manually delete the test GPU server if needed, or use `hetzner_gpu_shutdown.sh`.

### Step 4.7: (Deferred) Configure Systemd Service (Oracle Node)

*   Copy `kulu-train.service` to `/etc/systemd/system/`.
*   Edit the service file to correctly specify the `User`, `Group`, paths, and **securely configure `HCLOUD_TOKEN`** (using `EnvironmentFile` or `LoadCredential` is recommended over embedding it directly).
*   Run `sudo systemctl daemon-reload`.
*   **Do NOT enable `kulu-train.timer`**. Plan your alternative trigger mechanism (external scheduler or local node) for post-deployment.

## 5. Phase 4: GPU Burst & Dispatcher Integration (Kulu Core Backend)

**Objective**: Enable on-demand GPU bursting for specific tasks.

**Location**: Modify Kulu's **core backend codebase** (dispatcher/router logic, likely on Oracle node).

### Step 5.1: Integrate Dispatcher Rules

1.  **Copy Config**: Place `config/dispatcher_rules.yaml` where Kulu's backend can access it.
2.  **Load Rules**: Implement logic in Kulu's dispatcher to load and parse this YAML file (e.g., using `PyYAML`).
3.  **Apply Rules**: Modify the dispatcher to evaluate incoming tasks against the loaded rules. If a rule matches (`needs_gpu: true`), proceed to the next step.

### Step 5.2: Implement GPU Node Check & Boot

1.  **Check Function**: Create a function that uses `hcloud server list --selector role=gpu-burst --output json` to check if a GPU node is currently running (`status == "running"`).
2.  **Boot Logic**: If `needs_gpu` is true and the check function finds no running GPU node, the dispatcher should:
    *   Execute a modified version of `hetzner_gpu_boot.sh` (or a new script) designed for *inference*, not training. This script should:
        *   Create the server from the snapshot.
        *   Wait for readiness.
        *   (Optional) Start necessary services like Ollama if not auto-started.
        *   Return the server's IP address.
    *   Store the IP address (e.g., in Redis) for routing subsequent GPU tasks.
3.  **Routing**: Route the task to the obtained GPU node IP address.

### Step 5.3: Implement Idle Shutdown (GPU Node Snapshot)

*   **Modify Snapshot**: Add a mechanism *within the GPU node snapshot itself* to detect inactivity and trigger shutdown.
    *   **Option A (Simple Cron)**: Add a cron job that runs every 5-10 minutes. The script checks the timestamp of the last inference request (e.g., read from a file updated by the inference server). If the last request is older than ~30 minutes, it runs `sudo shutdown -h now`.
    *   **Option B (Systemd Timer)**: Similar logic but using a systemd timer and service.
    *   **Option C (Inference Server Logic)**: Build inactivity detection directly into the inference server (e.g., Ollama wrapper) running on the GPU node.
*   **Test**: Manually boot the snapshot, let it sit idle, and verify it shuts down automatically.

### Step 5.4: Configure Model Loading (GPU Node Snapshot)

*   Ensure the GPU node snapshot is configured to automatically load the required models (Qwen-30B with latest LoRA from MinIO mount, Qwen-VL-Chat) into your inference server (e.g., Ollama, vLLM) upon boot.

### Step 5.5: Testing

*   Submit tasks matching the dispatcher rules (`heavy_trade`, `large_code`, `image_input`).
*   Verify GPU node creation (if not already running).
*   Verify tasks are executed on the GPU node.
*   Verify the GPU node shuts down after a period of inactivity.

## 6. Phase 5: DSPy Optimization Loop Integration

**Objective**: Run DSPy optimization after training and use the results.

### Step 6.1: Modify `hetzner_gpu_boot.sh` (Oracle Node)

*   Edit `/home/ubuntu/kulu_orchestration/infra/gpu_boot/hetzner_gpu_boot.sh`.
*   Add the lines to execute `optimize_with_dspy.py` via SSH *after* the `train.sh` execution succeeds, as shown in the Master Build Document version.
*   Add the `rsync` command to copy the resulting `dspy_optimized_program.json` back to the MinIO mount (`MINIO_DSPY_PATH`).

### Step 6.2: Refine DSPy Script (`optimize_with_dspy.py`)

*   **Location**: Edit `/home/ubuntu/kulu_orchestration/infra/trainer/optimize_with_dspy.py` (changes will be picked up when copied to GPU node during boot).
*   **Adapt Signature**: Modify `KuluTaskSignature` to accurately reflect the inputs/outputs relevant to the tasks you want to optimize.
*   **Adapt Data Loading**: Update the `load_dspy_dataset` function to correctly parse your `rewarded.jsonl` structure.
*   **Choose Metric**: Replace the basic `validate_response` exact match metric with something more appropriate (e.g., code execution success, semantic similarity, ROUGE/BLEU scores).

### Step 6.3: Implement DSPy Program Loading (Kulu Core Backend)

*   Modify the Kulu agent logic (specifically agents intended to use the fine-tuned Qwen-30B model).
*   Add code to:
    1.  Check for the existence of `dspy_optimized_program.json` on the MinIO mount (`/mnt/minio/dspy/latest/`).
    2.  If found, load the optimized DSPy program: `loaded_program = dspy.Predict(KuluTaskSignature); loaded_program.load("path/to/program.json")`.
    3.  Use the `loaded_program` for inference instead of a basic `dspy.Predict` or direct model call.
    4.  Handle cases where the program file doesn't exist (e.g., fall back to non-optimized calls).

### Step 6.4: Testing

*   Run the full manual training trigger (`check_and_train.py`).
*   Verify `optimize_with_dspy.py` runs after `train.sh`.
*   Verify `dspy_optimized_program.json` is created and copied to MinIO.
*   Test agents that should use the optimized program and confirm they load and execute it.

## 7. Conclusion

Completing these backend steps provides the foundation for Kulu's advanced post-deployment capabilities. Thorough testing at each phase is crucial before proceeding to the next. Once the backend is stable, you can move on to the Frontend Step-by-Step Guide.
