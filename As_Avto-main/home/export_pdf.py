from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
from django.http import HttpResponse, StreamingHttpResponse
from django.utils import timezone
from django.db.models import Prefetch
from .models import Mehsul, Sifaris
import json

# Module-level font registration (one-time only)
try:
    pdfmetrics.registerFont(TTFont('NotoSans', 'static/fonts/NotoSans-Regular.ttf'))
except:
    pass

# Module-level style cache
_styles_cache = {}

def _get_style(name, **kwargs):
    """Get cached style or create new one"""
    cache_key = name
    if cache_key not in _styles_cache:
        styles = getSampleStyleSheet()
        if name == 'header':
            _styles_cache[cache_key] = ParagraphStyle(
                'HeaderStyle',
                parent=styles['Normal'],
                fontName='NotoSans',
                fontSize=9,
                textColor=colors.whitesmoke,
                alignment=1,
                spaceAfter=0,
                spaceBefore=0,
                leading=10
            )
        elif name == 'content':
            _styles_cache[cache_key] = ParagraphStyle(
                'ContentStyle',
                parent=styles['Normal'],
                fontName='NotoSans',
                fontSize=8,
                alignment=1,
                spaceAfter=0,
                spaceBefore=0,
                leading=10
            )
    return _styles_cache[cache_key]


