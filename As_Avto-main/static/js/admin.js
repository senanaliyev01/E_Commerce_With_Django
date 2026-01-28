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

        // Nəticələri göstər
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