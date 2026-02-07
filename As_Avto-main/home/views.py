from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Mehsul, Kateqoriya, Sifaris, SifarisItem, Firma, Avtomobil, PopupImage, Header_Message
from django.db.models import Q
from decimal import Decimal
from django.contrib import messages
import re
from django.http import JsonResponse, HttpResponseNotFound
from django.db.models.functions import Lower
from django.db.models import Value
from functools import reduce
from operator import and_, or_
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.views.decorators.http import require_http_methods

def custom_404(request, exception=None):
    return HttpResponseNotFound(render(request, '404.html').content)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('base')
    error_message = None
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Profil təsdiqlənmə yoxlaması
            if not user.profile.is_verified:
                error_message = 'Giriş üçün icazəniz yoxdur !'
                return render(request, 'login.html', {'error_message': error_message})
            
            login(request, user)
            return redirect('base')
        else:
            error_message = 'İstifadəçi adı və ya şifrə yanlışdır'
    return render(request, 'login.html', {'error_message': error_message})

@login_required
def home_view(request):
    # Yeni məhsulları əldə et
    new_products = Mehsul.objects.filter(yenidir=True)
    # Aktiv popup şəkilləri əldə et
    popup_images = PopupImage.objects.filter(aktiv=True)
    return render(request, 'base.html', {
        'new_products': new_products,
        'popup_images': popup_images
    })

@login_required
def products_view(request):
    search_query = request.GET.get('search', '')
    kateqoriya = request.GET.get('kateqoriya', '')
    firma = request.GET.get('firma', '')
    avtomobil = request.GET.get('avtomobil', '')
    
    mehsullar = Mehsul.objects.all()
    popup_images = PopupImage.objects.filter(aktiv=True)
    
    # Use the centralized search function
    mehsullar = get_search_filtered_products(mehsullar, search_query)
    
    if kateqoriya:
        mehsullar = mehsullar.filter(kateqoriya__adi=kateqoriya)
        
    if firma:
        mehsullar = mehsullar.filter(firma__adi=firma)
        
    if avtomobil:
        mehsullar = mehsullar.filter(avtomobil__adi=avtomobil)
    
    # İlk 5 məhsulu götür
    initial_products = mehsullar[:5]
    has_more = mehsullar.count() > 5
    
    kateqoriyalar = Kateqoriya.objects.all()
    firmalar = Firma.objects.all()
    avtomobiller = Avtomobil.objects.all()
    
    return render(request, 'products.html', {
        'mehsullar': initial_products,
        'has_more': has_more,
        'kateqoriyalar': kateqoriyalar,
        'firmalar': firmalar,
        'avtomobiller': avtomobiller,
        'search_query': search_query,
        'selected_kateqoriya': kateqoriya,
        'selected_firma': firma,
        'selected_avtomobil': avtomobil,
        'popup_images': popup_images
    })

@login_required
def load_more_products(request):
    offset = int(request.GET.get('offset', 0))
    limit = 5
    search_query = request.GET.get('search', '')
    kateqoriya = request.GET.get('kateqoriya', '')
    firma = request.GET.get('firma', '')
    avtomobil = request.GET.get('avtomobil', '')
    
    mehsullar = Mehsul.objects.all()
    
    # Use the centralized search function
    mehsullar = get_search_filtered_products(mehsullar, search_query)
    
    if kateqoriya:
        mehsullar = mehsullar.filter(kateqoriya__adi=kateqoriya)
        
    if firma:
        mehsullar = mehsullar.filter(firma__adi=firma)
        
    if avtomobil:
        mehsullar = mehsullar.filter(avtomobil__adi=avtomobil)
    
    # Get next batch of products
    products = mehsullar[offset:offset + limit]
    has_more = mehsullar.count() > (offset + limit)
    
    products_data = []
    for product in products:
        products_data.append({
            'id': product.id,
            'adi': product.adi,
            'sekil_url': product.sekil.url if product.sekil else None,
            'firma': product.firma.adi,
            'brend_kod': product.brend_kod,
            'oem': product.oem,
            'stok': product.stok,
            'qiymet': str(product.qiymet),
            'yenidir': product.yenidir,
        })
    
    return JsonResponse({
        'products': products_data,
        'has_more': has_more
    })