def generate_products_pdf(progress_callback=None):
    """Bütün məhsulların PDF-sini yaratmaq"""
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="mehsullar.pdf"'

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    elements = []

    styles = getSampleStyleSheet()
    styles['Title'].fontName = 'NotoSans'
    title = Paragraph("Qorxmaz Avto +994 55 236 90 09", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 20))

    headerStyle = _get_style('header')
    contentStyle = _get_style('content')

    # Fetch all data at once with select_related for optimization
    mehsullar = Mehsul.objects.select_related('firma', 'vitrin').all()
    total_products = mehsullar.count()
    
    if progress_callback:
        progress_callback(10)
    
    # Build table data efficiently
    headers = [
        Paragraph('№', headerStyle),
        Paragraph('Kod', headerStyle),
        Paragraph('Firma', headerStyle),
        Paragraph('Məhsul', headerStyle),
        Paragraph('Vitrin', headerStyle),
        Paragraph('Stok', headerStyle),
        Paragraph('Qiymət', headerStyle)
    ]
    
    data = [headers]
    for index, mehsul in enumerate(mehsullar, 1):
        row = [
            Paragraph(str(index), contentStyle),
            Paragraph(mehsul.brend_kod or '', contentStyle),
            Paragraph(mehsul.firma.adi if mehsul.firma else '-', contentStyle),
            Paragraph(mehsul.adi or '', contentStyle),
            Paragraph(str(mehsul.vitrin.nomre) if mehsul.vitrin else '-', contentStyle),
            Paragraph(str(mehsul.stok), contentStyle),
            Paragraph(f"{mehsul.qiymet} ₼", contentStyle)
        ]
        data.append(row)
        
        # Call progress callback
        if progress_callback and total_products > 0:
            progress = int(10 + (index / total_products) * 70)
            progress_callback(progress)

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2B5173')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'NotoSans'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('TOPPADDING', (0, 0), (-1, 0), 5),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'NotoSans'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#2B5173')),
        ('COLWIDTHS', (0, 0), (-1, -1), '*'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(table)
    
    if progress_callback:
        progress_callback(85)
    
    doc.build(elements)
    
    if progress_callback:
        progress_callback(95)
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    if progress_callback:
        progress_callback(100)

    return response


def generate_sifaris_pdf(sifaris_id, progress_callback=None):
    """Sifariş PDF-sini yaratmaq"""
    
    if progress_callback:
        progress_callback(5)
    
    # Optimized query with prefetch_related
    sifaris = Sifaris.objects.select_related('istifadeci').prefetch_related('sifarisitem_set__mehsul__firma', 'sifarisitem_set__mehsul__vitrin').get(id=sifaris_id)
    sifaris_items = sifaris.sifarisitem_set.all()
    statistics = Sifaris.get_order_statistics(sifaris.istifadeci)

    if progress_callback:
        progress_callback(15)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="sifaris_{sifaris_id}.pdf"'

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    elements = []

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
    except:
        pass

    # Info styles
    infoLabelStyle = ParagraphStyle(
        'InfoLabelStyle',
        parent=styles['Normal'],
        fontName='NotoSans',
        fontSize=8,
        textColor=colors.HexColor('#FFFFFF'),
        spaceAfter=0,
        spaceBefore=0,
        alignment=1,
        fontBold=True,
        leading=10
    )
    
    infoValueStyle = ParagraphStyle(
        'InfoValueStyle',
        parent=styles['Normal'],
        fontName='NotoSans',
        fontSize=10,
        textColor=colors.HexColor('#2B5173'),
        spaceAfter=0,
        spaceBefore=0,
        alignment=1,
        fontBold=True,
        leading=12
    )

    # Date formatting
    az_months = {
        1: 'Yanvar', 2: 'Fevral', 3: 'Mart', 4: 'Aprel',
        5: 'May', 6: 'İyun', 7: 'İyul', 8: 'Avqust',
        9: 'Sentyabr', 10: 'Oktyabr', 11: 'Noyabr', 12: 'Dekabr'
    }
    
    local_time = timezone.localtime(sifaris.tarix)
    az_date = f"{local_time.day} {az_months[local_time.month]} {local_time.year}, {local_time.strftime('%H:%M')}"
    
    # Order info
    info_data = [
        [
            Paragraph('Müştəri', infoLabelStyle),
            Paragraph('Tarix', infoLabelStyle),
            Paragraph('Çatdırılma', infoLabelStyle),
            Paragraph('Sifariş №', infoLabelStyle),
        ],
        [
            Paragraph(sifaris.istifadeci.username, infoValueStyle),
            Paragraph(az_date, infoValueStyle),
            Paragraph(sifaris.get_catdirilma_usulu_display(), infoValueStyle),
            Paragraph(str(sifaris_id), infoValueStyle),
        ]
    ]
    
    info_table = Table(info_data, colWidths=[130, 130, 130, 130])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2B5173')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#FFFFFF')),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#E8F0F6')),
        ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#2B5173')),
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#2B5173')),
        ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#2B5173')),
        ('LINELEFT', (0, 0), (0, -1), 1.5, colors.HexColor('#2B5173')),
        ('LINERIGHT', (-1, 0), (-1, -1), 1.5, colors.HexColor('#2B5173')),
        ('LINEBELOW', (0, -1), (-1, -1), 1.5, colors.HexColor('#2B5173')),
        ('LINEBETWEEN', (0, 0), (-1, -1), 1, colors.HexColor('#B8D1E8')),
        ('PADDING', (0, 0), (-1, 0), 12),
        ('PADDING', (0, 1), (-1, 1), 15),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    
    elements.append(info_table)
    
    # Notes section
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

    # Products table header
    headerStyle = _get_style('header')
    contentStyle = _get_style('content')

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

    # Build products data
    data = [headers]
    total_amount = 0
    items_count = len(list(sifaris_items))
    
    for index, item in enumerate(sifaris_items, 1):
        row = [
            Paragraph(str(index), contentStyle),
            Paragraph(item.mehsul.brend_kod or '', contentStyle),
            Paragraph(item.mehsul.firma.adi if item.mehsul.firma else '', contentStyle),
            Paragraph(item.mehsul.adi or '', contentStyle),
            Paragraph(str(item.mehsul.vitrin.nomre) if item.mehsul.vitrin else '-', contentStyle),
            Paragraph(str(item.miqdar), contentStyle),
            Paragraph(f"{item.qiymet} ₼", contentStyle),
            Paragraph(f"{item.umumi_mebleg} ₼", contentStyle)
        ]
        data.append(row)
        total_amount += item.umumi_mebleg
        
        # Progress callback
        if progress_callback and items_count > 0:
            progress = int(20 + (index / items_count) * 50)
            progress_callback(progress)

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2B5173')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'NotoSans'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('TOPPADDING', (0, 0), (-1, 0), 5),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'NotoSans'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.HexColor('#2B5173')),
        ('COLWIDTHS', (0, 0), (-1, -1), '*'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 15))

    # Totals
    totalStyle = ParagraphStyle(
        'TotalStyle',
        parent=styles['Normal'],
        fontName='NotoSans',
        fontSize=10,
        fontBold=True,
        alignment=0,
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
        alignment=2,
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

    align_table = Table([[total_table]], colWidths=[525])
    align_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
    ]))
    
    elements.append(align_table)
    elements.append(Spacer(1, 30))

    # Signatures
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

    if progress_callback:
        progress_callback(80)

    doc.build(elements)
    
    if progress_callback:
        progress_callback(90)
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    if progress_callback:
        progress_callback(100)

    return response
