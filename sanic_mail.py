"""Sanic-mail."""
import asyncio
from functools import partial
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.header import Header
from email.utils import parseaddr, formataddr
from typing import (
    Optional,
    Dict,
    List
)
import aiosmtplib


class Sanic_Mail:
    """邮件发送的主要部分."""

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
        #app.config.MAIL_SLL = confs.get("MAIL_SEND_PORT")
        return app

    def __init__(self, app=None):
        """初始化插件,可以后指定app."""
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
        return self

    async def send(self, content):
        """将邮件发送出去."""
        pass

    async def send_email(self,
                         targetlist: Union[List[str], str],
                         subject: str,
                         content: str,
                         sendername: Optinal[str]=None,
                         Cclist: Optional[List[str], str]=None,
                         html: bool=False,
                         msgimgs: Optional[Dict[str, str]]=None,
                         pics: Optional[Dict[str, str]]=None,
                         files: Optional[Dict[str, str]]=None):
        """执行发送email的动作.

        Parameters:
            targetlist (Union[List[str], str]): - 接受者的信息列表,也可以是单独的一条信息
            Cclist (Optional[List[str], str]): - 抄送者的信息列表,也可以是单独的一条信息
            subject (str): - 邮件主题
            content (str): - 邮件的文本内容
            sendername (Optinal[str]): - 发送者的发送名,默认为None
            html (bool): - 又见文本是否是html形式的富文本,默认为False
            msgimgs (Optional[Dict[str, str]]): - html格式的文本中插入的图片
            pics (Optional[Dict[str, str]]): - 附件中的图片,默认为None
            files (Optional[Dict[str, str]]): - 附件中的文件,默认为None

        """
        if sendername:
            sender = sendername + "<" + self.app.config.MAIL_SENDER + ">"
        else:
            sender = self.app.config.MAIL_SENDER
        targetlist = list(targetlist)

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

        message = make_message(sender=sender,
                               targets=targets,
                               subject=subject,
                               content=content,
                               html=html,
                               Cc=Cc,
                               msgimgs=msgimgs,
                               pics=pics,
                               files=files)
        await self.send(message)

    def send_email_no_wait(self,
                           targetlist: Union[List[str], str],
                           subject: str,
                           content: str,
                           sendername: str=None,
                           Cclist: Optional[List[str], str]=None,
                           html: bool=False,
                           msgimgs: Optional[Dict[str, str]]=None,
                           pics: Optional[Dict[str, str]]=None,
                           files: Optional[Dict[str, str]]=None):
        """执行发送email的动作但不等待而是继续执行下一步的操作.

        Parameters:
            targetlist (Union[List[str], str]): - 接受者的信息列表,也可以是单独的一条信息
            Cclist (Optional[List[str], str]): - 抄送者的信息列表,也可以是单独的一条信息
            subject (str): - 邮件主题
            content (str): - 邮件的文本内容
            sendername (Optinal[str]): - 发送者的发送名,默认为None
            html (bool): - 又见文本是否是html形式的富文本,默认为False
            msgimgs (Optional[Dict[str, str]]): - html格式的文本中插入的图片
            pics (Optional[Dict[str, str]]): - 附件中的图片,默认为None
            files (Optional[Dict[str, str]]): - 附件中的文件,默认为None

        """
        task = ensure_future(
            self.send_email(
                targetlist=targetlist,
                subject=subject,
                content=content,
                sendername=sendername,
                Cclist=Cclist,
                html=html,
                msgimgs=msgimgs,
                pics=pics,
                files=files
            )
        )
        return task



def format_addr(s):
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
        pics: Optional[Dict[str, str]]=None,
        files: Optional[Dict[str, str]]=None)-> MIMEMultipart:
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
        pics (Optional[Dict[str, str]]): - 附件中的图片,默认为None,
        files (Optional[Dict[str, str]]): - 附件中的文件,默认为None

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
            for i, v in msgimgs.items():
                postfix = i.split(".")[-1]
                msgImage = MIMEImage(v)
                msgImage.add_header('Content-Type', 'image/{}'.format(postfix))
                msgImage.add_header('Content-ID', '<{}>'.format(i))
                msgImage.add_header('Content-Disposition', 'inline')
                msg.attach(msgImage)
    else:
        text = MIMEText(content, 'plain')
        msg.attach(text)
    ctype = 'application/octet-stream'
    maintype, subtype = ctype.split('/', 1)
    for name, pic in pics.items():
        image = MIMEImage(pic, _subtype=subtype)
        image.add_header('Content-Disposition', 'attachment', filename=name)
        msg.attach(image)
    for name, file in files.items():
        file = MIMEBase(maintype, subtype)
        file.set_payload(file)
        file.add_header('Content-Disposition', 'attachment', filename=name)
        encoders.encode_base64(file)
        msg.attach(file)
    return msg


__all__ = ["Sanic_Mail"]
