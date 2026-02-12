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
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                padding: 20px;
                background: white;
                color: #333;
            }}
            
            .container {{
                max-width: 1000px;
                margin: 0 auto;
            }}
            
            .logo-container {{
                text-align: center;
                margin-bottom: 15px;
                page-break-after: avoid;
            }}
            
            .logo {{
                width: 120px;
                height: 80px;
                object-fit: contain;
            }}
            
            .header {{
                text-align: center;
                margin-bottom: 20px;
                padding-bottom: 15px;
                page-break-after: avoid;
            }}
            
            .header h1 {{
                color: #2B5173;
                font-size: 16px;
                margin-bottom: 0;
                font-weight: 600;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
                border: 1px solid #2B5173;
            }}
            
            thead {{
                background-color: #2B5173;
                color: whitesmoke;
            }}
            
            th {{
                padding: 5px 8px;
                text-align: center;
                font-weight: 600;
                font-size: 9px;
                border-right: 1px solid #1a3a52;
                border-bottom: 1px solid #1a3a52;
                line-height: 10px;
            }}
            
            th:last-child {{
                border-right: none;
            }}
            
            tbody tr {{
                border-bottom: 1px solid #CCCCCC;
            }}
            
            tbody tr td {{
                border-right: 1px solid #CCCCCC;
            }}
            
            tbody tr td:last-child {{
                border-right: none;
            }}
            
            tbody tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            
            tbody tr:last-child {{
                border-bottom: 1px solid #2B5173;
            }}
            
            td {{
                padding: 3px 8px;
                text-align: center;
                font-size: 8px;
                line-height: 10px;
                vertical-align: middle;
            }}
            
            .price {{
                color: #28a745;
                font-weight: 600;
            }}
            
            @media print {{
                body {{
                    padding: 0;
                    background: white;
                    margin: 0;
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
                        <td>{row['adi']}</td>
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
                <td>{row['adi']}</td>
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
                padding: 20px;
                background: white;
                color: #333;
            }}
            
            .container {{
                max-width: 600px;
                margin: 0 auto;
            }}
            
            .logo-container {{
                text-align: center;
                margin-bottom: 15px;
            }}
            
            .logo {{
                width: 120px;
                height: 80px;
                object-fit: contain;
            }}
            
            .info-table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 15px;
            }}
            
            .info-table td {{
                padding: 8px;
                font-size: 7px;
                text-align: center;
                line-height: 9px;
            }}
            
            .info-label {{
                background-color: #2B5173;
                color: white;
                font-weight: bold;
                border: 1px solid #2B5173;
            }}
            
            .info-value {{
                background-color: #E8F0F6;
                color: #2B5173;
                font-weight: bold;
                border: 1px solid #B8D1E8;
            }}
            
            .info-table tr:first-child td {{
                border-bottom: 2px solid #2B5173;
            }}
            
            .note-section {{
                background: #FFFACD;
                border-left: 4px solid #FFD700;
                padding: 8px;
                margin: 15px 0;
                border-radius: 3px;
                font-size: 9px;
                color: #555555;
            }}
            
            table.products {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
                border: 1px solid #2B5173;
            }}
            
            table.products thead {{
                background-color: #2B5173;
                color: whitesmoke;
            }}
            
            table.products th {{
                padding: 5px 4px;
                text-align: center;
                font-weight: 600;
                font-size: 9px;
                border-right: 1px solid #1a3a52;
                border-bottom: 1px solid #1a3a52;
                line-height: 10px;
            }}
            
            table.products th:last-child {{
                border-right: none;
            }}
            
            table.products tbody tr {{
                border-bottom: 1px solid #CCCCCC;
            }}
            
            table.products tbody tr td {{
                border-right: 1px solid #CCCCCC;
            }}
            
            table.products tbody tr td:last-child {{
                border-right: none;
            }}
            
            table.products tbody tr:nth-child(even) {{
                background-color: white;
            }}
            
            table.products tbody tr:last-child {{
                border-bottom: 1px solid #2B5173;
            }}
            
            table.products td {{
                padding: 3px 4px;
                text-align: center;
                font-size: 8px;
                line-height: 10px;
                vertical-align: middle;
            }}
            
            .total-cell {{
                color: #28a745;
                font-weight: 600;
            }}
            
            .totals-section {{
                display: flex;
                flex-direction: column;
                align-items: flex-end;
                margin-top: 15px;
                font-size: 10px;
                gap: 3px;
            }}
            
            .total-row {{
                display: flex;
                justify-content: space-between;
                width: 160px;
                font-weight: bold;
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
                margin-top: 40px;
                font-size: 9px;
                line-height: 10px;
            }}
            
            .signature-item {{
                text-align: center;
                flex: 1;
            }}
            
            .signature-line {{
                margin-top: 30px;
                padding-top: 3px;
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
            {logo_html}
            
            <table class="info-table">
                <tr>
                    <td class="info-label">Müştəri</td>
                    <td class="info-label">Ünvan</td>
                    <td class="info-label">Telefon</td>
                    <td class="info-label">Tarix</td>
                    <td class="info-label">Çatdırılma</td>
                    <td class="info-label">Sifariş №</td>
                </tr>
                <tr>
                    <td class="info-value">{sifaris.istifadeci.username}</td>
                    <td class="info-value">{user_address}</td>
                    <td class="info-value">{user_phone}</td>
                    <td class="info-value">{az_date}</td>
                    <td class="info-value">{sifaris.get_catdirilma_usulu_display()}</td>
                    <td class="info-value">{sifaris_id}</td>
                </tr>
            </table>
            
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
