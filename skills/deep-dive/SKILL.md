---
name: deep-dive
description: "Execute in-depth domain research. Collect professional information through multiple rounds of web searches and organize it into a series of structured Markdown documents. Supports local repository analysis when codebase is provided. Excels at mathematical derivation, engineering implementation comparison, and Mermaid visualization. Suitable for scenarios requiring comprehensive mastery of new technologies, algorithms, or complex concepts."
---

# Deep Dive Research Skill

## Skill Purpose
This skill is designed for executing in-depth domain research, aiming to systematically present a technical topic from concept, theory, and implementation to engineering deployment.

Core capabilities include: multi-round web/academic retrieval, horizontal comparison of key papers and implementations, detailed mathematical derivations with variable mappings, engineering implementations (including runnable examples), and visualization with experimental suggestions. The final output is a series of structured Markdown documents that help readers reproduce, evaluate, and optimize or improve upon the technology.

Optional perspectives (adjustable based on user needs): Theory-first / Engineering-first / Performance-optimization-first / Application-scenario-first.

## Core Workflow
When a user proposes a research topic, you must strictly follow these four phases:

### Phase 0: Local Repository Analysis (Conditional - When Local Code Base is Provided)
**Trigger**: If the user provides a local codebase path or uploads project files.

1. **Repository Structure Scanning**:
   - Analyze the directory structure to identify key modules, entry points, and configuration files.
   - Detect the programming language(s), framework versions (via `requirements.txt`, `package.json`, `Cargo.toml`, etc.), and build systems.
2. **Codebase Understanding**:
   - Identify core classes, functions, and data flow patterns.
   - Extract existing documentation (README, docstrings, comments) to understand current implementation intent.
   - Map out dependency graphs between modules.
3. **Gap Analysis**:
   - Compare the local implementation against known best practices or official references found during web search.
   - Identify potential bugs, performance bottlenecks, or missing features in the local code.
4. **Integration with Research Plan**:
   - Incorporate findings from the local code analysis into the `Research Plan`.
   - Tailor the research questions to address specific issues or extensions relevant to the user's local codebase.
   - Use the local code as the baseline for "Engineering Implementation" sections, suggesting concrete improvements rather than generic examples.

*Note: If no local code is provided, skip this phase and proceed directly to Phase 1.*

### Phase 1: Global Planning and Architecture Design (Planning)
1. **Preliminary Exploration and Noise Filtering**:
   - Use Web Search for broad exploration.
   - **Key Action**: Identify and filter out marketing content, outdated tutorials, and low-quality SEO content. Prioritize ArXiv papers, official documentation, high-star GitHub repositories, and tech giant blogs (e.g., AWS, Meta AI, Hugging Face).
2. **Knowledge Graph Construction**:
   - Identify core concepts, prerequisite knowledge, key mathematical principles, and engineering challenges.
3. **Documentation Structure Design**:
   - For complex topics, design a multi-level directory structure.
   - Generate a detailed `Research Plan` including:
     - **Root directory tree**.
     - **Filename, title, and core coverage points for each sub-document**.
     - **Key Questions List**: 5-10 core technical questions this research must answer.
4. **User Confirmation**: Present the plan to the user and ask if adjustments are needed (e.g., more focus on mathematical derivation vs. engineering implementation).

### Phase 2: In-depth Research and Content Generation (Execution)
For each module in the plan, execute the following steps:

1. **Critical Directed Search**:
   - **Academic/Official**: Search `[Topic] paper`, `[Topic] official documentation`, `[Topic] arxiv`.
   - **Engineering/Practical**: Search `[Topic] pytorch implementation`, `[Topic] tensorrt optimization`, `[Topic] source code analysis`.
   - **Community/Pitfalls**: Mandatory search `site:zhihu.com [Topic] pitfalls`, `site:juejin.cn [Topic] best practices`, `[Topic] common mistakes`, `[Topic] limitations`.
   - **Adversarial Validation**: Search `[Topic] vs [Alternative] benchmark` to understand disadvantages and applicable boundaries.

