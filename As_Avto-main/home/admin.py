from django.contrib import admin
from .models import Kateqoriya, Firma, Avtomobil, Mehsul, Sifaris, SifarisItem, Vitrin, PopupImage, Profile, Header_Message
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import path
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
import os
from .export_pdf import generate_products_pdf, generate_sifaris_pdf
from .import_excel import (
    handle_import_excel_view, 
    handle_import_excel_init, 
    handle_import_excel_batch, 
    handle_import_excel_finalize
)

@admin.register(Header_Message)
class Header_MessageAdmin(admin.ModelAdmin):
    list_display = ['mesaj']
    search_fields = ['mesaj']

@admin.register(Kateqoriya)
class KateqoriyaAdmin(admin.ModelAdmin):
    list_display = ['adi']
    search_fields = ['adi']

@admin.register(Vitrin)
class VitrinAdmin(admin.ModelAdmin):
    list_display = ['nomre']
    search_fields = ['nomre']

@admin.register(Firma)
class FirmaAdmin(admin.ModelAdmin):
    list_display = ['adi']
    search_fields = ['adi']

@admin.register(Avtomobil)
class AvtomobilAdmin(admin.ModelAdmin):
    list_display = ['adi']
    search_fields = ['adi']

@admin.register(Mehsul)
class MehsulAdmin(admin.ModelAdmin):
    list_display = ['brend_kod', 'firma', 'adi',  'olcu', 'vitrin', 'stok', 'maya_qiymet', 'qiymet',  'yenidir', 'sekil_preview', 'change_image_button']
    list_filter = ['kateqoriya', 'firma', 'avtomobil', 'vitrin', 'yenidir']
    search_fields = ['adi', 'brend_kod', 'oem', 'kodlar', 'olcu']
    change_list_template = 'admin/mehsul_change_list.html'
    actions = ['mark_as_new', 'remove_from_new']

    def sekil_preview(self, obj):
        if obj.sekil:
            return format_html('<img src="{}" id="product-image-{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;"/>', obj.sekil.url, obj.id)
        return '-'
    sekil_preview.short_description = 'Şəkil'

    def change_image_button(self, obj):
        if obj.sekil:
            return format_html(
                '<button type="button" class="change-image-btn" data-product-id="{}">Şəkil Dəyiş</button>',
                obj.id
            )
        else:
            return format_html(
                '<button type="button" class="change-image-btn" data-product-id="{}">Şəkil Əlavə Et</button>',
                obj.id
            )
    change_image_button.short_description = 'Şəkil Əməliyyatı'
    change_image_button.allow_tags = True

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-excel/', self.import_excel_view, name='import_excel'),
            path('export-pdf/', self.export_pdf, name='export_pdf'),
            path('import-excel-init/', self.import_excel_init, name='import_excel_init'),
            path('import-excel-batch/', self.import_excel_batch, name='import_excel_batch'),
            path('import-excel-finalize/', self.import_excel_finalize, name='import_excel_finalize'),
            path('change-image/', self.change_image, name='change_image'),
        ]
        return custom_urls + urls

    def export_pdf(self, request):
        """Bütün məhsulların PDF-sini yükləmə"""
        return generate_products_pdf()

    def mark_as_new(self, request, queryset):
        updated = queryset.update(yenidir=True)
        self.message_user(request, f'{updated} məhsul yeni olaraq işarələndi.')
    mark_as_new.short_description = "Seçilmiş məhsulları yeni olaraq işarələ"

    def remove_from_new(self, request, queryset):
        updated = queryset.update(yenidir=False)
        self.message_user(request, f'{updated} məhsul yenilikdən silindi.')
    remove_from_new.short_description = "Seçilmiş məhsulları yenilikdən sil"

    def import_excel_view(self, request):
        """Excel faylı import etmə məsələsi"""
        return handle_import_excel_view(request, self)

    def import_excel_init(self, request):
        """Excel faylını qəbul edir, sətirləri təmizləyib job faylına yazır"""
        return handle_import_excel_init(request)

    def import_excel_batch(self, request):
        """Verilən interval üzrə sətirləri emal edir"""
        return handle_import_excel_batch(request)

    def import_excel_finalize(self, request):
        """Excel-də olmayan məhsulları silir"""
        return handle_import_excel_finalize(request)

    def changelist_view(self, request, extra_context=None):
        # Statistikanı hesablayırıq
        from django.db.models import Sum, F, ExpressionWrapper, DecimalField
        
        total_stats = Mehsul.objects.aggregate(
            toplam_maya = Sum(ExpressionWrapper(
                F('stok') * F('maya_qiymet'),
                output_field=DecimalField()
            )),
            toplam_satis = Sum(ExpressionWrapper(
                F('stok') * F('qiymet'),
                output_field=DecimalField()
            ))
        )
        
        # Ümumi xeyiri hesablayırıq
        total_stats['toplam_xeyir'] = (total_stats['toplam_satis'] or 0) - (total_stats['toplam_maya'] or 0)

        extra_context = extra_context or {}
        extra_context['total_stats'] = total_stats
        
        return super().changelist_view(request, extra_context=extra_context)

    def change_image(self, request):
        if request.method == 'POST':
            try:
                product_id = request.POST.get('product_id')
                image_file = request.FILES.get('image')
                
                if not product_id or not image_file:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Məhsul ID və ya şəkil faylı tapılmadı.'
                    })
                
                # Validate image file
                if not image_file.content_type.startswith('image/'):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Yalnız şəkil faylları qəbul edilir.'
                    })
                
                # Get product and update image
                product = Mehsul.objects.get(id=product_id)
                
                # Delete old image if exists (but don't delete no_image.webp)
                if product.sekil:
                    old_image_path = product.sekil.path
                    old_image_name = os.path.basename(old_image_path)
                    if os.path.exists(old_image_path) and old_image_name != 'no_image.webp':
                        try:
                            os.remove(old_image_path)
                        except OSError:
                            pass  # Ignore file deletion errors
                
                # Save new image
                product.sekil = image_file
                product.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Şəkil uğurla yeniləndi!',
                    'new_image_url': product.sekil.url,
                    'product_id': product_id
                })
                
            except Mehsul.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Məhsul tapılmadı.'
                })
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Xəta baş verdi: {str(e)}'
                })
        
        return JsonResponse({
            'status': 'error',
            'message': 'Yalnız POST metodu qəbul edilir.'
        })

