"""Sanic-mail."""
import asyncio
from typing import (
    Union,
    Optional,
    Dict,
    List,
    Any,
    Tuple
)
import aiosmtplib
from sanic.log import logger
from sanic import Sanic

from .utils import make_message
from .exceptions import SMTPConnErr, SMTPContextErr


class Sanic_Mail:
    """sanic的邮件发送插件.

    使用后发送邮件会被绑定在`app对象`上,支持协程`send_email`,
    也支持方法`send_email_nowait`,其中`send_email_nowait`意为将任务交给协程发送而不等待发送完毕,
    会返回发送的task.

    """
    smtp: Optional[aiosmtplib.SMTP]

    def __init__(self, app: Optional[Sanic] = None) -> None:
        """初始化插件,可以后指定app."""
        self.smtp = None
        if app:
            self.init_app(app)
        else:
            pass

    def init_app(self, app: Sanic) -> "Sanic_Mail":
        """为app初始化插件."""
        self.app = app
        if "extensions" not in app.__dir__():
            app.ctx.extensions = {}
        app.ctx.extensions['EmailSender'] = self

        app.ctx.send_email_nowait = self.send_email_no_wait
        app.ctx.send_email = self.send_email
        app.register_listener(self.smtp_connection, "before_server_start")
        app.register_listener(self.smtp_close, "before_server_stop")
        return self

    async def smtp_connection(self, app: Sanic, loop: asyncio.AbstractEventLoop) -> None:
        self.smtp = aiosmtplib.SMTP(
            hostname=app.config.MAIL_SEND_HOST,
            port=app.config.MAIL_SEND_PORT,
            use_tls=app.config.MAIL_TLS,
            start_tls=app.config.MAIL_START_TLS
        )
        await self.smtp.connect()
        await self.smtp.login(
            app.config.MAIL_SENDER, app.config.MAIL_SENDER_PASSWORD
        )
        logger.info("[SanicMail] smtp connected !")

    async def smtp_close(self, app: Sanic, loop: asyncio.AbstractEventLoop) -> None:
        if self.smtp is None:
            raise SMTPConnErr("stmp not conn yet")
        self.smtp.close()
        self.smtp = None
        logger.info("[SanicMail] smtp connection closed !")
        # return True

    async def send_email(self,
                         targetlist: Union[List[str], Tuple, str],
                         subject: str,
                         content: str,
                         sendername: Optional[str] = None,
                         Cclist: Union[List[str], Tuple, str, None] = None,
                         html: bool = False,
                         msgimgs: Optional[Dict[str, str]] = None,
                         attachments: Optional[Dict[str, str]] = None) -> Any:
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
            raise SMTPContextErr("unsupport type for targetlist")

        if Cclist:
            if isinstance(Cclist, (list, tuple)):
                Cclist = tuple(Cclist)
                Cc = ", ".join(Cclist)
            elif isinstance(Cclist, str):
                Cc = Cclist
            else:
                raise SMTPContextErr("unsupport type for Cclist")
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
        if self.smtp:
            return await self.smtp.send_message(message)
        else:
            raise SMTPConnErr("stmp not conn yet")

    def send_email_no_wait(self,
                           targetlist: Union[List[str], str],
                           subject: str,
                           content: str,
                           sendername: Optional[str] = None,
                           Cclist: Union[List[str], str, None] = None,
                           html: bool = False,
                           msgimgs: Optional[Dict[str, str]] = None,
                           attachments: Optional[Dict[str, str]] = None) -> asyncio.Task:
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

        Return:
            (asyncio.Task): - 执行发送邮件的任务实例

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


__all__ = ["Sanic_Mail"]
