/**
 * ROS2 Wiki 前端应用
 * 米醋电子工作室 - 现代化前端优化
 */

class ROS2WikiApp {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || 'light';
        this.searchCache = new Map();
        this.notificationManager = new NotificationManager();
        this.init();
    }

    init() {
        this.setupTheme();
        this.setupSearch();
        this.setupLazyLoading();
        this.setupSmoothScroll();
        this.setupProgressBar();
        this.setupTooltips();
        this.setupModalManager();
        this.setupKeyboardShortcuts();
        
        console.log('🚀 ROS2 Wiki App 已初始化');
    }

    // 主题管理
    setupTheme() {
        this.applyTheme(this.currentTheme);
        
        // 主题切换按钮
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        }
    }

    toggleTheme() {
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(this.currentTheme);
        localStorage.setItem('theme', this.currentTheme);
        
        // 动画效果
        document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
        setTimeout(() => {
            document.body.style.transition = '';
        }, 300);
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        
        // 更新主题图标
        const themeIcon = document.querySelector('#themeToggle i');
        if (themeIcon) {
            themeIcon.className = theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
        }
    }

    // 搜索功能
    setupSearch() {
        const searchInput = document.getElementById('searchInput');
        const searchSuggestions = document.getElementById('searchSuggestions');
        
        if (searchInput) {
            let debounceTimer;
            
            searchInput.addEventListener('input', (e) => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    this.handleSearch(e.target.value, searchSuggestions);
                }, 300);
            });
            
            // 搜索建议点击
            if (searchSuggestions) {
                searchSuggestions.addEventListener('click', (e) => {
                    if (e.target.classList.contains('suggestion-item')) {
                        searchInput.value = e.target.textContent;
                        searchSuggestions.style.display = 'none';
                        this.performSearch(e.target.textContent);
                    }
                });
            }
        }
    }

    async handleSearch(query, suggestionsContainer) {
        if (!query.trim()) {
            if (suggestionsContainer) {
                suggestionsContainer.style.display = 'none';
            }
            return;
        }

        // 检查缓存
        if (this.searchCache.has(query)) {
            this.displaySuggestions(this.searchCache.get(query), suggestionsContainer);
            return;
        }

        try {
            const response = await fetch(`/api/search/suggestions?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.suggestions) {
                this.searchCache.set(query, data.suggestions);
                this.displaySuggestions(data.suggestions, suggestionsContainer);
            }
        } catch (error) {
            console.error('搜索建议获取失败:', error);
        }
    }

    displaySuggestions(suggestions, container) {
        if (!container) return;
        
        if (suggestions.length === 0) {
            container.style.display = 'none';
            return;
        }

        container.innerHTML = suggestions.map(suggestion => 
            `<div class="suggestion-item p-2 border-bottom">${suggestion}</div>`
        ).join('');
        
        container.style.display = 'block';
    }

    performSearch(query) {
        window.location.href = `/search?q=${encodeURIComponent(query)}`;
    }

    // 图片懒加载
    setupLazyLoading() {
        const images = document.querySelectorAll('img[data-src]');
        
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        img.classList.add('lazy-loaded');
                        imageObserver.unobserve(img);
                    }
                });
            });

            images.forEach(img => {
                img.classList.add('lazy');
                imageObserver.observe(img);
            });
        } else {
            // 回退方案
            images.forEach(img => {
                img.src = img.dataset.src;
            });
        }
    }

    // 平滑滚动
    setupSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    // 进度条
    setupProgressBar() {
        const progressBar = document.getElementById('readingProgress');
        
        if (progressBar) {
            window.addEventListener('scroll', () => {
                const windowHeight = window.innerHeight;
                const documentHeight = document.documentElement.scrollHeight - windowHeight;
                const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                const progress = (scrollTop / documentHeight) * 100;
                
                progressBar.style.width = Math.min(progress, 100) + '%';
            });
        }
    }

    // 工具提示
    setupTooltips() {
        const tooltips = document.querySelectorAll('[data-tooltip]');
        
        tooltips.forEach(element => {
            element.addEventListener('mouseenter', (e) => {
                this.showTooltip(e.target, e.target.dataset.tooltip);
            });
            
            element.addEventListener('mouseleave', () => {
                this.hideTooltip();
            });
        });
    }

    showTooltip(element, text) {
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip-popup';
        tooltip.textContent = text;
        tooltip.id = 'dynamic-tooltip';
        
        document.body.appendChild(tooltip);
        
        const rect = element.getBoundingClientRect();
        tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
        tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + 'px';
        
        // 动画显示
        requestAnimationFrame(() => {
            tooltip.style.opacity = '1';
            tooltip.style.transform = 'translateY(0)';
        });
    }

    hideTooltip() {
        const tooltip = document.getElementById('dynamic-tooltip');
        if (tooltip) {
            tooltip.remove();
        }
    }

    // 模态框管理
    setupModalManager() {
        // 关闭按钮
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-close') || 
                e.target.classList.contains('modal-overlay')) {
                this.closeModal();
            }
        });

        // ESC键关闭
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
    }

    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'flex';
            modal.classList.add('modal-show');
            document.body.style.overflow = 'hidden';
        }
    }

    closeModal() {
        const modals = document.querySelectorAll('.modal.modal-show');
        modals.forEach(modal => {
            modal.classList.remove('modal-show');
            setTimeout(() => {
                modal.style.display = 'none';
            }, 300);
        });
        document.body.style.overflow = '';
    }

    // 键盘快捷键
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+K 或 Cmd+K 聚焦搜索
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.getElementById('searchInput');
                if (searchInput) {
                    searchInput.focus();
                }
            }
            
            // Ctrl+/ 或 Cmd+/ 显示快捷键帮助
            if ((e.ctrlKey || e.metaKey) && e.key === '/') {
                e.preventDefault();
                this.openModal('shortcutsModal');
            }
        });
    }

    // 通知系统
    showNotification(message, type = 'info', duration = 3000) {
        this.notificationManager.show(message, type, duration);
    }

    // 加载状态管理
    showLoading(element) {
        element.classList.add('loading');
        element.disabled = true;
    }

    hideLoading(element) {
        element.classList.remove('loading');
        element.disabled = false;
    }

    // API调用封装
    async apiCall(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        };

        const mergedOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, mergedOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API调用失败:', error);
            this.showNotification('请求失败，请稍后重试', 'error');
            throw error;
        }
    }

    // 表单验证
    validateForm(formElement) {
        const inputs = formElement.querySelectorAll('input[required], textarea[required]');
        let isValid = true;
        
        inputs.forEach(input => {
            if (!input.value.trim()) {
                this.showFieldError(input, '此字段为必填项');
                isValid = false;
            } else {
                this.clearFieldError(input);
            }
        });
        
        return isValid;
    }

    showFieldError(input, message) {
        input.classList.add('is-invalid');
        
        // 移除已存在的错误消息
        const existingError = input.parentNode.querySelector('.invalid-feedback');
        if (existingError) {
            existingError.remove();
        }
        
        // 添加新的错误消息
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        input.parentNode.appendChild(errorDiv);
    }

    clearFieldError(input) {
        input.classList.remove('is-invalid');
        const errorDiv = input.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    }
}

// 通知管理器
class NotificationManager {
    constructor() {
        this.container = this.createContainer();
        this.notifications = [];
    }

    createContainer() {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'notification-container';
        document.body.appendChild(container);
        return container;
    }

    show(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${this.getIcon(type)}"></i>
                <span>${message}</span>
            </div>
            <button class="notification-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;

        this.container.appendChild(notification);
        this.notifications.push(notification);

        // 动画显示
        requestAnimationFrame(() => {
            notification.classList.add('notification-show');
        });

        // 自动移除
        if (duration > 0) {
            setTimeout(() => {
                this.remove(notification);
            }, duration);
        }
    }

    remove(notification) {
        notification.classList.remove('notification-show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
            
            const index = this.notifications.indexOf(notification);
            if (index > -1) {
                this.notifications.splice(index, 1);
            }
        }, 300);
    }

    getIcon(type) {
        const icons = {
            'info': 'info-circle',
            'success': 'check-circle',
            'warning': 'exclamation-triangle',
            'error': 'times-circle'
        };
        return icons[type] || 'info-circle';
    }
}

// 性能监控
class PerformanceMonitor {
    constructor() {
        this.metrics = {};
        this.init();
    }

    init() {
        if ('performance' in window) {
            this.measurePageLoad();
            this.measureUserInteraction();
        }
    }

    measurePageLoad() {
        window.addEventListener('load', () => {
            const perfData = performance.getEntriesByType('navigation')[0];
            this.metrics.pageLoad = {
                dns: perfData.domainLookupEnd - perfData.domainLookupStart,
                tcp: perfData.connectEnd - perfData.connectStart,
                request: perfData.responseStart - perfData.requestStart,
                response: perfData.responseEnd - perfData.responseStart,
                dom: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
                total: perfData.loadEventEnd - perfData.navigationStart
            };
            
            console.log('📊 页面加载性能:', this.metrics.pageLoad);
        });
    }

    measureUserInteraction() {
        let interactionCount = 0;
        
        ['click', 'keydown', 'scroll'].forEach(eventType => {
            document.addEventListener(eventType, () => {
                interactionCount++;
            });
        });

        // 每30秒报告一次交互数据
        setInterval(() => {
            if (interactionCount > 0) {
                console.log(`📈 用户交互: ${interactionCount} 次`);
                interactionCount = 0;
            }
        }, 30000);
    }

    getMetrics() {
        return this.metrics;
    }
}

// 服务工作者（PWA支持）
class ServiceWorkerManager {
    constructor() {
        this.init();
    }

    init() {
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                this.registerServiceWorker();
            });
        }
    }

    async registerServiceWorker() {
        try {
            const registration = await navigator.serviceWorker.register('/sw.js');
            console.log('✅ Service Worker 注册成功:', registration);
            
            // 检查更新
            registration.addEventListener('updatefound', () => {
                console.log('🔄 Service Worker 更新可用');
                this.showUpdateNotification();
            });
        } catch (error) {
            console.error('❌ Service Worker 注册失败:', error);
        }
    }

    showUpdateNotification() {
        const app = window.ros2WikiApp;
        if (app) {
            app.showNotification('应用有新版本可用，刷新页面以更新', 'info', 5000);
        }
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.ros2WikiApp = new ROS2WikiApp();
    window.performanceMonitor = new PerformanceMonitor();
    window.serviceWorkerManager = new ServiceWorkerManager();
});

// 导出给其他模块使用
window.ROS2WikiApp = ROS2WikiApp;
window.NotificationManager = NotificationManager;