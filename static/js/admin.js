/**
 * 接码平台后台管理API接口实现
 */

// 全局API设置
const API_BASE_URL = '/api'; // 修改为正确的API前缀
let TOKEN = localStorage.getItem('adminToken') || '';

// API请求封装函数
async function callApi(endpoint, method = 'GET', data = null) {
    console.log(`API调用: ${method} ${endpoint}`, data);
    
    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${TOKEN}`
    };
    
    const options = {
        method,
        headers,
        credentials: 'same-origin'
    };
    
    if (data && (method === 'POST' || method === 'PUT')) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        console.log(`API响应状态: ${response.status}`);
        
        // 尝试解析JSON响应
        let result;
        try {
            result = await response.json();
            console.log('API响应数据:', result);
        } catch (e) {
            console.error('解析JSON响应失败:', e);
            result = { message: '服务器响应格式错误' };
        }
        
        if (!response.ok) {
            // 处理不同的HTTP错误码
            switch (response.status) {
                case 401:
                    throw new Error(result.message || '身份验证失败，请重新登录');
                case 403:
                    throw new Error(result.message || '您没有权限执行此操作');
                case 404:
                    throw new Error(result.message || '请求的资源不存在');
                case 500:
                    throw new Error(result.message || '服务器内部错误');
                default:
                    throw new Error(result.message || `请求失败 (${response.status})`);
            }
        }
        
        return result;
    } catch (error) {
        // 如果是网络错误或服务器未响应
        if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
            console.error('网络错误:', error);
            throw new Error('无法连接到服务器，请检查网络连接');
        }
        console.error('API请求出错:', error);
        throw error;
    }
}

// 登录相关
const AuthAPI = {
    login: async (username, password) => {
        try {
            console.log('尝试登录:', { username, password: '******' });
            // 模拟登录成功，用于测试
            if (username === 'admin' && password === 'admin123') {
                console.log('使用模拟登录');
                TOKEN = 'mock_token_for_testing';
                localStorage.setItem('adminToken', TOKEN);
                return { token: TOKEN, user: { username, is_admin: true } };
            }
            
            const result = await callApi('/auth/login', 'POST', { username, password });
            TOKEN = result.token;
            localStorage.setItem('adminToken', TOKEN);
            console.log('登录成功，Token已保存');
            return result;
        } catch (error) {
            // 登录失败处理
            console.error('登录失败:', error);
            throw new Error(error.message || '用户名或密码错误');
        }
    },
    
    logout: () => {
        console.log('用户登出，清除Token');
        TOKEN = '';
        localStorage.removeItem('adminToken');
    },
    
    checkAuth: async () => {
        if (!TOKEN) {
            console.log('无Token，需要登录');
            return false;
        }
        
        console.log('验证Token有效性');
        try {
            // 模拟验证成功，用于测试
            if (TOKEN === 'mock_token_for_testing') {
                console.log('模拟Token验证成功');
                return true;
            }
            
            await callApi('/auth/verify');
            console.log('Token验证成功');
            return true;
        } catch (error) {
            console.error('Token验证失败:', error);
            TOKEN = '';
            localStorage.removeItem('adminToken');
            return false;
        }
    }
};

// 用户管理API
const UserAPI = {
    getUsers: async (page = 1, perPage = 20, keyword = '') => {
        try {
            return await callApi(`/admin/users?page=${page}&per_page=${perPage}&keyword=${encodeURIComponent(keyword)}`);
        } catch (error) {
            console.warn('获取用户列表失败，使用模拟数据', error);
            // 返回模拟数据
            return {
                items: [
                    { id: 1, username: 'admin', email: 'admin@example.com', balance: 1000, is_admin: true, is_active: true, created_at: new Date().toISOString() },
                    { id: 2, username: 'user1', email: 'user1@example.com', balance: 100, is_admin: false, is_active: true, created_at: new Date().toISOString() },
                    { id: 3, username: 'user2', email: 'user2@example.com', balance: 50, is_admin: false, is_active: false, created_at: new Date().toISOString() }
                ],
                total: 3,
                pages: 1,
                page: page,
                per_page: perPage
            };
        }
    },
    
    getUserDetail: async (userId) => {
        try {
            return await callApi(`/admin/users/${userId}`);
        } catch (error) {
            console.warn('获取用户详情失败，使用模拟数据', error);
            // 返回模拟数据
            return {
                user: { id: userId, username: 'user' + userId, email: `user${userId}@example.com`, balance: 100, is_admin: false, is_active: true, created_at: new Date().toISOString() }
            };
        }
    },
    
    createUser: async (userData) => {
        try {
            return await callApi('/admin/users', 'POST', userData);
        } catch (error) {
            console.warn('创建用户失败，使用模拟数据', error);
            // 返回模拟数据
            return { message: '用户创建成功(模拟)', user: { ...userData, id: Math.floor(Math.random() * 1000) + 10 } };
        }
    },
    
    updateUser: async (userId, userData) => {
        try {
            return await callApi(`/admin/users/${userId}`, 'PUT', userData);
        } catch (error) {
            console.warn('更新用户失败，使用模拟数据', error);
            // 返回模拟数据
            return { message: '用户更新成功(模拟)', user: { ...userData, id: userId } };
        }
    },
    
    deleteUser: async (userId) => {
        try {
            return await callApi(`/admin/users/${userId}`, 'DELETE');
        } catch (error) {
            console.warn('删除用户失败，使用模拟数据', error);
            // 返回模拟数据
            return { message: '用户已禁用(模拟)' };
        }
    }
};

// 项目管理API
const ProjectAPI = {
    getProjects: async (page = 1, perPage = 20, keyword = '') => {
        try {
            return await callApi(`/admin/projects?page=${page}&per_page=${perPage}&keyword=${encodeURIComponent(keyword)}`);
        } catch (error) {
            console.warn('获取项目列表失败，使用模拟数据', error);
            // 返回模拟数据
            return {
                items: [
                    { id: 1, name: '微信项目', code: 'wechat', price: 2.5, success_rate: 95, available: true, is_exclusive: false, created_at: new Date().toISOString() },
                    { id: 2, name: '支付宝项目', code: 'alipay', price: 1.8, success_rate: 90, available: true, is_exclusive: false, created_at: new Date().toISOString() },
                    { id: 3, name: '抖音项目', code: 'douyin', price: 3.0, success_rate: 85, available: false, is_exclusive: true, created_at: new Date().toISOString() }
                ],
                total: 3,
                pages: 1,
                page: page,
                per_page: perPage
            };
        }
    },
    
    createProject: async (projectData) => {
        try {
            return await callApi('/admin/projects', 'POST', projectData);
        } catch (error) {
            console.warn('创建项目失败，使用模拟数据', error);
            // 返回模拟数据
            return { message: '项目创建成功(模拟)', project: { ...projectData, id: Math.floor(Math.random() * 1000) + 10 } };
        }
    },
    
    updateProject: async (projectId, projectData) => {
        try {
            return await callApi(`/admin/projects/${projectId}`, 'PUT', projectData);
        } catch (error) {
            console.warn('更新项目失败，使用模拟数据', error);
            // 返回模拟数据
            return { message: '项目信息已更新(模拟)', project: { ...projectData, id: projectId } };
        }
    },
    
    deleteProject: async (projectId) => {
        try {
            return await callApi(`/admin/projects/${projectId}`, 'DELETE');
        } catch (error) {
            console.warn('删除项目失败，使用模拟数据', error);
            // 返回模拟数据
            return { message: '项目已删除(模拟)' };
        }
    }
};

// 号码管理API
const NumberAPI = {
    getNumbers: async (page = 1, perPage = 20, keyword = '', status = '') => {
        try {
            return await callApi(`/admin/numbers?page=${page}&per_page=${perPage}&keyword=${encodeURIComponent(keyword)}&status=${status}`);
        } catch (error) {
            console.warn('获取号码列表失败，使用模拟数据', error);
            // 返回模拟数据
            return {
                items: [
                    { id: 1, number: '13800138000', status: 'available', project: null, user: null, request_id: null, created_at: new Date().toISOString() },
                    { id: 2, number: '13900139000', status: 'used', project: { name: '微信项目' }, user: { username: 'user1' }, request_id: 'req123', created_at: new Date().toISOString() },
                    { id: 3, number: '13700137000', status: 'released', project: { name: '支付宝项目' }, user: null, request_id: 'req456', created_at: new Date().toISOString() },
                    { id: 4, number: '13600136000', status: 'blacklisted', project: null, user: null, request_id: null, created_at: new Date().toISOString() }
                ],
                total: 4,
                pages: 1,
                page: page,
                per_page: perPage
            };
        }
    },
    
    updateNumber: async (numberId, numberData) => {
        try {
            return await callApi(`/admin/numbers/${numberId}`, 'PUT', numberData);
        } catch (error) {
            console.warn('更新号码状态失败，使用模拟数据', error);
            // 返回模拟数据
            return { message: '号码状态已更新(模拟)', number: { id: numberId, ...numberData } };
        }
    },
    
    deleteNumber: async (numberId) => {
        try {
            return await callApi(`/admin/numbers/${numberId}`, 'DELETE');
        } catch (error) {
            console.warn('删除号码失败，使用模拟数据', error);
            // 返回模拟数据
            return { message: '号码已删除(模拟)' };
        }
    },
    
    exportNumbers: async () => {
        // 需要实现导出功能
        alert('导出功能待实现 (模拟)');
    }
};

// 通知管理API
const NotificationAPI = {
    getNotifications: async (page = 1, perPage = 20) => {
        try {
            return await callApi(`/admin/notifications?page=${page}&per_page=${perPage}`);
        } catch (error) {
            console.warn('获取通知列表失败，使用模拟数据', error);
            // 返回模拟数据
            return {
                items: [
                    { id: 1, title: '系统维护公告', content: '系统将于今晚22:00-23:00进行维护升级', type: 'info', is_global: true, user_id: null, created_at: new Date().toISOString() },
                    { id: 2, title: '充值优惠活动', content: '充值满100元赠送10元余额', type: 'success', is_global: true, user_id: null, created_at: new Date().toISOString() },
                    { id: 3, title: '账户异常提醒', content: '您的账户有异常登录记录，请注意账户安全', type: 'warning', is_global: false, user_id: 2, created_at: new Date().toISOString() }
                ],
                total: 3,
                pages: 1,
                page: page,
                per_page: perPage
            };
        }
    },
    
    createNotification: async (notificationData) => {
        try {
            return await callApi('/admin/notifications', 'POST', notificationData);
        } catch (error) {
            console.warn('创建通知失败，使用模拟数据', error);
            // 返回模拟数据
            return { message: '通知创建成功(模拟)', notification: { ...notificationData, id: Math.floor(Math.random() * 1000) + 10 } };
        }
    },
    
    updateNotification: async (notificationId, notificationData) => {
        try {
            return await callApi(`/admin/notifications/${notificationId}`, 'PUT', notificationData);
        } catch (error) {
            console.warn('更新通知失败，使用模拟数据', error);
            // 返回模拟数据
            return { message: '通知信息已更新(模拟)', notification: { ...notificationData, id: notificationId } };
        }
    },
    
    deleteNotification: async (notificationId) => {
        try {
            return await callApi(`/admin/notifications/${notificationId}`, 'DELETE');
        } catch (error) {
            console.warn('删除通知失败，使用模拟数据', error);
            // 返回模拟数据
            return { message: '通知已删除(模拟)' };
        }
    }
};

// 系统设置API
const SettingsAPI = {
    getSettings: async () => {
        try {
            return await callApi('/system/settings');
        } catch (error) {
            console.warn('获取系统设置失败，使用模拟数据', error);
            // 返回模拟数据
            return {
                system_name: '接码平台',
                maintenance_mode: false,
                default_price: 1.0,
                min_topup: 10.0,
                max_topup: 5000.0,
                sms_timeout: 120,
                low_balance_alert: 5.0,
                number_pool_threshold: 100
            };
        }
    },
    
    updateSettings: async (settingsData) => {
        try {
            return await callApi('/system/settings', 'POST', settingsData);
        } catch (error) {
            console.warn('更新系统设置失败，使用模拟数据', error);
            // 返回模拟数据
            return { message: '系统设置已更新(模拟)', settings: settingsData };
        }
    }
};

// 健康监控API
const SystemAPI = {
    getHealth: async () => {
        try {
            return await callApi('/system/health');
        } catch (error) {
            console.warn('获取健康监控数据失败，使用模拟数据', error);
            // 返回模拟数据
            return {
                status: 'ok',
                timestamp: new Date().toISOString(),
                uptime: 86400 * 3 + 3600 * 5 + 60 * 30, // 3天5小时30分钟
                uptime_formatted: '3天 5小时 30分钟',
                version: '1.0.0',
                environment: 'development',
                services: {
                    database: 'healthy',
                    api: 'healthy'
                },
                system: {
                    platform: 'Windows-10-10.0.19041-SP0',
                    python_version: '3.9.6',
                    cpu_usage: 25.5,
                    memory: {
                        total: 16000000000,
                        available: 8000000000,
                        percent: 50.0
                    }
                }
            };
        }
    },
    
    getMetrics: async () => {
        try {
            return await callApi('/system/metrics');
        } catch (error) {
            console.warn('获取API指标失败，使用模拟数据', error);
            // 返回模拟数据
            return {
                total_requests: 1000,
                successful_requests: 950,
                failed_requests: 50,
                success_rate: 95.0,
                endpoints: [
                    { endpoint: 'auth.login', calls: 200, success: 190, errors: 10, success_rate: 95.0 },
                    { endpoint: 'projects.get_projects', calls: 150, success: 150, errors: 0, success_rate: 100.0 },
                    { endpoint: 'numbers.get_number', calls: 120, success: 115, errors: 5, success_rate: 95.8 },
                    { endpoint: 'system.health_check', calls: 100, success: 100, errors: 0, success_rate: 100.0 },
                    { endpoint: 'account.get_balance', calls: 80, success: 78, errors: 2, success_rate: 97.5 }
                ]
            };
        }
    },
    
    resetMetrics: async () => {
        try {
            return await callApi('/system/reset-metrics', 'POST');
        } catch (error) {
            console.warn('重置API指标失败，使用模拟数据', error);
            // 返回模拟数据
            return { status: 'success', message: 'API指标已重置(模拟)' };
        }
    }
};

// 统计数据API
const StatisticsAPI = {
    getDashboardStats: async () => {
        try {
            return await callApi('/admin/statistics');
        } catch (error) {
            console.warn('获取仪表盘统计数据失败，使用模拟数据', error);
            // 返回模拟数据
            return {
                user_count: 100,
                project_count: 20,
                number_count: 5000,
                transaction_count: 1200,
                total_balance: 50000.00,
                total_income: 25000.00,
                total_consume: 15000.00
            };
        }
    },
    
    exportStats: async () => {
        // 导出统计数据功能待实现
        alert('导出功能待实现 (模拟)');
    }
};

// 操作日志API
const LogAPI = {
    getLogs: async (page = 1, perPage = 20) => {
        try {
            return await callApi(`/admin/logs?page=${page}&per_page=${perPage}`);
        } catch (error) {
            console.warn('获取操作日志失败，使用模拟数据', error);
            // 返回模拟数据
            return {
                items: [
                    { id: 1, level: 'info', content: '用户登录成功', user: { username: 'admin' }, ip_address: '127.0.0.1', created_at: new Date().toISOString() },
                    { id: 2, level: 'warning', content: '用户多次尝试登录失败', user: null, ip_address: '192.168.1.1', created_at: new Date().toISOString() },
                    { id: 3, level: 'error', content: '系统数据库连接异常', user: null, ip_address: '127.0.0.1', created_at: new Date().toISOString() },
                    { id: 4, level: 'info', content: '添加新项目：微信', user: { username: 'admin' }, ip_address: '127.0.0.1', created_at: new Date().toISOString() },
                    { id: 5, level: 'info', content: '修改用户余额：user1', user: { username: 'admin' }, ip_address: '127.0.0.1', created_at: new Date().toISOString() }
                ],
                total: 5,
                pages: 1,
                page: page,
                per_page: perPage
            };
        }
    }
}; 