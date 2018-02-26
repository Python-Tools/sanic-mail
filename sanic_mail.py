"""Sanic-mail."""
import asyncio
import mimetypes
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.nonmultipart import MIMENonMultipart
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.header import Header
from email.utils import parseaddr, formataddr
from email.utils import make_msgid
from typing import (
    Union,
    Optional,
    Dict,
    List,
    Any
)
import aiosmtplib
from sanic.log import logger


class Sanic_Mail:
    """sanic的邮件发送插件.
    
    使用后发送邮件会被绑定在`app对象`上,支持协程`send_email`,
    也支持方法`send_email_nowait`,其中`send_email_nowait`意为将任务交给协程发送而不等待发送完毕,
    会返回发送的task.

    """

    @staticmethod
    def SetConfig(app, **confs):
        """将设置绑定到app对象."""
        app.config.MAIL_SENDER = (
            confs.get("MAIL_SENDER") or app.config.MAIL_SENDER
        )
        app.config.MAIL_SENDER_PASSWORD = (
            confs.get("MAIL_SENDER_PASSWORD") or app.config.MAIL_SENDER_PASSWORD
        )
        app.config.MAIL_SEND_HOST = (
            confs.get("MAIL_SEND_HOST") or app.config.MAIL_SEND_HOST
        )
        app.config.MAIL_SEND_PORT = (
            confs.get("MAIL_SEND_PORT") or app.config.MAIL_SEND_PORT
        )
        app.config.MAIL_TLS = confs.get("MAIL_TLS") or app.config.MAIL_TLS or Ture
        return app

    def __init__(self, app=None):
        """初始化插件,可以后指定app."""
        self.smtp = None
        if app:
            self.init_app(app)
        else:
            pass

    def init_app(self, app):
        """为app初始化插件."""
        self.app = app
        if "extensions" not in app.__dir__():
            app.extensions = {}
        app.extensions['EmailSender'] = self

        app.send_email_nowait = self.send_email_no_wait
        app.send_email = self.send_email

        @app.listener("before_server_start")
        async def stmp_connection(app, loop):
            self.smtp = aiosmtplib.SMTP(
                loop=loop,
                hostname=app.config.MAIL_SEND_HOST,
                port=app.config.MAIL_SEND_PORT,
                use_tls=app.config.MAIL_TLS
            )
            await self.smtp.connect()
            await self.smtp.login(
                app.config.MAIL_SENDER, app.config.MAIL_SENDER_PASSWORD
            )
            logger.info("[SanicMail] smtp connected !")

        @app.listener("before_server_stop")
        async def stmp_close(app, loop):
            self.smtp.close()
            self.smtp = None
            logger.info("[SanicMail] smtp connection closed !")
            return True

        return self

    async def send_email(self,
                         targetlist: Union[List[str], str],
                         subject: str,
                         content: str,
                         sendername: Optional[str]=None,
                         Cclist: Union[List[str], str, None]=None,
                         html: bool=False,
                         msgimgs: Optional[Dict[str, str]]=None,
                         attachments: Optional[Dict[str, str]]=None)->Any:
        """执行发送email的动作.

        Parameters:
            targetlist (Union[List[str], str]): - 接受者的信息列表,也可以是单独的一条信息
            Cclist (Optional[List[str], str]): - 抄送者的信息列表,也可以是单独的一条信息
            subject (str): - 邮件主题
            content (str): - 邮件的文本内容
            sendername (Optinal[str]): - 发送者的发送名,默认为None
            html (bool): - 又见文本是否是html形式的富文本,默认为False
            msgimgs (Optional[Dict[str, str]]): - html格式的文本中插入的图片
            attachments (Optional[Dict[str, str]]): - 附件中的文件,默认为None

        """
        if sendername:
            sender = sendername + "<" + self.app.config.MAIL_SENDER + ">"
        else:
            sender = self.app.config.MAIL_SENDER
        if isinstance(targetlist, (list, tuple)):
            targetlist = tuple(targetlist)
            targets = ", ".join(targetlist)
        elif isinstance(targetlist, str):
            targets = targetlist
        else:
            raise AttributeError("unsupport type for targetlist")

        if Cclist:
            if isinstance(Cclist, (list, tuple)):
                Cclist = tuple(Cclist)
                Cc = ", ".join(Cclist)
            elif isinstance(Cclist, str):
                Cc = Cclist
            else:
                raise AttributeError("unsupport type for Cclist")
        else:
            Cc = None
        message = make_message(sender=sender,
                               targets=targets,
                               subject=subject,
                               content=content,
                               html=html,
                               Cc=Cc,
                               msgimgs=msgimgs,
                               attachments=attachments)
        return await self.smtp.send_message(message)

    def send_email_no_wait(self,
                           targetlist: Union[List[str], str],
                           subject: str,
                           content: str,
                           sendername: str=None,
                           Cclist: Union[List[str], str, None]=None,
                           html: bool=False,
                           msgimgs: Optional[Dict[str, str]]=None,
                           attachments: Optional[Dict[str, str]]=None)->asyncio.Task:
        """执行发送email的动作但不等待而是继续执行下一步的操作.

        Parameters:
            targetlist (Union[List[str], str]): - 接受者的信息列表,也可以是单独的一条信息
            Cclist (Optional[List[str], str]): - 抄送者的信息列表,也可以是单独的一条信息
            subject (str): - 邮件主题
            content (str): - 邮件的文本内容
            sendername (Optinal[str]): - 发送者的发送名,默认为None
            html (bool): - 又见文本是否是html形式的富文本,默认为False
            msgimgs (Optional[Dict[str, str]]): - html格式的文本中插入的图片
            attachments (Optional[Dict[str, str]]): - 附件中的文件,默认为None

        """
        task = asyncio.ensure_future(
            self.send_email(
                targetlist=targetlist,
                subject=subject,
                content=content,
                sendername=sendername,
                Cclist=Cclist,
                html=html,
                msgimgs=msgimgs,
                attachments=attachments
            )
        )
        return task


