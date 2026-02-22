function toggleStatistics() {
    var container = document.getElementById('statisticsContainer');
    var button = document.querySelector('.show-stats-btn');

    // Safely return if elements are not present on the current page
    if (!container || !button) return;

    if (container.style.display === 'none' || container.style.display === '') {
        container.style.display = 'block';
        button.innerHTML = '<i class="fas fa-times"></i> Statistikanı Gizlət';
    } else {
        container.style.display = 'none';
        button.innerHTML = '<i class="fas fa-chart-bar"></i> İstifadəçi Statistikasına Bax';
    }
}

let searchTimeout = null;

// views.py ilə eyni Azərbaycan hərfi normalizə etmə
function normalizeAzerbaijaniChars(text) {
    const charMap = {
        'ə': ['e'], 'e': ['ə'],
        'ö': ['o'], 'o': ['ö'],
        'ğ': ['g'], 'g': ['ğ'],
        'ı': ['i'], 'i': ['ı'],
        'ü': ['u'], 'u': ['ü'],
        'ş': ['s'], 's': ['ş'],
        'ç': ['c'], 'c': ['ç'],
    };

    const variations = new Set([text.toLowerCase()]);
    
    for (const char in charMap) {
        const replacements = charMap[char];
        const newVars = [];
        
        variations.forEach(v => {
            if (v.includes(char)) {
                replacements.forEach(repl => {
                    newVars.push(v.split(char).join(repl));
                });
            }
        });
        
        newVars.forEach(v => variations.add(v));
    }
    
    return Array.from(variations);
}

// Axtarış sözlərini hazırla (views.py ilə uyumlu)
function getSearchWords(query) {
    // Boşluqları normallaşdır
    const processed = query.replace(/\s+/g, ' ').trim();
    return processed.split(' ').filter(word => word.length > 0);
}

// İstifadəçi adına mətni bir cümlə ilə yoxla (views.py ilə uyumlu)
function matchesSearch(userName, searchQuery) {
    const searchWords = getSearchWords(searchQuery);
    
    // Hər sözün ən azı bir varyasiyası istifadəçi adında olmalıdır (AND logic)
    return searchWords.every(word => {
        const variations = normalizeAzerbaijaniChars(word);
        // OR: sözün hər hansı varyasiyası tapılsa kefi
        return variations.some(variation => 
            userName.toLowerCase().includes(variation)
        );
    });
}

function filterUsers() {
    clearTimeout(searchTimeout);
    
    searchTimeout = setTimeout(() => {
        const input = document.getElementById('userSearch');
        if (!input) return; // no search input on this page

        const searchText = input.value;
        const table = document.querySelector('.stats-table');
        const clearButton = document.querySelector('.clear-search');
        const noResults = document.querySelector('.no-results');

        if (!table || !clearButton || !noResults) return; // required elements missing
        const tr = table.getElementsByTagName('tr');
        let hasResults = false;
        let matches = [];

        // Təmizlə düyməsini göstər/gizlət
        clearButton.style.display = searchText ? 'block' : 'none';

        // Əgər axtarış mətni boşdursa - bütün sətirləri göstər
        if (!searchText) {
            for (let i = 1; i < tr.length; i++) {
                tr[i].style.display = '';
                const td = tr[i].getElementsByTagName('td')[0];
                if (td) td.innerHTML = td.textContent; // Highlight-ları təmizlə
            }
            noResults.style.display = 'none';
            return;
        }

        // views.py ilə eyni - bütün sətirləri yoxla
        for (let i = 1; i < tr.length; i++) {
            const td = tr[i].getElementsByTagName('td')[0];
            if (td) {
                const originalText = td.textContent || td.innerText;
                
                // views.py ilə eyni mantıq: matchesSearch
                if (matchesSearch(originalText, searchText)) {
                    matches.push({
                        row: tr[i],
                        cell: td,
                        text: originalText
                    });
                    hasResults = true;
                } else {
                    tr[i].style.display = 'none';
                }
            }
        }

        // Nəticələri göstər
        matches.forEach(match => {
            match.row.style.display = '';
            
            // Highlight et - axtarış sözlərinin bütün varyasiyalarını
            let displayText = match.text;
            const searchWords = getSearchWords(searchText);
            
            // Hər sözün varyasiyalarını highlight et
            const highlightedWords = new Set();
            searchWords.forEach(word => {
                const variations = normalizeAzerbaijaniChars(word);
                variations.forEach(variation => {
                    if (variation && !highlightedWords.has(variation)) {
                        highlightedWords.add(variation);
                        // Case-insensitive highlight
                        const regex = new RegExp(`\\b(${variation})\\b`, 'gi');
                        displayText = displayText.replace(regex, '<span class="highlight">$1</span>');
                    }
                });
            });
            
            match.cell.innerHTML = displayText;
        });

        // "Nəticə tapılmadı" mesajını göstər/gizlət
        noResults.style.display = !hasResults && searchText ? 'block' : 'none';
    }, 300);
}

