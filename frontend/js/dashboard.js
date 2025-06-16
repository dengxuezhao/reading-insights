/**
 * ReadingInsights - 阅读数据分析平台仪表盘模块
 */

class KOReaderDashboard {
    constructor() {
        // 自动检测当前访问地址，构建正确的API基础URL
        this.baseURL = `${window.location.protocol}//${window.location.host}/api/v1`;
        
        // 确保baseURL使用HTTPS和正确的域名
        this.baseURL = this.baseURL
            .replace('http://', 'https://')
            .replace('152.70.115.148', 'koreader.xuezhao.space');
            
        console.log('🔧 初始化baseURL:', this.baseURL);
        
        this.charts = {};
        this.currentUser = null;
        this.authToken = null;
        
        // 状态标记
        this.mixedContentWarningShown = false;
        
        this.init();
    }

    /**
     * 加载认证令牌
     */
    async loadAuthToken() {
        console.log('🔑 开始加载认证令牌...');
        try {
            // 优先尝试从默认用户API获取令牌
            console.log('🌐 尝试从默认用户API获取令牌...');
            const defaultToken = await this.getDefaultUserToken();
            
            if (defaultToken) {
                this.authToken = defaultToken.access_token;
                this.currentUser = {
                    username: defaultToken.username,
                    isDefault: defaultToken.is_default
                };
                console.log('✅ 默认用户令牌获取成功:', defaultToken.username);
                console.log('🔑 令牌前缀:', defaultToken.access_token.substring(0, 20) + '...');
                return;
            }
            
            // 回退到localStorage
            console.log('📱 尝试从localStorage获取令牌...');
            let token = localStorage.getItem('auth_token');
            console.log('📱 localStorage中的令牌:', token ? '存在' : '不存在');
            
            if (!token) {
                // 最后尝试从test_token.txt获取（仅用于测试）
                console.log('📄 尝试从test_token.txt获取令牌...');
                const response = await fetch('/test_token.txt');
                console.log('📄 test_token.txt响应状态:', response.status, response.statusText);
                
                if (response.ok) {
                    token = await response.text();
                    token = token.trim();
                    console.log('📄 从文件获取的令牌长度:', token.length);
                    localStorage.setItem('auth_token', token);
                    console.log('💾 令牌已保存到localStorage');
                }
            }
            
            if (token) {
                this.authToken = token;
                console.log('✅ 认证令牌已加载，长度:', token.length);
                console.log('🔑 令牌前缀:', token.substring(0, 20) + '...');
            } else {
                console.warn('⚠️ 未找到认证令牌，将使用模拟数据');
            }
        } catch (error) {
            console.error('❌ 加载认证令牌失败:', error);
            console.warn('⚠️ 将使用模拟数据');
        }
    }

    /**
     * 获取默认用户令牌
     */
    async getDefaultUserToken() {
        try {
            const response = await fetch(`${this.baseURL}/public/default-token`);
            if (response.ok) {
                const data = await response.json();
                console.log('🎯 默认用户API响应成功');
                return data;
            } else {
                console.warn('⚠️ 默认用户API响应失败:', response.status);
                return null;
            }
        } catch (error) {
            console.warn('⚠️ 默认用户API请求失败:', error.message);
            return null;
        }
    }

