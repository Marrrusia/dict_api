class TranslationApp {
    constructor() {
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        document.getElementById('translateForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleTranslation();
        });

        document.getElementById('loadHistoryBtn').addEventListener('click', () => {
            this.loadHistory();
        });
    }

    async handleTranslation() {
        const formData = new FormData(document.getElementById('translateForm'));
        const data = {
            text: formData.get('text'),
            source_lang: formData.get('source_lang'),
            target_lang: formData.get('target_lang'),
            adaptation_type: formData.get('adaptation_type') || null
        };

        this.showLoading('translateBtn', 'Перевожу...');
        this.hideResult();
        this.hideError();

        try {
            const response = await fetch('/translate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                this.showResult(result);
            } else {
                this.showError(result.detail || 'Ошибка перевода');
            }
        } catch (error) {
            this.showError('Сетевая ошибка: ' + error.message);
        } finally {
            this.hideLoading('translateBtn', 'Перевести');
        }
    }

    async loadHistory() {
        this.showLoading('loadHistoryBtn', 'Загружаю...');

        try {
            const response = await fetch('/history/translations?limit=10');
            const history = await response.json();

            if (response.ok) {
                this.displayHistory(history);
            } else {
                this.showError('Не удалось загрузить историю');
            }
        } catch (error) {
            this.showError('Ошибка загрузки: ' + error.message);
        } finally {
            this.hideLoading('loadHistoryBtn', 'Загрузить историю');
        }
    }

    showResult(result) {
        document.getElementById('translatedText').textContent = result.translated_text;
        document.getElementById('translationId').textContent = result.id;
        document.getElementById('result').style.display = 'block';
        document.getElementById('result').scrollIntoView({ behavior: 'smooth' });
    }

    showError(message) {
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('error').style.display = 'block';
    }

    hideResult() {
        document.getElementById('result').style.display = 'none';
    }

    hideError() {
        document.getElementById('error').style.display = 'none';
    }

    showLoading(buttonId, text) {
        const button = document.getElementById(buttonId);
        button.innerHTML = `<div class="spinner"></div>${text}`;
        button.disabled = true;
    }

    hideLoading(buttonId, text) {
        const button = document.getElementById(buttonId);
        button.textContent = text;
        button.disabled = false;
    }

    displayHistory(history) {
        const historyContainer = document.getElementById('history');

        if (!Array.isArray(history) || history.length === 0) {
            historyContainer.innerHTML = '<p>История переводов пуста.</p>';
            return;
        }

        historyContainer.innerHTML = history.map(item => `
            <div class="history-item">
                <div class="history-original">
                    <strong>Оригинал (${item.source_lang}):</strong> ${this.escapeHtml(item.original_text)}
                </div>
                <div class="history-translated">
                    <strong>Перевод (${item.target_lang}):</strong> ${this.escapeHtml(item.translated_text)}
                </div>
                <div class="history-meta">
                    <span>${new Date(item.created_at).toLocaleString('ru-RU')}</span>
                </div>
            </div>
        `).join('');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new TranslationApp();
});