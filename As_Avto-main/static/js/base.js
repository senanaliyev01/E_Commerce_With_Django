document.addEventListener('DOMContentLoaded', function() {
    // Search functionality
    initializeSearch();
    
    // Cart functionality
    initializeCart();
    
    // Modal functionality
    initializeModal();
    
    // Initialize Swiper
    initializeSwiper();

    // User dropdown functionality
    initializeUserDropdown();

    // Initialize Image Modal
    initializeImageModal();

    // Popup Modal
    initializePopupModal();

    // Add cart sidebar initialization
    initializeCartSidebar();

    // Initialize products page functionality
    initializeProductsPage();

    // Initialize Details Modal
    initializeDetailsModal();

    // Initialize Logo Slider
    initializeLogoSlider();

    // Initialize Header Messages
    initializeHeaderMessages();
    // Initialize orders "load more" if present
    initializeOrdersLoadMore();
});

// Load more orders handler (previously inline in templates/orders.html)
function initializeOrdersLoadMore() {
    const btn = document.getElementById('load-more-orders');
    if (!btn) return;

    btn.addEventListener('click', async function() {
        let offset = parseInt(btn.dataset.offset, 10) || 0;
        const url = btn.dataset.url || '/load-more-orders/';
        btn.disabled = true;
        const originalText = btn.textContent;
        btn.textContent = 'Yüklənir...';

        try {
            const resp = await fetch(url + '?offset=' + offset, { method: 'GET' });
            if (!resp.ok) throw new Error('Network error');
            const data = await resp.json();
            const tbody = document.getElementById('orders-tbody');
            data.orders.forEach(order => {
                const tr = document.createElement('tr');

                // Determine status class using status_code (falls back to display text lowercased)
                const statusClassRaw = (order.status_code || order.status || '').toString().toLowerCase();
                const safeStatusClass = statusClassRaw.replace(/[^a-z0-9\-_]/g, '-');

                tr.innerHTML = `
                    <td><a href="/orders/${order.id}/" class="order-link">#${order.id}</a></td>
                    <td>${order.tarix}</td>
                    <td><span class="status-badge status-${safeStatusClass}">${order.status}</span></td>
                    <td><span class="delivery-badge">${order.catdirilma_usulu}</span></td>
                    <td>${order.umumi_mebleg} ₼</td>
                    <td>${order.odenilen_mebleg} ₼</td>
                    <td>${order.qaliq_borc} ₼</td>
                `;

                tbody.appendChild(tr);
            });

            offset += data.orders.length;
            btn.dataset.offset = offset;

            if (data.has_more) {
                btn.disabled = false;
                btn.textContent = originalText || 'Daha çox göstər';
            } else {
                btn.textContent = 'Hamısı göstərildi';
                btn.disabled = true;
            }
        } catch (e) {
            console.error(e);
            btn.disabled = false;
            btn.textContent = 'Xəta, yenidən cəhd et';
        }
    });
}