function clearSearch() {
    const input = document.getElementById('userSearch');
    if (!input) return;
    input.value = '';
    filterUsers();
    input.focus();
}

// Event listener-ləri əlavə et
document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('userSearch');
    if (!input) return; // don't attach handlers when input not present

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

    // Input-a yazıldıqda yalnız icazə verilən simvolları saxla (views.py ilə uyumlu)
    input.addEventListener('input', function() {
        let value = this.value;
        // Yalnız hərflər, rəqəmlər, Azərbaycan hərfləri və boşluq simvoluna icazə ver
        value = value.replace(/[^a-zA-ZəƏçÇşŞöÖğĞüÜıİ0-9 ]/g, '');
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
    if (totalDebtItem) {
        const span = totalDebtItem.querySelector('span');
        if (span) {
            const totalDebtAmount = parseFloat(span.textContent.replace('₼', '').trim()) || 0;
            if (totalDebtAmount > 0) {
                totalDebtItem.classList.add('positive');
            } else if (totalDebtAmount < 0) {
                totalDebtItem.classList.add('negative');
            } else {
                totalDebtItem.classList.add('zero');
            }
        }
    }
});

// PDF AJAX Download Function
document.addEventListener('DOMContentLoaded', function() {
    initializePdfButtons();
});

function initializePdfButtons() {
    // Sifaris HTML düymələri
    const sifarisButtons = document.querySelectorAll('.pdf-download-btn[data-sifaris-id]');
    sifarisButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const sifarisId = this.getAttribute('data-sifaris-id');
            downloadPdfAjax(
                `/sabuhi085-habil054/home/sifaris/export-pdf/${sifarisId}/`, 
                `sifaris-${sifarisId}.html`, 
                this
            );
        });
    });
    
    // Mehsullar HTML düyməsi
    const productsButton = document.getElementById('downloadProductsPdfBtn');
    if (productsButton) {
        productsButton.addEventListener('click', function(e) {
            e.preventDefault();
            downloadPdfAjax(
                '/sabuhi085-habil054/home/mehsul/export-pdf/', 
                'mehsullar.html', 
                this
            );
        });
    }
}

