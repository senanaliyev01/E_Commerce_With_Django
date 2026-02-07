from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
from django.http import HttpResponse
from django.utils import timezone
from .models import Mehsul, Sifaris


def generate_products_pdf():
    """Bütün məhsulların PDF-sini yaratmaq"""
    
    # Font qeydiyyatı
    pdfmetrics.registerFont(TTFont('NotoSans', 'static/fonts/NotoSans-Regular.ttf'))

    # PDF yaratmaq
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="mehsullar.pdf"'

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    elements = []

    # Başlıq
    styles = getSampleStyleSheet()
    styles['Title'].fontName = 'NotoSans'
    title = Paragraph("AS AVTO +994 77 305 95 85", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 20))

    # Başlıq stilləri - Sifaris kimi
    headerStyle = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontName='NotoSans',
        fontSize=9,
        textColor=colors.whitesmoke,
        alignment=1,  # Mərkəz
        spaceAfter=0,
        spaceBefore=0,
        leading=10
    )

    # Məhsul məlumatları üçün stil - Sifaris kimi
    contentStyle = ParagraphStyle(
        'ContentStyle',
        parent=styles['Normal'],
        fontName='NotoSans',
        fontSize=8,
        alignment=1,  # Mərkəz
        spaceAfter=0,
        spaceBefore=0,
        leading=10
    )

    # Cədvəl başlıqları - Paragraph ilə
    headers = [
        Paragraph('№', headerStyle),
        Paragraph('Kod', headerStyle),
        Paragraph('Firma', headerStyle),
        Paragraph('Məhsul', headerStyle),
        Paragraph('Vitrin', headerStyle),
        Paragraph('Stok', headerStyle),
        Paragraph('Qiymət', headerStyle)
    ]
    
    # Məhsul məlumatları
    data = [headers]
    for index, mehsul in enumerate(Mehsul.objects.all(), 1):
        row = [
            Paragraph(str(index), contentStyle),
            Paragraph(mehsul.brend_kod, contentStyle),
            Paragraph(mehsul.firma.adi if mehsul.firma else '-', contentStyle),
            Paragraph(mehsul.adi, contentStyle),  # Uzun adlar alta düşəcək
            Paragraph(str(mehsul.vitrin.nomre) if mehsul.vitrin else '-', contentStyle),
            Paragraph(str(mehsul.stok), contentStyle),
            Paragraph(f"{mehsul.qiymet} ₼", contentStyle)
        ]
        data.append(row)

    # Cədvəl yaratmaq - Sifaris kimi
    table = Table(data)
    table.setStyle(TableStyle([
        # Başlıq sətri
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2B5173')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'NotoSans'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('TOPPADDING', (0, 0), (-1, 0), 5),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        
        # Məhsul sətirləri
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'NotoSans'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        
        # Cədvəl xətləri
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#2B5173')),
        
        # Sütun enləri - Sifaris kimi
        ('COLWIDTHS', (0, 0), (-1, -1), '*'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(table)

    # PDF-i yarat
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response


def generate_sifaris_pdf(sifaris_id):
    """Sifariş PDF-sini yaratmaq"""
    sifaris = Sifaris.objects.get(id=sifaris_id)
    sifaris_items = sifaris.sifarisitem_set.all()
    statistics = Sifaris.get_order_statistics(sifaris.istifadeci)

    # PDF yaratmaq
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="sifaris_{sifaris_id}.pdf"'

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    elements = []

    # Universal font qeydiyyatı
    pdfmetrics.registerFont(TTFont('NotoSans', 'static/fonts/NotoSans-Regular.ttf'))

    # Logo və başlıq
    styles = getSampleStyleSheet()
    styles['Title'].fontName = 'NotoSans'
    styles['Normal'].fontName = 'NotoSans'
    styles['Normal'].spaceBefore = 0
    styles['Normal'].spaceAfter = 0
    
    # Logo əlavə et
    logo_path = 'static/images/Header_Logo.png'
    try:
        logo = Image(logo_path, width=120, height=80)
        header_table = Table([[logo]], colWidths=[530])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 15))
    except Exception as e:
        print(f"Logo əlavə edilərkən xəta: {e}")

    # Sifariş bilgileri stil
    infoValueStyle = ParagraphStyle(
        'InfoValueStyle',
        parent=styles['Normal'],
        fontName='NotoSans',
        fontSize=9,
        textColor=colors.black,
        spaceAfter=0,
        spaceBefore=0,
        alignment=1  # Merkez
    )

    # Tarixi Azərbaycan formatında
    az_months = {
        1: 'Yanvar', 2: 'Fevral', 3: 'Mart', 4: 'Aprel',
        5: 'May', 6: 'İyun', 7: 'İyul', 8: 'Avqust',
        9: 'Sentyabr', 10: 'Oktyabr', 11: 'Noyabr', 12: 'Dekabr'
    }
    
    local_time = timezone.localtime(sifaris.tarix)
    az_date = f"{local_time.day} {az_months[local_time.month]} {local_time.year}, {local_time.strftime('%H:%M')}"
    
    # Sifariş bilgileri - 4 sütunlu tablo
    info_data = [
        [
            Paragraph(f"<b>Müştəri</b><br/>{sifaris.istifadeci.username}", infoValueStyle),
            Paragraph(f"<b>Tarix</b><br/>{az_date}", infoValueStyle),
            Paragraph(f"<b>Çatdırılma</b><br/>{sifaris.get_catdirilma_usulu_display()}", infoValueStyle),
            Paragraph(f"<b>Sifariş №</b><br/>{sifaris_id}", infoValueStyle),
        ]
    ]
    
    info_table = Table(info_data, colWidths=[130, 130, 130, 130])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0F4F8')),
        ('BORDER', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('PADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    
    elements.append(info_table)
    
    # Qeyd bölməsi
    if sifaris.qeyd:
        elements.append(Spacer(1, 10))
        noteStyle = ParagraphStyle(
            'NoteStyle',
            parent=styles['Normal'],
            fontName='NotoSans',
            fontSize=9,
            textColor=colors.HexColor('#555555'),
            spaceAfter=5,
            spaceBefore=5,
            leading=12
        )
        note_data = [[Paragraph(f"<b>Qeyd:</b> {sifaris.qeyd}", noteStyle)]]
        note_table = Table(note_data, colWidths=[530])
        note_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFACD')),
            ('BORDER', (0, 0), (-1, -1), 0.5, colors.HexColor('#FFD700')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(note_table)
    
    elements.append(Spacer(1, 15))

    # Məhsullar cədvəli - başlıqları mərkəzləşdirmək üçün Paragraph istifadə edirik
    headerStyle = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontName='NotoSans',
        fontSize=9,
        textColor=colors.whitesmoke,
        alignment=1,  # Mərkəz
        spaceAfter=0,
        spaceBefore=0,
        leading=10
    )

    headers = [
        Paragraph('№', headerStyle),
        Paragraph('Kod', headerStyle),
        Paragraph('Firma', headerStyle),
        Paragraph('Məhsul', headerStyle),
        Paragraph('Vitrin', headerStyle),
        Paragraph('Miqdar', headerStyle),
        Paragraph('Qiymət', headerStyle),
        Paragraph('Cəmi', headerStyle)
    ]

    # Məhsullar cədvəli
    data = [headers]
    total_amount = 0
    
    # Məhsul məlumatları üçün stil
    contentStyle = ParagraphStyle(
        'ContentStyle',
        parent=styles['Normal'],
        fontName='NotoSans',
        fontSize=8,
        alignment=1,  # Mərkəz
        spaceAfter=0,
        spaceBefore=0,
        leading=10
    )

    for index, item in enumerate(sifaris_items, 1):
        row = [
            Paragraph(str(index), contentStyle),
            Paragraph(item.mehsul.brend_kod, contentStyle),
            Paragraph(item.mehsul.firma.adi, contentStyle),
            Paragraph(item.mehsul.adi, contentStyle),
            Paragraph(str(item.mehsul.vitrin.nomre) if item.mehsul.vitrin else '-', contentStyle),
            Paragraph(str(item.miqdar), contentStyle),
            Paragraph(f"{item.qiymet} ₼", contentStyle),
            Paragraph(f"{item.umumi_mebleg} ₼", contentStyle)
        ]
        data.append(row)
        total_amount += item.umumi_mebleg

    # Cədvəl stilləri
    table = Table(data)
    table.setStyle(TableStyle([
        # Başlıq sətri
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2B5173')),  # Tünd mavi
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'NotoSans'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('TOPPADDING', (0, 0), (-1, 0), 5),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        
        # Məhsul sətirləri - alternativ rənglər
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'NotoSans'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        
        # Cədvəl xətləri
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.HexColor('#2B5173')),
        
        # Sütun enləri
        ('COLWIDTHS', (0, 0), (-1, -1), '*'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 15))

    # Ümumi məbləğ və Qalıq borc cədvəli
    totalStyle = ParagraphStyle(
        'TotalStyle',
        parent=styles['Normal'],
        fontName='NotoSans',
        fontSize=10,
        fontBold=True,
        alignment=0,  # Sol tərəf
        spaceAfter=0,
        spaceBefore=0,
        leading=12
    )

    amountStyle = ParagraphStyle(
        'AmountStyle',
        parent=styles['Normal'],
        fontName='NotoSans',
        fontSize=10,
        fontBold=True,
        alignment=2,  # Sağ tərəf
        spaceAfter=0,
        spaceBefore=0,
        leading=12,
        textColor=colors.HexColor('#2B5173')
    )

    total_data = [
        [Paragraph('Ümumi Cəmi :', totalStyle), Paragraph(f"{total_amount} ₼", amountStyle)],
        [Paragraph('Qalıq Borc :', totalStyle), Paragraph(f"{statistics['umumi_borc']} ₼", amountStyle)]
    ]

    total_table = Table(total_data, colWidths=[100, 100])
    total_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (0, -1), 20),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F0F4F8')),
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#F0F4F8')),
    ]))

    # Cədvəli sağa tərəfə yerləşdirmək üçün
    align_table = Table([[total_table]], colWidths=[525])
    align_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
    ]))
    
    elements.append(align_table)
    elements.append(Spacer(1, 30))

    # İmzalar bölməsi
    signature_data = [[
        Paragraph("Təhvil Verdi: _________________", styles['Normal']),
        Paragraph(f"Təhvil Aldı: {sifaris.istifadeci.username} _________________", styles['Normal'])
    ]]
    signature_table = Table(signature_data, colWidths=[250, 250])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(signature_table)

    # PDF-i yarat
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response
