"""The initial curated snapshot, verified on 2026-11-10. Does not overwrite a catalog."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pcb_lit.core import catalog_category, record, write_json

ROOT = Path(__file__).resolve().parent.parent
REF = "https://arxiv.org/html/2611.08175v1#bib"
MOD = "https://yhhan.com/PDFs/ModuPlace_paper.pdf"


def seed(key, title, authors, year, url, tasks, methods, note, *, ids=None,
         venue="", kind="preprint", evidence="", links=None, sources=None):
    p = record(title, authors.split("; "), year, url, "manual-primary-source", identifiers=ids)
    p.update(id=key, status="approved", tasks=tasks.split(), methods=methods.split(),
             summary=note, summary_kind="human", venue=venue, publication_type=kind,
             venue_verified=bool(evidence), verified_on="2026-11-10", discovered_on="2026-11-10",
             links=links or {})
    if evidence:
        p["venue_evidence"] = evidence
    if sources:
        p["sources"] += [{"provider": "manual-reference-check", "url": s} for s in sources]
    p["category"] = catalog_category(p)
    return p


papers = [
    seed("pcbworld2026", "PCBWorld: A Benchmark Environment for Engine-Grounded PCB Design Automation",
         "Hyungseok Song; Junseok Park; Won-Seok Choi; Seohui Bae; Han-Seul Jeong; Youngjoon Park; Soonyoung Lee",
         2026, "https://arxiv.org/abs/2607.05915", "routing benchmark constraints", "rl llm-agent",
         "An interactive PCB routing environment built on KiCad's native engine and DRC feedback, with synthetic and real-board benchmarks for comparing reinforcement learning, tool-using agents, and rule-based routers.",
         ids={"arxiv": ["2607.05915"]}, venue="KDD 2026 Workshop on Evaluation and Trustworthiness of Agentic AI",
         kind="workshop", evidence="https://github.com/LGAI-Research/PCBWorld",
         links={"code": "https://github.com/LGAI-Research/PCBWorld"}),
    seed("pcbrouteagent2026", "PCBRouteAgent: How Close Are LLM Agents to Becoming PCB Routing Engineers?",
         "Yue Zhang; Jilei Sun; Liqiang Jing; Yijie Wei; Ruohan Yang", 2026,
         "https://arxiv.org/abs/2611.08175", "routing constraints", "llm-agent",
         'Combines a multimodal global routing planner with a KiCad-based detailed executor. Structured failure feedback supports targeted replanning while preserving completed routes.',
         ids={"arxiv": ["2611.08175"]}, links={"code": "https://github.com/chip-ai-agent/PCBRouteAgent"}),
    seed("pcbschemagen2026", "PCBSchemaGen: Reward-Guided LLM Code Synthesis for Printed Circuit Boards (PCB) Schematic Design with Structured Verification",
         "Huanghaohe Zou; Peng Han; Emad Nazerian; Mafu Zhang; Zhicheng Guo; Alex Q. Huang", 2026,
         "https://arxiv.org/abs/2602.00510", "schematic constraints benchmark", "llm-agent",
         'Uses datasheet-derived domain knowledge, a deterministic layered verifier, and reward-guided inference-time refinement for PCB schematic code synthesis. The catalog uses the arXiv v2 title; the earlier Constraint-Guided Schematic Design via LLM title refers to the same work.',
         ids={"arxiv": ["2602.00510"]}, links={"code": "https://github.com/HZou9/PCBSchemaGen_v2"}),
    seed("pcb-migrator2026", "PCB-Migrator: Automated PCB PnR Migration",
         "Yaohui Han; Beichen Li; Rongliang Fu; Qunsong Ye; Zhiyuan Lu; Junchen Liu; Bei Yu; Tsung-Yi Ho; Tinghuan Chen", 2026,
         "https://yhhan.com/PDFs/PCB-Migrator_paper.pdf", "migration placement routing constraints", "classical",
         'Adapts expert PCB layouts to changed board boundaries and obstacles. Offset constraint graphs preserve component relationships, while routing-path graphs and graph matching guide route migration.',
         ids={"doi": ["10.23919/date69613.2026.11539307"]}, venue="DATE 2026", kind="conference", evidence="https://yhhan.com/"),
    seed("schgen2026", "SchGen: PCB Schematic Generation with Semantic-Grounded Code Representations",
         "Qinpei Luo; Ruichun Ma; Xinyu Zhang; Lili Qiu", 2026, "https://arxiv.org/abs/2605.30345",
         "schematic benchmark", "llm-agent",
         'Introduces a semantic code representation based on relative placement and pin-name wiring for generating editable PCB schematics from natural-language requirements, together with a dataset construction pipeline.',
         ids={"arxiv": ["2605.30345"]}),
    seed("pcb-bench2026", "PCB-Bench: Benchmarking LLMs for Printed Circuit Board Placement and Routing",
         "Jindong Li; Lianrong Chen; Bin Yang; Jiadong Zhu; Ying Wang; Yuzhe Ma; Menglin Yang", 2026,
         "https://openreview.net/forum?id=Q5QLu7XTWx", "benchmark placement routing", "llm-agent",
         'Evaluates PCB design knowledge through text questions, multimodal reasoning, and real-design comprehension. Its reasoning tasks complement benchmarks that execute routes and check design-rule compliance.',
         ids={"openreview": ["Q5QLu7XTWx"]}, venue="ICLR 2026", kind="conference",
         evidence="https://proceedings.iclr.cc/paper_files/paper/2026/hash/051f3997af1dd65da8e14397b6a72f8e-Abstract-Conference.html",
         links={"code": "https://github.com/digailab/PCB-Bench"}),
    seed("hwe-bench2026", "HWE-Bench: Can Language Models Perform Board-level Schematic Designs?",
         "Weibo Qiu; Yinhao Xiao; Runyu Pan", 2026, "https://arxiv.org/abs/2603.18102",
         "schematic benchmark constraints", "llm-agent",
         'Benchmarks board-level schematic generation using real IC datasheets, static electrical-rule checks, and dynamic circuit simulation. The full title distinguishes it from unrelated projects with similar names.',
         ids={"arxiv": ["2603.18102"]}, links={"code": "https://github.com/EDI-Systems/HWE-Bench"}),
    seed("omnirouting2026", "OmniRouting: A Semantic-Coupled Multimodal Benchmark for Constraint-Aware Spatial Reasoning in PCB Routing",
         "Taiting Lu; Kaiyuan Lin; Ziwei Dong; Sisong Bei; Haolin Ye; Yuxin Tian; Runze Liu; Mingjia Wang; Jingying Zeng; Hongxing Pan; Kai Zhang; Haoyu Wang; Guoliang Shi; Ling Ma; Yifan Yang; Jiaying Lu; Qi He; Yi-Chao Chen; Sung-Liang Chen; Yincheng Jin; Mahanth Gowda", 2026,
         "https://arxiv.org/abs/2608.04434", "routing benchmark constraints", "llm-agent",
         'Combines schematic semantics with PCB geometry, connectivity, and manufacturing constraints to evaluate geometric reasoning, design-rule compliance, electrical functionality, and tool-assisted routing.',
         ids={"arxiv": ["2608.04434"]}, links={"project": "https://www.omnieda.com/routing/"}),
    seed("moduplace2026", "ModuPlace: LLM-Assisted Modular PCB Placement via Preference-Optimized Constraint Graph Generation",
         "Yaohui Han; Beichen Li; Mingyang Zhao; Rongliang Fu; Qunsong Ye; Tinghuan Chen; Bei Yu; Tsung-Yi Ho", 2026,
         MOD, "placement constraints", "classical llm-agent rl",
         'Uses hierarchical module partitioning and constraint-graph generation for PCB placement. Fine-tuning and preference optimization incorporate expert design preferences into placement decisions.',
         ids={"doi": ["10.1145/3770743.3803892"]}, venue="DAC 2026", kind="conference", evidence=MOD),
    seed("lee1961", "An Algorithm for Path Connections and Its Applications",
         "C. Y. Lee", 1961, "https://doi.org/10.1109/TEC.1961.5219222", "routing foundations", "classical",
         'A foundational maze-routing algorithm for path connection problems. Included as background for PCB path search rather than as a board-specific benchmark.',
         ids={"doi": ["10.1109/tec.1961.5219222"]}, venue="IRE Transactions on Electronic Computers", kind="journal", sources=[REF]),
    seed("unified-routing2021", "A Unified Printed Circuit Board Routing Algorithm With Complicated Constraints and Differential Pairs",
         "Ting-Chou Lin; Devon Merrill; Yen-Yi Wu; Chester Holtz; Chung-Kuan Cheng", 2021,
         "https://doi.org/10.1145/3394885.3431568", "routing constraints", "classical",
         'Studies PCB routing with complex constraints and differential pairs, providing a classical algorithmic reference for learning-based and agent-based routing methods.',
         ids={"doi": ["10.1145/3394885.3431568"]}, venue="ASP-DAC 2021", kind="conference", sources=[REF]),
    seed("fanoutnet2023", "FanoutNet: A Neuralized PCB Fanout Automation Method Using Deep Reinforcement Learning",
         "H. Li; J. Zhang; N. Xu; M. Liu", 2023, "https://doi.org/10.1609/aaai.v37i7.26030",
         "routing escape-fanout", "rl neural",
         'Applies deep reinforcement learning to PCB fanout automation. Fanout and escape routing form a distinct task family with different inputs, action spaces, and evaluation criteria from full-board routing.',
         ids={"doi": ["10.1609/aaai.v37i7.26030"]}, venue="AAAI 2023", kind="conference", sources=[REF]),
    seed("gpcb2025", "GPCB Routing: Generative Pretrained Transformers-Based Printed Circuit Board Routing Method",
         "J. Chen; J. Tu; H. Wang; J. Zheng; H. Liu; S. Bai; X. He; W. Qian", 2025,
         "https://doi.org/10.1109/TCAD.2024.3486241", "routing", "neural",
         'Applies generative pretrained transformers to PCB routing. The catalog uses the final journal-volume year, 2025, rather than the 2024 registration year embedded in its DOI.',
         ids={"doi": ["10.1109/tcad.2024.3486241"]}, venue="IEEE TCAD 44(4), 2025", kind="journal", sources=[REF]),
    seed("pcb-agent2025", "PCBAgent: An Agent-based Framework for High-Density Printed Circuit Board Placement",
         "L. Chen; R. Chen; S. Hu; X. Yao; Z. Tang; S. Kai; S. Xu; M. Yuan; J. Hao; B. Yu; J. Xu", 2025,
         "https://doi.org/10.1145/3658617.3697736", "placement", "llm-agent rl",
         'An agent-based framework for high-density PCB component placement, connecting research on placement automation with downstream routability and routing tasks.',
         ids={"doi": ["10.1145/3658617.3697736"]}, venue="ASP-DAC 2025", kind="conference", sources=[REF, MOD]),
    seed("ns-place2022", "Net Separation-Oriented Printed Circuit Board Placement via Margin Maximization",
         "Chung-Kuan Cheng; Chia-Tung Ho; Chester Holtz", 2022,
         "https://arxiv.org/abs/2210.14259", "placement constraints", "classical",
         'Optimizes PCB placement through net separation and congestion reduction using margin maximization. Provides a reference for evaluating routability during placement.',
         ids={"arxiv": ["2210.14259"], "doi": ["10.1109/asp-dac52403.2022.9712480"]},
         venue="ASP-DAC 2022", kind="conference", sources=[MOD],
         evidence="https://www.aspdac.com/aspdac2022/taoka/program/program_abst.html")
]

edges = [{"citing": "pcbrouteagent2026", "cited": k, "source": "manual-reference-check"}
         for k in ["pcbworld2026", "lee1961", "unified-routing2021", "fanoutnet2023", "gpcb2025", "pcb-agent2025", "pcb-bench2026", "omnirouting2026"]]
edges += [{"citing": "moduplace2026", "cited": k, "source": "manual-reference-check"}
          for k in ["pcb-migrator2026", "ns-place2022", "pcb-agent2025"]]

if __name__ == "__main__":
    target = ROOT / "data/papers.json"
    if target.exists():
        raise SystemExit("Catalog exists; bootstrap aborted to preserve editorial work.")
    write_json(target, sorted(papers, key=lambda p: p["id"]))
    write_json(ROOT / "data/relations.json", sorted(edges, key=lambda e: (e["citing"], e["cited"])))
    print(f"Created {len(papers)} seeds and {len(edges)} checked citation edges")
