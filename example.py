import aiofiles
from sanic import Sanic
from sanic_session import InMemorySessionInterface
from sanic_jinja2 import SanicJinja2
from sanic.response import json
from sanic_mail import Sanic_Mail

app = Sanic(__name__)
jinja = SanicJinja2(app)
Sanic_Mail.SetConfig(
    app,
    MAIL_SENDER='csd@hszofficial.site',
    MAIL_SENDER_PASSWORD='Hszsword881224',
    MAIL_SEND_HOST='smtp.exmail.qq.com',
    MAIL_SEND_PORT=465,
    MAIL_TLS=True
)
sender = Sanic_Mail(app)


@app.get('/send')
async def send(request):
    # task = app.send_email_nowait(
    #    targetlist="hsz1273327@gmail.com",
    #    subject="测试发送",
    #    content="测试发送Ï"
    # )
    attachments = {}
    async with aiofiles.open("source/fastoredis.log", "rb") as f:
        attachments["fastoredis.log"] = await f.read()
    async with aiofiles.open('source/猫.jpg', "rb") as f:
        attachments['猫.jpg'] = await f.read()
    await app.send_email(
        targetlist="hsz1273327@gmail.com",
        subject="测试发送",
        content="测试发送uu",
        attachments=attachments
    )
    return json({"result": "ok"})

@app.get('/send_html')
async def send_html(request):
    # task = app.send_email_nowait(
    #    targetlist="hsz1273327@gmail.com",
    #    subject="测试发送",
    #    content="测试发送Ï"
    # )
    attachments = {}
    async with aiofiles.open("source/fastoredis.log", "rb") as f:
        attachments["fastoredis.log"] = await f.read()
    async with aiofiles.open('source/猫.jpg', "rb") as f:
        attachments['猫.jpg'] = await f.read()
    await app.send_email(
        targetlist="hsz1273327@gmail.com",
        subject="测试发送",
        content="测试发送uu",
        html=True
        attachments=attachments
    )
    return jinja.render('index.html', request, greetings='Hello, sanic!')

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)