@login_required
def cart_view(request):
    if 'cart' not in request.session:
        request.session['cart'] = {}
    
    cart = request.session['cart']
    cart_items = []
    total = Decimal('0.00')
    popup_images = PopupImage.objects.filter(aktiv=True)
    invalid_products = []  # Mövcud olmayan məhsulları izləmək üçün
    
    for product_id, quantity in cart.items():
        try:
            product = Mehsul.objects.get(id=product_id)
            subtotal = product.qiymet * Decimal(str(quantity))
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal
            })
            total += subtotal
        except Mehsul.DoesNotExist:
            invalid_products.append(product_id)  # Mövcud olmayan məhsulu qeyd et
    
    # Mövcud olmayan məhsulları səbətdən sil
    if invalid_products:
        for product_id in invalid_products:
            if str(product_id) in cart:
                del cart[str(product_id)]
        request.session.modified = True
        messages.warning(request, 'Bəzi məhsullar artıq mövcud olmadığı üçün səbətdən silindi.')
    
    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total': total,
        'popup_images': popup_images
    })

@login_required
def add_to_cart(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Mehsul, id=product_id)
        quantity = int(request.POST.get('quantity', 1))
        
        response_data = {
            'status': 'error',
            'message': ''
        }
        
        if quantity > product.stok:
            response_data['message'] = f'{product.adi} məhsulundan stokda yalnız {product.stok} ədəd var!'
            return JsonResponse(response_data)
        
        if 'cart' not in request.session:
            request.session['cart'] = {}
        
        cart = request.session['cart']
        current_quantity = cart.get(str(product_id), 0)
        new_quantity = current_quantity + quantity
        
        if new_quantity > product.stok:
            response_data['message'] = f'{product.adi} məhsulundan stokda yalnız {product.stok} ədəd var!'
            return JsonResponse(response_data)
        
        cart[str(product_id)] = new_quantity
        request.session['cart'] = cart
        request.session.modified = True
        
        response_data.update({
            'status': 'success',
            'message': f'{product.adi} məhsulundan {quantity} ədəd səbətə əlavə edildi!',
            'cart_count': len(cart)
        })
        
        return JsonResponse(response_data)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def remove_from_cart(request, product_id):
    if request.method == 'POST':
        if 'cart' in request.session:
            cart = request.session['cart']
            if str(product_id) in cart:
                del cart[str(product_id)]
                request.session.modified = True
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Məhsul səbətdən silindi!',
                    'cart_count': len(cart)
                })
    
        return JsonResponse({
            'status': 'error',
            'message': 'Məhsul tapılmadı!'
        })
        
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })

@login_required
def orders_view(request):
    orders = Sifaris.objects.filter(istifadeci=request.user).order_by('-tarix')
    statistics = Sifaris.get_order_statistics(request.user)
    popup_images = PopupImage.objects.filter(aktiv=True)

    # Show first 5 orders by default
    initial_limit = 5
    initial_orders = orders[:initial_limit]
    has_more = orders.count() > initial_limit

    return render(request, 'orders.html', {
        'orders': initial_orders,
        'statistics': statistics,
        'popup_images': popup_images,
        'has_more': has_more
    })


@login_required
def load_more_orders(request):
    try:
        offset = int(request.GET.get('offset', 0))
    except ValueError:
        offset = 0

    limit = 5
    orders_qs = Sifaris.objects.filter(istifadeci=request.user).order_by('-tarix')
    orders = orders_qs[offset:offset + limit]
    has_more = orders_qs.count() > (offset + limit)

    orders_data = []
    for order in orders:
        orders_data.append({
            'id': order.id,
            'tarix': order.tarix.strftime('%d.%m.%Y %H:%M') if order.tarix else '',
            'status': order.get_status_display(),
            'status_code': order.status,
            'catdirilma_usulu': order.get_catdirilma_usulu_display(),
            'umumi_mebleg': str(order.umumi_mebleg),
            'odenilen_mebleg': str(getattr(order, 'odenilen_mebleg', 0)),
            'qaliq_borc': str(getattr(order, 'qaliq_borc', 0)),
        })

    return JsonResponse({
        'orders': orders_data,
        'has_more': has_more
    })

