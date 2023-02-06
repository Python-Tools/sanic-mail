"""例子兼测试工具."""
import aiofiles
from sanic import Sanic, Request, HTTPResponse
from sanic_jinja2 import SanicJinja2
from sanic.response import json
import sys
from pathlib import Path
ippath = str(Path(__file__).absolute().parent.parent)
print(ippath)
sys.path.append(ippath)
from sanic_mail import Sanic_Mail

app = Sanic(__name__)
jinja = SanicJinja2(app)
app.config.MAIL_SEND_HOST = "<邮箱服务器地址>"
app.config.MAIL_SEND_PORT = 0  # <端口>
app.config.MAIL_TLS = True  # <是否使用TLS>
app.config.MAIL_START_TLS = False  # <是否启动tls>,与MAIL_TLS冲突不能同时为True
app.config.MAIL_SENDER = "<你的发送邮箱>"
app.config.MAIL_SENDER_PASSWORD = "<你的密码>"
# Sanic_Mail.SetConfig(
#     app,
#     MAIL_SENDER=<你的发送邮箱>,
#     MAIL_SENDER_PASSWORD=<你的密码>,
#     MAIL_SEND_HOST=<邮箱服务器地址>,
#     MAIL_SEND_PORT=<端口>,
#     MAIL_TLS=<是否使用TLS>
# )
sender = Sanic_Mail(app)


@app.get('/send')
async def send(request: Request) -> HTTPResponse:
    attachments = {}
    async with aiofiles.open("source/README.md", "rb") as f:
        attachments["README.md"] = await f.read()
    async with aiofiles.open('source/猫.jpg', "rb") as f:
        attachments['猫.jpg'] = await f.read()
    await app.ctx.send_email(
        targetlist="hsz1273327@gmail.com",
        subject="测试发送",
        content="测试发送uu",
        attachments=attachments
    )
    return json({"result": "ok"})


@app.get('/send_html')
async def send_html(request: Request) -> HTTPResponse:
    attachments = {}
    msgimgs = {}
    async with aiofiles.open("source/README.md", "rb") as f:
        attachments["README.md"] = await f.read()
    async with aiofiles.open('source/猫.jpg', "rb") as f:
        attachments['猫.jpg'] = await f.read()
        msgimgs['猫.jpg'] = attachments['猫.jpg']

    content = jinja.env.get_template('default.html').render(
        name='sanic!', pic1="猫"
    )
    await app.ctx.send_email(
        targetlist="hsz1273327@gmail.com",
        subject="测试发送",
        content=content,
        html=True,
        msgimgs=msgimgs,
        attachments=attachments
    )
    return json({"result": "ok"})

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)