function initializeSearch() {
    const searchInput = document.getElementById('query');
    const searchResults = document.getElementById('search-results');
    let searchTimeout;

    if (searchInput && searchResults) {
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length > 0) {
                searchTimeout = setTimeout(() => {
                    fetch(`/search-suggestions/?search=${encodeURIComponent(query)}`)
                        .then(response => response.json())
                        .then(data => {
                            searchResults.innerHTML = '';
                            if (data.suggestions.length > 0) {
                                data.suggestions.forEach(item => {
                                    const div = document.createElement('div');
                                    div.className = 'search-result-item';
                                    div.innerHTML = `
                                        <img src="${item.sekil_url || '/static/images/no_image.jpg'}" alt="${item.adi}" class="search-result-image">
                                        <div class="search-result-info">
                                            <div class="search-result-title">${item.adi}</div>
                                            <div class="search-result-details">
                                                Brend Kodu: ${item.brend_kod}<br>
                                                OEM: ${item.oem}<br>
                                                ${item.olcu ? `Ölçü: ${item.olcu}` : ''}
                                            </div>
                                        </div>
                                        <div class="search-result-price">${item.qiymet} ₼</div>
                                    `;
                                    div.addEventListener('click', () => {
                                        searchInput.value = item.brend_kod;
                                        searchResults.style.display = 'none';
                                        document.querySelector('form.search-form').submit();
                                    });
                                    searchResults.appendChild(div);
                                });
                                
                                // Show "Daha Çox Göstər" button if there are more results
                                if (data.has_more) {
                                    const showMoreBtn = document.createElement('div');
                                    showMoreBtn.className = 'search-show-more';
                                    showMoreBtn.innerHTML = `<a href="/products/?search=${encodeURIComponent(data.search_query)}">Daha Çox Göstər</a>`;
                                    showMoreBtn.addEventListener('click', () => {
                                        window.location.href = `/products/?search=${encodeURIComponent(data.search_query)}`;
                                    });
                                    searchResults.appendChild(showMoreBtn);
                                }
                                
                                searchResults.style.display = 'block';
                            } else {
                                searchResults.style.display = 'none';
                            }
                        });
                }, 300);
            } else {
                searchResults.style.display = 'none';
            }
        });

        // Close search results when clicking outside
        document.addEventListener('click', function(e) {
            if (!searchResults.contains(e.target) && e.target !== searchInput) {
                searchResults.style.display = 'none';
            }
        });
    }
}

function initializeCart() {
    const cartContainer = document.querySelector('.cart-container');
    if (!cartContainer) return;
    
    const selectAll = cartContainer.querySelector('#select-all');
    const checkboxes = cartContainer.querySelectorAll('.item-checkbox');
    const selectedTotal = cartContainer.querySelector('#selected-total');
    const checkoutButton = cartContainer.querySelector('#checkout-button');
    const updateForms = cartContainer.querySelectorAll('.update-form');

    // Add event listener for update forms
    if (updateForms) {
        updateForms.forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                const formData = new FormData(this);
                const productId = this.closest('tr').dataset.productId;
                
                fetch(`/cart/update/${productId}/`, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        // Update subtotal for this item
                        const row = this.closest('tr');
                        const subtotalCell = row.querySelector('.subtotal');
                        if (subtotalCell) {
                            subtotalCell.textContent = data.subtotal;
                        }
                        
                        // Update cart total
                        const cartTotal = document.getElementById('cart-total');
                        if (cartTotal && data.cart_total) {
                            cartTotal.textContent = data.cart_total;
                        }

                        // Update selected total if the item is checked
                        const checkbox = row.querySelector('.item-checkbox');
                        if (checkbox && checkbox.checked) {
                            updateSelectedTotal();
                        }
                        
                        // Show success message
                        showMessage('success', data.message);
                    } else {
                        showMessage('error', data.message);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showMessage('error', 'Xəta baş verdi. Zəhmət olmasa yenidən cəhd edin.');
                });
            });
        });
    }

    if (selectAll && checkboxes.length > 0 && selectedTotal && checkoutButton) {
        function updateSelectedTotal() {
            let total = 0;
            checkboxes.forEach(checkbox => {
                if (checkbox.checked) {
                    const row = checkbox.closest('tr');
                    const subtotalText = row.querySelector('.subtotal').textContent;
                    // Remove currency symbol and convert to number
                    const subtotal = parseFloat(subtotalText.replace(' ₼', '').replace(',', '.'));
                    if (!isNaN(subtotal)) {
                        total += subtotal;
                    }
                    row.classList.add('selected');
                } else {
                    checkbox.closest('tr').classList.remove('selected');
                }
            });
            
            // Format total with 2 decimal places and proper currency symbol
            selectedTotal.textContent = total.toFixed(2).replace('.', ',') + ' ₼';
            
            const hasSelectedItems = Array.from(checkboxes).some(checkbox => checkbox.checked);
            checkoutButton.disabled = !hasSelectedItems;
        }

        selectAll.addEventListener('change', function() {
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateSelectedTotal();
        });

        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const allChecked = Array.from(checkboxes).every(cb => cb.checked);
                selectAll.checked = allChecked;
                updateSelectedTotal();
            });
        });
    }
}

