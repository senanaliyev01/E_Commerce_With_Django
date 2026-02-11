import pandas as pd
import math
import os
import uuid
import json
from django.http import JsonResponse
from django.conf import settings
from django.db import transaction
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseRedirect
from .models import Kateqoriya, Firma, Avtomobil, Mehsul, Vitrin


def handle_import_excel_view(request, admin_instance):
    """Excel faylı import etmə məsələsi"""
    if request.method == 'POST':
        excel_file = request.FILES.get("excel_file")
        if not excel_file:
            admin_instance.message_user(request, 'Zəhmət olmasa Excel faylı seçin', level=messages.ERROR)
            return HttpResponseRedirect("../")
            
        if not excel_file.name.endswith('.xlsx'):
            admin_instance.message_user(request, 'Yalnız .xlsx faylları qəbul edilir', level=messages.ERROR)
            return HttpResponseRedirect("../")
            
        try:
            df = pd.read_excel(excel_file)
            print(f"Excel faylının sütunları: {df.columns.tolist()}")
            print(f"Excel faylında {len(df)} sətir var")
            
            new_count = 0
            update_count = 0
            error_count = 0
            deleted_count = 0
            # Excel faylındakı məhsulların açarları: (brend_kod, firma_id)
            excel_product_keys = set()
            
            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        print(f"\nSətir {index + 1} emal edilir:")
                        print(f"Məlumatlar: {dict(row)}")
                        
                        # Sətirin bütün sütun adlarını təmizləyirik
                        row = {str(k).strip().lower(): v for k, v in row.items()}
                        
                        # Kateqoriya, firma və avtomobili tap və ya yarat
                        kateqoriya = None
                        firma = None
                        avtomobil = None
                        vitrin = None
                        
                        if 'kateqoriya' in row and pd.notna(row['kateqoriya']):
                            kateqoriya, _ = Kateqoriya.objects.get_or_create(adi=str(row['kateqoriya']).strip())
                            print(f"Kateqoriya: {kateqoriya}")
                        
                        if 'firma' in row and pd.notna(row['firma']):
                            firma, _ = Firma.objects.get_or_create(adi=str(row['firma']).strip())
                            print(f"Firma: {firma}")
                        
                        if 'avtomobil' in row and pd.notna(row['avtomobil']):
                            avtomobil, _ = Avtomobil.objects.get_or_create(adi=str(row['avtomobil']).strip())
                            print(f"Avtomobil: {avtomobil}")

                        if 'vitrin' in row and pd.notna(row['vitrin']):
                            vitrin, _ = Vitrin.objects.get_or_create(nomre=str(row['vitrin']).strip())
                            print(f"Vitrin: {vitrin}")

                        # Məhsulun adını təmizlə
                        if 'adi' not in row or pd.isna(row['adi']):
                            print("XƏTA: Məhsulun adı yoxdur")
                            admin_instance.message_user(request, f'Sətir {index + 1}: Məhsulun adı boşdur', level=messages.ERROR)
                            error_count += 1
                            continue

                        temiz_ad = str(row['adi']).strip()
                        temiz_ad = ' '.join(temiz_ad.split())
                        print(f"Təmizlənmiş ad: {temiz_ad}")

                        # brend_kod-u təyin et
                        brend_kod = None
                        if 'brend_kod' in row and pd.notna(row['brend_kod']):
                            value = row['brend_kod']
                            if isinstance(value, float) and math.isnan(value):
                                brend_kod = None
                            else:
                                brend_kod = str(value).strip()
                                if brend_kod.lower() == 'nan' or brend_kod == '':
                                    brend_kod = None

                        if not brend_kod:
                            print("XƏTA: Brend kodu boşdur")
                            admin_instance.message_user(request, f'Sətir {index + 1}: Brend kodu boşdur', level=messages.ERROR)
                            error_count += 1
                            continue

                        print(f"Brend kod: {brend_kod}")

                        # Bu sətirdəki məhsulun açarını yadda saxla
                        excel_product_keys.add((brend_kod, firma.id if firma else None))

                        # Mövcud məhsulu həm brend_kod, həm firma ilə yoxla
                        if firma:
                            existing_product = Mehsul.objects.filter(brend_kod=brend_kod, firma=firma).first()
                        else:
                            existing_product = Mehsul.objects.filter(brend_kod=brend_kod, firma__isnull=True).first()

                        try:
                            if existing_product:
                                # Mövcud məhsulu yenilə
                                existing_product.adi = temiz_ad
                                
                                # Excel-də olan məlumatları yenilə, olmayanları None et
                                existing_product.kateqoriya = kateqoriya
                                existing_product.firma = firma
                                existing_product.avtomobil = avtomobil
                                existing_product.vitrin = vitrin
                                
                                # Digər məlumatları yenilə
                                existing_product.brend_kod = brend_kod
                                existing_product.olcu = str(row['olcu']).strip() if 'olcu' in row and pd.notna(row['olcu']) else ''
                                existing_product.maya_qiymet = float(row['maya_qiymet']) if 'maya_qiymet' in row and pd.notna(row['maya_qiymet']) else 0
                                existing_product.qiymet = float(row['qiymet']) if 'qiymet' in row and pd.notna(row['qiymet']) else 0
                                existing_product.stok = int(row['stok']) if 'stok' in row and pd.notna(row['stok']) else 0
                                existing_product.kodlar = str(row['kodlar']) if 'kodlar' in row and pd.notna(row['kodlar']) else ''
                                existing_product.melumat = str(row['melumat']) if 'melumat' in row and pd.notna(row['melumat']) else ''
                                
                                existing_product.save()
                                print(f"Məhsul yeniləndi: {existing_product}")
                                update_count += 1
                            else:
                                # Yeni məhsul yarat
                                mehsul_data = {
                                    'adi': temiz_ad,
                                    'kateqoriya': kateqoriya,
                                    'firma': firma,
                                    'avtomobil': avtomobil,
                                    'vitrin': vitrin,
                                    'brend_kod': brend_kod,
                                    'oem': '',  # oem-i boş saxla
                                    'olcu': str(row['olcu']).strip() if 'olcu' in row and pd.notna(row['olcu']) else '',
                                    'maya_qiymet': float(row['maya_qiymet']) if 'maya_qiymet' in row and pd.notna(row['maya_qiymet']) else 0,
                                    'qiymet': float(row['qiymet']) if 'qiymet' in row and pd.notna(row['qiymet']) else 0,
                                    'stok': int(row['stok']) if 'stok' in row and pd.notna(row['stok']) else 0,
                                    'kodlar': str(row['kodlar']) if 'kodlar' in row and pd.notna(row['kodlar']) else '',
                                    'melumat': str(row['melumat']) if 'melumat' in row and pd.notna(row['melumat']) else '',
                                    'yenidir': False
                                }
                                
                                yeni_mehsul = Mehsul.objects.create(**mehsul_data)
                                print(f"Yeni məhsul yaradıldı: {yeni_mehsul}")
                                new_count += 1

                        except Exception as e:
                            print(f"Məhsul əlavə edilərkən xəta: {e}")
                            admin_instance.message_user(request, f'Sətir {index + 1}: {str(e)}', level=messages.ERROR)
                            error_count += 1
                            continue

                    except Exception as e:
                        print(f"Sətir {index + 1} emal edilərkən xəta: {e}")
                        admin_instance.message_user(request, f'Sətir {index + 1}: {str(e)}', level=messages.ERROR)
                        error_count += 1
                        continue

                # Excel-də olmayan məhsulları sil
                if excel_product_keys:
                    all_products = Mehsul.objects.all()
                    to_delete_ids = []
                    for p in all_products:
                        product_key = (p.brend_kod, p.firma_id)
                        if product_key not in excel_product_keys:
                            to_delete_ids.append(p.id)
                    
                    if to_delete_ids:
                        # delete() returns total deleted rows including cascaded related objects.
                        # We want to report number of Mehsul records deleted, so count them first.
                        deleted_count = Mehsul.objects.filter(id__in=to_delete_ids).count()
                        Mehsul.objects.filter(id__in=to_delete_ids).delete()

                # Nəticəni göstər
                success_message = f"Excel faylı uğurla import edildi! "
                if new_count > 0:
                    success_message += f"{new_count} yeni məhsul əlavə edildi. "
                if update_count > 0:
                    success_message += f"{update_count} məhsul yeniləndi. "
                if deleted_count > 0:
                    success_message += f"{deleted_count} məhsul Excel-də olmadığı üçün silindi. "
                if error_count > 0:
                    success_message += f"{error_count} xəta baş verdi."
                
                admin_instance.message_user(request, success_message, level=messages.SUCCESS)
                return HttpResponseRedirect("../")

        except Exception as e:
            print(f"Excel faylı oxunarkən xəta: {e}")
            admin_instance.message_user(request, f'Excel faylı oxunarkən xəta: {str(e)}', level=messages.ERROR)
            return HttpResponseRedirect("../")

    # GET request üçün
    context = {
        'title': 'Excel faylı import et',
        'has_permission': True,
    }
    return render(request, 'admin/import_excel.html', context)


