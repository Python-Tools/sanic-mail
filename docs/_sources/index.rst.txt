.. sanic_mail documentation master file, created by
   sphinx-quickstart on Sat Feb 24 14:51:04 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to sanic_mail's documentation!
======================================

* version: 0.0.3

* status: dev

* author: hsz

* email: hsz1273327@gmail.com

Desc
--------------------------------

async email sender extension for sanic!


keywords:email,sanic


Feature
----------------------
* asyncio send email 
* html,attachments support

Usage
-------------------


Setting
>>>>>>>>>>>>>>

We can use a static mrthod to setup Sanic_Mail

.. code:: python

    Sanic_Mail.SetConfig(
        app,
        MAIL_SENDER=<your sender email address>,
        MAIL_SENDER_PASSWORD=<your sender email password>,
        MAIL_SEND_HOST=<your sender email's host>,
        MAIL_SEND_PORT=<your sender email host's port>,
        MAIL_TLS=<use TLS or not>
    )


if the `app.config` has already include these field, you don't need to setup with this method.
But `SetConfig` has priority over `app.config`.

Initialization
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

As the same with other sanic's extensions, there are 2 ways to initialization.

1. Use `Sanic_Mail(app)`
2. Instantiate Sanic_Mail like `sm=Sanic_Mail()`,then use `sm.init_app(app)`

Send mails
>>>>>>>>>>>>>>>>>>>

there are 2 ways to send email:

+ coroutines `send_email`
+ method `send_email_nowait`

`send_email_nowait` means run the task without waiting for the action completed,
and this method will return the certain task instance

these 2 method will also bind on the app instance,we can get app instance by `request.app`


Attention point
>>>>>>>>>>>>>>>>>>>>>>>>>>>>

* images in html

    We can embed images in html like `<img src="cid:<pic1>">`. pic1 must be the picture's name without postfix.


Example
-------------------------------

.. code:: python

    import aiofiles
    import base64
    from sanic import Sanic
    from sanic_jinja2 import SanicJinja2
    from sanic.response import json
    from sanic_mail import Sanic_Mail

    app = Sanic(__name__)
    jinja = SanicJinja2(app)
    Sanic_Mail.SetConfig(
        app,
        MAIL_SENDER=<your sender email address>,
        MAIL_SENDER_PASSWORD=<your sender email password>,
        MAIL_SEND_HOST=<your sender email's host>,
        MAIL_SEND_PORT=<your sender email host's port>,
        MAIL_TLS=<use TLS or not>
    )
    sender = Sanic_Mail(app)


    @app.get('/send')
    async def send(request):
        attachments = {}
        async with aiofiles.open("source/README.md", "rb") as f:
            attachments["README.md"] = await f.read()
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
        await app.send_email(
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


Install
--------------------------------

- ``python -m pip install sanic_mail``

API
--------------------

.. toctree::
   :maxdepth: 4
   :caption: Contents:

   sanic_mail


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
