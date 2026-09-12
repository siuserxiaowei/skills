# 在手机上用 Claude Code 写代码，我是怎么把飞书接上去的

故事是这样的。

我最近有一个很蠢但又很真实的焦虑，用 Claude Code 的朋友可能都懂，就是那种 token 用不完的焦虑。

对，你没看错。不是没 token 用焦虑，是用不完也焦虑。

Max 订阅一个月好几百刀，每天有一大堆 token 额度，但你总不能 24 小时坐在电脑前吧？通勤的时候、等人的时候、躺床上刷手机的时候，那些 token 就在那里安静地过期。你就眼睁睁看着它们消失。

没有 token 用焦虑，用不完 token 也焦虑。两头堵。

然后我就想，能不能在手机上也用 Claude Code？

不是那种阉割版的 AI 对话，是完整的 Claude Code，能读文件、能跑命令、能改代码的那种。手机上发一句「帮我把那个 bug 修了」，它就真的去改代码了。

听起来有点离谱对吧。但我还真搞出来了。

## 怎么想到的

刷 GitHub 的时候看到一个叫 Claude-to-IM-skill 的项目，op7418 做的，1800 多个 star。这哥们做了一套 skill，能把 Claude Code 桥接到 Telegram、Discord、飞书、QQ、微信，基本上主流 IM 全覆盖了。

项目地址在这：https://github.com/op7418/Claude-to-IM-skill

我当时看到就觉得，卧槽这不就是我想要的东西吗。

然后就开始折腾。

## 折腾的过程

坦率的讲，Claude-to-IM-skill 这个项目思路是非常好的，但我实际跑的时候遇到了问题。

它的 package.json 里有一个核心依赖叫 claude-to-im，写的是 `file:../Claude-to-IM`，指向本地的一个目录。但这个目录里缺了 `src/lib/bridge/` 整个模块，这个核心库没发布到 npm。结果就是 `npm run build` 直接报 5 个 resolve 错误，编译不过。

用 `npx skills add` 装也一样的问题。

我当时就愣住了。1800 个 star 的项目，build 不过？？？

研究了一会儿发现，这个项目是从另一个叫 CodePilot 的桌面应用里抽出来的，那个核心库应该是 CodePilot 的私有模块，没有一起开源出来。所以单独 clone 这个 skill 仓库是跑不起来的。

那怎么办呢。

我看了一下它的架构，其实核心思路很简单，飞书 SDK 的 WebSocket 长连接收消息，Claude Agent SDK 处理消息，然后把结果发回去。中间那层「桥」不需要搞得很复杂。

所以我决定自己写一个。

## 从零开始写

最后出来的东西就一个文件，bridge.mjs，200 来行代码。

两个核心 SDK：

`@larksuiteoapi/node-sdk` 负责跟飞书通信。飞书官方的 SDK，支持 WebSocket 长连接。这个方案的好处是不需要公网 IP，不需要域名，不需要 ngrok，你电脑能上网就行。

`@anthropic-ai/claude-agent-sdk` 负责启动 Claude Code 会话。注意这个不是普通的 API 调用。它会起一个完整的 Claude Code 子进程，能读写文件、执行 bash 命令、用所有工具。跟你在终端里用 Claude Code 是一模一样的体验。

然后我加了一些实用功能，消息去重、并发控制、思考提示、长消息分片、群聊 @过滤。

写完之后往 GitHub 上一推：https://github.com/siuserxiaowei/feishu-claude-code-bridge

跟原项目做个对比的话：

Claude-to-IM-skill 是一个完整的多平台框架，10 多个 TypeScript 模块，支持 5 个 IM 平台，有 daemon 管理、有持久化、有流式卡片。它的设计是全面的，如果核心库发布出来能 build 通过，那确实是最佳方案。

我这个就是一个专注飞书的轻量版。一个 JS 文件，不需要编译，clone 下来 npm install 就能跑。功能上没有原项目那么丰富，但核心的「手机发消息 → Claude Code 干活」这条链路是完整的。

## 飞书那边要做什么

去飞书开放平台创建一个自建应用，加上机器人能力。

权限加三个：im:message、im:message.group_at_msg、im:message.p2p_msg。

事件订阅加 im.message.receive_v1，投递方式选长连接。

然后发一个版本让管理员审批。如果是你自己的企业，秒批。

## 启动

```bash
git clone https://github.com/siuserxiaowei/feishu-claude-code-bridge.git
cd feishu-claude-code-bridge
npm install

FEISHU_APP_ID=你的appid \
FEISHU_APP_SECRET=你的secret \
AUTO_APPROVE=true \
node bridge.mjs
```

看到 `✅ WebSocket connected, listening...` 就算接上了。

去飞书私聊你的机器人，发条消息试试。

## 踩的其他坑

飞书 SDK 的 WSClient API 变了。网上的教程和一些 skill 里写的是在构造函数里传 eventDispatcher，但新版 SDK 改成了在 start() 方法里传。就这么一个参数位置的变化，报错信息是 `Cannot destructure property 'eventDispatcher' of 'params' as it is undefined`，看着挺懵的。

还有飞书的权限审批是两阶段的。你在开发者后台加了权限，必须发一个新版本让管理员审批通过，权限才真的生效。如果后面又加了新权限，得再发一个版本。

## 现在的效果

通勤的时候，掏出手机打开飞书，给机器人发一句话，它就在我电脑上跑 Claude Code 帮我干活。

私聊直接对话，群里 @机器人也行。支持上下文，多轮对话没问题。

最爽的是 AUTO_APPROVE=true 开了之后全自动。你说「帮我把那个函数重构一下」，它就真的去改文件了。改坏了？git reset 就行，反正有版本控制。

token 焦虑的问题算是解决了。现在等地铁的时候也能写代码了。

虽然这又带来了一个新问题，就是 token 用得更快了。

算了不想了。

## 相关链接

- Claude-to-IM-skill（架构思路来源，支持5个平台）：https://github.com/op7418/Claude-to-IM-skill
- 本项目（轻量飞书版，开箱即用）：https://github.com/siuserxiaowei/feishu-claude-code-bridge
- 卡兹克老师的写作 skill：https://github.com/KKKKhazix/khazix-skills
- 活人感写作 skill（基于卡兹克风格逆向工程）：https://github.com/siuserxiaowei/alive-writer-skill

以上，既然看到这里了，如果觉得不错，随手点个赞、在看、转发三连吧，
如果想第一时间收到推送，也可以给我个星标⭐～
谢谢你看我的文章，我们，下次再见。
