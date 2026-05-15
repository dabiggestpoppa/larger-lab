# Kulu Post-Deployment Enhancements: Roadmap

This roadmap outlines the recommended phases for implementing the advanced features (Nightly LoRA Training, GPU Burst Capabilities, OpenRouter Budget Guardrail, DSPy Integration) *after* the core Kulu Node Orchestration System (including Strategic Breath Layer + Shia Integration) is successfully deployed and operational.

**Goal**: Incrementally enhance Kulu with specialized model capabilities and cost optimization features while maintaining stability.

**Prerequisites**: Core Kulu system deployed and functioning across Oracle Free Tier and Hetzner CX31 nodes.

## Phase 1: Foundational Services Setup (Week 1-2)

**Objective**: Establish the persistent services required for state management, storage, and budget tracking.

**Tasks**:
1.  **Deploy Hetzner CX31**: Ensure the persistent CX31 node is running.
2.  **Install & Configure Redis**: Set up Redis on CX31 for state, messaging, and budget tracking (`SPENT_COUNTER_KEY`, `LAST_RESET_KEY`). Secure with password and enable persistence.
3.  **Install & Configure MinIO**: Set up MinIO on CX31 for object storage. Create buckets for LoRA adapters (`adapters`), training data (`training-data`), and DSPy programs (`dspy`). Configure SSE-S3 encryption and access policies.
4.  **Mount MinIO**: Configure relevant nodes (Oracle, CX31, future GPU node) to mount MinIO buckets (e.g., using `s3fs` or similar) for easy access to adapters and data.
5.  **Testing**: Verify Redis connectivity and MinIO read/write access from Oracle and CX31 nodes.

**Deliverable**: Operational Redis and MinIO services on the CX31 node.

## Phase 2: OpenRouter Budget Guardrail Implementation (Week 3)

**Objective**: Implement and integrate the budget control mechanism for OpenRouter API calls.

**Tasks**:
1.  **Integrate `budget_guardrail.py`**: Incorporate the `openrouter_budget_guard` decorator into Kulu's core LLM calling mechanism within worker agents.
2.  **Implement Fallback Logic**: Ensure the `local_qwen_small_fallback` function (using Qwen 1.8B on Oracle/CX31) is correctly implemented and called when the budget is exceeded.
3.  **Configure Environment Variables**: Set `KULU_REDIS_HOST`, `KULU_REDIS_PORT`, `KULU_REDIS_PASSWORD`, `KULU_OPENROUTER_BUDGET_USD` in the worker agent environments.
4.  **Testing**: Simulate budget exhaustion scenarios. Verify fallback to the local model. Monitor Redis keys (`SPENT_COUNTER_KEY`, `LAST_RESET_KEY`) for correct updates and monthly reset.

**Deliverable**: Functional OpenRouter budget guardrail integrated into Kulu worker agents.

## Phase 3: GPU Node Snapshot & Training Trigger Setup (Week 4-5)

**Objective**: Prepare the GPU node environment and set up the automated LoRA training trigger mechanism.

**Tasks**:
1.  **Create Base GPU Snapshot**: Manually provision a Hetzner AX161 instance. Install all necessary drivers (NVIDIA), software (Conda, Python, Docker/Podman if needed), and Python dependencies (`infra/trainer/requirements.txt`, including Unsloth and DSPy). Configure the environment (e.g., activate conda env in `.bashrc`). Create a snapshot and record its ID in `infra/gpu_boot/snapshot_id.txt`.
2.  **Configure Hetzner API Access**: Ensure the Oracle node (or wherever the trigger runs) has the `hcloud` CLI installed and the `HCLOUD_TOKEN` environment variable securely configured (e.g., via systemd credentials or environment file as noted in `kulu-train.service`).
3.  **Deploy Training Trigger Components**: Copy `infra/gpu_boot/`, `infra/trainer/`, and `infra/oracle_timers/` scripts/configs to the appropriate locations on the Oracle node.
4.  **Configure `check_and_train.py`**: Set correct paths for `REWARD_DATA_PATH` (MinIO mount point) and `GPU_BOOT_SCRIPT_PATH`.
5.  **Configure `hetzner_gpu_boot.sh`**: Set correct paths for `SNAPSHOT_ID_FILE`, `TRAINER_SCRIPT`, `LOCAL_REWARD_DATA` (MinIO mount point), and `MINIO_ADAPTER_PATH` (MinIO mount point).
6.  **Set Permissions**: Ensure all `.sh` and `.py` scripts are executable (`chmod +x`).
7.  **Setup Training Data Collection**: Implement the mechanism within Kulu to collect interaction data and save it to `rewarded.jsonl` in the designated MinIO bucket.
8.  **(Deferred) Enable Training Timer**: *Initially, test the trigger manually*. Due to system limitations on scheduled tasks, plan to use an external scheduler or local node trigger to run `check_and_train.py` nightly post-deployment, instead of enabling the systemd timer.
9.  **Testing**: Manually run `check_and_train.py` with sufficient dummy data in `rewarded.jsonl`. Verify GPU node creation, data transfer, script execution (`train.sh`), adapter transfer back to MinIO, and node shutdown.

