import io
from typing import Union

from api import consts
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def create_pdf(
    data: list, filename: Union[str, io.BytesIO], header: str
) -> None:
    """
    Создает pdf файл для на основе входных данных.

    :param data: Список, каждый элемент которого - новая строка
    :param filename: Имя файла или объект буффера
    :param header: Заголовок файла
    """
    pdf = canvas.Canvas(filename=filename, pagesize=A4)
    pdfmetrics.registerFont(TTFont('DejaVu-Bold', 'DejaVuSans-Bold.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
    pdf.setFont('DejaVu-Bold', 16)
    width, height = A4
    y = height - consts.TOP_MARGIN
    x = consts.LEFT_MARGIN
    pdf.drawString(
        x=x,
        y=y,
        text=header,
    )
    y -= consts.MARGIN_AFTER_HEADER
    pdf.setFont('DejaVu', 14)

    for line in data:
        if y < consts.BOTTOM:
            pdf.showPage()
            pdf.setFont('DejaVu', 14)
            y = height - consts.TOP_MARGIN
        pdf.drawString(x, y, line)
        y -= consts.LEADING

    pdf.showPage()
    pdf.save()
