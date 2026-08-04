# Manual Gates

Consult this file ahead of any workflow involving login, credentials, proxy, certificates, or WeChat desktop.

## Only The User Can Do These

- Scan the exporter login QR code.
- Pick the correct WeChat Official Account or service account at login time.
- Approve the use of any auth-key or credentials file.
- Open article/history pages in WeChat desktop whenever credential capture calls for it.
- Scroll through the historical article list during a proxy/history fallback.
- Eyeball downloaded content personally where copyright, restricted access, or publication risk is at stake.

## Always Ask First

- Installing mitmproxy or wxdown-service dependencies.
- Trusting a mitmproxy root CA certificate.
- Enabling, disabling, or tweaking macOS system proxy settings.
- Launching a proxy that intercepts WeChat article HTTPS traffic.
- Persisting credentials to a local file or to Keychain.
- Driving the exporter UI with browser automation once logged in.

## Off Limits Entirely

- Never drive the user's WeChat UI.
- Never publish, delete, mass-send, follow, unfollow, or message.
- Never work around login, paywalls, deleted articles, private content, or permission checks.
- Never borrow another person's account/session as some account pool.
- Never expose cookies, auth-key, token, pass_ticket, key, uin, credential JSON, or QR login secrets.
- Never walk away with the system proxy still aimed at a local interceptor.

## Failure Modes User Help Cannot Fix

- WeChat alters endpoint behavior or page markup.
- Commenting is disabled or hidden on the article.
- Metrics hinge on fresh credentials that lapse fast.
- Image or media URLs go stale.
- Public exporter endpoints throttle or turn requests away.
- A local proxy clashes with Clash or other system proxy configuration.

## Prompting The User Safely

Word the asks short and plain, e.g.:

```text
这一步需要你扫码登录公众号后台，微信本身我不碰。扫码并选好对应公众号之后，回我一句“已登录”。
```

```text
抓阅读量和评论得先启动本地 wxdown-service 并信任 mitmproxy 证书。你确认以后我只负责起本地服务，微信里的页面要你自己打开。
```

```text
接下来需要把系统 HTTP/HTTPS 代理临时指向 127.0.0.1:<port>。当前设置我会先备份，用完恢复。可以吗？
```
