# sanic_mail

+ version: 0.0.2
+ status: dev
+ author: hsz
+ email: hsz1273327@gmail.com

## Description

使用`async await`异步执行邮件发送的任务

keywords:email,sanic

## Feature

+ 异步发邮件
+ 支持html,html内嵌图片,附件

## 使用方法

### 设置

```python
app.config.update({
    'MAIL_SENDER': < 你的发送邮箱 >,
    'MAIL_SENDER_PASSWORD': < 你的密码 >,
    'MAIL_SEND_HOST': < 邮箱服务器地址 >,
    'MAIL_SEND_PORT': < 端口 >,
    'MAIL_TLS': < 是否使用TLS >
})
```

其中:

+ MAIL_SEND_HOST 为邮件服务器地址
+ MAIL_SEND_PORT 为邮件服务器端口
+ MAIL_TLS 为邮件服务是否使用TLS
+ MAIL_SENDER 为你的发件邮箱
+ MAIL_SENDER_PASSWORD 为你的发件箱密码

~~如果你的`app.config`对象中已经包含上述字段,那么也可以不用这个方法来设置,但优先级使用`SetConfig`高于配置文件中定义字段~~

虽然有一个被注释的静态的方法，但是它有一个bug，还是建议使用`app.config`对象

### 插件初始化

和其他sanic插件一致有两种初始化方法:

1. 使用`Sanic_Mail(app)`初始化.
2. 先实例化`sm=Sanic_Mail()`再初始化`sm.init_app(app)`

### 发送

发送邮件的方法有两个:

+ 协程`send_email`
+ 方法`send_email_nowait`

其中`send_email_nowait`意为将任务交给协程发送而不等待发送完毕,同时会返回发送的task.

这个两个方法除了在`Sanic_Mail`实例上绑定外也会被绑定在`app`对象上

在蓝图中或者比较复杂的项目中,app对象可以通过回掉函数的参数`request`上的`app`字段上获取到

```python
request.app.send_email(xxxx)
```

### 使用时的注意点:

+ html邮件中的图片

    html邮件中可以插入图片,不过要求其中的cid为图片名去掉后缀的结果.

## Example

```python
import aiofiles
import base64
from sanic import Sanic
from sanic_jinja2 import SanicJinja2
from sanic.response import json
from sanic_mail import Sanic_Mail

app = Sanic(__name__)
jinja = SanicJinja2(app)
app.config.update({
    'MAIL_SENDER': < 你的发送邮箱 >,
    'MAIL_SENDER_PASSWORD': < 你的密码 >,
    'MAIL_SEND_HOST': < 邮箱服务器地址 >,
    'MAIL_SEND_PORT': < 端口 >,
    'MAIL_TLS': < 是否使用TLS >
})
sender = Sanic_Mail(app)


@app.get('/send')
async def send(request):
    attachments = {}
    async with aiofiles.open("source/README.md", "rb") as f:
        attachments["README.md"] = await f.read()
    async with aiofiles.open('source/猫.jpg', "rb") as f:
        attachments['猫.jpg'] = await f.read()
    await sender.send_email(
        targetlist="hsz1273327@gmail.com",
        subject="测试发送",
        content="测试发送uu",
        attachments=attachments
    )
    return json({"result": "ok"})


@app.get('/send_html')
async def send_html(request):
    attachments = {}
    msgimgs = {}
    async with aiofiles.open("source/README.md", "rb") as f:
        attachments["README.md"] = await f.read()
    async with aiofiles.open('source/猫.jpg', "rb") as f:
        attachments['猫.jpg'] = await f.read()
        msgimgs['猫.jpg'] = attachments['猫.jpg']

    content = jinja.env.get_template('default.html').render(
        name='sanic!',pic1="猫"
    )
    await sender.send_email(
        targetlist="hsz1273327@gmail.com",
        subject="测试发送",
        content=content,
        html=True,
        msgimgs = msgimgs,
        attachments=attachments
    )
    return json({"result": "ok"})

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)
````

## Install

`python -m pip install sanic_mail`

## Documentation

Documentation on github page <https://github.com/Sanic-Extensions/sanic-mail>
