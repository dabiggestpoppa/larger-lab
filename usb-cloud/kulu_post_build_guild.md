# Kulu Post-Deployment Enhancements: Comprehensive Guide

**Version**: 1.0
**Date**: 2025-04-29

## 1. Introduction

This document provides a comprehensive guide for implementing significant post-deployment enhancements to the core Kulu Node Orchestration System (which includes the Strategic Breath Layer and Shia Integration). These enhancements focus on leveraging specialized AI models, optimizing performance through GPU acceleration, managing costs effectively, and enabling continuous model improvement through automated fine-tuning and DSPy integration.

**Key Enhancements Covered:**

1.  **Nightly LoRA Training**: Automated fine-tuning of a Qwen 3-30B model using collected interaction data.
2.  **On-Demand GPU Burst**: Dynamic spawning of a Hetzner AX161 GPU node for heavy compute (LoRA training) and vision tasks (Qwen-VL-Chat).
3.  **OpenRouter Budget Guardrail**: Strict cost control ($30/month cap) for using external OpenRouter models, with fallback to a local lightweight model.
4.  **DSPy Integration**: Using DSPy to optimize prompts and potentially the fine-tuned LoRA model itself.

**Important Note**: These features are designed to be implemented *after* the core Kulu system is successfully deployed and operational.

## 2. Enhanced Architecture Overview

The enhanced architecture builds upon the existing three-tier Kulu structure (Oracle Free Tier, Hetzner CX31 Persistent, Local Node) by adding an on-demand Hetzner AX161 GPU tier and integrating OpenRouter with strict budget controls. Redis and MinIO on the CX31 node play crucial roles in state management, budget tracking, and data/model storage.

**(Refer to `/home/ubuntu/kulu_orchestration/docs/unified_expansion/infrastructure_design.md` for detailed diagrams and specifications)**

**Key Components & Roles:**

*   **Oracle Free Tier**: Hosts core Kulu logic, anchors, dispatcher, and the *trigger* for nightly training.
*   **Hetzner CX31 (Persistent)**: Runs Redis (state/budget), MinIO (data/adapters/DSPy programs), and fallback worker agents.
*   **Hetzner AX161 GPU (On-Demand)**: Executes LoRA training (`train.sh`), DSPy optimization (`optimize_with_dspy.py`), heavy text tasks (Qwen-30B-LoRA), and vision tasks (Qwen-VL-Chat).
*   **OpenRouter**: Provides access to external models (Gemini, Haiku) for light tasks, managed by the budget guardrail.
*   **Local Node**: User interface and primary interaction point.

## 3. Component Implementation Details

This section details the scripts and configuration files created for these enhancements.

### 3.1 GPU Node Management (`infra/gpu_boot/`)

*   **`snapshot_id.txt`**: Contains the Hetzner Snapshot ID of the pre-configured AX161 GPU image. **Must be created manually** after setting up the base GPU image.
*   **`hetzner_gpu_boot.sh`**: 
    *   **Purpose**: Creates an AX161 server from the specified snapshot, waits for it, copies training data (`rewarded.jsonl`) via rsync, executes `train.sh` (and subsequently `optimize_with_dspy.py`) via SSH, copies the resulting LoRA adapter and DSPy program back to MinIO mount points via rsync, and schedules a delayed shutdown (+15 min by default) of the GPU server.
    *   **Dependencies**: `hcloud` CLI, `rsync`, `ssh`, valid `HCLOUD_TOKEN` environment variable, SSH key configured in Hetzner Cloud.
    *   **Configuration**: Paths to snapshot ID, trainer script, data files, MinIO mount points, server details (type, location, label), SSH user/key, shutdown delay.
*   **`hetzner_gpu_shutdown.sh`**: 
    *   **Purpose**: Finds any *stopped* Hetzner servers with the label `role=gpu-burst` and deletes them. Acts as a cleanup mechanism.
    *   **Dependencies**: `hcloud` CLI, `jq`.
    *   **Usage**: Can be run periodically (e.g., via cron on CX31) or manually to clean up any failed/stopped GPU instances.