class SifarisItemInline(admin.TabularInline):
    model = SifarisItem
    extra = 1
    can_delete = True
    readonly_fields = ['mehsul']
    fields = ['mehsul', 'miqdar', 'qiymet']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "mehsul":
            kwargs["queryset"] = Mehsul.objects.filter(stok__gt=0)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.sifaris.update_total()

    def delete_model(self, request, obj):
        sifaris = obj.sifaris
        super().delete_model(request, obj)
        sifaris.update_total()

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.can_delete = True
        return formset

@admin.register(Sifaris)
class SifarisAdmin(admin.ModelAdmin):
    list_display = ['id', 'istifadeci', 'tarix', 'status', 'catdirilma_usulu', 'umumi_mebleg', 'odenilen_mebleg', 'qaliq_borc', 'pdf_button']
    list_filter = ['status', 'catdirilma_usulu', 'tarix', 'istifadeci']
    search_fields = ['istifadeci__username']
    readonly_fields = ['istifadeci', 'tarix', 'umumi_mebleg', 'qaliq_borc']
    fields = ['istifadeci', 'tarix', 'status', 'catdirilma_usulu', 'umumi_mebleg', 'odenilen_mebleg', 'qaliq_borc', 'qeyd']
    inlines = [SifarisItemInline]
    change_list_template = 'admin/sifaris_change_list.html'

    def pdf_button(self, obj):
        return format_html(
            '<a class="button" href="export-pdf/{}" style="background-color: #417690; color: white; '
            'padding: 5px 10px; border-radius: 4px; text-decoration: none;">PDF</a>',
            obj.id
        )
    pdf_button.short_description = 'PDF'
    pdf_button.allow_tags = True

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-pdf/<int:sifaris_id>/', self.export_pdf, name='export-pdf'),
        ]
        return custom_urls + urls

    def export_pdf(self, request, sifaris_id):
        """Sifariş PDF-sini yükləmə"""
        return generate_sifaris_pdf(sifaris_id)

    def has_add_permission(self, request):
        return False  # Sifarişlər yalnız saytdan əlavə edilə bilər

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            instance.save()
        # Silinən elementləri emal et
        for obj in formset.deleted_objects:
            obj.delete()
        formset.save_m2m()
        form.instance.update_total()

    def changelist_view(self, request, extra_context=None):
        # İstifadəçilər üzrə statistikanı hesablayırıq
        from django.db.models import Count, Sum, F
        from django.contrib.auth.models import User
        
        user_stats = User.objects.annotate(
            sifaris_sayi=Count('sifaris'),
            umumi_mebleg=Sum('sifaris__umumi_mebleg'),
            umumi_odenilen=Sum('sifaris__odenilen_mebleg'),
            umumi_borc=Sum(F('sifaris__umumi_mebleg') - F('sifaris__odenilen_mebleg'))
        ).values('username', 'sifaris_sayi', 'umumi_mebleg', 'umumi_odenilen', 'umumi_borc')

        # Ümumi statistika
        total_stats = {
            'total_orders': sum(stat['sifaris_sayi'] for stat in user_stats),
            'total_amount': sum(stat['umumi_mebleg'] or 0 for stat in user_stats),
            'total_paid': sum(stat['umumi_odenilen'] or 0 for stat in user_stats),
            'total_debt': sum(stat['umumi_borc'] or 0 for stat in user_stats),
        }

        extra_context = extra_context or {}
        extra_context['user_statistics'] = user_stats
        extra_context['total_statistics'] = total_stats
        
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(PopupImage)
class PopupImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'basliq', 'aktiv', 'sira', 'yaradilma_tarixi', 'sekil_preview']
    list_editable = ['aktiv', 'sira']
    ordering = ['sira', '-yaradilma_tarixi']
    
    def sekil_preview(self, obj):
        if obj.sekil:
            return format_html('<img src="{}" id="popup-image-{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;"/>', obj.sekil.url, obj.id)
        return '-'
    sekil_preview.short_description = 'Şəkil'

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'address', 'is_verified', 'verification_button']
    list_filter = ['is_verified']
    search_fields = ['user__username', 'phone', 'address']
    actions = ['verify_profiles', 'unverify_profiles']

    def verification_button(self, obj):
        if obj.is_verified:
            return mark_safe('<span style="color: green;">✓ Təsdiqlənib</span>')
        return mark_safe('<span style="color: red;">✗ Təsdiqlənməyib</span>')
    verification_button.short_description = 'Status'

    def verify_profiles(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, f'{queryset.count()} profil təsdiqləndi.')
    verify_profiles.short_description = "Seçilmiş profilləri təsdiqlə"

    def unverify_profiles(self, request, queryset):
        queryset.update(is_verified=False)
        self.message_user(request, f'{queryset.count()} profilin təsdiqi ləğv edildi.')
    unverify_profiles.short_description = "Seçilmiş profillərin təsdiqini ləğv et"