def handle_import_excel_init(request):
    """Excel faylını qəbul edir, sətirləri təmizləyib job faylına yazır, job_id qaytarır"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Yalnız POST.'}, status=405)

    excel_file = request.FILES.get("excel_file")
    if not excel_file:
        return JsonResponse({'status': 'error', 'message': 'Excel faylı seçin.'}, status=400)
    if not excel_file.name.endswith('.xlsx'):
        return JsonResponse({'status': 'error', 'message': 'Yalnız .xlsx faylı qəbul edilir.'}, status=400)

    # Faylı media/imports altına yaz
    imports_dir = os.path.join(settings.MEDIA_ROOT, 'imports')
    os.makedirs(imports_dir, exist_ok=True)
    job_id = str(uuid.uuid4())
    saved_path = os.path.join(imports_dir, f'admin_{job_id}.xlsx')
    with open(saved_path, 'wb+') as dest:
        for chunk in excel_file.chunks():
            dest.write(chunk)

    # Exceli oxu və sətirləri təmizlə
    try:
        df = pd.read_excel(saved_path)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Excel oxunmadı: {e}'}, status=400)

    cleaned_rows = []
    columns_display = [str(c) for c in df.columns]
    columns_lower = [str(c).strip().lower() for c in df.columns]
    for index, row in df.iterrows():
        row = {str(k).strip().lower(): v for k, v in row.items()}
        cleaned_rows.append(row)

    total_rows = len(cleaned_rows)

    # Job state faylı
    jobs_dir = os.path.join(imports_dir, 'jobs')
    os.makedirs(jobs_dir, exist_ok=True)
    job_state_path = os.path.join(jobs_dir, f'{job_id}.json')
    job_state = {
        'file_path': saved_path,
        'total_rows': total_rows,
        'processed_rows': 0,
        'new_count': 0,
        'update_count': 0,
        'error_count': 0,
        'deleted_count': 0,
        'excel_product_keys': [],  # (brend_kod, firma_id)
        'error_details': [],  # ['5-ci sətir: ...', ...]
        'rows': cleaned_rows,
        'columns': columns_lower,
        'columns_display': columns_display,
    }
    with open(job_state_path, 'w', encoding='utf-8') as f:
        json.dump(job_state, f, ensure_ascii=False)

    return JsonResponse({'status': 'ok', 'job_id': job_id, 'total_rows': total_rows})


def handle_import_excel_batch(request):
    """Verilən interval üzrə (start, size) sətirləri emal edir"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Yalnız POST.'}, status=405)

    job_id = request.POST.get('job_id')
    try:
        start = int(request.POST.get('start', 0))
        size = int(request.POST.get('size', 100))
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'start/size yanlışdır.'}, status=400)

    imports_dir = os.path.join(settings.MEDIA_ROOT, 'imports')
    job_state_path = os.path.join(imports_dir, 'jobs', f'{job_id}.json')
    if not os.path.exists(job_state_path):
        return JsonResponse({'status': 'error', 'message': 'Job tapılmadı.'}, status=404)

    with open(job_state_path, 'r', encoding='utf-8') as f:
        state = json.load(f)

    rows = state.get('rows', [])
    subset = rows[start:start+size]
    if not subset:
        return JsonResponse({'status': 'ok', 'message': 'Heç nə yoxdur', 'processed_rows': state['processed_rows'], 'new_count': state['new_count'], 'update_count': state['update_count'], 'error_count': state['error_count']})

    new_count = state['new_count']
    update_count = state['update_count']
    error_count = state['error_count']
    excel_keys = set(tuple(k) for k in state.get('excel_product_keys', []))
    error_details = state.get('error_details', [])
    batch_errors = []

    # Emal məntiqi
    for idx, row in enumerate(subset, start=start):
        try:
            excel_line_no = idx + 2  # Başlıq 1-ci sətir, data 2-dən başlayır
            # Model referansları
            kateqoriya = None
            firma = None
            avtomobil = None
            vitrin = None

            if 'kateqoriya' in row and pd.notna(row['kateqoriya']):
                kateqoriya, _ = Kateqoriya.objects.get_or_create(adi=str(row['kateqoriya']).strip())
            if 'firma' in row and pd.notna(row['firma']):
                firma, _ = Firma.objects.get_or_create(adi=str(row['firma']).strip())
            if 'avtomobil' in row and pd.notna(row['avtomobil']):
                avtomobil, _ = Avtomobil.objects.get_or_create(adi=str(row['avtomobil']).strip())
            if 'vitrin' in row and pd.notna(row['vitrin']):
                vitrin, _ = Vitrin.objects.get_or_create(nomre=str(row['vitrin']).strip())

            # Hazırla: sətirin bütün dəyərləri və xəta yığımı
            full_row = {str(k): ('' if (k not in row or pd.isna(row.get(k))) else str(row.get(k))) for k in row.keys()}
            row_errors = []
            def add_err(field_name, message):
                row_errors.append({
                    'line': excel_line_no,
                    'message': message,
                    'field': field_name,
                    'row': full_row,
                })

            # Tələb olunan sahələr: adi , brend_kod , firma , avtomobil, maya_qiymet, qiymet, stok
            # adi
            if ('adi' not in row) or pd.isna(row.get('adi')) or str(row.get('adi')).strip() == '':
                add_err('adi', 'Məhsulun adı boşdur')

            temiz_ad = str(row['adi']).strip()
            temiz_ad = ' '.join(temiz_ad.split())

            # brend_kod
            brend_kod = None
            if 'brend_kod' in row and pd.notna(row['brend_kod']):
                value = row['brend_kod']
                if not (isinstance(value, float) and math.isnan(value)):
                    candidate = str(value).strip()
                    if candidate.lower() != 'nan' and candidate != '':
                        brend_kod = candidate
            if not brend_kod:
                add_err('brend_kod', 'Brend kodu boşdur')

            # firma (required)
            firma_name = row.get('firma') if 'firma' in row else ''
            if (firma_name is None) or (str(firma_name).strip() == '') or pd.isna(firma_name):
                add_err('firma', 'Firma boşdur')
            else:
                firma, _ = Firma.objects.get_or_create(adi=str(firma_name).strip())

            # avtomobil (required)
            avtomobil_name = row.get('avtomobil') if 'avtomobil' in row else ''
            if (avtomobil_name is None) or (str(avtomobil_name).strip() == '') or pd.isna(avtomobil_name):
                add_err('avtomobil', 'Avtomobil boşdur')
            else:
                avtomobil, _ = Avtomobil.objects.get_or_create(adi=str(avtomobil_name).strip())

            # maya_qiymet (required float)
            maya_qiymet_value = row.get('maya_qiymet')
            if maya_qiymet_value is None or (str(maya_qiymet_value).strip() == '') or pd.isna(maya_qiymet_value):
                add_err('maya_qiymet', 'maya_qiymet boşdur')
                maya_qiymet_parsed = None
            else:
                try:
                    maya_qiymet_parsed = float(str(maya_qiymet_value).replace(',', '.'))
                except Exception:
                    maya_qiymet_parsed = None
                    add_err('maya_qiymet', 'maya_qiymet rəqəm olmalıdır')

            # qiymet (required float)
            qiymet_value = row.get('qiymet')
            if qiymet_value is None or (str(qiymet_value).strip() == '') or pd.isna(qiymet_value):
                add_err('qiymet', 'qiymet boşdur')
                qiymet_parsed = None
            else:
                try:
                    qiymet_parsed = float(str(qiymet_value).replace(',', '.'))
                except Exception:
                    qiymet_parsed = None
                    add_err('qiymet', 'qiymet rəqəm olmalıdır')

            # stok (required int)
            stok_value = row.get('stok')
            if stok_value is None or (str(stok_value).strip() == '') or pd.isna(stok_value):
                add_err('stok', 'stok boşdur')
                stok_parsed = None
            else:
                try:
                    stok_parsed = int(float(str(stok_value).replace(',', '.')))
                except Exception:
                    stok_parsed = None
                    add_err('stok', 'stok tam ədəd olmalıdır')

            # Yığılmış xəta varsa bu sətiri keç
            if row_errors:
                error_count += len(row_errors)
                batch_errors.extend(row_errors)
                continue

            excel_keys.add((brend_kod, firma.id if firma else None))

            # Bu nöqtədə tələb olunanlar var, firmada var
            existing_product = Mehsul.objects.filter(brend_kod=brend_kod, firma=firma).first()

            if existing_product:
                existing_product.adi = temiz_ad
                existing_product.kateqoriya = kateqoriya
                existing_product.avtomobil = avtomobil
                existing_product.vitrin = vitrin
                existing_product.olcu = str(row['olcu']).strip() if 'olcu' in row and pd.notna(row['olcu']) else ''
                existing_product.maya_qiymet = maya_qiymet_parsed or 0
                existing_product.qiymet = qiymet_parsed or 0
                existing_product.stok = stok_parsed or 0
                existing_product.kodlar = str(row['kodlar']) if 'kodlar' in row and pd.notna(row['kodlar']) else ''
                existing_product.melumat = str(row['melumat']) if 'melumat' in row and pd.notna(row['melumat']) else ''
                existing_product.save()
                update_count += 1
            else:
                mehsul_data = {
                    'adi': temiz_ad,
                    'kateqoriya': kateqoriya,
                    'firma': firma,
                    'avtomobil': avtomobil,
                    'vitrin': vitrin,
                    'brend_kod': brend_kod,
                    'oem': '',
                    'olcu': str(row['olcu']).strip() if 'olcu' in row and pd.notna(row['olcu']) else '',
                    'maya_qiymet': maya_qiymet_parsed or 0,
                    'qiymet': qiymet_parsed or 0,
                    'stok': stok_parsed or 0,
                    'kodlar': str(row['kodlar']) if 'kodlar' in row and pd.notna(row['kodlar']) else '',
                    'melumat': str(row['melumat']) if 'melumat' in row and pd.notna(row['melumat']) else '',
                    'yenidir': False
                }
                Mehsul.objects.create(**mehsul_data)
                new_count += 1
        except Exception as e:
            error_count += 1
            full_row = {str(k): ('' if (k not in row or pd.isna(row.get(k))) else str(row.get(k))) for k in row.keys()}
            batch_errors.append({
                'line': excel_line_no,
                'message': str(e),
                'field': None,
                'row': full_row,
            })
            continue

    # State-i yenilə
    state['new_count'] = new_count
    state['update_count'] = update_count
    state['error_count'] = error_count
    state['processed_rows'] = min(state['total_rows'], start + len(subset))
    state['excel_product_keys'] = list(excel_keys)
    # Toplam error detallarını yığ
    if batch_errors:
        error_details.extend(batch_errors)
        state['error_details'] = error_details
    with open(job_state_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False)

    return JsonResponse({
        'status': 'ok',
        'processed_rows': state['processed_rows'],
        'total_rows': state['total_rows'],
        'new_count': new_count,
        'update_count': update_count,
        'error_count': error_count,
        'errors': batch_errors,
        'columns': state.get('columns_display') or [],
    })