@login_required
def checkout(request):
    if request.method == 'POST':
        if 'cart' not in request.session or not request.session['cart']:
            messages.error(request, 'Səbətiniz boşdur.')
            return redirect('cart')

        # Seçilmiş məhsulları al
        selected_items = request.POST.getlist('selected_items[]')
        catdirilma_usulu = request.POST.get('catdirilma_usulu')
        qeyd = request.POST.get('qeyd', '').strip()  # Get note from form
        
        if not selected_items:
            messages.error(request, 'Zəhmət olmasa ən azı bir məhsul seçin.')
            return redirect('cart')
            
        if not catdirilma_usulu:
            messages.error(request, 'Zəhmət olmasa çatdırılma üsulunu seçin.')
            return redirect('cart')

        cart = request.session['cart']
        total = Decimal('0.00')
        order_items = []
        remaining_cart = {}  # Seçilməmiş məhsullar üçün

        # Məhsulları və ümumi məbləği hesablayırıq
        for product_id, quantity in cart.items():
            if product_id in selected_items:
                product = get_object_or_404(Mehsul, id=product_id)
                if product.stok < quantity:
                    messages.error(request, f'{product.adi} məhsulundan kifayət qədər stok yoxdur.')
                    return redirect('cart')
                
                subtotal = product.qiymet * Decimal(str(quantity))
                total += subtotal
                order_items.append({
                    'product': product,
                    'quantity': quantity,
                    'price': product.qiymet
                })
            else:
                # Seçilməmiş məhsulları yeni səbətə əlavə et
                remaining_cart[product_id] = quantity

        try:
            # Sifariş yaradırıq (qeydi də əlavə edirik)
            order = Sifaris.objects.create(
                istifadeci=request.user,
                umumi_mebleg=total,
                catdirilma_usulu=catdirilma_usulu,
                qeyd=qeyd if qeyd else None  # Add note if provided
            )

            # Sifariş elementlərini yaradırıq
            for item in order_items:
                SifarisItem.objects.create(
                    sifaris=order,
                    mehsul=item['product'],
                    miqdar=item['quantity'],
                    qiymet=item['price']
                )

            # Səbəti yeniləyirik (yalnız seçilməmiş məhsulları saxlayırıq)
            request.session['cart'] = remaining_cart
            request.session.modified = True
            
            messages.success(request, 'Sifarişiniz uğurla yaradıldı.')
            return redirect('orders')
            
        except Exception as e:
            if 'order' in locals():
                order.delete()
            messages.error(request, 'Sifariş yaradılarkən xəta baş verdi. Zəhmət olmasa yenidən cəhd edin.')
            return redirect('cart')

    return redirect('cart')

@login_required
def update_cart(request, product_id):
    if request.method == 'POST':
        try:
            product = get_object_or_404(Mehsul, id=product_id)
            quantity = int(request.POST.get('quantity', 1))
            
            response_data = {
                'status': 'error',
                'message': ''
            }
            
            if quantity > product.stok:
                response_data['message'] = f'{product.adi} məhsulundan stokda yalnız {product.stok} ədəd var!'
                return JsonResponse(response_data)
            
            if quantity < 1:
                response_data['message'] = 'Miqdar 1-dən az ola bilməz!'
                return JsonResponse(response_data)
            
            cart = request.session.get('cart', {})
            cart[str(product_id)] = quantity
            request.session['cart'] = cart
            request.session.modified = True
            
            # Calculate new subtotal and cart total
            subtotal = product.qiymet * quantity
            cart_total = sum(
                Mehsul.objects.get(id=int(pid)).qiymet * qty
                for pid, qty in cart.items()
            )
            
            response_data.update({
                'status': 'success',
                'message': f'{product.adi} məhsulunun miqdarı yeniləndi!',
                'subtotal': f'{subtotal} ₼',
                'cart_total': f'{cart_total} ₼'
            })
            
            return JsonResponse(response_data)
            
        except ValueError:
            return JsonResponse({
                'status': 'error',
                'message': 'Yanlış miqdar daxil edildi!'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': 'Xəta baş verdi. Zəhmət olmasa yenidən cəhd edin.'
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })

@login_required
def order_detail_view(request, order_id):
    if not request.user.is_authenticated:
        return redirect('login')
    
    order = get_object_or_404(Sifaris, id=order_id, istifadeci=request.user)
    popup_images = PopupImage.objects.filter(aktiv=True)
    
    return render(request, 'order_detail.html', {
        'order': order,
        'popup_images': popup_images
    })