function downloadPdfAjax(url, filename, button) {
    const originalText = button.textContent;
    
    // Düymə statusu dəyişdir
    button.disabled = true;
    button.style.opacity = '0.6';
    button.textContent = 'Yüklənir...';
    
    // AJAX sorğusu - HTML mətnini al
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
        return response.text();
    })
    .then(htmlContent => {
        // Gizli iframe yaratmaq
        const iframe = document.createElement('iframe');
        iframe.style.display = 'none';
        document.body.appendChild(iframe);
        
        // iframe-ə HTML yazma
        const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
        iframeDoc.open();
        iframeDoc.write(htmlContent);
        iframeDoc.close();
        
        // Print dialog açma
        setTimeout(() => {
            iframe.contentWindow.print();
            
            // Print bittikdən sonra iframe sil
            setTimeout(() => {
                document.body.removeChild(iframe);
                
                // Düymə statusu bərpa et
                button.disabled = false;
                button.textContent = originalText;
                button.style.opacity = '1';
            }, 500);
        }, 300);
    })
    .catch(error => {
        console.error('PDF yüklənərkən xəta:', error);
        
        // Düymə statusu bərpa et
        button.disabled = false;
        button.textContent = originalText;
        button.style.opacity = '1';
        
        showNotification(`Xəta: ${error.message}`, 'error');
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

/* JS moved from templates/admin/mehsul_change_list.html */
// Excel import modal controls and batch import logic
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('excelImportModal');
    const showBtn = document.getElementById('showExcelImportModal');
    const closeBtns = document.querySelectorAll('.close, .closeBtn');
    const form = document.querySelector('#excelImportModal form');
    const importBtn = document.getElementById('importBtn');
    const progressDiv = document.getElementById('importProgress');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const statusText = document.getElementById('statusText');
    const errorSummary = document.getElementById('errorSummary');
    const errorList = document.getElementById('errorList');
    const errorDetailsModal = document.getElementById('errorDetailsModal');
    const errorDetailsContent = document.getElementById('errorDetailsContent');

    // Show modal
    if (showBtn) {
        showBtn.onclick = function() {
            modal.style.display = 'block';
        }
    }

    // Close modal
    closeBtns.forEach(btn => {
        btn.onclick = function() {
            modal.style.display = 'none';
            resetProgress();
        }
    });

    // Close modal when clicking outside
    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = 'none';
            resetProgress();
        }
        if (event.target == errorDetailsModal) {
            errorDetailsModal.style.display = 'none';
        }
    }

    // Handle form submission
    if (form) {
        form.onsubmit = function(e) {
            e.preventDefault();
            performBatchImport();
        }
    }

    function resetProgress() {
        if (!progressDiv) return;
        progressDiv.style.display = 'none';
        progressBar.style.width = '0%';
        progressText.textContent = '0%';
        statusText.textContent = '';
        errorSummary.style.display = 'none';
        errorList.innerHTML = '';
        importBtn.disabled = false;
        importBtn.textContent = 'İdxal Et';
    }

    function updateProgress(processed, total, newCount, updateCount, errorCount) {
        const percentage = Math.round((processed / total) * 100);
        progressBar.style.width = percentage + '%';
        progressText.textContent = percentage + '%';
        statusText.textContent = `${processed}/${total} sətir emal edildi. Yeni: ${newCount}, Yeniləndi: ${updateCount}, Xəta: ${errorCount}`;
    }

    async function performBatchImport() {
        const fileInput = form.querySelector('input[type="file"]');
        const file = fileInput.files[0];
        if (!file) return;

        importBtn.disabled = true;
        importBtn.textContent = 'İdxal edilir...';
        progressDiv.style.display = 'block';
        statusText.textContent = 'Excel faylı oxunur...';
        errorSummary.style.display = 'none';
        errorList.innerHTML = '';

        try {
            // Step 1: Initialize import
            const formData = new FormData();
            formData.append('excel_file', file);
            formData.append('csrfmiddlewaretoken', form.querySelector('[name="csrfmiddlewaretoken"]').value);

            const initResponse = await fetch('import-excel-init/', {
                method: 'POST',
                body: formData
            });

            const initResult = await initResponse.json();
            if (initResult.status !== 'ok') {
                throw new Error(initResult.message);
            }

            const jobId = initResult.job_id;
            const totalRows = initResult.total_rows;

            // Step 2: Process in batches
            const batchSize = 50;
            let processed = 0;
            let newCount = 0;
            let updateCount = 0;
            let errorCount = 0;
            let allErrors = [];

            while (processed < totalRows) {
                const batchFormData = new FormData();
                batchFormData.append('job_id', jobId);
                batchFormData.append('start', processed);
                batchFormData.append('size', batchSize);
                batchFormData.append('csrfmiddlewaretoken', form.querySelector('[name="csrfmiddlewaretoken"]').value);

                const batchResponse = await fetch('import-excel-batch/', {
                    method: 'POST',
                    body: batchFormData
                });

                const batchResult = await batchResponse.json();
                if (batchResult.status !== 'ok') {
                    throw new Error(batchResult.message);
                }

                processed = parseInt(batchResult.processed_rows, 10) || 0;
                newCount = parseInt(batchResult.new_count, 10) || 0;
                updateCount = parseInt(batchResult.update_count, 10) || 0;
                errorCount = parseInt(batchResult.error_count, 10) || 0;

                // Collect errors from batch
                if (batchResult.errors && batchResult.errors.length > 0) {
                    allErrors = allErrors.concat(batchResult.errors);
                }

                updateProgress(processed, totalRows, newCount, updateCount, errorCount);

                // Small delay to allow UI to update
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            // Step 3: Finalize (delete products not in Excel)
            statusText.textContent = 'Excel-də olmayan məhsullar silinir...';

            const finalizeFormData = new FormData();
            finalizeFormData.append('job_id', jobId);
            finalizeFormData.append('csrfmiddlewaretoken', form.querySelector('[name="csrfmiddlewaretoken"]').value);

            const finalizeResponse = await fetch('import-excel-finalize/', {
                method: 'POST',
                body: finalizeFormData
            });

            const finalizeResult = await finalizeResponse.json();
            if (finalizeResult.status !== 'ok') {
                throw new Error(finalizeResult.message);
            }

            const deletedCount = parseInt(finalizeResult.deleted_count, 10) || 0;

            // Show final results
            progressBar.style.width = '100%';
            progressText.textContent = '100%';
            statusText.textContent = `Tamamlandı! Yeni: ${newCount}, Yeniləndi: ${updateCount}, Silindi: ${deletedCount}, Xəta: ${errorCount}`;

            // Show error summary if there are errors
            if (allErrors.length > 0) {
                showErrorSummary(allErrors);
            }

        } catch (error) {
            console.error('Import error:', error);
            statusText.textContent = 'Xəta: ' + error.message;
            resetProgress();
        }
    }

    function showErrorSummary(errors) {
        errorSummary.style.display = 'block';

        // Group errors by line number
        const errorsByLine = {};
        errors.forEach(error => {
            const line = error.line || 'Bilinməyən';
            if (!errorsByLine[line]) {
                errorsByLine[line] = [];
            }
            errorsByLine[line].push(error);
        });

        // Create error list with clickable items
        const errorListHTML = Object.keys(errorsByLine).map(line => {
            const lineErrors = errorsByLine[line];
            const errorCount = lineErrors.length;
            return `
                <div class="error-line-item" data-line="${line}" style="cursor: pointer; padding: 5px; margin: 2px 0; background-color: #fff; border: 1px solid #ddd; border-radius: 3px;">
                    <strong>Sətir ${line}:</strong> ${errorCount} xəta
                    <span style="float: right; color: #007bff;">Detallar →</span>
                </div>
            `;
        }).join('');

        errorList.innerHTML = errorListHTML;

        // Add click handlers to error items
        document.querySelectorAll('.error-line-item').forEach(item => {
            item.onclick = function() {
                const line = this.getAttribute('data-line');
                const lineErrors = errorsByLine[line];
                showErrorDetails(line, lineErrors);
            };
        });
    }

    function showErrorDetails(line, errors) {
        errorDetailsModal.style.display = 'block';

        const errorDetailsHTML = `
            <h4>Sətir ${line} - Xəta Detalları:</h4>
            ${errors.map(error => `
                <div style="margin-bottom: 15px; padding: 10px; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px;">
                    <strong>Xəta:</strong> ${error.message || 'Bilinməyən xəta'}<br>
                    ${error.field ? `<strong>Sahə:</strong> ${error.field}<br>` : ''}
                    ${error.row ? `<strong>Sətir məlumatları:</strong><br>
                        <div style="margin-top: 5px; font-family: monospace; font-size: 12px; background-color: #fff; padding: 5px; border-radius: 3px;">
                            ${Object.entries(error.row).map(([key, value]) => `${key}: ${value}`).join('<br>')}
                        </div>` : ''}
                </div>
            `).join('')}
        `;

        errorDetailsContent.innerHTML = errorDetailsHTML;
    }

    // Close error details modal
    const errorDetailsClose = document.querySelector('#errorDetailsModal .close');
    if (errorDetailsClose) {
        errorDetailsClose.onclick = function() {
            errorDetailsModal.style.display = 'none';
        }
    }
});

