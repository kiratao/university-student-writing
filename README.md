<div align="center">

<img src="skills/university-student-writing/assets/branding/logo.png" alt="大学生多文体写作 Logo" width="160">

# 大学生多文体写作

### University Student Writing for ChatGPT & Codex

**先辨认文体和规则，再生成结构正确、事实可核验、能够继续编辑和编译的 LaTeX 项目。**

`70 种文体` · `6 类校园场景` · `中英文支持` · `XeLaTeX` · `MIT`

</div>

---

大学生活里的写作远不止课程论文。

请假条、实验报告、社会实践方案、活动策划书、会议纪要、校园新闻、竞选稿、简历、求职信……它们看起来都叫“写文章”，真正需要的结构、语气、证据和版式却完全不同。

**大学生多文体写作**是一个面向 ChatGPT 与 Codex 的 Skill。它会先判断文体与接收对象，再选择相应规范和 LaTeX 模板；信息不足时保留醒目的待填写字段，不替用户虚构经历、数据、引语、奖项或审批事实。



## 它能做什么

| 场景 | 常见文体 | 它关注的重点 |
|---|---|---|
| 学习与学术 | 课程论文、文献综述、实验报告、开题报告、APA、MLA | 论证结构、引用、方法、参考文献与学校模板 |
| 日常学习生活 | 请假条、申请书、情况说明、申诉、正式邮件 | 身份、事实、明确请求、时间和附件 |
| 社会实践与实习 | 实践方案、调查报告、访谈报告、实习报告、结项报告 | 对象、过程、数据、伦理、成果与反思 |
| 学生组织工作 | 活动策划、通知、会议纪要、工作总结、述职、竞选稿 | 分工、预算、时间、责任、安全与可执行性 |
| 校园新闻 | 消息、通讯、人物采访、新闻通稿、简报、公众号文章 | 新闻事实、六要素、引语核验与图片说明 |
| 升学与求职 | 中英文简历、求职信、个人陈述、研究计划、申请邮件 | 岗位或项目匹配、证据、隐私和真实经历 |

完整文体列表可运行：

```powershell
python skills/university-student-writing/scripts/create_document.py --list
```

## 它与普通写作提示词的区别

- **先识别规则来源。** 学校、课程、比赛或接收单位的现行模板优先于通用样式。
- **区分“必须”和“建议”。** 国家标准、国际体例、高校惯例和可读性建议不会混为一谈。
- **不编造缺失事实。** 未提供的信息会保留为 `[[待填写：…]]`，而不是由模型猜测。
- **生成完整工程。** 输出包括 `main.tex`、共享样式、资源目录和文档清单，不是一段难以维护的零散代码。
- **可以实际检查。** 校验器会检查文体登记、必备结构、项目外路径、图片、待填写字段、编译日志和 PDF 新鲜度。
- **保留学校模板。** 用户提供的模板会被原样保存；无法可靠自动适配时会明确提示人工处理，不冒充已经套用。

## 直接这样使用

在 ChatGPT 或 Codex 中安装后，可以自然描述任务：

```text
帮我写一份社会实践调查报告。学校要求有摘要、调查方法、数据分析、局限和附录，先建立 LaTeX 项目，不要替我编调查数据。
```

也可以显式调用：

```text
$university-student-writing 把我的活动资料整理成一份可执行的迎新晚会策划书，并标出缺失的预算和安全信息。
```

如果已有学校模板：

```text
$university-student-writing 以我提供的学校模板为最高优先级，生成课程论文；不要改变文档类、字体或页边距。
```

## 安装

### OpenAI 插件目录

公开审核通过后，可在 ChatGPT 与 Codex 共用的插件目录中搜索“大学生多文体写作”并安装。当前仓库提供的是待提交的 `1.0.0` 插件包，不冒充已经上架的产品。

### 作为用户级 Skill 安装

从当前仓库根目录执行：

Windows PowerShell：

```powershell
New-Item -ItemType Directory "$HOME\.agents\skills" -Force | Out-Null
Copy-Item .\skills\university-student-writing "$HOME\.agents\skills" -Recurse
```