@login_required
def search_suggestions(request):
    search_query = request.GET.get('search', '')
    
    if search_query:
        mehsullar = Mehsul.objects.all()
        # Use the centralized search function
        mehsullar = get_search_filtered_products(mehsullar, search_query)
        
        # Check if there are more than 5 results
        total_count = mehsullar.count()
        has_more = total_count > 5
        
        # Limit to 5 suggestions
        mehsullar = mehsullar[:5]
        
        suggestions = []
        for mehsul in mehsullar:
            suggestions.append({
                'id': mehsul.id,
                'adi': mehsul.adi,
                'brend_kod': mehsul.brend_kod,
                'oem': mehsul.oem,
                'olcu': mehsul.olcu,
                'qiymet': str(mehsul.qiymet),
                'sekil_url': mehsul.sekil.url if mehsul.sekil else None,
            })
        return JsonResponse({'suggestions': suggestions, 'has_more': has_more, 'search_query': search_query})
    
    return JsonResponse({'suggestions': [], 'has_more': False})

@login_required
def new_products_view(request):
    # Yeni məhsulları əldə et
    mehsullar = Mehsul.objects.filter(yenidir=True).order_by('-id')  # Ən son əlavə edilən yeni məhsullardan başla
    
    # İlk 5 məhsulu götür
    initial_products = mehsullar[:5]
    has_more = mehsullar.count() > 5
    
    kateqoriyalar = Kateqoriya.objects.all()
    firmalar = Firma.objects.all()
    avtomobiller = Avtomobil.objects.all()
    popup_images = PopupImage.objects.filter(aktiv=True)
    
    return render(request, 'new_products.html', {
        'mehsullar': initial_products,
        'has_more': has_more,
        'kateqoriyalar': kateqoriyalar,
        'firmalar': firmalar,
        'avtomobiller': avtomobiller,
        'popup_images': popup_images
    })

@login_required
def load_more_new_products(request):
    offset = int(request.GET.get('offset', 0))
    limit = 5
    
    mehsullar = Mehsul.objects.filter(yenidir=True).order_by('-id')
    
    # Get next batch of products
    products = mehsullar[offset:offset + limit]
    has_more = mehsullar.count() > (offset + limit)
    
    products_data = []
    for product in products:
        products_data.append({
            'id': product.id,
            'adi': product.adi,
            'sekil_url': product.sekil.url if product.sekil else None,
            'firma': product.firma.adi,
            'brend_kod': product.brend_kod,
            'oem': product.oem,
            'stok': product.stok,
            'qiymet': str(product.qiymet),
            'yenidir': product.yenidir,
        })
    
    return JsonResponse({
        'products': products_data,
        'has_more': has_more
    })

@login_required
def logout_view(request):
    logout(request)
    # Sessiya və keşi təmizləyirik
    request.session.flush()
    
    # İstifadəçini login səhifəsinə yönləndiririk
    return redirect('login')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('base')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        
        # Username validasiyası
        if not username:
            messages.error(request, 'İstifadəçi adı boş ola bilməz!')
            return render(request, 'register.html')
            
        # Username formatı yoxlaması
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            messages.error(request, 'İstifadəçi adı yalnız ingilis hərfləri, rəqəmlər və _ simvolundan ibarət ola bilər!')
            return render(request, 'register.html')
            
        # Şifrə validasiyası
        if len(password) < 8:
            messages.error(request, 'Şifrə minimum 8 simvol olmalıdır!')
            return render(request, 'register.html')
            
        # Telefon nömrəsi validasiyası
        if not phone.startswith('+994'):
            messages.error(request, 'Telefon nömrəsi +994 ilə başlamalıdır!')
            return render(request, 'register.html')
            
        # Unvan validasiyası
        if not address:
            messages.error(request, 'Ünvan boş ola bilməz!')
            return render(request, 'register.html')
            
        # Username mövcudluğu yoxlaması
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Bu istifadəçi adı artıq mövcuddur!')
            return render(request, 'register.html')
            
        # Telefon nömrəsi mövcudluğu yoxlaması
        if User.objects.filter(profile__phone=phone).exists():
            messages.error(request, 'Bu telefon nömrəsi artıq qeydiyyatdan keçirilib!')
            return render(request, 'register.html')
            
        try:
            # Yeni istifadəçi yaradırıq
            user = User.objects.create_user(username=username, password=password)
            
            # Profil məlumatlarını əlavə edirik
            user.profile.phone = phone
            user.profile.address = address
            user.profile.is_verified = False  # Profil təsdiqlənməmiş olaraq yaradılır
            user.profile.save()
            
            messages.success(request, 'Qeydiyyat uğurla tamamlandı!')
            return redirect('register')
            
        except Exception as e:
            messages.error(request, 'Qeydiyyat zamanı xəta baş verdi. Zəhmət olmasa yenidən cəhd edin.')
            return render(request, 'register.html')
            
    return render(request, 'register.html')