2. **Information Synthesis and Verification**:
   - Cross-verify different sources. If engineering tips from Zhihu conflict with official documentation, analyze the reasons (e.g., version differences, specific hardware environments).
   - Extract key mathematical principles and prepare them in LaTeX format.
   - Extract key engineering implementation details and prepare runnable code snippets.
   - **Record Sources**: When extracting information, always retain the original URL for generating citation links later.

3. **Modular Writing (Strict Writing Standards)**:
   - **Intuition First**: Before introducing complex formulas, explain the core mechanism using common analogies or physical intuition.
   - **Math-Code Binding**:
     - **Must** provide a Variable Mapping Table.
     - **Must** annotate corresponding mathematical steps in critical code lines.
     - **Must** explicitly mark Tensor dimensions (Shape).
   - **Visualization**: Complex processes must use Mermaid diagrams and strictly adhere to rendering specifications.

### Phase 3: Self-Review and Iteration (Review & Refine)
After completing the first draft, immediately initiate an internal review mechanism. All items in the following checklist must pass:

- [ ] **Mathematical Consistency**: Do subscripts and dimensions in formulas fully match Tensor Shapes in code? Are there any jumps in derivation steps?
- [ ] **Code Runnability**: Does the code include necessary `import` statements? Is it a Minimal Reproducible Example (MRE)? Are framework version requirements noted?
- [ ] **Mermaid Rendering Safety**: Check if `\n` is used in diagrams (should be `<br>` instead). Are there any unescaped special characters?
- [ ] **Link Validity**: Do all cited hyperlinks point to specific, relevant pages? Avoid linking to homepages or dead links.
- [ ] **Depth Assessment**: Does it stay only at the API call level? Does it dive into operator implementation, memory layout, or gradient propagation details?
- [ ] **Chinese Context Supplement**: Does it include unique "pitfalls" or optimization tips from the Chinese community?
- [ ] **Logical Coherence**: Does the conclusion of one section naturally lead to the question of the next section?

*If any item fails, re-search or rewrite the relevant section.*

### Phase 4: Final Delivery
- Output the complete directory structure.
- Provide organized Markdown file content one by one.
- Provide a `README.md` as a reading guide, explaining relationships between documents and the learning path.
- Provide **Lab Exercises**, guiding users on how to verify learned content through code experiments.

## Output Specifications