    /**
     * 初始化应用
     */
    async init() {
        this.setupEventListeners();
        
        // 确保认证令牌加载完成
        await this.loadAuthToken();
        
        // 启动时立即同步一次数据 - 已禁用自动同步，避免页面刷新时频繁同步
        // await this.performStartupSync();
        
        await this.loadData();
        this.setupCharts();
    }

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        // 标签页切换
        const tabButtons = document.querySelectorAll('.tab-button');
        tabButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                this.switchTab(e.target.closest('.tab-button').dataset.tab);
            });
        });

        // 窗口大小改变时重置图表大小
        window.addEventListener('resize', () => {
            this.resizeCharts();
        });
    }

    /**
     * 切换标签页
     */
    switchTab(tabName) {
        // 移除所有激活状态
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });

        // 激活选中的标签页
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(`${tabName}-tab`).classList.add('active');

        // 如果切换到数据概览页面，重新调整图表大小
        if (tabName === 'dashboard') {
            setTimeout(() => this.resizeCharts(), 100);
        }
    }

    /**
     * 显示加载状态
     */
    showLoading() {
        document.getElementById('loading-overlay').classList.remove('hidden');
    }

    /**
     * 隐藏加载状态
     */
    hideLoading() {
        document.getElementById('loading-overlay').classList.add('hidden');
    }

    /**
     * API 请求封装
     */
    async apiRequest(endpoint, options = {}) {
        let url = `${this.baseURL}${endpoint}`;
        
        // 临时修正：确保所有请求都使用HTTPS协议和正确域名
        if (url.includes('152.70.115.148') || url.startsWith('http://')) {
            const correctedUrl = url
                .replace('http://', 'https://')
                .replace('152.70.115.148', 'koreader.xuezhao.space');
            console.log('🔧 URL协议修正:', url, '->', correctedUrl);
            url = correctedUrl;
        }
        
        console.log('🌐 发起API请求:', url);
        
        try {
            const config = {
                headers: {
                    'Content-Type': 'application/json',
                    ...(this.authToken && { 'Authorization': `Bearer ${this.authToken}` })
                },
                redirect: 'manual', // 手动处理重定向
                ...options
            };
            
            console.log('📋 请求配置:', {
                url,
                method: config.method || 'GET',
                hasAuth: !!this.authToken,
                headers: Object.keys(config.headers),
                redirect: config.redirect
            });

            const response = await fetch(url, config);
            console.log('📡 API响应状态:', response.status, response.statusText);
            
            // 处理重定向响应 (3xx状态码)
            if (response.status >= 300 && response.status < 400) {
                const location = response.headers.get('Location');
                console.log('🔄 检测到重定向:', location);
                
                if (location) {
                    // 修正重定向URL为HTTPS
                    let correctedLocation = location;
                    if (location.includes('152.70.115.148') || location.startsWith('http://')) {
                        correctedLocation = location
                            .replace('http://', 'https://')
                            .replace('152.70.115.148', 'koreader.xuezhao.space');
                        console.log('🔧 重定向URL修正:', location, '->', correctedLocation);
                    }
                    
                    // 重新发起请求到修正后的URL
                    console.log('🔄 重新请求修正后的URL:', correctedLocation);
                    const redirectConfig = { ...config };
                    delete redirectConfig.redirect; // 使用默认重定向处理
                    
                    const redirectResponse = await fetch(correctedLocation, redirectConfig);
                    console.log('📡 重定向请求响应状态:', redirectResponse.status, redirectResponse.statusText);
                    
                    if (!redirectResponse.ok) {
                        const errorText = await redirectResponse.text();
                        console.error('❌ 重定向请求失败:', redirectResponse.status, errorText);
                        throw new Error(`HTTP error! status: ${redirectResponse.status}, message: ${errorText}`);
                    }
                    
                    const data = await redirectResponse.json();
                    console.log('✅ 重定向请求成功:', endpoint, '数据大小:', JSON.stringify(data).length);
                    return data;
                } else {
                    throw new Error(`重定向响应缺少Location头: ${response.status}`);
                }
            }
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('❌ API请求失败:', response.status, errorText);
                throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
            }
            
            const data = await response.json();
            console.log('✅ API请求成功:', endpoint, '数据大小:', JSON.stringify(data).length);
            return data;
        } catch (error) {
            console.error('❌ API请求异常:', endpoint, error);
            
            // 如果是Mixed Content错误，尝试修正URL后重试
            if (error.message && error.message.includes('Mixed Content')) {
                console.log('🔧 检测到Mixed Content错误，尝试修正URL重试...');
                
                // 显示Mixed Content警告
                this.showMixedContentWarning();
                
                // 尝试修正URL并重试
                const retryUrl = url
                    .replace('http://', 'https://')
                    .replace('152.70.115.148', 'koreader.xuezhao.space');
                
                if (retryUrl !== url) {
                    console.log('🔄 重试修正后的URL:', retryUrl);
                    try {
                        const retryConfig = { ...options };
                        delete retryConfig.redirect;
                        
                        const retryResponse = await fetch(retryUrl, {
                            headers: {
                                'Content-Type': 'application/json',
                                ...(this.authToken && { 'Authorization': `Bearer ${this.authToken}` })
                            },
                            ...retryConfig
                        });
                        
                        if (retryResponse.ok) {
                            const data = await retryResponse.json();
                            console.log('✅ 重试请求成功:', endpoint, '数据大小:', JSON.stringify(data).length);
                            return data;
                        }
                    } catch (retryError) {
                        console.error('❌ 重试请求也失败:', retryError);
                    }
                }
            }
            
            return null;
        }
    }

    /**
     * 启动时执行数据同步
     */
    async performStartupSync() {
        console.log('🔄 启动时数据同步开始...');
        
        if (!this.authToken) {
            console.warn('⚠️ 没有认证令牌，跳过启动同步');
            return;
        }

        try {
            // 显示同步提示
            this.showSyncStatus('正在同步最新数据...', 'loading');
            
            let syncResult;
            
            // 如果是默认用户，使用公开同步API
            if (this.currentUser && this.currentUser.isDefault) {
                console.log('🔄 使用默认用户同步API...');
                syncResult = await this.apiRequest('/public/sync-data', {
                    method: 'POST'
                });
            } else {
                console.log('🔄 使用认证用户同步API...');
                syncResult = await this.apiRequest('/sync/manual', {
                    method: 'POST'
                });
            }
            
            if (syncResult && syncResult.success) {
                const { books_synced = 0, sessions_synced = 0 } = syncResult;
                this.showSyncStatus(
                    `数据同步完成！同步了 ${books_synced} 本书籍，${sessions_synced} 条阅读记录`, 
                    'success'
                );
                console.log('✅ 启动同步成功:', syncResult);
            } else {
                this.showSyncStatus('数据同步完成，但可能没有新数据', 'info');
                console.log('ℹ️ 启动同步完成，无新数据或同步失败');
            }
            
        } catch (error) {
            console.error('❌ 启动同步失败:', error);
            this.showSyncStatus('数据同步失败，将使用现有数据', 'warning');
        }
        
        // 3秒后隐藏同步状态
        setTimeout(() => {
            this.hideSyncStatus();
        }, 3000);
    }

    /**
     * 显示同步状态
     */
    showSyncStatus(message, type = 'info') {
        // 移除已存在的同步状态
        const existingStatus = document.getElementById('sync-status');
        if (existingStatus) {
            existingStatus.remove();
        }
        
        // 创建同步状态元素
        const statusDiv = document.createElement('div');
        statusDiv.id = 'sync-status';
        statusDiv.className = `sync-status sync-status-${type}`;
        
        let icon = '📊';
        if (type === 'loading') icon = '🔄';
        else if (type === 'success') icon = '✅';
        else if (type === 'warning') icon = '⚠️';
        else if (type === 'error') icon = '❌';
        
        statusDiv.innerHTML = `
            <span class="sync-icon">${icon}</span>
            <span class="sync-message">${message}</span>
        `;
        
        // 添加到页面
        document.body.appendChild(statusDiv);
        
        // 添加动画
        setTimeout(() => {
            statusDiv.classList.add('show');
        }, 100);
    }

    /**
     * 隐藏同步状态
     */
    hideSyncStatus() {
        const statusDiv = document.getElementById('sync-status');
        if (statusDiv) {
            statusDiv.classList.add('hide');
            setTimeout(() => {
                statusDiv.remove();
            }, 300);
        }
    }

    /**
     * 显示Mixed Content警告（仅显示一次）
     */
    showMixedContentWarning() {
        // 检查是否已经显示过警告
        if (this.mixedContentWarningShown) {
            return;
        }
        this.mixedContentWarningShown = true;

        console.warn('⚠️ 检测到Mixed Content问题，建议修复反向代理配置');
        
        // 创建警告提示
        const warningDiv = document.createElement('div');
        warningDiv.id = 'mixed-content-warning';
        warningDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 15px;
            max-width: 400px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            z-index: 10000;
            font-size: 14px;
            line-height: 1.5;
            color: #856404;
        `;
        
        warningDiv.innerHTML = `
            <div style="margin-bottom: 10px;">
                <strong>⚠️ Mixed Content 安全警告</strong>
            </div>
            <div style="margin-bottom: 10px;">
                检测到API请求从HTTPS重定向到HTTP，浏览器已阻止该请求。
            </div>
            <div style="margin-bottom: 10px; font-size: 12px;">
                <strong>建议修复反向代理配置：</strong><br>
                1. 将proxy_pass改为HTTPS<br>
                2. 修正proxy_set_header Host为域名
            </div>
            <button onclick="this.parentElement.remove()" style="
                background: #ffc107;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
                cursor: pointer;
                color: #856404;
                font-size: 12px;
            ">关闭</button>
        `;
        
        document.body.appendChild(warningDiv);
        
        // 10秒后自动隐藏
        setTimeout(() => {
            if (warningDiv && warningDiv.parentNode) {
                warningDiv.remove();
            }
        }, 10000);
    }

    /**
     * 加载所有数据
     */
    async loadData() {
        this.showLoading();
        
        try {
            if (this.authToken) {
                // 尝试使用真实API
                console.log('📡 正在从API获取真实数据...');
                await this.loadRealData();
            } else {
                // 使用模拟数据
                console.log('🎭 使用模拟数据...');
                this.loadMockData();
            }
            
        } catch (error) {
            console.error('数据加载失败:', error);
            console.log('🎭 回退到模拟数据...');
            this.loadMockData();
        } finally {
            this.hideLoading();
        }
    }

    /**
     * 加载真实API数据
     */
    async loadRealData() {
        // 并行获取所有需要的数据
        const [summaryData, calendarData, trendsData, weeklyData, booksData] = await Promise.all([
            this.apiRequest('/dashboard/summary'),
            this.apiRequest('/dashboard/calendar'),
            this.apiRequest('/statistics/trends?days=30'),
            this.apiRequest('/statistics/weekly'),
            this.apiRequest('/books?page=1&page_size=20')
        ]);

        if (!summaryData || !calendarData || !trendsData) {
            throw new Error('API数据获取失败');
        }

        // 详细日志输出书籍API的返回数据
        console.log('📚 书籍API返回数据:', booksData);
        console.log('📚 书籍数据类型:', typeof booksData);
        console.log('📚 是否有books字段:', booksData && booksData.books);
        if (booksData && booksData.books) {
            console.log('📚 书籍数量:', booksData.books.length);
            console.log('📚 第一本书示例:', booksData.books[0]);
        }

        // 转换API数据为前端格式
        this.chartData = {
            summary: summaryData,
            calendar: this.convertCalendarData(calendarData),
            trends: this.convertTrendsData(trendsData),
            hourlyData: this.generateHourlyData(), // 暂时使用模拟数据
            progressData: this.calculateBookProgress(booksData),
            readingList: this.convertReadingListData(booksData),
            weeklyData: weeklyData,
            monthlyData: calendarData // 使用日历数据作为月度数据的基础
        };

        // 更新统计卡片
        this.updateStatsCards(this.chartData.summary);
        
        console.log('✅ 真实数据加载成功');
        console.log('📚 最终书单数据:', this.chartData.readingList);
    }

    /**
     * 加载模拟数据（原有逻辑）
     */
    loadMockData() {
        // 模拟数据 - 在实际环境中这些将从API获取
        const mockData = this.generateMockData();
        
        // 更新统计卡片
        this.updateStatsCards(mockData.summary);
        
        // 设置图表数据
        this.chartData = mockData;
    }

    /**
     * 转换日历数据格式
     */
    convertCalendarData(apiData) {
        // API返回格式: {year: 2025, data: [{date: "2025-01-01", reading_time: 3600}, ...]}
        // 转换为ECharts格式: [["2025-01-01", 3600], ...]
        if (apiData && apiData.data) {
            return apiData.data.map(item => [item.date, item.reading_time]); // 保持原始秒数，tooltip中再转换
        }
        return [];
    }

    /**
     * 转换趋势数据格式
     */
    convertTrendsData(apiData) {
        // API返回格式: {period_days: 7, trends: [{date: "2025-01-01", duration: 3600, sessions: 5}, ...]}
        // 转换为前端格式: [{date: "2025-01-01", readingTime: 3600, pages: 25}, ...]
        if (apiData && apiData.trends) {
            return apiData.trends.map(item => ({
                date: item.date,
                readingTime: item.duration, // API返回的已经是秒，不需要转换
                pages: item.sessions || 0 // 暂时使用会话数，后续需要API返回真实页数
            }));
        }
        return [];
    }

    /**
     * 计算书籍完成进度（使用85%阈值）
     */
    calculateBookProgress(booksData) {
        if (!booksData || !booksData.books) {
            // 使用模拟数据的默认值
            console.log('使用模拟数据默认值');
            return {
                completed: 9,
                inProgress: 3
            };
        }

        let completed = 0;
        let inProgress = 0;

        booksData.books.forEach(book => {
            const progress = book.reading_progress || 0;
            
            // 使用85%作为完成阈值
            if (progress >= 85) {
                completed++;
                console.log(`📚 已完成: ${book.title} (${progress}%)`);
            } else if (progress > 0) {
                inProgress++;
                console.log(`📖 进行中: ${book.title} (${progress}%)`);
            }
            // 进度为0的书籍不计入统计
        });

        console.log(`📊 进度统计: 已完成 ${completed} 本，进行中 ${inProgress} 本，总计 ${completed + inProgress} 本`);

        return {
            completed,
            inProgress
        };
    }

    /**
     * 转换书籍列表数据格式
     */
    convertReadingListData(booksData) {
        console.log('🔄 开始转换书籍列表数据...');
        
        if (!booksData) {
            console.warn('⚠️ booksData为空，使用模拟数据');
            return this.generateReadingListData();
        }
        
        if (!booksData.books) {
            console.warn('⚠️ booksData.books字段不存在，booksData结构:', Object.keys(booksData));
            return this.generateReadingListData();
        }
        
        if (!Array.isArray(booksData.books)) {
            console.warn('⚠️ booksData.books不是数组，类型:', typeof booksData.books);
            return this.generateReadingListData();
        }
        
        if (booksData.books.length === 0) {
            console.log('ℹ️ 书籍列表为空，返回空数组');
            return [];
        }
        
        console.log(`✅ 成功获取 ${booksData.books.length} 本书籍，开始转换格式...`);
        
        const convertedBooks = booksData.books.map((book, index) => {
            console.log(`📖 转换第 ${index + 1} 本书:`, book.title);
            
            const progress = book.reading_progress || 0;
            const totalPages = book.total_pages || 0;
            let currentPage = book.read_pages_count || 0;
            
            // 如果当前页数为0但有进度和总页数，从进度计算当前页数
            if (currentPage === 0 && progress > 0 && totalPages > 0) {
                currentPage = Math.round(progress * totalPages / 100);
                console.log(`📄 从进度计算当前页数: ${currentPage}页 (${progress}% × ${totalPages}页)`);
            }
            
            const convertedBook = {
                id: book.id,
                title: book.title,
                author: book.author || '未知作者',
                cover: book.cover_image_url || '/default-book-cover.jpg',
                progress: progress,
                currentPage: currentPage,
                totalPages: totalPages,
                readingTime: book.total_reading_time || 0,
                lastRead: book.last_read_time || new Date().toISOString()
            };
            
            console.log(`✅ 转换完成:`, convertedBook);
            return convertedBook;
        });
        
        console.log('🎉 书籍列表转换完成，返回真实数据');
        return convertedBooks;
    }

    /**
     * 加载真实在读书单
     */
    async loadRealReadingList() {
        try {
            // 这里应该调用书籍列表API，暂时使用模拟数据
            return this.generateReadingListData();
        } catch (error) {
            console.warn('加载书单失败，使用模拟数据:', error);
            return this.generateReadingListData();
        }
    }

    /**
     * 生成阅读列表模拟数据
     */
    generateReadingListData() {
        const books = [
            { id: 1, title: '深度学习实战', author: 'François Chollet', reading_progress: 95, total_pages: 400, read_pages_count: 380, total_reading_time: 18000 },
            { id: 2, title: 'Python编程：从入门到实践', author: 'Eric Matthes', reading_progress: 68, total_pages: 624, read_pages_count: 424, total_reading_time: 25200 },
            { id: 3, title: '算法导论', author: 'Thomas H. Cormen', reading_progress: 23, total_pages: 1292, read_pages_count: 297, total_reading_time: 14400 },
            { id: 4, title: '代码大全', author: 'Steve McConnell', reading_progress: 88, total_pages: 914, read_pages_count: 804, total_reading_time: 32400 },
            { id: 5, title: '机器学习实战', author: 'Peter Harrington', reading_progress: 41, total_pages: 336, read_pages_count: 138, total_reading_time: 12600 },
            { id: 6, title: 'JavaScript高级程序设计', author: 'Nicholas C. Zakas', reading_progress: 92, total_pages: 896, read_pages_count: 824, total_reading_time: 28800 },
            { id: 7, title: '设计模式', author: 'Erich Gamma', reading_progress: 15, total_pages: 395, read_pages_count: 59, total_reading_time: 7200 },
            { id: 8, title: '重构：改善既有代码的设计', author: 'Martin Fowler', reading_progress: 78, total_pages: 431, read_pages_count: 336, total_reading_time: 21600 }
        ];

        return books.map(book => ({
            id: book.id,
            title: book.title,
            author: book.author,
            progress: book.reading_progress,
            currentPage: book.read_pages_count,
            totalPages: book.total_pages,
            readingTime: book.total_reading_time,
            lastRead: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString()
        }));
    }

    /**
     * 生成模拟数据
     */
    generateMockData() {
        const now = new Date();
        const currentYear = now.getFullYear();
        const mockReadingList = this.generateReadingListData();
        
        return {
            summary: {
                total_reading_time: 25680, // 7.13小时
                total_books: mockReadingList.length,
                total_pages_read: 2847,
                reading_streak: 15,
                books_in_progress: 3,
                books_completed: 9,
                favorite_reading_hour: 21
            },
            calendar: this.generateCalendarData(currentYear),
            trends: this.generateTrendsData(30),
            hourlyData: this.generateHourlyData(),
            progressData: this.calculateBookProgress({ books: mockReadingList.map(book => ({ reading_progress: book.progress })) }),
            readingList: mockReadingList
        };
    }

    /**
     * 生成日历热力图数据
     */
    generateCalendarData(year) {
        const data = [];
        const startDate = new Date(year, 0, 1);
        const endDate = new Date(year, 11, 31);
        
        for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
            const dateStr = d.toISOString().split('T')[0];
            // 确保有部分日期有阅读数据，部分为0，形成完整的热力图
            const readingTime = Math.random() > 0.6 ? Math.floor(Math.random() * 7200) : 0;
            
            data.push([dateStr, readingTime]);
        }
        
        return data;
    }

    /**
     * 生成趋势数据
     */
    generateTrendsData(days) {
        const data = [];
        const now = new Date();
        
        for (let i = days - 1; i >= 0; i--) {
            const date = new Date(now);
            date.setDate(date.getDate() - i);
            
            const dateStr = date.toISOString().split('T')[0];
            const readingTime = Math.random() > 0.3 ? Math.floor(Math.random() * 5400) : 0; // 0-1.5小时
            
            data.push({
                date: dateStr,
                readingTime: readingTime,
                pages: readingTime > 0 ? Math.floor(readingTime / 60) : 0
            });
        }
        
        return data;
    }

    /**
     * 生成每小时阅读数据
     */
    generateHourlyData() {
        const data = [];
        const hours = ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11',
                      '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23'];
        
        hours.forEach((hour, index) => {
            let value = 0;
            // 模拟阅读高峰时段
            if (index >= 7 && index <= 9) value = Math.random() * 30 + 10; // 早晨
            else if (index >= 12 && index <= 14) value = Math.random() * 20 + 5; // 午休
            else if (index >= 19 && index <= 23) value = Math.random() * 50 + 20; // 晚上
            else value = Math.random() * 10;
            
            data.push([hour, Math.floor(value)]);
        });
        
        return data;
    }

    /**
     * 生成月度日历数据
     */
    async setupMonthCalendar() {
        const container = document.getElementById('month-calendar');
        if (!container) return;
        
        const now = new Date();
        const currentYear = now.getFullYear();
        const currentMonth = now.getMonth() + 1;
        
        await this.renderMonthCalendar(container, currentYear, currentMonth);
    }
    
    /**
     * 渲染月度日历
     */
    async renderMonthCalendar(container, year, month) {
        // 使用真实数据而非模拟数据
        const calendarData = await this.generateMonthCalendarFromRealData(year, month);
        const today = new Date();
        const isCurrentMonth = year === today.getFullYear() && month === today.getMonth() + 1;
        const todayDate = isCurrentMonth ? today.getDate() : -1;
        
        const monthNames = [
            '一月', '二月', '三月', '四月', '五月', '六月',
            '七月', '八月', '九月', '十月', '十一月', '十二月'
        ];
        
        const weekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
        
        container.innerHTML = `
            <div class="calendar-header">
                <div class="calendar-month">${year}年 ${monthNames[month - 1]}</div>
                <div class="calendar-nav">
                    <button class="calendar-nav-btn" onclick="dashboard.navigateMonth(-1)">‹ 上月</button>
                    <button class="calendar-nav-btn" onclick="dashboard.navigateMonth(1)">下月 ›</button>
                </div>
            </div>
            <div class="calendar-grid">
                ${weekDays.map(day => `<div class="day-header">${day}</div>`).join('')}
                ${this.renderCalendarDays(calendarData, todayDate)}
            </div>
        `;
        
        // 存储当前月份信息
        this.currentCalendarYear = year;
        this.currentCalendarMonth = month;
    }
    
    /**
     * 从真实数据生成月度日历数据
     */
    async generateMonthCalendarFromRealData(year, month) {
        try {
            // 获取详细的日历数据
            const detailedData = await this.apiRequest(`/statistics/calendar/detailed?year=${year}&month=${month}`);
            
            const daysInMonth = new Date(year, month, 0).getDate();
            const firstDay = new Date(year, month - 1, 1).getDay();
            const data = [];
            
            // 创建日期映射
            const dayDataMap = {};
            if (detailedData && detailedData.data) {
                for (const dayInfo of detailedData.data) {
                    const day = new Date(dayInfo.date).getDate();
                    dayDataMap[day] = dayInfo;
                }
            }
            
            for (let day = 1; day <= daysInMonth; day++) {
                const dayInfo = dayDataMap[day];
                
                if (dayInfo && dayInfo.books && dayInfo.books.length > 0) {
                    const books = dayInfo.books.map((book, index) => {
                        const hours = Math.floor(book.reading_time / 3600);
                        const minutes = Math.floor((book.reading_time % 3600) / 60);
                        const timeStr = hours > 0 ? `${hours}h${minutes}m` : `${minutes}m`;
                        
                        return {
                            title: book.title,
                            author: book.author,
                            time: timeStr,
                            timeSeconds: book.reading_time,
                            isContinuous: book.continuous_days > 1,
                            continuousDay: book.continuous_days || 1,
                            isStart: book.is_streak_start || false,
                            isEnd: book.is_streak_end || false,
                            shape: this.getBookShape(book.book_id, index), // 为不同书籍分配形状
                            color: this.getBookColor(book.book_id, index)  // 为不同书籍分配颜色
                        };
                    });
                    
                    data.push({
                        date: day,
                        hasReading: true,
                        readingTime: dayInfo.total_reading_time,
                        books: books
                    });
                } else {
                    data.push({
                        date: day,
                        hasReading: false,
                        readingTime: 0,
                        books: []
                    });
                }
            }
            
            return { data, firstDay, daysInMonth };
        } catch (error) {
            console.error('获取详细日历数据失败:', error);
            // 回退到简单数据
            return this.generateSimpleMonthCalendar(year, month);
        }
    }

    /**
     * 获取书籍形状标识
     */
    getBookShape(bookId, index) {
        const shapes = ['●', '■', '▲', '◆', '⬟', '⬢'];
        return shapes[(bookId || index) % shapes.length];
    }

    /**
     * 获取书籍颜色
     */
    getBookColor(bookId, index) {
        const colors = ['#3b82f6', '#8b5cf6', '#ef4444', '#10b981', '#f59e0b', '#06b6d4'];
        return colors[(bookId || index) % colors.length];
    }

    /**
     * 生成简单月度日历数据（回退方案）
     */
    generateSimpleMonthCalendar(year, month) {
        const daysInMonth = new Date(year, month, 0).getDate();
        const firstDay = new Date(year, month - 1, 1).getDay();
        const data = [];
        
        // 从API数据中获取该月的真实数据
        const monthlyCalendarData = this.chartData?.monthlyData?.data || [];
        
        for (let day = 1; day <= daysInMonth; day++) {
            const dateStr = `${year}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
            const dayData = monthlyCalendarData.find(d => d.date === dateStr);
            
            if (dayData && dayData.reading_time > 0) {
                const hours = Math.floor(dayData.reading_time / 3600);
                const minutes = Math.floor((dayData.reading_time % 3600) / 60);
                const timeStr = hours > 0 ? `${hours}h${minutes}m` : `${minutes}m`;
                
                data.push({
                    date: day,
                    hasReading: true,
                    readingTime: dayData.reading_time,
                    books: [{
                        title: `阅读记录 ${dayData.sessions || 1}次`,
                        time: timeStr,
                        timeSeconds: dayData.reading_time,
                        isContinuous: false,
                        continuousDay: 0,
                        shape: '●',
                        color: '#3b82f6'
                    }]
                });
            } else {
                data.push({
                    date: day,
                    hasReading: false,
                    readingTime: 0,
                    books: []
                });
            }
        }
        
        return { data, firstDay, daysInMonth };
    }
    
    /**
     * 渲染日历天数
     */
    renderCalendarDays(calendarData, todayDate) {
        const { data, firstDay, daysInMonth } = calendarData;
        const days = [];
        
        // 添加上月末尾的日期
        const adjustedFirstDay = firstDay === 0 ? 6 : firstDay - 1; // 调整为周一开始
        for (let i = 0; i < adjustedFirstDay; i++) {
            days.push('<div class="calendar-day other-month"></div>');
        }
        
        // 添加当月日期
        data.forEach(dayData => {
            const isToday = dayData.date === todayDate;
            const classes = ['calendar-day'];
            
            if (isToday) classes.push('today');
            if (dayData.hasReading) classes.push('has-reading');
            
            const readingEntries = dayData.books.map(book => {
                let entryClass = 'reading-entry';
                if (book.isContinuous) {
                    entryClass += ' continuous';
                    if (book.isStart) {
                        entryClass += ' continuous-start';
                    } else if (book.isEnd) {
                        entryClass += ' continuous-end';
                    } else {
                        entryClass += ' continuous-middle';
                    }
                }
                
                // 根据屏幕宽度动态调整截断长度
                let maxTitleLength = 8; // 默认长度
                if (window.innerWidth < 480) {
                    maxTitleLength = 6; // 小屏幕更短
                } else if (window.innerWidth < 768) {
                    maxTitleLength = 7; // 中等屏幕稍短
                }
                
                // 截取书名（太长的话）
                const displayTitle = book.title.length > maxTitleLength ? book.title.substring(0, maxTitleLength) + '...' : book.title;
                
                return `<div class="${entryClass}" style="color: ${book.color};" title="${book.title} - ${book.author}&#10;阅读时长: ${book.time}">
                    <span class="book-shape">${book.shape}</span>
                    <span class="book-title">${displayTitle}</span>
                    <span class="reading-time">${book.time}</span>
                </div>`;
            }).join('');
            
            days.push(`
                <div class="${classes.join(' ')}" onclick="dashboard.showDayDetail(${dayData.date})">
                    <div class="day-number">${dayData.date}</div>
                    <div class="reading-entries">${readingEntries}</div>
                </div>
            `);
        });
        
        return days.join('');
    }
    
    /**
     * 导航月份
     */
    navigateMonth(direction) {
        let newMonth = this.currentCalendarMonth + direction;
        let newYear = this.currentCalendarYear;
        
        if (newMonth > 12) {
            newMonth = 1;
            newYear++;
        } else if (newMonth < 1) {
            newMonth = 12;
            newYear--;
        }
        
        const container = document.getElementById('month-calendar');
        this.renderMonthCalendar(container, newYear, newMonth);
    }
    
    /**
     * 显示天详情
     */
    showDayDetail(day) {
        // 这里可以显示该天的详细阅读信息
        console.log(`显示 ${day} 日的阅读详情`);
    }
    
    /**
     * 设置周统计面板
     */
    setupWeekStats() {
        const container = document.getElementById('week-stats');
        if (!container) return;
        
        // 使用真实API数据而非模拟数据
        const weekData = this.generateWeekStatsFromRealData();
        this.renderWeekStats(container, weekData);
    }
    
    /**
     * 从真实数据生成周统计
     */
    generateWeekStatsFromRealData() {
        // 先生成每日数据
        const weekData = this.generateDailyWeekData();
        
        // 从每日数据计算汇总统计
        const totalPages = weekData.reduce((sum, day) => sum + day.pages, 0);
        const totalTime = weekData.reduce((sum, day) => sum + day.time, 0); // 已经是分钟
        const avgPages = weekData.length > 0 ? Math.round(totalPages / weekData.length) : 0;
        const avgTime = weekData.length > 0 ? Math.round(totalTime / weekData.length) : 0;
        
        // 找到今天的数据
        const todayData = weekData.find(day => day.isToday) || { pages: 0, time: 0 };
        
        return {
            totalPages: totalPages,
            totalTime: totalTime,
            avgPages: avgPages,
            avgTime: avgTime,
            weekData: weekData,
            todayPages: todayData.pages,
            todayTime: todayData.time
        };
    }
    
    /**
     * 生成每日周数据
     */
    generateDailyWeekData() {
        const weekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
        const now = new Date();
        const weekData = [];
        
        // 从真实趋势数据中获取最近7天的数据
        const trendsData = this.chartData?.trends || [];
        
        for (let i = 6; i >= 0; i--) {
            const date = new Date(now);
            date.setDate(date.getDate() - i);
            
            const dateStr = date.toISOString().split('T')[0];
            // 从所有趋势数据中查找匹配的日期
            const dayTrend = trendsData.find(d => d.date === dateStr);
            
            // 使用转换后的字段名: readingTime 和 pages
            const pages = dayTrend?.pages || 0;
            const time = dayTrend ? Math.floor(dayTrend.readingTime / 60) : 0; // readingTime是秒，转换为分钟
            
            weekData.push({
                dayName: weekDays[date.getDay() === 0 ? 6 : date.getDay() - 1],
                date: `${date.getMonth() + 1}-${String(date.getDate()).padStart(2, '0')}`,
                pages: pages,
                time: time,
                isToday: i === 0
            });
        }
        
        return weekData;
    }

    /**
     * 渲染周统计
     */
    renderWeekStats(container, weekData) {
        const maxTime = Math.max(...weekData.weekData.map(d => d.time), 1); // 避免除以0
        
        container.innerHTML = `
            <div class="week-summary">
                <div class="week-stat-item">
                    <div class="week-stat-value">${weekData.totalPages}</div>
                    <div class="week-stat-label">总页数</div>
                </div>
                <div class="week-stat-item">
                    <div class="week-stat-value">${Math.floor(weekData.totalTime / 60)}:${String(weekData.totalTime % 60).padStart(2, '0')}</div>
                    <div class="week-stat-label">时长</div>
                </div>
                <div class="week-stat-item">
                    <div class="week-stat-value">${weekData.avgPages}</div>
                    <div class="week-stat-label">日均页数</div>
                </div>
                <div class="week-stat-item">
                    <div class="week-stat-value">${Math.floor(weekData.avgTime / 60)}:${String(weekData.avgTime % 60).padStart(2, '0')}</div>
                    <div class="week-stat-label">日均时长</div>
                </div>
            </div>
            
            <div class="week-progress">
                <div class="week-progress-title">一周进度</div>
                <div class="week-days">
                    ${weekData.weekData.map(day => {
                        // 让最大值填满容器（100%），其他按比例计算
                        const progressWidth = maxTime > 0 ? (day.time / maxTime) * 100 : 0;
                        const minWidth = 3; // 最小宽度3%，确保有数据时至少可见
                        const actualWidth = day.time > 0 ? Math.max(minWidth, progressWidth) : 0;
                        
                        // 为不同时间段使用不同颜色，基于相对于最大值的比例
                        let barColor = '#e5e7eb'; // 默认灰色
                        if (day.time > 0) {
                            const relativeRatio = day.time / maxTime;
                            if (relativeRatio >= 0.8) {
                                barColor = '#10b981'; // 绿色 - 高活跃度
                            } else if (relativeRatio >= 0.6) {
                                barColor = '#3b82f6'; // 蓝色 - 中等活跃度  
                            } else if (relativeRatio >= 0.3) {
                                barColor = '#f59e0b'; // 黄色 - 低活跃度
                            } else {
                                barColor = '#ef4444'; // 红色 - 很低活跃度
                            }
                        }
                        
                        return `
                        <div class="week-day ${day.isToday ? 'today' : ''}">
                            <div class="week-day-info">
                                <div class="week-day-name">${day.dayName}</div>
                                <div class="week-day-date">${day.date}</div>
                            </div>
                            <div class="week-day-progress-container">
                                <div class="week-day-progress-bar" style="width: ${actualWidth}%; background: ${barColor}; transition: width 0.5s ease;"></div>
                            </div>
                            <div class="week-day-stats">
                                <div class="week-day-time">${day.time}分</div>
                                <div class="week-day-pages">${day.pages}页</div>
                            </div>
                        </div>`;
                    }).join('')}
                </div>
            </div>
            
            <div class="comparison-section">
                <div class="comparison-title">统计对比</div>
                <div class="comparison-stats">
                    <div class="comparison-item">
                        <div class="comparison-label">周平均</div>
                        <div class="comparison-value">${Math.floor(weekData.avgTime / 60)}:${String(weekData.avgTime % 60).padStart(2, '0')}</div>
                        <div class="comparison-pages">${weekData.avgPages} 页数</div>
                    </div>
                    <div class="comparison-item">
                        <div class="comparison-label">今天</div>
                        <div class="comparison-value">${Math.floor(weekData.todayTime / 60)}:${String(weekData.todayTime % 60).padStart(2, '0')}</div>
                        <div class="comparison-pages">${weekData.todayPages} 页数</div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 设置在读书单
     */
    async setupReadingList() {
        const readingListContainer = document.getElementById('reading-list');
        const books = this.chartData.readingList;

        console.log('📋 设置在读书单, 书籍数据:', books);
        console.log('📋 书籍数量:', books ? books.length : 0);

        if (!books || books.length === 0) {
            console.log('📋 书单为空，显示空状态');
            readingListContainer.innerHTML = `
                <div class="empty-state" style="text-align: center; color: var(--text-muted); padding: 2rem;">
                    <div style="font-size: 2rem; margin-bottom: 1rem;">📚</div>
                    <div>暂无在读书籍</div>
                    <div style="font-size: 0.875rem; margin-top: 1rem; opacity: 0.7;">
                        可能原因：KOReader中还没有阅读记录，或者数据同步中...
                    </div>
                </div>
            `;
            return;
        }

        console.log('📋 开始渲染书单...');

        const formatReadingTime = (seconds) => {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            return hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
        };

        const formatDate = (dateStr) => {
            const date = new Date(dateStr);
            const today = new Date();
            const diffTime = today - date;
            const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
            
            if (diffDays === 0) return '今天';
            if (diffDays === 1) return '昨天';
            if (diffDays < 7) return `${diffDays}天前`;
            return date.toLocaleDateString('zh-CN');
        };

        // 直接生成最终的HTML结构，使用默认封面
        const booksHtml = books.map(book => `
            <div class="book-item" data-book-id="${book.id}">
                <div class="book-cover-container">
                    <img class="book-cover-img" 
                         src="${this.getDefaultCover(book.title)}" 
                         alt="${book.title}" 
                         style="width: 80px; height: 110px; object-fit: cover; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                </div>
                <div class="book-info">
                    <div class="book-title">${book.title}</div>
                    <div class="book-author">${book.author}</div>
                    <div class="book-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${book.progress}%"></div>
                        </div>
                        <div class="progress-text">${book.progress.toFixed(1)}%</div>
                    </div>
                </div>
                <div class="book-stats">
                    <div class="reading-time">${formatReadingTime(book.readingTime)}</div>
                    <div class="last-read">最后阅读: ${formatDate(book.lastRead)}</div>
                    <div>${book.currentPage}/${book.totalPages} 页</div>
                </div>
            </div>
        `).join('');

        readingListContainer.innerHTML = booksHtml;

        // 添加点击事件
        const bookItems = readingListContainer.querySelectorAll('.book-item');
        bookItems.forEach(item => {
            item.addEventListener('click', () => {
                const bookId = item.dataset.bookId;
                this.showBookDetail(bookId);
            });
        });
        
        console.log('✅ 书单渲染完成');
    }

    /**
     * 显示书籍详情
     */
    showBookDetail(bookId) {
        const book = this.chartData.readingList.find(b => b.id == bookId);
        if (!book) return;

        // 确保数据有效性并提供默认值
        const title = book.title || '未知书籍';
        const author = book.author || '未知作者';
        const progress = (book.progress || 0).toFixed(1);
        const currentPage = book.currentPage || 0; // 修正字段名
        const totalPages = book.totalPages || 0;
        const readingTime = book.readingTime || 0; // 修正字段名
        const lastRead = book.lastRead || '未知';
        
        // 格式化阅读时长
        const hours = Math.floor(readingTime / 3600);
        const minutes = Math.floor((readingTime % 3600) / 60);
        const timeStr = hours > 0 ? `${hours}小时${minutes}分钟` : `${minutes}分钟`;
        
        // 创建美观的模态对话框
        this.showBookModal(title, author, progress, currentPage, totalPages, timeStr, lastRead);
    }
    
    /**
     * 显示书籍详情模态对话框
     */
    showBookModal(title, author, progress, currentPage, totalPages, timeStr, lastRead) {
        // 移除已存在的模态框
        const existingModal = document.getElementById('book-detail-modal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // 创建模态框HTML
        const modalHtml = `
            <div id="book-detail-modal" class="book-modal-overlay">
                <div class="book-modal-content">
                    <div class="book-modal-header">
                        <h3 class="book-modal-title">书籍详情</h3>
                        <button class="book-modal-close" onclick="this.closest('.book-modal-overlay').remove()">×</button>
                    </div>
                    <div class="book-modal-body">
                        <div class="book-detail-row">
                            <span class="book-detail-label">标题：</span>
                            <span class="book-detail-value">${title}</span>
                        </div>
                        <div class="book-detail-row">
                            <span class="book-detail-label">作者：</span>
                            <span class="book-detail-value">${author}</span>
                        </div>
                        <div class="book-detail-row">
                            <span class="book-detail-label">进度：</span>
                            <span class="book-detail-value">${progress}% (${currentPage}/${totalPages} 页)</span>
                        </div>
                        <div class="book-detail-row">
                            <span class="book-detail-label">阅读时长：</span>
                            <span class="book-detail-value">${timeStr}</span>
                        </div>
                        <div class="book-detail-row">
                            <span class="book-detail-label">最后阅读：</span>
                            <span class="book-detail-value">${lastRead}</span>
                        </div>
                    </div>
                    <div class="book-modal-footer">
                        <button class="book-modal-btn" onclick="this.closest('.book-modal-overlay').remove()">确定</button>
                    </div>
                </div>
            </div>
        `;
        
        // 添加到页面
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // 点击背景关闭模态框
        const modal = document.getElementById('book-detail-modal');
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    /**
     * 调整所有图表大小
     */
    resizeCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.resize === 'function') {
                chart.resize();
            }
        });
        
        // 重新渲染月度日历（如果需要）
        if (this.currentCalendarYear && this.currentCalendarMonth) {
            const container = document.getElementById('month-calendar');
            if (container) {
                this.renderMonthCalendar(container, this.currentCalendarYear, this.currentCalendarMonth);
            }
        }
    }

    /**
     * 显示错误信息
     */
    showError(message) {
        // 创建错误提示元素
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #fee2e2;
            color: #dc2626;
            padding: 12px 16px;
            border-radius: 8px;
            border: 1px solid #fecaca;
            z-index: 1001;
            max-width: 300px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        `;
        errorDiv.textContent = message;
        
        document.body.appendChild(errorDiv);
        
        // 3秒后自动移除
        setTimeout(() => {
            if (errorDiv && errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 3000);
    }

    /**
     * 销毁所有图表实例
     */
    destroy() {
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.dispose === 'function') {
                chart.dispose();
            }
        });
        this.charts = {};
    }

    /**
     * 更新统计卡片
     */
    updateStatsCards(summary) {
        const formatTime = (seconds) => {
            const hours = Math.floor(seconds / 3600);
            return hours.toFixed(1);
        };

        document.getElementById('total-reading-time').textContent = formatTime(summary.total_reading_time);
        document.getElementById('total-books').textContent = summary.total_books;
        document.getElementById('total-pages').textContent = summary.total_pages_read.toLocaleString();
        document.getElementById('reading-streak').textContent = summary.reading_streak;
    }

    /**
     * 设置所有图表
     */
    setupCharts() {
        this.setupCalendarChart();
        this.setupTrendChart();
        this.setupHourChart();
        this.setupProgressChart();
        this.setupMonthCalendar();
        this.setupWeekStats();
        this.setupReadingList();
    }

    /**
     * 设置日历热力图
     */
    setupCalendarChart() {
        const chartDom = document.getElementById('calendar-chart');
        const myChart = echarts.init(chartDom);
        
        const option = {
            title: {
                text: `${new Date().getFullYear()}年阅读热力图`,
                left: 'center',
                textStyle: {
                    fontSize: 20,
                    fontWeight: '500',
                    color: '#374151',
                    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
                }
            },
            tooltip: {
                position: 'top',
                formatter: function(params) {
                    const date = params.data[0];
                    const seconds = params.data[1];
                    const hours = Math.floor(seconds / 3600);
                    const minutes = Math.floor((seconds % 3600) / 60);
                    
                    let timeStr = '';
                    if (seconds === 0) {
                        timeStr = '未阅读';
                    } else if (hours > 0) {
                        timeStr = `${hours}小时${minutes}分钟`;
                    } else if (minutes > 0) {
                        timeStr = `${minutes}分钟`;
                    } else {
                        timeStr = `${seconds}秒`;
                    }
                    
                    return `${timeStr} on ${date}`;
                }
            },
            visualMap: {
                type: 'piecewise',
                orient: 'horizontal',
                left: 'center',
                bottom: 10,
                itemWidth: 15,
                itemHeight: 15,
                text: ['多', '少'],
                textGap: 10,
                textStyle: { 
                    color: '#555',
                    fontSize: 12
                },
                pieces: [
                    { min: 5400, color: '#216e39' },
                    { min: 3600, max: 5399, color: '#30a14e' },
                    { min: 1800, max: 3599, color: '#40c463' },
                    { min: 1, max: 1799, color: '#9be9a8' },
                    { value: 0, color: '#ebedf0' }
                ]
            },
            calendar: {
                range: new Date().getFullYear().toString(),
                top: 90,
                cellSize: [22, 22],
                right: 30,
                left: 50,
                splitLine: { 
                    show: true, 
                    lineStyle: { 
                        color: 'rgba(0,0,0,0.1)', 
                        width: 1, 
                        type: 'solid' 
                    } 
                },
                itemStyle: { 
                    borderWidth: 4, 
                    borderColor: '#fff' 
                },
                monthLabel: { 
                    nameMap: 'cn',
                    align: 'center',
                    color: '#586069',
                    fontSize: 13
                },
                dayLabel: { 
                    show: true,
                    color: '#586069',
                    fontSize: 11
                },
                yearLabel: { show: false }
            },
            series: {
                type: 'heatmap',
                coordinateSystem: 'calendar',
                data: this.chartData.calendar
            }
        };

        myChart.setOption(option);
        this.charts.calendar = myChart;
    }

    /**
     * 设置趋势图表
     */
    setupTrendChart() {
        const chartDom = document.getElementById('trend-chart');
        const myChart = echarts.init(chartDom);
        
        const dates = this.chartData.trends.map(item => item.date.slice(5)); // MM-DD
        const readingTimes = this.chartData.trends.map(item => Math.floor(item.readingTime / 60)); // 转换为分钟
        const pages = this.chartData.trends.map(item => item.pages);

        const option = {
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross'
                }
            },
            legend: {
                data: ['阅读时长', '阅读页数'],
                top: 10
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                boundaryGap: false,
                data: dates,
                axisLabel: {
                    color: '#64748b'
                }
            },
            yAxis: [
                {
                    type: 'value',
                    name: '分钟',
                    position: 'left',
                    axisLabel: {
                        color: '#64748b'
                    }
                },
                {
                    type: 'value',
                    name: '页数',
                    position: 'right',
                    axisLabel: {
                        color: '#64748b'
                    }
                }
            ],
            series: [
                {
                    name: '阅读时长',
                    type: 'line',
                    smooth: true,
                    data: readingTimes,
                    itemStyle: {
                        color: '#3b82f6'
                    },
                    areaStyle: {
                        color: {
                            type: 'linear',
                            x: 0,
                            y: 0,
                            x2: 0,
                            y2: 1,
                            colorStops: [{
                                offset: 0, color: 'rgba(59, 130, 246, 0.3)'
                            }, {
                                offset: 1, color: 'rgba(59, 130, 246, 0.05)'
                            }]
                        }
                    }
                },
                {
                    name: '阅读页数',
                    type: 'bar',
                    yAxisIndex: 1,
                    data: pages,
                    itemStyle: {
                        color: '#8b5cf6'
                    }
                }
            ]
        };

        myChart.setOption(option);
        this.charts.trend = myChart;
    }

    /**
     * 设置时段分布图表
     */
    setupHourChart() {
        const chartDom = document.getElementById('hour-chart');
        const myChart = echarts.init(chartDom);
        
        const option = {
            title: {
                text: '24小时阅读分布',
                left: 'center',
                textStyle: {
                    fontSize: 14,
                    fontWeight: 'normal',
                    color: '#64748b'
                }
            },
            tooltip: {
                trigger: 'axis',
                formatter: function(params) {
                    return `${params[0].axisValue}:00<br/>阅读时长: ${params[0].data} 分钟`;
                }
            },
            grid: {
                left: '5%',
                right: '5%',
                bottom: '10%',
                top: '20%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: this.chartData.hourlyData.map(item => item[0]),
                axisLabel: {
                    color: '#64748b',
                    interval: 3
                }
            },
            yAxis: {
                type: 'value',
                name: '分钟',
                axisLabel: {
                    color: '#64748b'
                }
            },
            series: [{
                type: 'bar',
                data: this.chartData.hourlyData.map(item => item[1]),
                itemStyle: {
                    color: {
                        type: 'linear',
                        x: 0,
                        y: 0,
                        x2: 0,
                        y2: 1,
                        colorStops: [{
                            offset: 0, color: '#60a5fa'
                        }, {
                            offset: 1, color: '#3b82f6'
                        }]
                    }
                },
                barWidth: '60%'
            }]
        };

        myChart.setOption(option);
        this.charts.hour = myChart;
    }

    /**
     * 设置进度环形图
     */
    setupProgressChart() {
        const chartDom = document.getElementById('progress-chart');
        const myChart = echarts.init(chartDom);
        
        const { completed, inProgress } = this.chartData.progressData;
        const total = completed + inProgress;

        const option = {
            title: {
                text: `${completed}/${total}`,
                subtext: '已完成/总数',
                left: 'center',
                top: 'center',
                textStyle: {
                    fontSize: 24,
                    fontWeight: 'bold',
                    color: '#1e293b'
                },
                subtextStyle: {
                    fontSize: 12,
                    color: '#64748b'
                }
            },
            tooltip: {
                trigger: 'item',
                formatter: '{a} <br/>{b}: {c} ({d}%)'
            },
            legend: {
                bottom: 10,
                left: 'center'
            },
            series: [
                {
                    name: '阅读进度',
                    type: 'pie',
                    radius: ['40%', '70%'],
                    center: ['50%', '50%'],
                    avoidLabelOverlap: false,
                    label: {
                        show: false
                    },
                    emphasis: {
                        label: {
                            show: true,
                            fontSize: '14',
                            fontWeight: 'bold'
                        }
                    },
                    data: [
                        {
                            value: completed,
                            name: '已完成',
                            itemStyle: { color: '#10b981' }
                        },
                        {
                            value: inProgress,
                            name: '进行中',
                            itemStyle: { color: '#f59e0b' }
                        }
                    ]
                }
            ]
        };

        myChart.setOption(option);
        this.charts.progress = myChart;
    }

    /**
     * 书籍封面服务（简化版）
     */
    async getCoverImage(title, author) {
        // 直接返回默认封面，不再调用第三方API
        return this.getDefaultCover(title);
    }
    
    /**
     * 生成默认封面
     */
    getDefaultCover(title) {
        // 扩展颜色方案，包含渐变色
        const colorSchemes = [
            { bg: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', text: 'white' },
            { bg: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', text: 'white' },
            { bg: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', text: 'white' },
            { bg: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)', text: 'white' },
            { bg: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)', text: 'white' },
            { bg: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)', text: '#333' },
            { bg: 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)', text: '#333' },
            { bg: 'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)', text: 'white' },
            { bg: 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)', text: '#333' },
            { bg: 'linear-gradient(135deg, #ff8177 0%, #ff867a 100%)', text: 'white' }
        ];
        
        const firstChar = title ? title.charAt(0).toUpperCase() : '📚';
        const colorIndex = title ? title.length % colorSchemes.length : 0;
        const scheme = colorSchemes[colorIndex];
        
        // 生成基于标题的唯一ID，用于渐变定义
        const gradientId = `grad_${title ? title.replace(/[^a-zA-Z0-9]/g, '') : 'default'}`;
        
        // 返回一个带渐变的SVG数据URL作为默认封面
        const svg = `
            <svg width="120" height="160" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="${gradientId}" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:${scheme.bg.match(/#[a-fA-F0-9]{6}/g)?.[0] || '#3b82f6'};stop-opacity:1" />
                        <stop offset="100%" style="stop-color:${scheme.bg.match(/#[a-fA-F0-9]{6}/g)?.[1] || '#8b5cf6'};stop-opacity:1" />
                    </linearGradient>
                    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
                        <feDropShadow dx="2" dy="2" stdDeviation="3" flood-color="rgba(0,0,0,0.3)"/>
                    </filter>
                </defs>
                <rect width="120" height="160" fill="url(#${gradientId})" rx="8" filter="url(#shadow)"/>
                <text x="60" y="85" text-anchor="middle" fill="${scheme.text}" 
                      font-family="'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" 
                      font-size="42" 
                      font-weight="600"
                      style="text-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                    ${firstChar}
                </text>
                <rect x="8" y="8" width="104" height="144" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="1" rx="6"/>
            </svg>
        `;
        
        return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
    }
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.koReaderDashboard = new KOReaderDashboard();
    window.dashboard = window.koReaderDashboard; // 为HTML onclick提供全局引用
});

// 页面卸载时清理资源
window.addEventListener('beforeunload', () => {
    if (window.koReaderDashboard) {
        window.koReaderDashboard.destroy();
    }
}); 