def handle_import_excel_finalize(request):
    """Excel-də olmayan məhsulları silir və job fayllarını təmizləyir"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Yalnız POST.'}, status=405)

    job_id = request.POST.get('job_id')
    imports_dir = os.path.join(settings.MEDIA_ROOT, 'imports')
    job_state_path = os.path.join(imports_dir, 'jobs', f'{job_id}.json')
    if not os.path.exists(job_state_path):
        return JsonResponse({'status': 'error', 'message': 'Job tapılmadı.'}, status=404)

    with open(job_state_path, 'r', encoding='utf-8') as f:
        state = json.load(f)

    excel_keys = set(tuple(k) for k in state.get('excel_product_keys', []))
    deleted_count = 0
    if excel_keys:
        all_products = Mehsul.objects.all()
        to_delete_ids = []
        for p in all_products:
            product_key = (p.brend_kod, p.firma_id)
            if product_key not in excel_keys:
                to_delete_ids.append(p.id)
    if to_delete_ids:
        # Report number of Mehsul records (not cascaded related deletions)
        deleted_count = Mehsul.objects.filter(id__in=to_delete_ids).count()
        Mehsul.objects.filter(id__in=to_delete_ids).delete()

    # Faylları təmizlə
    try:
        if os.path.exists(state.get('file_path', '')):
            os.remove(state['file_path'])
    except Exception:
        pass
    try:
        os.remove(job_state_path)
    except Exception:
        pass

    return JsonResponse({
        'status': 'ok',
        'deleted_count': deleted_count,
        'total_errors': len(state.get('error_details', [])),
        'error_details': state.get('error_details', []),
        'columns': state.get('columns_display') or []
    })