### 3.2 LoRA Training & DSPy Optimization (`infra/trainer/`)

*   **`requirements.txt`**: 
    *   **Purpose**: Lists Python dependencies for the training environment on the GPU node snapshot.
    *   **Key Packages**: `unsloth`, `transformers`, `bitsandbytes`, `accelerate`, `xformers`, `torch`, `dspy-ai`.
*   **`train.sh`**: 
    *   **Purpose**: Executes the Unsloth LoRA fine-tuning process for the Qwen 3-30B model using data from `/data/rewarded.jsonl`. Includes an optional validation step.
    *   **Dependencies**: Conda environment (`kulu-qwen` by default), Unsloth, Python dependencies from `requirements.txt`.
    *   **Configuration**: Conda environment name, base model name, dataset path, output directory, LoRA rank, epochs, batch size, etc.
*   **`optimize_with_dspy.py`**: 
    *   **Purpose**: Runs *after* `train.sh`. Loads the newly trained LoRA adapter, defines a DSPy program/signature, loads training/dev data from `rewarded.jsonl`, configures DSPy to use the fine-tuned model, runs a DSPy optimizer (e.g., `BootstrapFewShot`), saves the optimized program locally, and copies it to the MinIO mount point.
    *   **Dependencies**: DSPy, PyTorch, Transformers, PEFT, Python dependencies from `requirements.txt`.
    *   **Configuration**: Base model name, adapter path, dataset path, DSPy output paths (local and MinIO), DSPy training/dev set sizes.
    *   **Note**: The DSPy signature and metric need refinement based on the actual `rewarded.jsonl` structure and desired task performance.

### 3.3 Training Trigger (`infra/oracle_timers/`)

*   **`check_and_train.py`**: 
    *   **Purpose**: Python script intended to be run nightly. Checks if the `rewarded.jsonl` file (on a MinIO mount) exists and contains a minimum number of lines (e.g., 2000). If the threshold is met, it executes `hetzner_gpu_boot.sh` to start the training process.
    *   **Dependencies**: Python 3, access to MinIO mount point, `hetzner_gpu_boot.sh`.
    *   **Configuration**: Path to reward data, minimum line threshold, path to boot script, log file location.
*   **`kulu-train.service`**: 
    *   **Purpose**: Systemd service unit file to run `check_and_train.py` as a one-shot service on the Oracle node.
    *   **Configuration**: User/Group, path to `check_and_train.py`, secure method for providing `HCLOUD_TOKEN` (EnvironmentFile or LoadCredential recommended).
*   **`kulu-train.timer`**: 
    *   **Purpose**: Systemd timer unit file to trigger `kulu-train.service` daily at 02:00 server time with randomized delay.
    *   **Configuration**: `OnCalendar` schedule, `RandomizedDelaySec`.
    *   **IMPORTANT**: Due to system limitations, this timer **cannot be enabled directly** in the current environment. An alternative trigger (manual, external scheduler, local node) must be used post-deployment.

### 3.4 Budget Guardrail (`core/budget_guardrail.py`)

*   **Purpose**: Python module providing a decorator (`@openrouter_budget_guard`) to wrap functions making OpenRouter API calls.
*   **Functionality**: Checks current monthly spending (stored in Redis) against a configured budget (`KULU_OPENROUTER_BUDGET_USD`). If under budget, allows the API call and increments spending in Redis. If over budget, calls a specified fallback function (e.g., using the local Qwen 1.8B model).
*   **Dependencies**: `redis-py`.
*   **Configuration**: Redis connection details (host, port, password), budget amount, Redis keys for counter and last reset.
*   **Integration**: Decorator needs to be applied to the relevant LLM call functions within Kulu worker agents.

### 3.5 Dispatcher Rules (`config/dispatcher_rules.yaml`)

*   **Purpose**: YAML configuration file defining rules for Kulu's task dispatcher.
*   **Functionality**: Specifies conditions (e.g., domain, complexity, input type) under which tasks should be routed to the on-demand GPU node. Sets flags (`needs_gpu`, `needs_vision`) and model preferences (Qwen-30B-LoRA, Qwen-VL-Chat).
*   **Integration**: Needs to be loaded and interpreted by Kulu's core task routing logic.

