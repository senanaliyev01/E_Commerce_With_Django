function toggleStatistics() {
    var container = document.getElementById('statisticsContainer');
    var button = document.querySelector('.show-stats-btn');
    
    if (container.style.display === 'none' || container.style.display === '') {
        container.style.display = 'block';
        button.innerHTML = '<i class="fas fa-times"></i> Statistikanı Gizlət';
    } else {
        container.style.display = 'none';
        button.innerHTML = '<i class="fas fa-chart-bar"></i> İstifadəçi Statistikasına Bax';
    }
}

let searchTimeout = null;

// Mətni təmizləmək üçün funksiya
function cleanText(text) {
    // Yalnız hərflər, rəqəmlər, Azərbaycan hərfləri və "_" simvoluna icazə ver
    return text.replace(/[^a-zA-Z0-9əƏçÇşŞöÖğĞüÜıİ_]/g, '').toLowerCase();
}

// İki mətni müqayisə etmək üçün funksiya
function compareTexts(text1, text2) {
    const cleanText1 = cleanText(text1);
    const cleanText2 = cleanText(text2);
    
    // Tam uyğunluq
    if (cleanText1 === cleanText2) return 2;
    // Hissəvi uyğunluq
    if (cleanText2.includes(cleanText1)) return 1;
    // Uyğunsuzluq
    return 0;
}

function filterUsers() {
    clearTimeout(searchTimeout);
    
    searchTimeout = setTimeout(() => {
        const input = document.getElementById('userSearch');
        const searchText = input.value;
        const cleanSearchText = cleanText(searchText);
        const table = document.querySelector('.stats-table');
        const tr = table.getElementsByTagName('tr');
        const clearButton = document.querySelector('.clear-search');
        const noResults = document.querySelector('.no-results');
        let hasResults = false;
        let matches = [];

        // Təmizlə düyməsini göstər/gizlət
        clearButton.style.display = searchText ? 'block' : 'none';

        // Əgər axtarış mətni boşdursa
        if (!cleanSearchText) {
            for (let i = 1; i < tr.length; i++) {
                tr[i].style.display = '';
                const td = tr[i].getElementsByTagName('td')[0];
                if (td) td.innerHTML = td.textContent; // Highlight-ları təmizlə
            }
            noResults.style.display = 'none';
            return;
        }

        // Bütün sətirləri yoxla və uyğunluq dərəcəsini hesabla
        for (let i = 1; i < tr.length; i++) {
            const td = tr[i].getElementsByTagName('td')[0];
            if (td) {
                const originalText = td.textContent || td.innerText;
                const matchLevel = compareTexts(cleanSearchText, originalText);
                
                if (matchLevel > 0) {
                    matches.push({
                        row: tr[i],
                        cell: td,
                        text: originalText,
                        level: matchLevel
                    });
                    hasResults = true;
                } else {
                    tr[i].style.display = 'none';
                }
            }
        }

        // Nəticələri uyğunluq dərəcəsinə görə sırala
        matches.sort((a, b) => b.level - a.level);

        // Nəticələri göstə
        matches.forEach(match => {
            match.row.style.display = '';
            
            // Axtarış sözünü highlight et
            let displayText = match.text;
            const searchTerms = cleanSearchText.split('_').filter(Boolean); // "_" simvolu ilə ayrılmış sözləri al
            
            searchTerms.forEach(term => {
                const regex = new RegExp(`(${term})`, 'gi');
                displayText = displayText.replace(regex, '<span class="highlight">$1</span>');
            });
            
            match.cell.innerHTML = displayText;
        });

        // "Nəticə tapılmadı" mesajını göstər/gizlət
        noResults.style.display = !hasResults && searchText ? 'block' : 'none';
    }, 300);
}

function clearSearch() {
    const input = document.getElementById('userSearch');
    input.value = '';
    filterUsers();
    input.focus();
}

// Event listener-ləri əlavə et
document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('userSearch');
    
    // Enter düyməsinə basıldıqda səhifənin yenilənməsinin qarşısını al
    input.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
        }
    });

    // Input-a focus olduqda bütün mətni seç
    input.addEventListener('focus', function() {
        if (this.value) {
            this.select();
        }
    });

    // Input-a yazıldıqda avtomatik böyük hərfə çevir və yalnız icazə verilən simvolları saxla
    input.addEventListener('input', function() {
        let value = this.value.toUpperCase();
        // Yalnız hərflər, rəqəmlər, Azərbaycan hərfləri və "_" simvoluna icazə ver
        value = value.replace(/[^A-ZƏÇŞÖĞÜİ0-9_]/g, '');
        this.value = value;
    });
});

// Excel Import Modal Functions
document.addEventListener('DOMContentLoaded', function() {
    initializeExcelModal();
});