function initializeModal() {
    const modal = document.getElementById('quantityModal');
    const closeBtn = document.querySelector('.close');
    const form = document.getElementById('addToCartForm');
    
    if (modal && closeBtn && form) {
        closeBtn.onclick = () => modal.style.display = 'none';
        
        window.onclick = function(event) {
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        }

        // Handle form submission
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const url = this.action;
            
            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Show success message
                    showMessage('success', data.message);
                    // Update cart counter
                    if (data.cart_count !== undefined) {
                        updateCartCounter(data.cart_count);
                    }
                    // Close modal
                    modal.style.display = 'none';
                } else {
                    // Show error message
                    showMessage('error', data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showMessage('error', 'Xəta baş verdi. Zəhmət olmasa yenidən cəhd edin.');
            });
        });
    }
}

// Function to remove item from cart
function removeFromCart(productId) {
    fetch(`/cart/remove/${productId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Show success message
            showMessage('success', data.message);
            
            // Remove the row from the table
            const row = document.querySelector(`tr[data-product-id="${productId}"]`);
            if (row) {
                row.remove();
            }
            
            // Update cart counter
            if (data.cart_count !== undefined) {
                updateCartCounter(data.cart_count);
            }
            
            // Check if cart is empty
            const cartItems = document.querySelectorAll('.cart-item');
            if (cartItems.length === 0) {
                // Handle empty cart in both main page and sidebar
                const cartContainer = document.querySelector('.cart-container');
                const cartHeader = document.querySelector('.cart-header');
                const sidebarContent = document.querySelector('.cart-sidebar-content');
                
                // Create empty cart message
                const emptyCartHTML = `
                    <div class="empty-cart" style="margin: 20px;">
                        <i class="fas fa-shopping-cart"></i>
                        <p>Səbətiniz boşdur.</p>
                        <a href="/products/" class="btn btn-primary">Məhsullara bax</a>
                    </div>
                `;
                
                // Update sidebar content if we're in the sidebar
                if (sidebarContent) {
                    sidebarContent.innerHTML = emptyCartHTML;
                }
                
                // Update main page content if we're on the cart page
                if (cartContainer) {
                    cartContainer.style.display = 'none';
                }
                if (cartHeader) {
                    cartHeader.style.display = 'none';
                }
                
                const mainContent = document.querySelector('.main-content .container');
                if (mainContent && !sidebarContent) {
                    // Remove any existing empty cart message
                    const existingEmptyCart = mainContent.querySelector('.empty-cart');
                    if (existingEmptyCart) {
                        existingEmptyCart.remove();
                    }
                    
                    // Add new empty cart message to main page
                    const emptyCartDiv = document.createElement('div');
                    emptyCartDiv.className = 'empty-cart';
                    emptyCartDiv.style.marginTop = '2rem';
                    emptyCartDiv.innerHTML = emptyCartHTML;
                    mainContent.appendChild(emptyCartDiv);
                }
            }
        } else {
            showMessage('error', data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('error', 'Xəta baş verdi. Zəhmət olmasa yenidən cəhd edin.');
    });
}

// Function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Function to update cart total
function updateCartTotal() {
    const subtotalElements = document.querySelectorAll('.subtotal');
    let total = 0;
    
    subtotalElements.forEach(element => {
        const value = parseFloat(element.textContent.replace(' ₼', '').replace(',', '.'));
        if (!isNaN(value)) {
            total += value;
        }
    });
    
    const totalElement = document.getElementById('cart-total');
    if (totalElement) {
        totalElement.textContent = total.toFixed(2).replace('.', ',') + ' ₼';
    }
    
    // If cart is empty, show empty cart message
    const cartTable = document.querySelector('.table');
    const emptyCartMessage = document.querySelector('.empty-cart');
    
    if (subtotalElements.length === 0) {
        if (cartTable) cartTable.style.display = 'none';
        if (emptyCartMessage) emptyCartMessage.style.display = 'block';
    }
}

// Helper function to show messages
function showMessage(type, message) {
    const messagesContainer = document.createElement('div');
    messagesContainer.className = 'messages';
    messagesContainer.style.position = 'fixed';
    messagesContainer.style.top = '20px';
    messagesContainer.style.right = '-300px'; // Start off-screen
    messagesContainer.style.zIndex = '9999';
    messagesContainer.style.width = '300px';
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;
    
    const icon = document.createElement('i');
    icon.className = type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle';
    
    messageDiv.appendChild(icon);
    messageDiv.appendChild(document.createTextNode(' ' + message));
    messagesContainer.appendChild(messageDiv);
    
    document.body.appendChild(messagesContainer);
    
    // Animate in
    setTimeout(() => {
        messagesContainer.style.transition = 'right 0.5s ease';
        messagesContainer.style.right = '20px';
    }, 100);
    
    // Auto-hide message after 3 seconds
    setTimeout(() => {
        messagesContainer.style.right = '-300px';
        setTimeout(() => messagesContainer.remove(), 500);
    }, 3000);
}

// Modal functions
    window.openQuantityModal = function(productId, maxStock) {
        const modal = document.getElementById('quantityModal');
        const form = document.getElementById('addToCartForm');
        const quantityInput = document.getElementById('quantityInput');
        
        quantityInput.max = maxStock;
        form.action = `/cart/add/${productId}/`;
        modal.style.display = 'block';
    }

    window.closeQuantityModal = function() {
        const modal = document.getElementById('quantityModal');
        modal.style.display = 'none';
    }

function initializeSwiper() {
    if (document.querySelector('.new-products-swiper')) {
        new Swiper('.new-products-swiper', {
            slidesPerView: 4,
            spaceBetween: 20,
            loop: true,
            autoplay: {
                delay: 3000,
                disableOnInteraction: false,
            },
            pagination: {
                el: '.swiper-pagination',
                clickable: true,
            },
            navigation: {
                nextEl: '.swiper-button-next',
                prevEl: '.swiper-button-prev',
            },
            breakpoints: {
                320: {
                    slidesPerView: 1,
                    spaceBetween: 10
                },
                480: {
                    slidesPerView: 2,
                    spaceBetween: 15
                },
                768: {
                    slidesPerView: 3,
                    spaceBetween: 15
                },
                1024: {
                    slidesPerView: 4,
                    spaceBetween: 20
                }
            }
        });
    }
}

// Function to update cart counter
function updateCartCounter(count) {
    const counter = document.querySelector('.cart-counter');
    if (counter) {
        counter.textContent = count;
    }
}

// Function to get current cart count
function getCartCount() {
    const cart = JSON.parse(sessionStorage.getItem('cart') || '{}');
    return Object.keys(cart).length;
}

function initializeUserDropdown() {
    const userButton = document.querySelector('.user-button');
    const dropdownContent = document.querySelector('.user-dropdown-content');

    if (userButton && dropdownContent) {
        // Düyməyə klik hadisəsini əlavə edirik
        userButton.addEventListener('click', function(e) {
            e.stopPropagation();
            dropdownContent.classList.toggle('active');
            userButton.classList.toggle('active'); // Ox işarəsini çevirmək üçün
        });

        // Səhifənin istənilən yerinə klik edildikdə dropdown-u bağlayırıq
        document.addEventListener('click', function(e) {
            if (!dropdownContent.contains(e.target)) {
                dropdownContent.classList.remove('active');
                userButton.classList.remove('active'); // Ox işarəsini geri qaytarmaq üçün
            }
        });
    }
}

function initializeImageModal() {
    const modal = document.getElementById('imageModal');
    const closeBtn = document.querySelector('.image-modal-close');
    
    if (modal && closeBtn) {
        closeBtn.onclick = closeImageModal;
        
        // Modal xaricində kliklədikdə bağla
        modal.onclick = function(e) {
            if (e.target === modal) {
                closeImageModal();
            }
        };
        
        // ESC düyməsi ilə bağla
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && modal.style.display === 'block') {
                closeImageModal();
            }
        });
    }
}

function openImageModal(imageSrc) {
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('modalImage');
    if (modal && modalImg && imageSrc) {
        modalImg.src = imageSrc;
        modal.style.display = 'block';
        setTimeout(() => {
            modal.classList.add('show');
        }, 10);
    }
}

function closeImageModal() {
    const modal = document.getElementById('imageModal');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.style.display = 'none';
        }, 300);
    }
}

function initializePopupModal() {
    const modal = document.getElementById('popupModal');
    if (!modal) return;

    const closeBtn = document.querySelector('.popup-close');
    const yeniliklerLink = document.getElementById('yeniliklerLink');
    let popupSwiper = null;
    
    // Initialize Swiper function
    function initPopupSwiper() {
        if (popupSwiper) {
            popupSwiper.destroy();
        }
        
        popupSwiper = new Swiper('.popup-swiper', {
            loop: true,
            autoplay: {
                delay: 3000,
                disableOnInteraction: false,
            },
            pagination: {
                el: '.swiper-pagination',
                clickable: true
            },
            navigation: {
                nextEl: '.swiper-button-next',
                prevEl: '.swiper-button-prev',
            }
        });
    }
    
    // Check if we should show the popup
    function shouldShowPopup() {
        const lastShown = localStorage.getItem('lastPopupShown');
        if (!lastShown) return true;
        
        const thirtyMinutesInMs = 30 * 60 * 1000;
        const timeSinceLastShown = Date.now() - parseInt(lastShown);
        
        return timeSinceLastShown >= thirtyMinutesInMs;
    }

    // Function to show popup
    function showPopup() {
        modal.style.display = 'block';
        localStorage.setItem('lastPopupShown', Date.now().toString());
        // Initialize Swiper when modal is shown
        setTimeout(() => {
            initPopupSwiper();
        }, 100);
    }
    
    // Show modal initially if enough time has passed
    if (shouldShowPopup()) {
        showPopup();
    }

    // Yenilikler linkine klik edəndə modalı göstər
    if (yeniliklerLink) {
        yeniliklerLink.addEventListener('click', function(e) {
            e.preventDefault();
            showPopup();
        });
    }

    // Close modal when clicking close button
    closeBtn.onclick = function() {
        modal.style.display = 'none';
        // Destroy Swiper instance when modal is closed
        if (popupSwiper) {
            popupSwiper.destroy();
            popupSwiper = null;
        }
    }

    // Prevent modal from closing when clicking inside modal content
    const popupContent = document.querySelector('.popup-content');
    if (popupContent) {
        popupContent.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    }
}

function initializeCartSidebar() {
    const cartToggle = document.getElementById('cartSidebarToggle');
    const cartSidebar = document.getElementById('cartSidebar');
    const closeSidebar = document.getElementById('closeSidebar');
    const overlay = document.getElementById('sidebarOverlay');
    
    if (cartToggle && cartSidebar && closeSidebar && overlay) {
        // Load cart content when sidebar is opened
        function loadCartContent() {
            fetch('/cart/')
                .then(response => response.text())
                .then(html => {
                    // Create a temporary container
                    const temp = document.createElement('div');
                    temp.innerHTML = html;
                    
                    // Find the cart container in the response
                    const cartContent = temp.querySelector('.cart-container');
                    
                    // Update the sidebar content
                    const sidebarContent = document.querySelector('.cart-sidebar-content');
                    
                    if (cartContent) {
                        sidebarContent.innerHTML = cartContent.outerHTML;
                    } else {
                        // Create empty cart message for sidebar
                        sidebarContent.innerHTML = `
                            <div class="empty-cart" style="margin: 20px;">
                                <i class="fas fa-shopping-cart"></i>
                                <p>Səbətiniz boşdur.</p>
                                <a href="/products/" class="btn btn-primary">Məhsullara bax</a>
                            </div>
                        `;
                    }
                    
                    // Reinitialize cart functionality for the loaded content
                    initializeCart();
                    
                    // Prevent checkout form submission and open modal instead
                    const checkoutForm = document.getElementById('checkout-form');
                    if (checkoutForm) {
                        checkoutForm.addEventListener('submit', function(e) {
                            e.preventDefault();
                            openNoteModal();
                        });
                    }
                })
                .catch(error => {
                    console.error('Error loading cart content:', error);
                });
        }

        // Open sidebar
        cartToggle.addEventListener('click', function(e) {
            e.preventDefault();
            cartSidebar.classList.add('active');
            overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
            loadCartContent();
        });

        // Close sidebar
        function closeSidebarHandler() {
            cartSidebar.classList.remove('active');
            overlay.classList.remove('active');
            document.body.style.overflow = '';
        }

        closeSidebar.addEventListener('click', closeSidebarHandler);
        overlay.addEventListener('click', closeSidebarHandler);

        // Close on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && cartSidebar.classList.contains('active')) {
                closeSidebarHandler();
            }
        });
    }
}

// Products Page Functions
function initializeProductsPage() {
    let offset = 5;
    let loading = false;
    const tbody = document.getElementById('products-tbody');
    const spinner = document.getElementById('loading-spinner');
    let hasMore = false; // Bu dəyər HTML-dən gələcək

    // hasMore dəyərini HTML-dən alırıq
    if (tbody) {
        const hasMoreElement = document.querySelector('[data-has-more]');
        if (hasMoreElement) {
            hasMore = hasMoreElement.dataset.hasMore === 'true';
        }
    }

    function loadMoreProducts() {
        if (loading || !hasMore) return;
        
        loading = true;
        if (spinner) {
            spinner.style.display = 'flex';
        }
        
        const params = new URLSearchParams(window.location.search);
        params.append('offset', offset);
        
        // Determine if we're on the new products page
        const isNewProductsPage = window.location.pathname.includes('new-products');
        const endpoint = isNewProductsPage ? '/load-more-new-products/' : '/load-more-products/';
        
        setTimeout(() => {
            fetch(`${endpoint}?${params.toString()}`)
                .then(response => response.json())
                .then(data => {
                    if (tbody) {
                        data.products.forEach(product => {
                            const row = document.createElement('tr');
                            row.innerHTML = `
                                <td><img src="${product.sekil_url || '/static/images/no_image.webp'}" alt="${product.adi}" class="product-image" onclick="openImageModal('${product.sekil_url}')"></td>
                                <td>${product.brend_kod}</td>
                                <td>${product.firma}</td>
                                <td>
                                    ${product.adi}
                                    ${product.yenidir ? '<span class="new-badge">Yeni</span>' : ''}
                                </td>
                                <td>${product.stok}</td>
                                <td>${product.qiymet} ₼</td>
                                <td>
                                    <button type="button" 
                                            class="cart-add-btn" 
                                            ${product.stok === 0 ? 'disabled' : ''}
                                            onclick="openQuantityModal(${product.id}, ${product.stok})">
                                        <i class="fas fa-shopping-cart"></i>
                                    </button>
                                </td>
                                <td>
                                    <button type="button" 
                                            class="details-btn" 
                                            onclick="openDetailsModal(${product.id})">
                                        <i class="fas fa-info-circle"></i>
                                    </button>
                                </td>
                            `;
                            tbody.appendChild(row);
                        });
                        
                        hasMore = data.has_more;
                        offset += 5;
                        
                        // Initialize image modal for new images
                        initializeImageModal();
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                })
                .finally(() => {
                    loading = false;
                    if (spinner) {
                        spinner.style.display = 'none';
                    }
                });
        }, 500); // 0.5 saniyə gözləmə
    }

    // Scroll event listener
    if (tbody) {
        window.addEventListener('scroll', () => {
            if ((window.innerHeight + window.scrollY) >= document.documentElement.scrollHeight - 200) {
                loadMoreProducts();
            }
        });
    }
}

// Details Modal Functions
function openDetailsModal(productId) {
    const modal = document.getElementById('detailsModal');
    if (!modal) return;

    // Fetch product details
    fetch(`/product-details/${productId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Update modal content
                document.getElementById('detailsImage').src = data.product.sekil_url || '/static/images/no_image.jpg';
                document.getElementById('detailsName').textContent = data.product.adi || '';
                document.getElementById('detailsCategory').textContent = data.product.kateqoriya || '-';
                document.getElementById('detailsFirma').textContent = data.product.firma || '';
                document.getElementById('detailsAvtomobil').textContent = data.product.avtomobil || '';
                document.getElementById('detailsBrendKod').textContent = data.product.brend_kod || '';

                document.getElementById('detailsOlcu').textContent = data.product.olcu || '-';
                document.getElementById('detailsQiymet').textContent = data.product.qiymet ? `${data.product.qiymet} ₼` : '';
                document.getElementById('detailsStok').textContent = data.product.stok ? `${data.product.stok} ədəd` : '';
                document.getElementById('detailsMelumat').textContent = data.product.melumat || '-';

                // Show modal with animation
                modal.style.display = 'block';
                setTimeout(() => {
                    modal.classList.add('show');
                }, 10);
            } else {
                showMessage('error', data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('error', 'Xəta baş verdi. Zəhmət olmasa yenidən cəhd edin.');
        });
}

function closeDetailsModal() {
    const modal = document.getElementById('detailsModal');
    if (!modal) return;

    modal.classList.remove('show');
    setTimeout(() => {
        modal.style.display = 'none';
    }, 300);
}

// Initialize Details Modal
function initializeDetailsModal() {
    const modal = document.getElementById('detailsModal');
    const closeBtn = document.querySelector('.details-modal-close');
    
    if (modal && closeBtn) {
        closeBtn.onclick = closeDetailsModal;
        
        // Close modal when clicking outside
        modal.onclick = function(e) {
            if (e.target === modal) {
                closeDetailsModal();
            }
        };
        
        // Close modal with ESC key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && modal.style.display === 'block') {
                closeDetailsModal();
            }
        });
    }
}