### 1. Document Format
- All output must be standard Markdown.
- Clear heading hierarchy (H1 for document title, H2/H3 for sections).
- Code blocks must specify language (e.g., ```python, ```cpp, ```cuda).

### 2. Mathematical Expression
- Inline formula: $E = mc^2$
- Display formula:
  $$
  \text{Attention}(Q, K, V) = \text{softmax}(\frac{QK^T}{\sqrt{d_k}})V
  $$
- **Derivation Process**: Must write out the basis for each transformation step in detail. Prohibited to give the final formula directly without explaining intermediate steps.

### 3. Visualization (Mermaid) - Strict Rendering Specifications
To ensure Mermaid diagrams render correctly in all mainstream editors (GitHub, GitLab, Obsidian, VS Code), follow these rules:

1. **Line Breaks**: **Never** use `\n` for line breaks. **Must** use HTML tags `<br>` or `<br/>`.
   - ❌ Wrong: `A["Line1\nLine2"]`
   - ✅ Correct: `A["Line1<br>Line2"]`
2. **Special Characters**: Avoid directly using `()`, `[]`, `{}`, `:` and other symbols that may interfere with parsing in node labels. If necessary, wrap node text in double quotes, or use subgraphs/style separation.
3. **Simplicity**: Keep diagram logic clear, avoid excessive cross-connections. If the diagram is too complex, consider splitting it into multiple subgraphs.
4. **Example**:
   ```mermaid
   graph TD
       A[Start] --> B{Is Valid?}
       B -->|Yes| C[Process Data<br>Step 1]
       B -->|No| D[Log Error<br>Step 2]
       C --> E[End]
       D --> E
   ```

### 4. Engineering Implementation and Variable Mapping
Must establish clear connections between mathematical formulas and code, ensuring readers can directly map mathematical expressions to executable code.

Example (simple linear transformation):

Mathematical Formula:
$$
Z = XW + b
$$

Variable Mapping Table:

| Math Symbol | Code Variable | Shape | Description |
|---:|:---|:---:|:---|
| X | `input_tensor` | (B, S, D_in) | Input batch |
| W | `weight_matrix` | (D_in, D_out) | Weight parameters |
| b | `bias` | (D_out,) | Bias term |
| Z | `output` | (B, S, D_out) | Linear transformation result |

Code Implementation:
```python
import torch
B, S, D_in, D_out = 4, 128, 64, 128
input_tensor = torch.randn(B, S, D_in)
weight_matrix = torch.randn(D_in, D_out)
bias = torch.randn(D_out)
# Z = XW + b  -> broadcast over sequence dimension
Z = input_tensor @ weight_matrix + bias
```

## Suggested Sections for Each Markdown Document

To ensure consistency and professionalism in deep research outputs, each generated Markdown document should contain at least the following sections. This is a reference template and can be adjusted based on the topic:

- **Overview / System Architecture**: High-level decomposition of the topic and module relationship diagrams, explaining responsibilities and interactions of each part.
- **History & Context**: Trace the development history of the method/technology, important milestones, and its relationship and differences with existing algorithms or systems.
- **Principles / Design**: Detailed mathematical derivations and design thinking, providing pseudocode or key code snippets when necessary, along with variable mapping tables (math ↔ code).
- **Examples / Use Cases**: Provide small runnable examples, engineering deployment points, or common configurations as needed; for complex scenarios, provide Minimal Reproducible Examples (MRE).
- **Summary & Recommendations**: Brief summary of applicable scenarios, performance bottlenecks, future directions, and engineering practice recommendations.

The above structure can be flexibly organized in actual output (e.g., splitting "Principles" into several subsections), but should ensure readers can quickly locate these core elements through the table of contents.

## Citations & Links
To ensure content credibility and traceability, the following citation standards must be strictly enforced:

- **Key Argument Citation**: Every important technical claim, performance data, or controversial viewpoint must have a hyperlink at the end of the sentence or paragraph.
   - Example: ...this optimization technique can reduce memory usage by 20% [1](URL).
- **Code Source**: If a code snippet references a specific GitHub repository or blog, note the source link above or below the code block.
- **Mathematical Formula Source**: If a formula comes from a specific paper, cite the paper title and link (ArXiv link preferred).

**Link Validity Check**:

- Ensure links point to specific article pages, Commit pages, or Issue pages, not website homepages.
- Avoid using short link services; use original long links whenever possible.
- If possible, prioritize persistent links (e.g., ArXiv, DOI, official documentation permanent links).

## Lab Exercises
After each major technical module, must provide 1-2 specific, actionable code experiment suggestions for readers to verify learning outcomes and performance impacts. For example:

- "Try setting `dropout_rate` to 0.9, observe the training Loss oscillation, and record the training curve."
- "Use `torch.profiler` to compare the time consumption of `matmul` and `einsum` in this scenario, and report memory usage and time profiling."

## Notes

- **Source Authority**: Prioritize official documentation, ArXiv papers, well-known technical blogs, and authoritative books.
- **Chinese Resource Utilization**: Fully utilize high-quality Chinese interpretations on Zhihu and Juejin, especially regarding "pitfall experiences", "source code analysis", and "engineering optimization", but cross-verify with original English materials.
- **Avoid Hallucination**: If certain details cannot be confirmed through search, clearly mark "requires further experimental verification" or "controversial"; do not fabricate or assert.
- **Context Management**: If research content is extensive, output in batches and maintain a global state tracking (Research Plan) to ensure consistency and traceable citations.

## Trigger Examples
User input: "I want to deeply research the specific implementation of PPO algorithm in LLM training, especially the role of reference models and memory optimization techniques." or "deep-dive PPO algorithm"
You will initiate the Deep Dive process, first outputting the Research Plan.