**Deliverable**: Prepared GPU snapshot, configured trigger scripts, and a tested manual workflow for LoRA training.

## Phase 4: GPU Burst & Dispatcher Integration (Week 6)

**Objective**: Enable on-demand GPU bursting for heavy/vision tasks by integrating dispatcher rules.

**Tasks**:
1.  **Integrate Dispatcher Rules**: Load and parse `config/dispatcher_rules.yaml` within Kulu's task routing logic.
2.  **Implement GPU Node Check**: Add logic to the dispatcher to check if a GPU node (with label `role=gpu-burst`) is already running before potentially creating a new one.
3.  **Implement On-Demand GPU Boot**: Integrate a call to `hetzner_gpu_boot.sh` (or a modified version for inference-only) when a task matches a `needs_gpu: true` rule and no GPU node is active.
4.  **Implement Idle Shutdown**: Ensure the GPU node snapshot includes a mechanism (e.g., a simple cron job or systemd timer *on the GPU node itself*) that triggers `hetzner_gpu_shutdown.sh` (or just `sudo shutdown -h now`) after ~30 minutes of inactivity (e.g., no incoming inference requests).
5.  **Configure Model Loading**: Ensure the GPU node automatically loads the required models (Qwen-30B-LoRA, Qwen-VL-Chat) via Ollama or similar upon boot.
6.  **Testing**: Submit tasks matching the dispatcher rules (heavy trade, large code, image input). Verify GPU node creation (if needed), task execution on the GPU node, and idle shutdown.

**Deliverable**: Functional on-demand GPU bursting for specific tasks integrated with Kulu's dispatcher.

## Phase 5: DSPy Optimization Loop Integration (Week 7-8)

**Objective**: Integrate the DSPy optimization script into the post-training workflow.

**Tasks**:
1.  **Modify `hetzner_gpu_boot.sh`**: Add a step *after* `train.sh` successfully completes to execute `infra/trainer/optimize_with_dspy.py`.
2.  **Refine DSPy Signature/Program**: Update `optimize_with_dspy.py` with a more accurate `KuluTaskSignature` and potentially a more complex DSPy program (e.g., `ChainOfThought`) based on the actual structure of `rewarded.jsonl` and target tasks.
3.  **Refine DSPy Metric**: Choose or implement a more robust evaluation metric than exact match for the `BootstrapFewShot` optimizer.
4.  **Implement DSPy Program Loading**: Add logic to Kulu agents (specifically those using the fine-tuned Qwen-30B model) to load and use the optimized DSPy program (`dspy_optimized_program.json`) from MinIO.
5.  **Testing**: Run the full training cycle. Verify that `optimize_with_dspy.py` runs after `train.sh`, saves the optimized program, and copies it to MinIO. Test agents using the optimized program.

**Deliverable**: Integrated DSPy optimization loop that runs after nightly LoRA training, with agents capable of loading and using the optimized DSPy program.

## Continuous Improvement (Ongoing)

- Monitor costs closely and adjust GPU usage/shutdown timers.
- Refine LoRA training data collection and filtering.
- Experiment with different DSPy optimizers and metrics.
- Update base models and dependencies as needed.
- Enhance security posture based on operational experience.