// Initialize Logo Slider
function initializeLogoSlider() {
    const logoSwiper = new Swiper('.logo-swiper', {
        slidesPerView: 'auto',
        spaceBetween: 3,
        loop: true,
        autoplay: {
            delay: 2000,
            disableOnInteraction: false,
        },
        breakpoints: {
            320: {
                slidesPerView: 4,
                spaceBetween: 0
            },
            480: {
                slidesPerView: 6,
                spaceBetween: 0
            },
            768: {
                slidesPerView: 8,
                spaceBetween: 0
            },
            1024: {
                slidesPerView: 10,
                spaceBetween: 0
            }
        }
    });
}

function initializeHeaderMessages() {
    const messages = document.querySelectorAll('.message-slide');
    if (messages.length <= 1) return;

    let currentIndex = 0;
    const interval = 5000; // 5 saniyə
    const transitionDelay = 1000; // 1 saniyə keçid vaxtı

    function showMessage(index) {
        messages.forEach(msg => {
            msg.classList.remove('active');
            msg.style.display = 'none';
        });
        
        messages[index].style.display = 'block';
        // Force reflow
        void messages[index].offsetHeight;
        messages[index].classList.add('active');
    }

    function nextMessage() {
        currentIndex = (currentIndex + 1) % messages.length;
        showMessage(currentIndex);
    }

    // İlk mesajı göstər
    showMessage(0);

    // Hər 5 saniyədən bir növbəti mesaja keç
    setInterval(nextMessage, interval);
}

