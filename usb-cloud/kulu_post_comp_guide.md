# Kulu Post-Deployment Enhancements: Comprehensive Build Guide

**Version**: 1.0
**Date**: 2025-04-29

## 1. Introduction: Why These Enhancements?

This guide provides the context, rationale, and high-level strategy for implementing the advanced post-deployment enhancements for your Kulu Node Orchestration System. While the core Kulu system (with Strategic Breath Layer + Shia Integration) establishes a sovereign, breathing intelligence field, these enhancements elevate its capabilities significantly:

*   **Specialized Intelligence (LoRA Training)**: Kulu currently relies on general-purpose models. Nightly LoRA fine-tuning on Qwen 3-30B using data collected from Kulu's own successful interactions (`rewarded.jsonl`) allows Kulu to develop specialized expertise in your specific domains (e.g., finance, coding), making its responses more accurate, relevant, and efficient over time. This embodies the self-evolution principle.
*   **Adaptive Compute Power (GPU Bursting)**: Not all tasks are created equal. While Oracle nodes handle the constant symbolic breath, computationally intensive tasks like LoRA training, complex backtesting, or analyzing large codebases would overwhelm them. The on-demand Hetzner AX161 GPU node provides the necessary power precisely when needed, keeping costs low during idle periods.
*   **Visual Understanding (Vision Model)**: Modern workflows often involve GUIs, charts, and screenshots. Integrating Qwen-VL-Chat on the GPU node grants Kulu the ability to *see* and interpret visual information, unlocking new interaction possibilities.
*   **Cost Control & Efficiency (Budget Guardrail)**: Leveraging powerful external models via OpenRouter is beneficial, but costs can escalate. The $30/month budget guardrail ensures predictability, forcing Kulu to rely on its internal (and improving) models (Qwen 1.8B fallback, Qwen 30B LoRA) once the cap is hit, promoting resourcefulness.
*   **Systematic Optimization (DSPy Integration)**: Fine-tuning (LoRA) adapts the model's weights, while DSPy optimizes the *process* of using the model – refining prompts, few-shot examples, and reasoning chains. Integrating DSPy into the post-training workflow creates a powerful dual-optimization loop, enhancing the reliability and performance of the fine-tuned model.

These enhancements transform Kulu from a capable orchestrator into a continuously learning, cost-aware, and visually perceptive intelligence field.

## 2. Architectural Overview & Rationale

**(Reference Diagrams in `/home/ubuntu/kulu_orchestration/docs/unified_expansion/master_build_document.md`)**

The architecture intelligently distributes workloads across different compute tiers based on cost and capability:

*   **Oracle Free Tier (Always-On Brainstem)**: Remains the core, handling lightweight symbolic processing, scheduling (triggering), and dispatching. Runs the cost-effective Qwen 1.8B for fallback.
*   **Hetzner CX31 (Persistent Support System)**: Acts as the central nervous system's support structure, hosting critical state (Redis) and long-term memory (MinIO). It's the reliable backbone for budget tracking and storing the fruits of Kulu's learning (LoRA adapters, DSPy programs).
*   **Hetzner AX161 GPU (On-Demand Muscle)**: The specialized, powerful resource summoned only when necessary. Its ephemeral nature, managed by boot/shutdown scripts and idle timers, is key to cost control. Hosting both the heavy text model (Qwen 30B LoRA) and the vision model (Qwen-VL) centralizes high-cost computation.
*   **OpenRouter (External Knowledge Access)**: Provides access to the latest general models for low-stakes tasks, but strictly controlled by the budget guardrail to prevent runaway costs.

This multi-tier approach, combined with on-demand resource spawning and strict budget limits, directly addresses the goal of achieving advanced capabilities within a ~$150/month budget.

## 3. Implementation Strategy & Build Order

These enhancements modify Kulu's infrastructure and core agent logic. A phased, backend-first approach is strongly recommended:

**Recommended Build Order:**