## 4. Post-Deployment Roadmap Summary

Implementation should follow these phases *after* the core Kulu system is stable:

1.  **Phase 1 (Week 1-2)**: Set up foundational services (Redis, MinIO on CX31).
2.  **Phase 2 (Week 3)**: Implement and test the OpenRouter Budget Guardrail.
3.  **Phase 3 (Week 4-5)**: Create GPU snapshot, configure API access, deploy trigger scripts (test manually).
4.  **Phase 4 (Week 6)**: Integrate dispatcher rules, implement on-demand GPU boot logic and idle shutdown.
5.  **Phase 5 (Week 7-8)**: Integrate DSPy optimization script (`optimize_with_dspy.py`) into the training workflow and enable agents to use the optimized DSPy program.

**(Refer to `/home/ubuntu/kulu_orchestration/docs/unified_expansion/post_deployment_roadmap.md` for full details)**

## 5. Setup and Configuration Summary

1.  **Hetzner Account**: Obtain API Token (`HCLOUD_TOKEN`). Add an SSH key.
2.  **GPU Snapshot**: Manually create the AX161 snapshot with all dependencies installed (NVIDIA drivers, Conda, Python env, `requirements.txt` packages).
3.  **Persistent Services (CX31)**: Install and configure Redis (with password, persistence) and MinIO (with SSE-S3, buckets, access keys).
4.  **MinIO Mounting**: Set up `s3fs` or similar on Oracle/CX31/GPU nodes to mount MinIO buckets (e.g., `/data` for `rewarded.jsonl`, `/mnt/minio/adapters` for LoRA, `/mnt/minio/dspy` for DSPy programs).
5.  **Environment Variables**: Securely configure `HCLOUD_TOKEN`, Redis details, MinIO keys, and `KULU_OPENROUTER_BUDGET_USD` in the appropriate service environments (systemd, container envs).
6.  **Script Deployment**: Copy all scripts and configuration files to their designated locations on the relevant nodes (Oracle, CX31).
7.  **Permissions**: Ensure all `.sh` and `.py` scripts are executable (`chmod +x`).
8.  **Systemd (Oracle)**: Configure `kulu-train.service` (especially `HCLOUD_TOKEN`). *Do not enable `kulu-train.timer` directly.* Plan alternative trigger.
9.  **Kulu Integration**: Modify Kulu's core logic to:
    *   Use the `budget_guardrail.py` decorator.
    *   Load and use `dispatcher_rules.yaml`.
    *   Implement the GPU node check and on-demand boot logic.
    *   Implement the data collection mechanism for `rewarded.jsonl`.
    *   Load and use the optimized DSPy program from MinIO.

## 6. Security Considerations Summary

*   **Network**: Use Tailscale ACLs to restrict inter-node traffic. Block GPU node internet egress.
*   **Containers**: Apply Podman hardening flags (`--cap-drop=ALL`, `--read-only`, etc.).
*   **Data**: Use LUKS for disk encryption and MinIO SSE-S3 for object storage encryption.
*   **Secrets**: Manage `HCLOUD_TOKEN`, MinIO keys, Redis password securely (e.g., systemd credentials, environment files with restricted permissions, secrets management tools).

## 7. Operational Notes

*   **Nightly Training Trigger**: The systemd timer (`kulu-train.timer`) cannot be enabled directly due to environment limitations. A manual trigger, external scheduler (e.g., GitHub Actions), or local node scheduler must be implemented post-deployment to run `check_and_train.py` nightly.
*   **Monitoring**: Implement monitoring for GPU node costs, OpenRouter spending, training success/failure, and DSPy optimization results.
*   **Snapshot Updates**: Periodically update the base GPU snapshot with OS updates and dependency upgrades.

This guide provides the blueprint for significantly enhancing Kulu's capabilities post-deployment, enabling specialized model usage, cost optimization, and continuous self-improvement within a defined budget.