macOS 或 Linux：

```bash
mkdir -p "$HOME/.agents/skills"
cp -R ./skills/university-student-writing "$HOME/.agents/skills/"
```

Codex 通常会自动发现新 Skill；若没有出现，请重新启动 Codex。也可以在 Codex 中使用 `$skill-installer` 从代码仓库安装 Skill。

### 仅在一个项目中使用

将 `skills/university-student-writing` 复制到目标项目的：

```text
.agents/skills/university-student-writing/
```

## 命令行生成与校验

列出文体：

```powershell
python skills/university-student-writing/scripts/create_document.py --list
```

创建项目：

```powershell
python skills/university-student-writing/scripts/create_document.py `
  --genre social-practice-report-zh `
  --output .\我的社会实践报告 `
  --title "社区数字服务使用情况调查" `
  --author "姓名" `
  --student-id "学号" `
  --university "学校" `
  --college "学院"
```

编译：

```powershell
latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
```

校验：

```powershell
python skills/university-student-writing/scripts/validate_document.py .\我的社会实践报告
```

内置模板默认使用 XeLaTeX。若学校模板指定其他引擎或参考文献工具，以学校说明为准。

## 规范依据

项目记录并区分以下来源：

- 中文学位论文、参考文献、标点和数字用法等国家标准；
- APA、MLA、IEEE 的官方或权威说明；
- 多所高校公开发布的社会实践、学生工作、校园新闻、邮件和求职材料规范；
- 仅用于可读性的可选设计建议。

详细来源及核验日期见 [`sources.md`](skills/university-student-writing/sources.md)。单一学校的字号、封面或审批栏不会被描述成全国统一要求。

## 项目结构

```text
plugin.json
.codex-plugin/plugin.json
skills/university-student-writing/
├── SKILL.md
├── agents/openai.yaml
├── assets/latex/
├── references/
├── scripts/
└── tests/
```

Skill 采用“共享基础设施 + 文体路由”结构：70 种文体通过注册表映射到 8 个模板家族，同时保留学术、校园生活、社会实践、学生组织、校园新闻和职业发展各自的写作规则。

## 开发与验证

运行测试：

```powershell
python -m unittest discover -s skills/university-student-writing/tests -v
```

生成插件上传包：

```powershell
python scripts/package_plugin.py
```

打包脚本会生成 `dist/university-student-writing-1.0.0.zip`，并排除 Git 历史、缓存、编译产物和开发期设计文档。

## 数据与隐私

随附脚本只在宿主提供的受控执行环境中读写文档，不包含遥测、远程账号连接或自动上传逻辑。用户仍应避免把身份证号、住址、未公开调查数据等敏感信息放入不受信任的环境。详见[隐私说明](docs/PRIVACY.md)。

## 使用边界

这个项目提供的是可靠基线，而不是学校审批、法律意见或期刊录用保证。以下情况必须服从接收方：

- 学校或教师提供了专用 Word、LaTeX 或在线表单；
- 竞赛、期刊、会议或招聘单位规定了官方模板；
- 文件需要盖章、签字、审批、保密处理或提交到专用系统。

## 参与改进

欢迎提交问题和改进建议，尤其是：

- 有公开、可核验来源的新文体；
- 已失效或更新的规范链接；
- 可以复现的 LaTeX 编译问题；
- 不同学校模板之间确实存在的冲突。

请不要提交真实身份证件、联系方式、未公开成绩、调查原始数据或他人的私人材料。

## License

[MIT License](LICENSE) © 2026 tyz

---

## English summary

University Student Writing is a skills-only plugin for ChatGPT and Codex. It routes 70 Chinese and English university writing genres across six common student contexts, generates editable LaTeX projects, preserves institution-specific authority, exposes missing facts instead of inventing them, and validates observable project structure and compilation state.

The package is ready for local testing and draft upload. Public submission still requires verified publisher information and production listing assets, and the project is not represented as approved or listed.