// Note Modal Functions
function openNoteModal() {
    console.log('openNoteModal called');
    
    // Get cart container
    const cartContainer = document.querySelector('.cart-container');
    console.log('Cart container found:', !!cartContainer);
    
    if (!cartContainer) {
        showMessage('error', 'Səbət bulunamadı.');
        return;
    }
    
    // Get all checked checkboxes
    const selectedCheckboxes = cartContainer.querySelectorAll('.item-checkbox:checked');
    
    console.log('Selected checkboxes count:', selectedCheckboxes.length);
    selectedCheckboxes.forEach(cb => console.log('Checkbox value:', cb.value));
    
    if (selectedCheckboxes.length === 0) {
        showMessage('error', 'Zəhmət olmasa ən azı bir məhsul seçin.');
        return;
    }
    
    const noteModal = document.getElementById('noteModal');
    const noteText = document.getElementById('noteText');
    noteText.value = ''; // Clear previous note
    
    // Reset delivery method in modal
    const modalDeliveryInputs = document.querySelectorAll('#noteForm input[name="catdirilma_usulu"]');
    modalDeliveryInputs.forEach(input => input.checked = false);
    
    noteModal.style.display = 'block';
}

function closeNoteModal() {
    const noteModal = document.getElementById('noteModal');
    noteModal.style.display = 'none';
}

