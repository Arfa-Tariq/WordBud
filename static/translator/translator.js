/**
 * Translator JavaScript - WordBud
 * Handles translation interface interactions and AJAX requests
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const sourceText = document.getElementById('sourceText');
    const targetText = document.getElementById('targetText');
    const sourceLang = document.getElementById('sourceLang');
    const targetLang = document.getElementById('targetLang');
    const translateBtn = document.getElementById('translateBtn');
    const clearBtn = document.getElementById('clearBtn');
    const copyBtn = document.getElementById('copyBtn');
    const swapBtn = document.getElementById('swapBtn');
    const detectBtn = document.getElementById('detectBtn');
    const charCount = document.getElementById('charCount');
    const translationInfo = document.getElementById('translationInfo');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const errorMessage = document.getElementById('errorMessage');
    const successMessage = document.getElementById('successMessage');
    const recentTranslations = document.getElementById('recentTranslations');
    const recentList = document.getElementById('recentList');
    const clearHistoryBtn = document.getElementById('clearHistoryBtn');
    
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                      getCookie('csrftoken');
    
    // State
    let recentHistory = loadHistory();
    updateRecentDisplay();
    
    // Event Listeners
    sourceText.addEventListener('input', handleSourceInput);
    translateBtn.addEventListener('click', performTranslation);
    clearBtn.addEventListener('click', clearSource);
    copyBtn.addEventListener('click', copyTranslation);
    swapBtn.addEventListener('click', swapLanguages);
    detectBtn.addEventListener('click', detectLanguage);
    clearHistoryBtn.addEventListener('click', clearHistory);
    
    // Enter to translate (with Ctrl/Cmd)
    sourceText.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            if (!translateBtn.disabled) {
                performTranslation();
            }
        }
    });
    
    /**
     * Handle source text input
     */
    function handleSourceInput() {
        const text = sourceText.value;
        const length = text.length;
        
        // Update character count
        charCount.textContent = `${length} / 5000`;
        
        // Enable/disable translate button
        translateBtn.disabled = length === 0;
        
        // Warning color for character limit
        if (length > 4500) {
            charCount.style.color = '#e74c3c';
        } else if (length > 4000) {
            charCount.style.color = '#f39c12';
        } else {
            charCount.style.color = '#7f8c8d';
        }
    }
    
    /**
     * Perform translation via AJAX
     */
    function performTranslation() {
        const text = sourceText.value.trim();
        const target = targetLang.value;
        const source = sourceLang.value;
        
        if (!text) {
            showError('Please enter text to translate');
            return;
        }
        
        // Show loading state
        setLoadingState(true);
        hideMessages();
        
        // Prepare form data
        const formData = new FormData();
        formData.append('text', text);
        formData.append('target_lang', target);
        formData.append('source_lang', source);
        
        // Send AJAX request
        fetch('/translator/ajax/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            setLoadingState(false);
            
            if (data.success) {
                // Display translation
                targetText.innerHTML = `<div style="color: #2c3e50; line-height: 1.6;">${escapeHtml(data.translated_text)}</div>`;
                
                // Update info
                translationInfo.textContent = `Translated from ${data.source_lang_name} to ${data.target_lang_name}`;
                
                // Enable copy button
                copyBtn.disabled = false;
                
                // Update source language if auto-detected
                if (source === 'auto' && data.source_lang) {
                    sourceLang.value = data.source_lang;
                }
                
                // Add to history
                addToHistory({
                    original: text,
                    translated: data.translated_text,
                    sourceLang: data.source_lang_name,
                    targetLang: data.target_lang_name,
                    timestamp: new Date().toISOString()
                });
                
                showSuccess('Translation completed!');
            } else {
                showError(data.error || 'Translation failed');
            }
        })
        .catch(error => {
            setLoadingState(false);
            showError('Network error. Please check your connection.');
            console.error('Translation error:', error);
        });
    }
    
    /**
     * Detect language of source text
     */
    function detectLanguage() {
        const text = sourceText.value.trim();
        
        if (!text) {
            showError('Please enter text to detect language');
            return;
        }
        
        setLoadingState(true);
        hideMessages();
        
        const formData = new FormData();
        formData.append('text', text);
        
        fetch('/translator/detect/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            setLoadingState(false);
            
            if (data.success) {
                sourceLang.value = data.detected_lang;
                showSuccess(`Detected language: ${data.language_name}`);
            } else {
                showError(data.error || 'Language detection failed');
            }
        })
        .catch(error => {
            setLoadingState(false);
            showError('Network error. Please try again.');
            console.error('Detection error:', error);
        });
    }
    
    /**
     * Clear source text
     */
    function clearSource() {
        sourceText.value = '';
        handleSourceInput();
        sourceText.focus();
    }
    
    /**
     * Copy translation to clipboard
     */
    function copyTranslation() {
        const text = targetText.textContent.trim();
        
        if (!text) return;
        
        // Modern clipboard API
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text)
                .then(() => {
                    showSuccess('Translation copied to clipboard!');
                    
                    // Visual feedback
                    const originalText = copyBtn.innerHTML;
                    copyBtn.innerHTML = '✓ Copied';
                    setTimeout(() => {
                        copyBtn.innerHTML = originalText;
                    }, 2000);
                })
                .catch(err => {
                    console.error('Copy failed:', err);
                    fallbackCopy(text);
                });
        } else {
            fallbackCopy(text);
        }
    }
    
    /**
     * Fallback copy method for older browsers
     */
    function fallbackCopy(text) {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        
        try {
            document.execCommand('copy');
            showSuccess('Translation copied to clipboard!');
        } catch (err) {
            showError('Failed to copy. Please copy manually.');
        }
        
        document.body.removeChild(textarea);
    }
    
    /**
     * Swap source and target languages
     */
    function swapLanguages() {
        // Can't swap if source is auto
        if (sourceLang.value === 'auto') {
            showError('Cannot swap when source is set to auto-detect');
            return;
        }
        
        // Swap language selections
        const tempLang = sourceLang.value;
        sourceLang.value = targetLang.value;
        targetLang.value = tempLang;
        
        // Swap text content if translation exists
        const targetContent = targetText.textContent.trim();
        if (targetContent && targetContent !== 'Translation will appear here...') {
            sourceText.value = targetContent;
            targetText.innerHTML = '<span class="placeholder-text">Translation will appear here...</span>';
            translationInfo.textContent = '';
            copyBtn.disabled = true;
            handleSourceInput();
        }
        
        // Add animation effect
        swapBtn.style.transform = 'rotate(180deg) scale(1.1)';
        setTimeout(() => {
            swapBtn.style.transform = '';
        }, 300);
    }
    
    /**
     * Add translation to history
     */
    function addToHistory(item) {
        // Add to beginning of array
        recentHistory.unshift(item);
        
        // Keep only last 5 translations
        if (recentHistory.length > 5) {
            recentHistory = recentHistory.slice(0, 5);
        }
        
        // Save to localStorage
        saveHistory();
        updateRecentDisplay();
    }
    
    /**
     * Update recent translations display
     */
    function updateRecentDisplay() {
        if (recentHistory.length === 0) {
            recentTranslations.style.display = 'none';
            return;
        }
        
        recentTranslations.style.display = 'block';
        recentList.innerHTML = '';
        
        recentHistory.forEach((item, index) => {
            const itemEl = document.createElement('div');
            itemEl.className = 'recent-item';
            itemEl.style.animationDelay = `${index * 0.05}s`;
            
            const time = new Date(item.timestamp);
            const timeStr = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            
            itemEl.innerHTML = `
                <div class="recent-item-header">
                    <span>${item.sourceLang} → ${item.targetLang}</span>
                    <span>${timeStr}</span>
                </div>
                <div class="recent-item-text">${escapeHtml(truncate(item.original, 80))}</div>
                <div class="recent-item-translation">${escapeHtml(truncate(item.translated, 80))}</div>
            `;
            
            // Click to restore
            itemEl.addEventListener('click', () => {
                sourceText.value = item.original;
                targetText.innerHTML = `<div style="color: #2c3e50; line-height: 1.6;">${escapeHtml(item.translated)}</div>`;
                copyBtn.disabled = false;
                handleSourceInput();
            });
            
            recentList.appendChild(itemEl);
        });
    }
    
    /**
     * Clear translation history
     */
    function clearHistory() {
        if (confirm('Are you sure you want to clear translation history?')) {
            recentHistory = [];
            saveHistory();
            updateRecentDisplay();
            showSuccess('Translation history cleared');
        }
    }
    
    /**
     * Save history to localStorage
     */
    function saveHistory() {
        try {
            localStorage.setItem('translationHistory', JSON.stringify(recentHistory));
        } catch (e) {
            console.warn('Could not save history:', e);
        }
    }
    
    /**
     * Load history from localStorage
     */
    function loadHistory() {
        try {
            const saved = localStorage.getItem('translationHistory');
            return saved ? JSON.parse(saved) : [];
        } catch (e) {
            console.warn('Could not load history:', e);
            return [];
        }
    }
    
    /**
     * Show/hide loading state
     */
    function setLoadingState(loading) {
        if (loading) {
            loadingSpinner.style.display = 'flex';
            translateBtn.disabled = true;
            detectBtn.disabled = true;
        } else {
            loadingSpinner.style.display = 'none';
            translateBtn.disabled = sourceText.value.trim().length === 0;
            detectBtn.disabled = false;
        }
    }
    
    /**
     * Show error message
     */
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            errorMessage.style.display = 'none';
        }, 5000);
    }
    
    /**
     * Show success message
     */
    function showSuccess(message) {
        successMessage.textContent = message;
        successMessage.style.display = 'block';
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            successMessage.style.display = 'none';
        }, 3000);
    }
    
    /**
     * Hide all messages
     */
    function hideMessages() {
        errorMessage.style.display = 'none';
        successMessage.style.display = 'none';
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Truncate text with ellipsis
     */
    function truncate(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }
    
    /**
     * Get CSRF cookie
     */
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
});