// Image Change Functionality (delegated click handler)
function changeProductImage(productId) {
    const fileInput = document.getElementById('imageFileInput');
    fileInput.onchange = function(e) {
        const file = e.target.files[0];
        if (file) {
            // Validate image file
            if (!file.type.startsWith('image/')) {
                alert('Yalnız şəkil faylları qəbul edilir.');
                return;
            }

            // Create FormData and send request
            const formData = new FormData();
            formData.append('product_id', productId);
            formData.append('image', file);
            formData.append('csrfmiddlewaretoken', document.querySelector('[name="csrfmiddlewaretoken"]').value);

            // Show loading state on button
            const button = document.querySelector(`button[data-product-id="${productId}"]`);
            const originalText = button.textContent;
            button.textContent = 'Yenilənir...';
            button.disabled = true;

            fetch('change-image/', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Update the image in the admin list using the specific ID
                    const imageCell = document.getElementById(`product-image-${productId}`);
                    if (imageCell) {
                        imageCell.src = data.new_image_url;
                        imageCell.style.width = '50px';
                        imageCell.style.height = '50px';
                        imageCell.style.objectFit = 'cover';
                        imageCell.style.borderRadius = '4px';
                    }

                    // Update button text
                    button.textContent = 'Şəkil Dəyişildi!';
                    setTimeout(() => {
                        button.textContent = originalText;
                        button.disabled = false;
                    }, 2000);
                } else {
                    alert('Xəta: ' + data.message);
                    button.textContent = originalText;
                    button.disabled = false;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Xəta baş verdi. Zəhmət olmasa yenidən cəhd edin.');
                button.textContent = originalText;
                button.disabled = false;
            });
        }

        // Reset file input
        fileInput.value = '';
    };

    // Trigger file selection
    fileInput.click();
}

// Delegated listener for change-image buttons
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('change-image-btn')) {
        const productId = e.target.getAttribute('data-product-id');
        changeProductImage(productId);
    }
});

/* End moved JS */