function submitNoteAndConfirm() {
    // Validate delivery method in modal
    const modalDeliveryMethod = document.querySelector('#noteForm input[name="catdirilma_usulu"]:checked');
    if (!modalDeliveryMethod) {
        showMessage('error', 'Zəhmət olmasa çatdırılma üsulunu seçin.');
        return;
    }
    
    const noteText = document.getElementById('noteText').value;
    const hiddenNote = document.getElementById('hidden-note');
    const hiddenDelivery = document.getElementById('hidden-delivery');
    
    hiddenNote.value = noteText;
    hiddenDelivery.value = modalDeliveryMethod.value;
    
    // Close note modal and open confirmation modal
    closeNoteModal();
    openConfirmationModal();
}

function openConfirmationModal() {
    const confirmationModal = document.getElementById('confirmationModal');
    confirmationModal.style.display = 'block';
}

function closeConfirmationModal() {
    const confirmationModal = document.getElementById('confirmationModal');
    confirmationModal.style.display = 'none';
}

function confirmOrderSubmit() {
    const checkoutForm = document.getElementById('checkout-form');
    
    if (!checkoutForm) {
        showMessage('error', 'Səbət formu tapılmadı.');
        return;
    }
    
    // Get cart container
    const cartContainer = document.querySelector('.cart-container');
    if (!cartContainer) {
        showMessage('error', 'Səbət bulunamadı.');
        closeConfirmationModal();
        return;
    }
    
    // Get all checked checkboxes from cart
    const selectedCheckboxes = cartContainer.querySelectorAll('.item-checkbox:checked');
    
    console.log('confirmOrderSubmit - Selected checkboxes:', selectedCheckboxes.length);
    
    if (selectedCheckboxes.length === 0) {
        showMessage('error', 'Zəhmət olmasa ən azı bir məhsul seçin.');
        closeConfirmationModal();
        return;
    }
    
    // Remove old hidden selected_items inputs
    checkoutForm.querySelectorAll('input[name="selected_items[]"]').forEach(input => input.remove());
    
    // Add new hidden inputs for each selected item
    selectedCheckboxes.forEach(checkbox => {
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = 'selected_items[]';
        hiddenInput.value = checkbox.value;
        checkoutForm.appendChild(hiddenInput);
        console.log('Added hidden input for product:', checkbox.value);
    });
    
    // Add delivery method
    const hiddenDelivery = document.getElementById('hidden-delivery');
    let deliveryInput = checkoutForm.querySelector('input[name="catdirilma_usulu"]');
    if (!deliveryInput) {
        deliveryInput = document.createElement('input');
        deliveryInput.type = 'hidden';
        deliveryInput.name = 'catdirilma_usulu';
        checkoutForm.appendChild(deliveryInput);
    }
    deliveryInput.value = hiddenDelivery.value;
    console.log('Delivery method set to:', hiddenDelivery.value);
    
    // Add note
    const hiddenNote = document.getElementById('hidden-note');
    let noteInput = checkoutForm.querySelector('input[name="qeyd"]');
    if (!noteInput) {
        noteInput = document.createElement('input');
        noteInput.type = 'hidden';
        noteInput.name = 'qeyd';
        checkoutForm.appendChild(noteInput);
    }
    noteInput.value = hiddenNote.value;
    console.log('Note set to:', hiddenNote.value);
    
    closeConfirmationModal();
    console.log('Submitting form...');
    checkoutForm.submit();
}

// Close modals when clicking outside
window.addEventListener('click', function(event) {
    const noteModal = document.getElementById('noteModal');
    const confirmationModal = document.getElementById('confirmationModal');
    
    if (event.target == noteModal) {
        closeNoteModal();
    }
    if (event.target == confirmationModal) {
        closeConfirmationModal();
    }
});

