# Analysis of Kulu Pre-Deployment Upgrade Requirements

This document analyzes the requirements provided by the user for upgrading the Kulu Node Orchestration System. Although termed "pre-deployment upgrades," the nature of these features (LoRA training, GPU bursting, budget guards) and the request for a *post-deployment* roadmap suggest they are enhancements to be implemented *after* the core Kulu system (including Strategic Breath Layer + Shia Integration) is operational.

## 1. Core Goal

Extend the operational Kulu system with:
- **Nightly LoRA Training**: Fine-tune a Qwen 3-30B model nightly using collected data.
- **On-Demand GPU Burst**: Dynamically spawn a GPU node (Hetzner AX161) for heavy compute (e.g., LoRA training) or vision tasks (using Qwen-VL-Chat).
- **OpenRouter Budget Guardrail**: Limit OpenRouter API usage for lightweight worker agents to a predefined budget ($30/month), falling back to a local small model (Qwen 3-1.8B) when the cap is reached.
- **Budget Constraint**: Keep the total monthly infrastructure cost under $150.

## 2. Model Lineup Analysis

- **Light (Oracle A1)**: Qwen 3-1.8B (4-bit) - For fast, low-cost reasoning on always-on nodes. Handles fallback when OpenRouter budget is exceeded.
- **Heavy Text (Hetzner GPU)**: Qwen 3-30B-A3B (4-bit) - Base model for nightly LoRA fine-tuning. Used for complex code/finance tasks when GPU node is active.
- **Vision (Hetzner GPU)**: Qwen-VL-Chat-14B (4-bit) - Activated specifically for image/screenshot analysis when `needs_vision=true`.
- **Elastic SaaS (OpenRouter)**: Various models (Gemini-2.5, Haiku) - Used by light workers for low-stakes tasks, strictly budget-controlled.

*Compatibility*: This lineup aligns with Kulu's multi-tier node structure and the need for specialized agents.

## 3. Compute Plan Analysis

- **Oracle Free Tier**: Hosts core Kulu components (anchors, scheduler, timers) at no cost.
- **Hetzner CX31 ($15/mo)**: Persistent small VM for essential services (Redis for state/budget tracking, MinIO for LoRA adapter storage, fallback worker capacity).
- **Hetzner AX161 GPU ($83/mo estimate)**: On-demand GPU node.
    - *LoRA Training*: ~4 hours/night triggered by Oracle timer. Estimated 120 hours/month.
    - *Heavy/Vision Inference*: Spawned on-demand based on dispatcher rules, with a 30-minute idle auto-shutdown.
    - *Cost Justification*: The estimate seems plausible based on Hetzner pricing, assuming efficient spawning/shutdown.
- **OpenRouter Cap ($30/mo)**: Hard limit enforced by a budget guardrail mechanism.
- **Total Estimated Cost**: ~$138/month, comfortably under the $150 target.

*Feasibility*: The compute plan is cost-effective and leverages on-demand resources efficiently. Requires robust automation for GPU node management.

## 4. Deliverables Analysis

The requested files form a coherent set of infrastructure-as-code components:
- `infra/gpu_boot/`: Scripts for booting (`hetzner_gpu_boot.sh`) and cleaning up (`hetzner_gpu_shutdown.sh`) the GPU node, referencing a snapshot ID (`snapshot_id.txt`).
- `infra/trainer/`: LoRA training script (`train.sh` using Unsloth) and dependencies (`requirements.txt`).
- `infra/oracle_timers/`: Systemd service (`kulu-train.service`) and timer (`kulu-train.timer`) to trigger training nightly via a check script (`check_and_train.py`).
- `Updated dispatcher YAML rules`: Logic to route tasks requiring GPU/Vision to the AX161 node.
- `Reward JSONL schema`: Definition for the data format used to collect examples for LoRA training.
- `README`: Instructions for setup, environment variables, and snapshot creation.

*Completeness*: These deliverables cover the core automation aspects of the GPU lifecycle and training process.

## 5. Code Snippets Analysis

- `hetzner_gpu_boot.sh`: Creates AX161 from snapshot, waits, gets IP, rsyncs training data, runs `train.sh` via SSH, rsyncs back LoRA adapter, schedules shutdown (+30 min). *Seems functional, needs error handling.* Requires `hcloud` CLI and `rsync`.
- `hetzner_gpu_shutdown.sh`: Finds stopped GPU servers via label and deletes them. *Simple cleanup, good safety measure.*
- `train.sh`: Activates conda env, runs Unsloth finetuning, calculates loss on a sample. *Standard LoRA training flow.*
- `requirements.txt`: Lists necessary Python packages for training.
- `kulu-train.service`/`.timer`: Standard systemd units for scheduled execution on the Oracle node.
- `check_and_train.py`: Checks if sufficient training data (`rewarded.jsonl` >= 2000 lines) exists before triggering `hetzner_gpu_boot.sh`. *Simple gatekeeping logic.*
- `Dispatch rules`: YAML defining conditions for routing tasks to the GPU node (`needs_gpu`, `needs_vision`).
- `OpenRouter budget guard`: Python concept using Redis to track spending and fall back to `local_qwen_small`. *Needs integration into Kulu's agent/LM calling mechanism.*

*Integration*: The snippets provide a solid base but need integration into Kulu's existing orchestration (e.g., dispatcher, agent LM client).

## 6. Security Defaults Analysis

- **Podman**: Standard hardening flags (`--cap-drop=ALL`, `--read-only`, `no-new-privileges`).
- **Tailnet ACL**: Restricts inter-node communication to essential ports (SSH, Ollama, MinIO). Critically, blocks internet egress for the GPU node, enhancing security during training.
- **Storage**: LUKS encryption for volumes and MinIO SSE-S3 for data at rest.

*Sufficiency*: These provide a reasonable baseline security posture.

## 7. DSPy Integration Context

The user wants DSPy integrated alongside these upgrades. Key opportunities:
- **Optimizing LoRA**: DSPy optimizers could potentially refine prompts *for* the fine-tuned Qwen-30B LoRA model, using the same `rewarded.jsonl` data or evaluation metrics derived from it.
- **Optimizing Base Models**: DSPy could optimize prompts for the base Qwen-1.8B (fallback) and the OpenRouter models used by light workers.
- **Data Feedback Loop**: The data collection for LoRA (`rewarded.jsonl`) could also serve as training/evaluation data for DSPy optimizers.

## 8. Conclusion

The requirements are well-defined and technically feasible within the specified budget. They represent significant enhancements to Kulu's capabilities, particularly in specialized model usage and cost management. The implementation should focus on robust automation for the GPU node lifecycle and careful integration of the budget guardrail and dispatcher rules into Kulu's core logic. DSPy integration should be planned alongside these upgrades, leveraging the new data sources and compute capabilities.
