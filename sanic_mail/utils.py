import mimetypes
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.nonmultipart import MIMENonMultipart
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.header import Header
from email.utils import parseaddr, formataddr
from typing import (
    Optional,
    Dict,
    Any
)


def format_addr(s: str) -> str:
    """将地址信息格式化为`名字<地址>`的形式."""
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))


def make_message(
        sender: str,
        targets: str,
        subject: str,
        content: str,
        html: bool = False,
        Cc: Optional[str] = None,
        msgimgs: Optional[Dict[str, str]] = None,
        attachments: Optional[Dict[str, str]] = None) -> MIMEMultipart:
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
            for i, v in msgimgs.items():
                ctype, encoding = mimetypes.guess_type(i)
                if ctype is None:
                    raise AttributeError("mimetypes.guess_type cannot guess ctype")
                _maintype, _subtype = ctype.split('/', 1)
                msgImage = MIMEImage(v, _subtype)
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
    def __init__(self, attachename: Any, _attachementdata: Any,
                 _encoder: Any = encoders.encode_base64, *, policy: Any = None, **_params: Any) -> None:
        ctype, encoding = mimetypes.guess_type(attachename)
        if ctype is None or encoding is not None:
            ctype = 'application/octet-stream'
        _maintype, _subtype = ctype.split('/', 1)
        MIMENonMultipart.__init__(self, _maintype, _subtype, policy=policy,
                                  **_params)
        self.set_payload(_attachementdata)
        _encoder(self)