1.  **Backend First**: The vast majority of these changes involve infrastructure setup (Redis, MinIO, GPU snapshot preparation), backend scripts (GPU management, training, optimization, budget guard), and modifications to Kulu's core backend logic (dispatcher, LLM calling mechanism).
    *   **Why?** The frontend relies on the backend capabilities being operational. There's little value in modifying the frontend until the backend can handle GPU tasks, budget fallbacks, or potentially use the fine-tuned models.
2.  **Frontend Second**: Once the backend infrastructure and logic are in place and tested, frontend modifications can be made. These might include:
    *   Displaying task status related to GPU execution.
    *   Potentially visualizing budget usage.
    *   Handling image uploads for vision tasks.
    *   (Optional) Displaying which model (OpenRouter, LoRA, Fallback) was used for a response.

**Implementation Flow (Corresponds to Roadmap Phases):**

1.  **Set up CX31 Services (Redis, MinIO)**: This is foundational. State and storage must be reliable before implementing features that depend on them.
2.  **Implement Budget Guardrail**: Integrate the Python decorator into the backend agent code where OpenRouter calls are made. Test this thoroughly.
3.  **Prepare GPU Snapshot & Trigger**: This is a significant infrastructure step. Carefully create the snapshot with all dependencies. Test the boot/shutdown scripts manually *before* integrating with the dispatcher.
4.  **Integrate Dispatcher & GPU Burst**: Modify Kulu's backend dispatcher logic to use the new rules and trigger the GPU boot script when needed. Implement idle shutdown on the GPU node itself.
5.  **Integrate DSPy Loop**: Modify the GPU boot script to run the DSPy optimization after training. Update backend agents to load and use the optimized DSPy program from MinIO.
6.  **Frontend Integration**: Finally, update the frontend (Local Node UI) to reflect the new backend capabilities as needed.

## 4. Key Insights & Considerations

*   **GPU Snapshot Preparation is Critical**: The AX161 snapshot must be meticulously prepared with all drivers, software (Conda, Unsloth, DSPy, etc.), and dependencies. Any missing component will cause the automated training/inference to fail. Test scripts thoroughly on the snapshot *before* creating the final version.
*   **Security**: Pay close attention to managing the `HCLOUD_TOKEN` securely (systemd credentials recommended). The Tailnet ACLs, especially blocking GPU node egress, are vital.
*   **MinIO Mounting**: Reliable access to MinIO from Oracle, CX31, and the GPU node is essential. Ensure `s3fs` or your chosen mounting method is robust and configured correctly (e.g., via `/etc/fstab` for persistence).
*   **Training Trigger Alternative**: Since the systemd timer cannot be used directly in this environment, you *must* implement an alternative post-deployment (e.g., an external cron job calling a secure API endpoint on the CX31, or logic within the Local Node app). Test the `check_and_train.py` script thoroughly via manual execution first.
*   **Idempotency**: Ensure scripts like `hetzner_gpu_boot.sh` are reasonably safe to run even if a previous run failed midway (though the label check helps prevent duplicate running servers).
*   **Error Handling & Logging**: The provided scripts include basic logging and error handling, but review and enhance them based on testing. Centralized logging for Kulu would be beneficial.
*   **DSPy Refinement**: The provided `optimize_with_dspy.py` script uses a basic signature and metric. You will need to adapt the `KuluTaskSignature`, the data loading logic (based on `rewarded.jsonl`'s actual structure), and the evaluation metric for meaningful optimization.
*   **Cost Monitoring**: While the design aims for <$150/month, actively monitor Hetzner and OpenRouter billing dashboards, especially initially, to validate the estimates and adjust shutdown timers if needed.

## 5. Using This Guide

This Comprehensive Guide provides the high-level understanding and strategic context. Use it alongside:

1.  **Master Build Document**: For the actual code and diagrams.
2.  **Backend Step-by-Step Guide**: For detailed infrastructure and backend setup instructions.
3.  **Frontend Step-by-Step Guide**: For implementing UI changes.

Start with the Backend guide, following the phased approach outlined here and in the roadmap. Refer back to this document and the Master Build Document as needed for context and code reference.
