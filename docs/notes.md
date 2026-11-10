# Reading notes

Human-written notes for approved records. Automatic excerpts are marked in the inbox.

## Automation of PCB autorouting via world-model reinforcement learning and freerouting integration

`dreamer-fr2026` · [Paper](https://doi.org/10.1016/j.eswa.2026.131424)

Integrates DreamerV3 world-model reinforcement learning with FreeRouting for PCB autorouting and net-order planning. Reported completion and generalization results belong to its own experimental setup and should not be treated as directly comparable to PCBWorld clean-pass scores.

## HWE-Bench: Can Language Models Perform Board-level Schematic Designs?

`hwe-bench2026` · [Paper](https://arxiv.org/abs/2603.18102)

Benchmarks board-level schematic generation using real IC datasheets, static electrical-rule checks, and dynamic circuit simulation. The full title distinguishes it from unrelated projects with similar names.

## ModuPlace: LLM-Assisted Modular PCB Placement via Preference-Optimized Constraint Graph Generation

`moduplace2026` · [Paper](https://yhhan.com/PDFs/ModuPlace_paper.pdf)

Uses hierarchical module partitioning and constraint-graph generation for PCB placement. Fine-tuning and preference optimization incorporate expert design preferences into placement decisions.

## Multi-agent based minimal-layer via routing algorithm for PCB design

`mlv-cbs2026` · [Paper](https://doi.org/10.1016/j.vlsi.2025.102533)

Adapts conflict-based multi-agent path finding to minimize routing layers and vias with adaptive map partitioning. It is symbolic multi-agent search, not deep reinforcement learning.

## OmniRouting: A Semantic-Coupled Multimodal Benchmark for Constraint-Aware Spatial Reasoning in PCB Routing

`omnirouting2026` · [Paper](https://arxiv.org/abs/2608.04434)

Combines schematic semantics with PCB geometry, connectivity, and manufacturing constraints to evaluate geometric reasoning, design-rule compliance, electrical functionality, and tool-assisted routing.

## PCB-Bench: Benchmarking LLMs for Printed Circuit Board Placement and Routing

`pcb-bench2026` · [Paper](https://openreview.net/forum?id=Q5QLu7XTWx)

Evaluates PCB design knowledge through text questions, multimodal reasoning, and real-design comprehension. Its reasoning tasks complement benchmarks that execute routes and check design-rule compliance.

## PCB-Migrator: Automated PCB PnR Migration

`pcb-migrator2026` · [Paper](https://yhhan.com/PDFs/PCB-Migrator_paper.pdf)

Adapts expert PCB layouts to changed board boundaries and obstacles. Offset constraint graphs preserve component relationships, while routing-path graphs and graph matching guide route migration.

## PCBRouteAgent: How Close Are LLM Agents to Becoming PCB Routing Engineers?

`pcbrouteagent2026` · [Paper](https://arxiv.org/abs/2611.08175)

Combines a multimodal global routing planner with a KiCad-based detailed executor. Structured failure feedback supports targeted replanning while preserving completed routes.

## PCBSchemaGen: Reward-Guided LLM Code Synthesis for Printed Circuit Boards \(PCB\) Schematic Design with Structured Verification

`pcbschemagen2026` · [Paper](https://arxiv.org/abs/2602.00510)

Uses datasheet-derived domain knowledge, a deterministic layered verifier, and reward-guided inference-time refinement for PCB schematic code synthesis. The catalog uses the arXiv v2 title; the earlier Constraint-Guided Schematic Design via LLM title refers to the same work.

## PCBWorld: A Benchmark Environment for Engine-Grounded PCB Design Automation

`pcbworld2026` · [Paper](https://arxiv.org/abs/2607.05915)

An interactive PCB routing environment built on KiCad's native engine and DRC feedback, with synthetic and real-board benchmarks for comparing reinforcement learning, tool-using agents, and rule-based routers.

## SchGen: PCB Schematic Generation with Semantic-Grounded Code Representations

`schgen2026` · [Paper](https://arxiv.org/abs/2605.30345)

Introduces a semantic code representation based on relative placement and pin-name wiring for generating editable PCB schematics from natural-language requirements, together with a dataset construction pipeline.

## Security-oriented printed-circuit-board routing with deep reinforcement learning

`security-routing2026` · [Paper](https://doi.org/10.1016/j.vlsi.2025.102602)

Combines A\*-based multilayer routing with DQN-guided test-point insertion to support board testing and security assessment. The learned component selects test points; routing itself uses classical search.

## ST-GAT: A Spatial-Temporal Graph Attention Network for Multi-Agent Reinforcement Learning-Based PCB Routing

`st-gat2026` · [Paper](https://doi.org/10.1109/ecie69549.2026.11565623)

Proposes spatial-temporal graph-attention multi-agent reinforcement learning for routing coordination. The publisher abstract reports ISPD benchmark evaluation; board-specific coverage and reproducibility need further full-text inspection.

## Surveying GenAI-based Automation in Printed Circuit Board Design and Test

`genai-pcb-survey2026` · [Paper](https://arxiv.org/abs/2606.17074)

Surveys generative AI across the PCB life cycle, including circuit design, layout, validation, and testing. Useful for placing routing research within the wider board-level design workflow.

## A Pad-Focused PCB Routing Algorithm Using Polygon-Based Dynamic Partitioning

`pad-focused-routing2025` · [Paper](https://doi.org/10.1109/access.2024.3386921)

Combines MCTS global routing with A\* detailed routing and dynamic polygon partitioning to coordinate pad-to-pad routing. This is search-based routing. The catalog uses the final volume year 2025; early publication was in 2024.

## Applying Existing Large Language Models for Print Circuit Board Routing

`llm-routing2025` · [Paper](https://doi.org/10.3390/engproc2025086002)

Explores few-shot prompting, chain-of-thought examples, and synthetic-data fine-tuning for simple PCB routing scenarios. Its small routing examples do not establish industrial full-board routing capability; the proceedings publication year is 2025.

## GPCB Routing: Generative Pretrained Transformers-Based Printed Circuit Board Routing Method

`gpcb2025` · [Paper](https://doi.org/10.1109/TCAD.2024.3486241)

Applies generative pretrained transformers to PCB routing. The catalog uses the final journal-volume year, 2025, rather than the 2024 registration year embedded in its DOI.

## Intelligent Ordered Escape Routing via Deep Reinforcement Learning and Hybrid Heuristics

`ordered-escape2025` · [Paper](https://doi.org/10.1109/cei66465.2025.11398471)

Uses PPO to select ordered escape endpoints and a hybrid artificial-potential-field/A\* method to construct paths. Conference year 2025 is retained despite IEEE indexing the record in 2026.

## PCBAgent: An Agent-based Framework for High-Density Printed Circuit Board Placement

`pcb-agent2025` · [Paper](https://doi.org/10.1145/3658617.3697736)

An agent-based framework for high-density PCB component placement, connecting research on placement automation with downstream routability and routing tasks.

## Reinforcement Learning Based PCB Routing Using Dueling Double Deep Q Network

`d3qn2024` · [Paper](https://doi.org/10.1109/icicm63644.2024.10814351)

Applies multi-agent reinforcement learning with local observations and a dueling double deep Q-network to PCB routing. Local observation and agent coordination are central aspects of its formulation.

## Routing Generative Pre-Trained Transformers for Printed Circuit Board

`prg2024` · [Paper](https://doi.org/10.1109/iseda62518.2024.10617906)

Tokenizes PCB routing flow encodings and predicts routing patterns with a generative pretrained transformer. This conference paper and the later GPCB journal article are related works with distinct publication identities.

## SER-NET: A Neuralize PCB Simulataneous Escape Routing Method Using Deep Reinforcement Learning

`ser-net2024` · [Paper](https://doi.org/10.1109/icicm63644.2024.10814469)

Combines learned escape-endpoint assignment with congestion-negotiated routing for simultaneous PCB escape routing. Uses graph and attention representations with policy optimization; the published title retains the spelling Simulataneous.

## Consumer Electronics Product Manufacturing Time Reduction and Optimization Using AI-Based PCB and VLSI Circuit Designing

`ai-pcb-vlsi-survey2023` · [Paper](https://doi.org/10.1109/tce.2023.3240249)

Reviews AI-assisted PCB and VLSI placement and routing for manufacturing productivity. This is a survey spanning both boards and chips, not a new PCB reinforcement-learning router.

## FanoutNet: A Neuralized PCB Fanout Automation Method Using Deep Reinforcement Learning

`fanoutnet2023` · [Paper](https://doi.org/10.1609/aaai.v37i7.26030)

Applies deep reinforcement learning to PCB fanout automation. Fanout and escape routing form a distinct task family with different inputs, action spaces, and evaluation criteria from full-board routing.

## TRouter: Thermal-Driven PCB Routing via Nonlocal Crisscross Attention Networks

`trouter2023` · [Paper](https://doi.org/10.1109/tcad.2023.3243544)

Uses a nonlocal crisscross-attention thermal predictor and its gradients to guide wire detours and via decisions. Thermal-aware routing illustrates why wirelength and connectivity alone are incomplete design objectives.

## Net Separation-Oriented Printed Circuit Board Placement via Margin Maximization

`ns-place2022` · [Paper](https://arxiv.org/abs/2210.14259)

Optimizes PCB placement through net separation and congestion reduction using margin maximization. Provides a reference for evaluating routability during placement.

## A Unified Printed Circuit Board Routing Algorithm With Complicated Constraints and Differential Pairs

`unified-routing2021` · [Paper](https://doi.org/10.1145/3394885.3431568)

Studies PCB routing with complex constraints and differential pairs, providing a classical algorithmic reference for learning-based and agent-based routing methods.

## A Hierarchy MCTS Algorithm for The Automated PCB Routing

`hierarchy-mcts2020` · [Paper](https://doi.org/10.1109/icca51439.2020.9264558)

Uses hierarchical Monte Carlo tree search to select coarse subgoals and refine PCB routing paths. This is AI search rather than a trained neural routing policy.

## Advances in PCB Routing

`pcb-routing-survey2012` · [Paper](https://doi.org/10.2197/ipsjtsldm.5.14)

Reviews classical PCB routing research, particularly escape routing and length matching. Provides problem definitions and historical context for modern AI-assisted routing.

## An Algorithm for Path Connections and Its Applications

`lee1961` · [Paper](https://doi.org/10.1109/TEC.1961.5219222)

A foundational maze-routing algorithm for path connection problems. Included as background for PCB path search rather than as a board-specific benchmark.