function initializeExcelModal() {
    var modal = document.getElementById('excelImportModal');
    var btn = document.getElementById('showExcelImportModal');
    var span = document.getElementsByClassName('close')[0];
    var closeBtn = document.getElementsByClassName('closeBtn')[0];

    if (!modal || !btn) {
        console.log('Modal elements not found');
        return;
    }

    // Modal açma düyməsi
    btn.addEventListener('click', function() {
        modal.style.display = "block";
    });

    // X düyməsi ilə bağlama
    if (span) {
        span.addEventListener('click', function() {
            modal.style.display = "none";
        });
    }

    // Bağla düyməsi ilə bağlama
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            modal.style.display = "none";
        });
    }

    // Modal xaricində kliklə bağlama
    window.addEventListener('click', function(event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    });
}


document.addEventListener('DOMContentLoaded', function() {
    // Cədvəldəki borc məbləğlərini yoxla və sinif əlavə et
    document.querySelectorAll('.stats-table .debt').forEach(cell => {
        const amount = parseFloat(cell.textContent.replace('₼', '').trim());
        if (amount > 0) {
            cell.classList.add('positive');
        } else if (amount < 0) {
            cell.classList.add('negative');
        } else {
            cell.classList.add('zero');
        }
    });

    // Ümumi statistikadakı borc məbləğini yoxla və sinif əlavə et
    const totalDebtItem = document.querySelector('.stats-item.debt');
    const totalDebtAmount = parseFloat(totalDebtItem.querySelector('span').textContent.replace('₼', '').trim());
    
    if (totalDebtAmount > 0) {
        totalDebtItem.classList.add('positive');
    } else if (totalDebtAmount < 0) {
        totalDebtItem.classList.add('negative');
    } else {
        totalDebtItem.classList.add('zero');
    }
});

// PDF AJAX Download Function
document.addEventListener('DOMContentLoaded', function() {
    initializePdfButtons();
});

function initializePdfButtons() {
    // Sifaris PDF düymələri
    const sifarisButtons = document.querySelectorAll('.pdf-download-btn[data-sifaris-id]');
    sifarisButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const sifarisId = this.getAttribute('data-sifaris-id');
            downloadPdfAjax(`/api/download-sifaris-pdf/${sifarisId}/`, `sifaris-${sifarisId}.pdf`, this);
        });
    });
    
    // Mehsullar PDF düyməsi
    const productsButton = document.getElementById('downloadProductsPdfBtn');
    if (productsButton) {
        productsButton.addEventListener('click', function(e) {
            e.preventDefault();
            downloadPdfAjax('/api/download-products-pdf/', 'mehsullar.pdf', this);
        });
    }
}

function downloadPdfAjax(url, filename, button) {
    const originalText = button.textContent;
    
    // Düymə statusu dəyişdir
    button.disabled = true;
    button.textContent = '⏳ Yüklənir...';
    button.style.opacity = '0.6';
    
    // AJAX sorğusu
    fetch(url, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.blob();
    })
    .then(blob => {
        // Blob-dan URL yaratmaq
        const blobUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = blobUrl;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        window.URL.revokeObjectURL(blobUrl);
        document.body.removeChild(link);
        
        // Uğur mesajı göstər
        showNotification('PDF uğurla yükləndi!', 'success');
        
        // Düymə statusu bərpa et
        button.disabled = false;
        button.textContent = originalText;
        button.style.opacity = '1';
    })
    .catch(error => {
        console.error('PDF yüklənərkən xəta:', error);
        showNotification(`Xəta: ${error.message}`, 'error');
        
        // Düymə statusu bərpa et
        button.disabled = false;
        button.textContent = originalText;
        button.style.opacity = '1';
    });
}

// Notification System
function showNotification(message, type = 'info') {
    // Əvvəlki notifikasiyaları sil
    const existingNotification = document.querySelector('.pdf-notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    const notification = document.createElement('div');
    notification.className = `pdf-notification pdf-notification-${type}`;
    notification.textContent = message;
    
    const styles = {
        'position': 'fixed',
        'top': '20px',
        'right': '20px',
        'padding': '15px 20px',
        'border-radius': '4px',
        'z-index': '10000',
        'font-size': '14px',
        'font-weight': '500',
        'box-shadow': '0 2px 8px rgba(0,0,0,0.15)',
        'animation': 'slideIn 0.3s ease-out'
    };
    
    if (type === 'success') {
        styles.backgroundColor = '#28a745';
        styles.color = 'white';
    } else if (type === 'error') {
        styles.backgroundColor = '#dc3545';
        styles.color = 'white';
    } else {
        styles.backgroundColor = '#17a2b8';
        styles.color = 'white';
    }
    
    Object.assign(notification.style, styles);
    document.body.appendChild(notification);
    
    // 3 saniyə sonra sil
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// CSS Animation stilləri əlavə et
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
    
    .pdf-download-btn {
        transition: all 0.3s ease;
    }
    
    .pdf-download-btn:hover:not(:disabled) {
        background-color: #2c5282 !important;
        transform: translateY(-2px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .pdf-download-btn:active:not(:disabled) {
        transform: translateY(0);
    }
    
    .pdf-download-btn:disabled {
        cursor: not-allowed;
    }
`;
if (document.head) {
    document.head.appendChild(style);
}