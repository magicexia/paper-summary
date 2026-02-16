# Paper Summary Skill 优化待办

## 优先级 P0 - 核心功能增强 ✅ 已完成

- [x] **扩展输入源支持**
  - [x] Semantic Scholar URL 解析
  - [x] PubMed ID (PMID) 支持
  - [x] DOI 增强解析（多出版社支持）
- [x] **增强 PDF 提取能力**
  - [x] 表格提取选项 (--tables)
  - [ ] 图表/图片提取选项
- [x] **输出格式多样化**
  - [x] JSON 结构化输出 (--format json)
  - [ ] Notion 格式导出

## 优先级 P1 - 工作流优化 ✅ 已完成

- [x] 自动加载 summary template 到 context
- [x] DOI 解析增强（多出版社支持）
- [x] 批量处理自动摘要 + 聚合报告 (--summarize)

## 优先级 P2 - 用户体验 ✅ 已完成

- [x] 进度条显示 (batch_extract.py)
- [x] 下载缓存机制 (--cache-dir)
- [x] 可配置超时参数 (--timeout)
- [x] 完善的日志记录 (--verbose, logging)

## 优先级 P3 - 高级功能 ✅ 已完成

- [x] **多论文对比模式** → `python3 advanced_analysis.py compare a.pdf b.pdf`
- [x] **引用网络分析** → `python3 advanced_analysis.py citations <id>`
- [x] **图表 OCR 提取** → `python3 advanced_analysis.py ocr <pdf>`
- [x] **相关论文推荐** → `python3 advanced_analysis.py recommend <id>`

## 待完成

- [ ] Notion 格式导出
- [ ] GitHub README 论文链接自动提取 PDF
- [ ] 图表/图片提取（高级版 OCR）
