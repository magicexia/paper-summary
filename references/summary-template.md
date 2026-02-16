# Paper Summary Template

Use this structure when generating a paper summary report. Adapt section depth based on paper length and complexity.

---

## 📄 基本信息 / Basic Info

| 字段 | 内容 |
|------|------|
| **标题** | {title} |
| **作者** | {authors} |
| **机构** | {affiliations} |
| **发表** | {venue, year} |
| **DOI/链接** | {link} |

## 🎯 一句话总结 / TL;DR

> {用1-2句话概括论文的核心贡献}

## 🔬 研究背景与动机 / Background & Motivation

- 该领域目前存在什么问题？
- 前人工作的不足是什么？
- 本文为什么要做这个研究？

## 💡 核心方法 / Core Method

- 提出了什么方法/框架/模型？
- 关键技术创新点是什么？
- 方法流程图/架构概述（用文字描述）

## 📊 实验与结果 / Experiments & Results

- 使用了什么数据集/基准？
- 与哪些基线方法对比？
- 核心指标和结果（用表格或列表呈现）
- 消融实验的关键发现

## 🔍 局限性与未来工作 / Limitations & Future Work

- 作者自述的局限性
- 你观察到的潜在问题
- 可能的改进方向

## 💬 个人评价 / Commentary

- 论文质量评估（方法新颖性、实验充分性、写作质量）
- 对该领域的影响和意义
- 与你已知的其他工作的关联

---

## Notes for Agent

- For non-English papers, output summary in the paper's original language with bilingual section headers
- For very short papers (< 4 pages), merge Background and Method sections
- For survey papers, replace Core Method with "分类体系 / Taxonomy" and add a section for "关键文献图谱 / Key References Map"
- Include quantitative results where available — don't just say "outperforms baselines"
- If the paper has clear figures/tables referenced, note them by number (e.g., "见 Figure 3")
