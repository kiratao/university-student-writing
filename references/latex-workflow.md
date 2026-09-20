# LaTeX 工作流

## 创建

```powershell
python scripts/create_document.py --list
python scripts/create_document.py --genre social-practice-report --output ./社会实践报告
```

可选参数：

- `--language zh|en`：覆盖注册表默认语言；
- `--title`、`--author`、`--student-id`、`--university`、`--college`：写入已知元数据；
- `--school-template <path>`：把学校模板原样复制到项目的 `school-template/`，记录其来源并提示人工适配；
- `--force`：只用于确认可以覆盖一个已经存在但为空的输出目录；不能覆盖非空目录。

## 编译

内置模板使用 XeLaTeX。项目根目录运行：

```powershell
latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
```

若学校或出版方模板指定 LuaLaTeX、pdfLaTeX、BibTeX 或 Biber，服从其说明。不要为了让模板“能跑”而删除文档类或改写版式。

## 校验

```powershell
python scripts/validate_document.py ./社会实践报告
```

校验器检查元数据、待填写字段、必备结构、文件引用和明显的 LaTeX 完整性错误。它不判断事实是否真实，也不能替代学校审批或人工版面检查。

## 字体

共享样式优先使用 Windows 常见的宋体、黑体、仿宋和楷体；缺失时回退到 TeX Live 自带 Fandol 字体并在编译日志中保留可观察信息。学校明确指定字体时，在项目副本中覆盖字体配置。

## 交付检查

- 成功编译当前源码；
- 日志无未解析引用、缺失字体、缺图或致命排版错误；
- 标题、分页、页眉页脚、表格、图片、落款和中英文混排可读；
- `document.json` 与实际文体一致；
- 待填写字段已填写，或在交付说明中逐项列出。
