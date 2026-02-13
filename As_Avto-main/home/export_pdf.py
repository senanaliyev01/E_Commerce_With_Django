from django.http import HttpResponse
from django.utils import timezone
from django.conf import settings
from .models import Mehsul, Sifaris
import os
import base64


def get_logo_base64():
    """Loqoyu base64 formatında al"""
    try:
        logo_path = os.path.join(settings.BASE_DIR, 'static/images/Header_Logo.png')
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
    except:
        pass
    return None


def generate_products_html():
    """Bütün məhsulların HTML-sini yaratmaq"""
    
    mehsullar = Mehsul.objects.select_related('firma', 'vitrin').all()
    
    # Loqo base64
    logo_base64 = get_logo_base64()
    logo_html = ""
    if logo_base64:
        logo_html = f'<img src="data:image/png;base64,{logo_base64}" alt="Logo" class="logo">'
    
    # Məhsullar üçün sətir verisi
    rows = []
    for index, mehsul in enumerate(mehsullar, 1):
        rows.append({
            'index': index,
            'brend_kod': mehsul.brend_kod or '',
            'firma': mehsul.firma.adi if mehsul.firma else '-',
            'adi': mehsul.adi or '',
            'vitrin': str(mehsul.vitrin.nomre) if mehsul.vitrin else '-',
            'stok': mehsul.stok,
            'qiymet': f"{mehsul.qiymet} ₼"
        })
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="az">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Məhsullar Siyahısı</title>
        <style>
            /* General reset */
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            /* Body and container - larger readable base font */
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                padding: 24px;
                background: white;
                color: #333;
                font-size: 13px; /* increased base size */
            }}

            .container {{
                max-width: 1100px;
                margin: 0 auto;
            }}

            .logo-container {{
                text-align: center;
                margin-bottom: 18px;
                page-break-after: avoid;
            }}

            .logo {{
                width: 160px;
                height: 100px;
                object-fit: contain;
            }}

            .header {{
                text-align: center;
                margin-bottom: 18px;
                padding-bottom: 12px;
                page-break-after: avoid;
            }}

            .header h1 {{
                color: #2B5173;
                font-size: 20px; /* larger header */
                margin-bottom: 0;
                font-weight: 700;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 12px;
                border: 1px solid #2B5173;
            }}

            thead {{
                background-color: #2B5173;
                color: whitesmoke;
            }}

            th {{
                padding: 8px 10px; /* increased padding */
                text-align: center;
                font-weight: 700;
                font-size: 11px; /* larger headings */
                border-right: 1px solid #1a3a52;
                border-bottom: 1px solid #1a3a52;
                line-height: 14px;
            }}

            th:last-child {{
                border-right: none;
            }}

            tbody tr {{
                border-bottom: 1px solid #DDDDDD;
            }}

            tbody tr td {{
                border-right: 1px solid #EEEEEE;
            }}

            tbody tr td:last-child {{
                border-right: none;
            }}

            tbody tr:nth-child(even) {{
                background-color: #fbfbfb;
            }}

            tbody tr:last-child {{
                border-bottom: 1px solid #2B5173;
            }}

            td {{
                padding: 8px 10px; /* increased padding */
                text-align: center;
                font-size: 11px; /* readable cell text */
                line-height: 16px;
                vertical-align: middle;
                white-space: nowrap; /* prevent other cells from wrapping */
            }}

            /* Product name should be allowed to wrap when long; limit visually to ~18 chars */
            .product-name {{
                white-space: normal;
                overflow-wrap: anywhere;
                word-break: break-word;
                max-width: 18ch;
                text-align: center;
                padding: 6px 6px; /* match table cell padding to keep borders aligned */
            }}

            .price {{
                color: #28a745;
                font-weight: 700;
            }}

            @media print {{
                body {{
                    padding: 0;
                    background: white;
                    margin: 0;
                    font-size: 12px;
                }}

                .container {{
                    max-width: 100%;
                    margin: 0;
                }}

                .logo-container {{
                    page-break-after: avoid;
                }}

                .header {{
                    page-break-after: avoid;
                }}

                table {{
                    page-break-inside: avoid;
                }}

                thead {{
                    display: table-header-group;
                }}

                tbody tr {{
                    page-break-inside: avoid;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo-container">
                {logo_html}
            </div>
            
            <div class="header">
                <h1>Qorxmaz Avto +994 55 236 90 09</h1>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>№</th>
                        <th>Kod</th>
                        <th>Firma</th>
                        <th>Məhsul</th>
                        <th>Vitrin</th>
                        <th>Stok</th>
                        <th>Qiymət</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for row in rows:
        html_content += f"""
                    <tr>
                        <td>{row['index']}</td>
                        <td>{row['brend_kod']}</td>
                        <td>{row['firma']}</td>
                        <td class="product-name">{row['adi']}</td>
                        <td>{row['vitrin']}</td>
                        <td>{row['stok']}</td>
                        <td class="price">{row['qiymet']}</td>
                    </tr>
        """
    
    html_content += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    
    response = HttpResponse(content_type='text/html; charset=utf-8')
    response['Content-Disposition'] = 'inline; filename="mehsullar.html"'
    response.write(html_content)
    return response


def generate_sifaris_html(sifaris_id):
    """Sifariş HTML-sini yaratmaq"""
    
    sifaris = Sifaris.objects.select_related('istifadeci', 'istifadeci__profile').prefetch_related(
        'sifarisitem_set__mehsul__firma',
        'sifarisitem_set__mehsul__vitrin'
    ).get(id=sifaris_id)
    
    sifaris_items = sifaris.sifarisitem_set.all()
    statistics = Sifaris.get_order_statistics(sifaris.istifadeci)
    
    # Profil məlumatları
    try:
        profile = sifaris.istifadeci.profile
        user_address = profile.address or '-'
        user_phone = profile.phone or '-'
    except:
        user_address = '-'
        user_phone = '-'
    
    # Loqo base64
    logo_base64 = get_logo_base64()
    logo_html = ""
    if logo_base64:
        logo_html = f'<div class="logo-container"><img src="data:image/png;base64,{logo_base64}" alt="Logo" class="logo"></div>'
    
    # Tarix format
    az_months = {
        1: 'Yanvar', 2: 'Fevral', 3: 'Mart', 4: 'Aprel',
        5: 'May', 6: 'İyun', 7: 'İyul', 8: 'Avqust',
        9: 'Sentyabr', 10: 'Oktyabr', 11: 'Noyabr', 12: 'Dekabr'
    }
    
    local_time = timezone.localtime(sifaris.tarix)
    az_date = f"{local_time.day} {az_months[local_time.month]} {local_time.year}, {local_time.strftime('%H:%M')}"
    
    # Məhsullar
    items_rows = []
    total_amount = 0
    
    for index, item in enumerate(sifaris_items, 1):
        items_rows.append({
            'index': index,
            'brend_kod': item.mehsul.brend_kod or '',
            'firma': item.mehsul.firma.adi if item.mehsul.firma else '',
            'adi': item.mehsul.adi or '',
            'vitrin': str(item.mehsul.vitrin.nomre) if item.mehsul.vitrin else '-',
            'miqdar': item.miqdar,
            'qiymet': f"{item.qiymet} ₼",
            'umumi_mebleg': f"{item.umumi_mebleg} ₼"
        })
        total_amount += item.umumi_mebleg
    
    items_html = ""
    for row in items_rows:
        items_html += f"""
            <tr>
                <td>{row['index']}</td>
                <td>{row['brend_kod']}</td>
                <td>{row['firma']}</td>
                <td class="product-name">{row['adi']}</td>
                <td>{row['vitrin']}</td>
                <td>{row['miqdar']}</td>
                <td>{row['qiymet']}</td>
                <td class="total-cell">{row['umumi_mebleg']}</td>
            </tr>
        """
    
    note_section = f"""
            <div class="note-section">
                <b>Qeyd:</b> {sifaris.qeyd}
            </div>
    """ if sifaris.qeyd else ""
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="az">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sifariş #{sifaris_id}</title>
        <style>
            @page {{
                margin: 0.5in;
            }}

            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                padding: 22px;
                background: white;
                color: #333;
                font-size: 13px;
            }}

            .container {{
                max-width: 720px; /* slightly wider for readability */
                margin: 0 auto;
            }}

            .logo-container {{
                text-align: center;
                margin-bottom: 14px;
            }}

            .logo {{
                width: 150px;
                height: 90px;
                object-fit: contain;
            }}

            /* Info row: logo left, customer info right */
            .info-row {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                gap: 18px;
                margin-bottom: 14px;
            }}

            .info-left {{
                flex: 0 0 auto;
            }}

            .info-right {{
                flex: 1 1 auto;
                text-align: right;
                font-size: 11px;
                line-height: 1.4;
            }}

            .info-right .info-item {{
                margin-bottom: 6px;
            }}

            .info-right .label {{
                font-weight: 700;
                color: #2B5173;
                margin-left: 6px;
            }}

            .note-section {{
                background: #FFFACD;
                border-left: 4px solid #FFD700;
                padding: 10px;
                margin: 14px 0;
                border-radius: 3px;
                font-size: 11px;
                color: #555555;
            }}

            table.products {{
                width: 100%;
                border-collapse: collapse;
                margin: 14px 0;
                border: 1px solid #2B5173;
            }}

            table.products thead {{
                background-color: #2B5173;
                color: whitesmoke;
            }}

            table.products th {{
                padding: 8px 6px;
                text-align: center;
                font-weight: 700;
                font-size: 10px;
                border-right: 1px solid #1a3a52;
                border-bottom: 1px solid #1a3a52;
                line-height: 14px;
            }}

            table.products th:last-child {{
                border-right: none;
            }}

            table.products tbody tr {{
                border-bottom: 1px solid #CCCCCC;
            }}

            table.products tbody tr td {{
                border-right: 1px solid #EEEEEE;
            }}

            table.products tbody tr td:last-child {{
                border-right: none;
            }}

            table.products tbody tr:nth-child(even) {{
                background-color: #ffffff;
            }}

            table.products tbody tr:last-child {{
                border-bottom: 1px solid #2B5173;
            }}

            table.products td {{
                padding: 6px 6px;
                text-align: center;
                font-size: 10px;
                line-height: 14px;
                vertical-align: middle;
            }}

            /* Product name wrapping and centering inside sifaris table */
            .product-name {{
                white-space: normal;
                overflow-wrap: anywhere;
                word-break: break-word;
                max-width: 18ch;
                text-align: center;
                padding: 6px 6px; /* match table cell padding to keep borders aligned */
            }}

            .total-cell {{
                color: #28a745;
                font-weight: 700;
            }}

            .totals-section {{
                display: flex;
                flex-direction: column;
                align-items: flex-end;
                margin-top: 16px;
                font-size: 12px;
                gap: 6px;
            }}

            .total-row {{
                display: flex;
                justify-content: space-between;
                width: 220px;
                font-weight: 700;
            }}

            .total-label {{
                color: #333;
            }}

            .total-value {{
                color: #2B5173;
                margin-left: 30px;
            }}

            .signature-section {{
                display: flex;
                justify-content: space-between;
                margin-top: 48px;
                font-size: 11px;
                line-height: 14px;
            }}

            .signature-item {{
                text-align: center;
                flex: 1;
            }}

            .signature-line {{
                margin-top: 36px;
                padding-top: 6px;
            }}

            @media print {{
                body {{
                    padding: 0;
                    background: white;
                }}

                .container {{
                    max-width: 100%;
                }}

                table {{
                    page-break-inside: avoid;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="info-row">
                <div class="info-left">
                    {logo_html}
                </div>
                <div class="info-right">
                    <div class="info-item"><span class="label">Müştəri:</span> {sifaris.istifadeci.username}</div>
                    <div class="info-item"><span class="label">Ünvan:</span> {user_address}</div>
                    <div class="info-item"><span class="label">Telefon:</span> {user_phone}</div>
                    <div class="info-item"><span class="label">Tarix:</span> {az_date}</div>
                    <div class="info-item"><span class="label">Çatdırılma:</span> {sifaris.get_catdirilma_usulu_display()}</div>
                    <div class="info-item"><span class="label">Sifariş №:</span> {sifaris_id}</div>
                </div>
            </div>
            
            {note_section}
            
            <table class="products">
                <thead>
                    <tr>
                        <th>№</th>
                        <th>Kod</th>
                        <th>Firma</th>
                        <th>Məhsul</th>
                        <th>Vitrin</th>
                        <th>Miqdar</th>
                        <th>Qiymət</th>
                        <th>Cəmi</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
            </table>
            
            <div class="totals-section">
                <div class="total-row">
                    <span class="total-label">Ümumi Cəmi :</span>
                    <span class="total-value">{total_amount} ₼</span>
                </div>
                <div class="total-row">
                    <span class="total-label">Qalıq Borc :</span>
                    <span class="total-value">{statistics['umumi_borc']} ₼</span>
                </div>
            </div>
            
            <div class="signature-section">
                <div class="signature-item">
                    <div class="signature-line">Təhvil Verdi: _________________</div>
                </div>
                <div class="signature-item">
                    <div class="signature-line">Təhvil Aldı: {sifaris.istifadeci.username} _________________</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    response = HttpResponse(content_type='text/html; charset=utf-8')
    response['Content-Disposition'] = 'inline; filename="sifaris.html"'
    response.write(html_content)
    
    return response
