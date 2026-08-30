# Lark Shared｜案例与详细说明

以下案例以当前 lark-cli 的运行时发现结果为准；命令、schema、profile、identity 和租户都必须在执行当次重新确认。

## 正向案例

- **用户请求：** “检查我的 lark-cli 登录身份和最小 scope，先别改任何东西。”
- **处理：** 只运行版本、profile、auth status、skills list/help/schema 等发现命令，明确 user/bot identity、tenant、scope 和本机版本差异。
- **验收证据：** 报告能回答正在用哪个 profile/identity、哪些能力可见、缺哪些 scope；没有输出 token，也没有发起登录或授权。

## 边界案例

- **场景：** 不因某业务失败就默认申请全部 scope、切换身份或更新 CLI；这些动作分别需要用户选择。
- **验收证据：** 任何额外写入、外部发送、权限或高风险动作均未越过用户本轮授权。

## 失败与恢复

- **场景与处理：** 认证状态不一致时先比较命令中的 profile/identity 与实际状态，提供最小修复步骤，不读取凭证文件内容。
- **验收证据：** 保留结构化错误、实际远端状态和下一步条件；没有把未知状态伪装成成功。
