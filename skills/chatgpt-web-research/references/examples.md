# ChatGPT Web Research examples

## 正向案例

**用户请求：** “用我工作 Chrome 里的 ChatGPT 网页版比较三款团队知识库，报告保存下来。”

**处理：** Match the named visible profile and existing ChatGPT tab, submit a dated comparison packet with a unique run token, wait for a terminal page state, and preserve raw and edited Markdown separately.

**验收证据：** The captured answer contains all three products and the token; `run.json` records the route and conversation URL; the saved report is read back and checked against the requested criteria.

## 边界案例

**场景：** “一定用我的付费账号”，但 only an unverified or free account is visible.

**处理：** Stop before entering the prompt and ask the user to expose the intended account. Do not inspect cookies or continue in another profile.

**验收证据：** No research message is submitted under the wrong account, and the missing visible condition is stated precisely.

## 失败与恢复

**场景：** The page shows a long completed response, but the copy action returns only the first section.

**处理：** Keep the incomplete copy as diagnostic evidence, extract the assistant message through the accessible page structure, and compare its beginning, end, and run token with the visible page.

**验收证据：** The final raw file contains the token and all visible sections; the report records the alternate capture method.

### Terminal interruption

**Situation:** The user closes the selected browser window during generation.

**Decision:** Mark the run interrupted and preserve any confirmed partial response. Do not move to a different account or pretend that an unrelated answer completed the run.

**Evidence:** The delivery distinguishes partial material from a finished report and states the minimum step needed to resume.