@require_http_methods(["GET"])
def product_details(request, product_id):
    try:
        product = Mehsul.objects.get(id=product_id)
        data = {
            'status': 'success',
            'product': {
                'id': product.id,
                'adi': product.adi,
                'kateqoriya': product.kateqoriya.adi if product.kateqoriya else None,
                'firma': product.firma.adi,
                'avtomobil': product.avtomobil.adi,
                'brend_kod': product.brend_kod,
                'olcu': product.olcu,
                'qiymet': str(product.qiymet),
                'stok': product.stok,
                'melumat': product.melumat,
                'sekil_url': product.sekil.url if product.sekil else None,
            }
        }
    except Mehsul.DoesNotExist:
        data = {
            'status': 'error',
            'message': 'Məhsul tapılmadı.'
        }
    except Exception as e:
        data = {
            'status': 'error',
            'message': 'Xəta baş verdi. Zəhmət olmasa yenidən cəhd edin.'
        }
    
    return JsonResponse(data)


def get_search_filtered_products(queryset, search_query):
    import re
    from functools import reduce
    from operator import and_, or_
    from django.db.models import Q, Value, CharField
    from django.db.models.functions import Concat, Lower, Replace

    if not search_query:
        return queryset.order_by('-id')

    # 🔹 axtarış üçün birləşdirilmiş mətn (adi + melumat)
    queryset = queryset.annotate(
        search_text=Concat(
            'adi', Value(' '),
            'melumat',
            output_field=CharField()
        )
    )

    # 🔹 boşluqları normallaşdır
    processed_query = re.sub(r'\s+', ' ', search_query).strip()
    search_words = processed_query.split()

    # 🔹 yalnız hərf + rəqəm (brend_kod üçün)
    clean_search = re.sub(r'[^a-zA-Z0-9]', '', search_query.lower())

    # 🔹 AZ hərf variasiyaları (məntiq saxlanılır)
    def normalize_azerbaijani_chars(text):
        char_map = {
            'ə': 'e', 'e': 'ə',
            'ö': 'o', 'o': 'ö',
            'ğ': 'g', 'g': 'ğ',
            'ı': 'i', 'i': 'ı',
            'ü': 'u', 'u': 'ü',
            'ş': 's', 's': 'ş',
            'ç': 'c', 'c': 'ç',
        }

        variations = {text.lower()}
        for char, repl in char_map.items():
            new_vars = set()
            for v in variations:
                if char in v:
                    new_vars.add(v.replace(char, repl))
            variations.update(new_vars)

        return variations

    filters = []

    # 🔥 BRƏND KOD – PYTHON LOOP YOX, DB LEVEL
    if clean_search:
        queryset = queryset.annotate(
            brend_kod_clean=Replace(
                Replace(
                    Replace(
                        Lower('brend_kod'),
                        Value(' '), Value('')
                    ),
                    Value('-'), Value('')
                ),
                Value('_'), Value('')
            )
        )

        filters.append(Q(brend_kod_clean__icontains=clean_search))
        filters.append(Q(kodlar__icontains=clean_search))
        filters.append(Q(olcu__icontains=clean_search))
        filters.append(Q(melumat__icontains=clean_search))

    # 🔥 WORD-BASED SEARCH (AND logic saxlanılır)
    if search_words:
        word_filters = []

        for word in search_words:
            variations = normalize_azerbaijani_chars(word)

            word_q = reduce(or_, [
                Q(adi__icontains=v) |
                Q(melumat__icontains=v) |
                Q(avtomobil__adi__icontains=v) |
                Q(firma__adi__icontains=v) |
                Q(olcu__icontains=v) |
                Q(search_text__icontains=v)
                for v in variations
            ])

            word_filters.append(word_q)

        filters.append(reduce(and_, word_filters))

    if filters:
        queryset = queryset.filter(reduce(or_, filters))

    return queryset.order_by('-id')


@require_http_methods(["GET"])
def download_sifaris_pdf(request, sifaris_id):
    """Sifaris PDF-sini AJAX ilə yükləmə"""
    from .export_pdf import generate_sifaris_pdf
    try:
        return generate_sifaris_pdf(sifaris_id)
    except Sifaris.DoesNotExist:
        return JsonResponse({'error': 'Sifaris tapılmadı'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def download_products_pdf(request):
    """Bütün məhsulların PDF-sini AJAX ilə yükləmə"""
    from .export_pdf import generate_products_pdf
    try:
        return generate_products_pdf()
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)