def format_addr(s: str)->str:
    """将地址信息格式化为`名字<地址>`的形式."""
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))


def make_message(
        sender: str,
        targets: str,
        subject: str,
        content: str,
        html: bool=False,
        Cc: str=None,
        msgimgs: Optional[Dict[str, str]]=None,
        attachments: Optional[Dict[str, str]]=None)-> MIMEMultipart:
    """创建信息.

    创建信息通过html标志指定内容是html的富文本还是普通文本.默认为普通文本.
    如果是html形式,可以用以下形式插入图片:

    <img src="cid:image1.jpg">

    使用`msgimgs`定义插入的图片,默认为None.以字典的形式传入,键为文本中对应的cid值,
    此处要求是图片的带后缀名,值则是从图片中读出的字节序列.

    与之类似的是pics和files,他们用于设置附件中的图片或者附件

    Parameters:
        sender (str): - 发送者的信息
        targets (str): - 接受者的信息
        Cc (str): - 抄送者的信息
        subject (str): - 邮件主题
        content (str): - 邮件的文本内容
        html (bool): - 又见文本是否是html形式的富文本,默认为False
        msgimgs (Optional[Dict[str, str]]): - html格式的文本中插入的图片
        attachments (Optional[Dict[str, str]]): - 附件中的文件,默认为None

    Returns:
        (MIMEMultipart): - 没有设置发送者和收件者的邮件内容对象

    """
    msg = MIMEMultipart()
    msg['Subject'] = Header(subject, "utf-8").encode()
    msg['From'] = format_addr(sender)
    msg['To'] = targets
    if Cc:
        msg['Cc'] = Cc
    if html:
        text = MIMEText(content, 'html', 'utf-8')
        msg.attach(text)
        if msgimgs:
            asparagus_cid = {}
            for i, v in msgimgs.items():
                ctype, encoding = mimetypes.guess_type(i)
                _maintype, _subtype = ctype.split('/', 1)
                #asparagus_cid[i] = make_msgid()
                #postfix = i.split(".")[-1]
                msgImage = MIMEImage(v, _subtype)
                #msgImage.add_header('Content-Type', 'image/{}'.format(postfix))
                msgImage.add_header('Content-ID', '<{}>'.format(i.split(".")[0]))
                msgImage.add_header('Content-Disposition', 'inline')
                msg.attach(msgImage)
    else:
        text = MIMEText(content, 'plain')
        msg.attach(text)
    if attachments:
        for name, file in attachments.items():
            attachment = MIMEAttachment(name, file)
            attachment.add_header('Content-Disposition', 'attachment', filename=name)
            msg.attach(attachment)
    return msg


class MIMEAttachment(MIMENonMultipart):
    def __init__(self, attachename, _attachementdata,
                 _encoder=encoders.encode_base64, *, policy=None, **_params):
        """
        """
        ctype, encoding = mimetypes.guess_type(attachename)
        if ctype is None or encoding is not None:
            ctype = 'application/octet-stream'
        _maintype, _subtype = ctype.split('/', 1)
        # if _subtype is None:
        #     raise TypeError('Could not guess image MIME subtype')
        MIMENonMultipart.__init__(self, _maintype, _subtype, policy=policy,
                                  **_params)
        self.set_payload(_attachementdata)
        _encoder(self)


__all__ = ["Sanic_Mail"]
