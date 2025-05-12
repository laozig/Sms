/**
 * 接码平台管理后台界面交互
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('管理面板页面加载完成，初始化管理面板');
    // 初始化
    initAdminPanel();
});

// 全局变量
let currentPage = {
    users: 1,
    projects: 1,
    numbers: 1,
    notifications: 1,
    logs: 1
};

// 初始化管理后台
async function initAdminPanel() {
    try {
        console.log('初始化管理后台');
        
        // 0. 添加错误页面
        createGlobalErrorAlert();
        
        // 1. 确保所有内容区都是隐藏的
        hideAllSections();
        
        // 2. 先隐藏侧边栏
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            console.log('隐藏侧边栏');
            sidebar.style.display = 'none';
        } else {
            console.error('找不到侧边栏元素');
        }
        
        // 3. 先显示登录面板
        const loginPanel = document.getElementById('loginPanel');
        if (loginPanel) {
            console.log('显示登录面板');
            loginPanel.classList.remove('d-none');
        } else {
            console.error('找不到登录面板元素');
            showGlobalError('页面加载错误', '找不到登录面板元素');
            return;
        }
        
        // 4. 检查是否已经登录
        console.log('检查登录状态');
        const isLoggedIn = await AuthAPI.checkAuth();
        console.log('登录状态:', isLoggedIn);
        
        if (isLoggedIn) {
            // 已登录，显示管理界面
            console.log('已登录，显示管理界面');
            showAdminPanel();
        } else {
            // 未登录，保持登录面板显示
            console.log('未登录，设置登录事件');
            setupLoginEvents();
        }
    } catch (error) {
        console.error('初始化管理后台失败:', error);
        showGlobalError('初始化失败', error.message);
    }
}

// 创建全局错误提示
function createGlobalErrorAlert() {
    if (!document.getElementById('globalErrorAlert')) {
        const alertContainer = document.createElement('div');
        alertContainer.id = 'globalErrorAlert';
        alertContainer.className = 'position-fixed top-0 start-0 end-0 p-3 d-none';
        alertContainer.style.zIndex = '9999';
        alertContainer.innerHTML = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                <h4 class="alert-heading" id="globalErrorTitle">错误</h4>
                <p id="globalErrorMessage">发生了未知错误</p>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        document.body.appendChild(alertContainer);
    }
}

// 显示全局错误
function showGlobalError(title, message) {
    const errorAlert = document.getElementById('globalErrorAlert');
    if (errorAlert) {
        document.getElementById('globalErrorTitle').textContent = title;
        document.getElementById('globalErrorMessage').textContent = message;
        errorAlert.classList.remove('d-none');
    } else {
        console.error('找不到全局错误提示元素');
        alert(`${title}: ${message}`);
    }
}

// 设置登录相关事件
function setupLoginEvents() {
    console.log('设置登录相关事件');
    
    // 注册登录按钮事件
    const loginBtn = document.getElementById('loginBtn');
    if (loginBtn) {
        console.log('绑定登录按钮点击事件');
        loginBtn.addEventListener('click', handleLogin);
    } else {
        console.error('找不到登录按钮');
    }
    
    // 添加回车键登录功能
    const passwordInput = document.getElementById('adminPassword');
    if (passwordInput) {
        console.log('绑定密码框回车事件');
        passwordInput.addEventListener('keyup', function(event) {
            if (event.key === "Enter") {
                console.log('密码框按下回车键');
                handleLogin();
            }
        });
    } else {
        console.error('找不到密码输入框');
    }
    
    const usernameInput = document.getElementById('adminUsername');
    if (usernameInput) {
        console.log('绑定用户名框回车事件');
        usernameInput.addEventListener('keyup', function(event) {
            if (event.key === "Enter") {
                console.log('用户名框按下回车键');
                if (passwordInput) {
                    passwordInput.focus();
                } else {
                    handleLogin();
                }
            }
        });
        
        // 自动聚焦用户名输入框
        setTimeout(() => {
            usernameInput.focus();
        }, 100);
    } else {
        console.error('找不到用户名输入框');
    }
}

// 显示登录面板
function showLoginPanel() {
    console.log('显示登录面板');
    
    // 隐藏侧边栏
    document.body.classList.remove('sidebar-visible');
    
    // 隐藏所有内容区
    hideAllSections();
    
    // 显示登录面板
    const loginPanel = document.getElementById('loginPanel');
    if (loginPanel) {
        loginPanel.classList.remove('d-none');
    } else {
        console.error('找不到登录面板元素');
    }
    
    // 设置登录事件
    setupLoginEvents();
}

// 显示管理面板
function showAdminPanel() {
    console.log('显示管理面板');
    
    // 显示侧边栏
    document.body.classList.add('sidebar-visible');
    
    // 隐藏登录面板
    const loginPanel = document.getElementById('loginPanel');
    if (loginPanel) {
        loginPanel.classList.add('d-none');
    } else {
        console.error('找不到登录面板元素');
    }
    
    // 注册菜单点击事件
    const menuItems = document.querySelectorAll('#sidebarMenu a');
    if (menuItems && menuItems.length > 0) {
        console.log('绑定菜单点击事件');
        menuItems.forEach(item => {
            item.addEventListener('click', function(e) {
                e.preventDefault();
                const section = this.getAttribute('data-section');
                console.log('点击菜单项:', section);
                switchSection(section);
                
                // 更新菜单活动状态
                menuItems.forEach(i => i.classList.remove('active'));
                this.classList.add('active');
            });
        });
    } else {
        console.error('找不到菜单项');
    }
    
    // 注册登出按钮事件
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        console.log('绑定登出按钮点击事件');
        logoutBtn.addEventListener('click', function() {
            console.log('点击登出按钮');
            AuthAPI.logout();
            showLoginPanel();
        });
    } else {
        console.error('找不到登出按钮');
    }
    
    // 注册其他事件
    registerEvents();
    
    // 默认加载仪表盘
    console.log('加载默认仪表盘');
    switchSection('dashboard');
}

// 隐藏所有内容区
function hideAllSections() {
    console.log('隐藏所有内容区');
    const sections = document.querySelectorAll('.content > div');
    if (sections && sections.length > 0) {
        sections.forEach(section => {
            section.classList.add('d-none');
        });
    } else {
        console.error('找不到内容区域');
    }
}

// 切换内容区
async function switchSection(section) {
    console.log('切换到内容区:', section);
    hideAllSections();
    const sectionId = `${section}Section`;
    const sectionEl = document.getElementById(sectionId);
    if (!sectionEl) {
        console.error(`找不到内容区: ${sectionId}`);
        return;
    }
    
    sectionEl.classList.remove('d-none');
    
    // 加载对应区域的数据
    try {
        console.log(`加载${section}数据`);
        switch (section) {
            case 'dashboard':
                await loadDashboard();
                break;
            case 'users':
                await loadUsers();
                break;
            case 'projects':
                await loadProjects();
                break;
            case 'numbers':
                await loadNumbers();
                break;
            case 'notifications':
                await loadNotifications();
                break;
            case 'settings':
                await loadSettings();
                break;
            case 'logs':
                await loadLogs();
                break;
            case 'health':
                await loadHealth();
                break;
            default:
                console.warn(`未知的内容区: ${section}`);
                break;
        }
    } catch (error) {
        console.error(`加载${section}数据失败:`, error);
        showAlert('加载失败', error.message, 'danger');
    }
}

// 处理登录
async function handleLogin() {
    console.log('处理登录');
    
    // 立即显示一个基础提示，确保有反馈
    alert('正在处理登录请求...');
    
    const username = document.getElementById('adminUsername')?.value || '';
    const password = document.getElementById('adminPassword')?.value || '';
    
    if (!username || !password) {
        console.warn('用户名或密码为空');
        alert('登录失败：请输入用户名和密码');
        showAlert('登录失败', '请输入用户名和密码', 'danger');
        return;
    }
    
    console.log('登录信息校验通过，尝试登录');
    
    // 显示登录中状态
    const loginBtn = document.getElementById('loginBtn');
    if (!loginBtn) {
        console.error('找不到登录按钮');
        alert('登录失败：页面元素错误');
        showAlert('登录失败', '页面元素错误', 'danger');
        return;
    }
    
    const originalText = loginBtn.innerHTML;
    loginBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 登录中...';
    loginBtn.disabled = true;
    
    try {
        console.log('调用登录API');
        
        // 模拟登录，无论是否连接到真实API都能工作
        if (username === 'admin' && password === 'admin123') {
            console.log('用户名和密码匹配，模拟登录成功');
            alert('登录成功！用户名和密码正确');
            
            // 手动设置token
            localStorage.setItem('adminToken', 'mock_token_for_testing');
            
            showAlert('登录成功', '欢迎使用管理后台', 'success');
            document.body.classList.add('sidebar-visible');
            
            // 隐藏登录面板
            const loginPanel = document.getElementById('loginPanel');
            if (loginPanel) {
                loginPanel.classList.add('d-none');
            }
            
            // 显示管理界面
            showAdminPanel();
            return;
        }
        
        // 尝试API登录
        await AuthAPI.login(username, password);
        console.log('登录成功');
        alert('登录成功！欢迎使用管理后台');
        showAlert('登录成功', '欢迎使用管理后台', 'success');
        showAdminPanel();
    } catch (error) {
        console.error('登录失败:', error);
        alert('登录失败：' + (error.message || '用户名或密码错误'));
        showAlert('登录失败', error.message || '用户名或密码错误', 'danger');
        // 清空密码字段
        const passwordInput = document.getElementById('adminPassword');
        if (passwordInput) {
            passwordInput.value = '';
            passwordInput.focus();
        }
    } finally {
        // 恢复按钮状态
        loginBtn.innerHTML = originalText;
        loginBtn.disabled = false;
    }
}

// 注册各种事件处理
function registerEvents() {
    console.log('注册管理界面各事件');
    // 用户管理
    const addUserBtn = document.getElementById('addUserBtn');
    if (addUserBtn) {
        addUserBtn.addEventListener('click', showAddUserModal);
    } else {
        console.error('找不到添加用户按钮');
    }
    
    const searchUserBtn = document.getElementById('searchUserBtn');
    if (searchUserBtn) {
        searchUserBtn.addEventListener('click', () => loadUsers(1));
    } else {
        console.error('找不到搜索用户按钮');
    }
    
    // 项目管理
    const addProjectBtn = document.getElementById('addProjectBtn');
    if (addProjectBtn) {
        addProjectBtn.addEventListener('click', showAddProjectModal);
    } else {
        console.error('找不到添加项目按钮');
    }
    
    const searchProjectBtn = document.getElementById('searchProjectBtn');
    if (searchProjectBtn) {
        searchProjectBtn.addEventListener('click', () => loadProjects(1));
    } else {
        console.error('找不到搜索项目按钮');
    }
    
    // 号码管理
    const searchNumberBtn = document.getElementById('searchNumberBtn');
    if (searchNumberBtn) {
        searchNumberBtn.addEventListener('click', () => loadNumbers(1));
    } else {
        console.error('找不到搜索号码按钮');
    }
    
    const exportNumbersBtn = document.getElementById('exportNumbersBtn');
    if (exportNumbersBtn) {
        exportNumbersBtn.addEventListener('click', NumberAPI.exportNumbers);
    } else {
        console.error('找不到导出号码按钮');
    }
    
    // 通知管理
    const addNotificationBtn = document.getElementById('addNotificationBtn');
    if (addNotificationBtn) {
        addNotificationBtn.addEventListener('click', showAddNotificationModal);
    } else {
        console.error('找不到添加通知按钮');
    }
    
    // 健康监控
    const resetMetricsBtn = document.getElementById('resetMetricsBtn');
    if (resetMetricsBtn) {
        resetMetricsBtn.addEventListener('click', resetApiMetrics);
    } else {
        console.error('找不到重置指标按钮');
    }
    
    // 统计数据
    const exportStatsBtn = document.getElementById('exportStatsBtn');
    if (exportStatsBtn) {
        exportStatsBtn.addEventListener('click', StatisticsAPI.exportStats);
    } else {
        console.error('找不到导出统计按钮');
    }
    
    // 系统设置
    const settingsForm = document.getElementById('settingsForm');
    if (settingsForm) {
        settingsForm.addEventListener('submit', saveSettings);
    } else {
        console.error('找不到设置表单');
    }
    
    // 注册模态框事件
    registerModalEvents();
}

// 加载仪表盘数据
async function loadDashboard() {
    try {
        const stats = await StatisticsAPI.getDashboardStats();
        
        // 更新仪表盘统计卡片
        const dashboardStats = document.getElementById('dashboardStats');
        dashboardStats.innerHTML = `
            <div class="col-md-3 mb-3">
                <div class="card text-white bg-primary">
                    <div class="card-body">
                        <h5 class="card-title">总用户数</h5>
                        <h2>${stats.user_count}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="card text-white bg-success">
                    <div class="card-body">
                        <h5 class="card-title">项目数量</h5>
                        <h2>${stats.project_count}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="card text-white bg-info">
                    <div class="card-body">
                        <h5 class="card-title">号码总数</h5>
                        <h2>${stats.number_count}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="card text-white bg-warning">
                    <div class="card-body">
                        <h5 class="card-title">交易笔数</h5>
                        <h2>${stats.transaction_count}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-4 mb-3">
                <div class="card bg-light">
                    <div class="card-body">
                        <h5 class="card-title">用户总余额</h5>
                        <h2>¥ ${stats.total_balance.toFixed(2)}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-4 mb-3">
                <div class="card bg-light">
                    <div class="card-body">
                        <h5 class="card-title">累计收入</h5>
                        <h2>¥ ${stats.total_income.toFixed(2)}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-4 mb-3">
                <div class="card bg-light">
                    <div class="card-body">
                        <h5 class="card-title">累计消费</h5>
                        <h2>¥ ${stats.total_consume.toFixed(2)}</h2>
                    </div>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('加载仪表盘失败:', error);
        showAlert('加载失败', '获取仪表盘数据失败', 'danger');
    }
}

// 加载用户管理数据
async function loadUsers(page = currentPage.users) {
    try {
        currentPage.users = page;
        const keyword = document.getElementById('userSearchKeyword').value;
        const result = await UserAPI.getUsers(page, 20, keyword);
        
        // 更新用户表格
        const userTableBody = document.getElementById('userTableBody');
        userTableBody.innerHTML = '';
        
        result.items.forEach(user => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${user.id}</td>
                <td>${user.username}</td>
                <td>${user.email}</td>
                <td>¥ ${user.balance.toFixed(2)}</td>
                <td>${user.is_admin ? '<span class="badge bg-warning">是</span>' : '<span class="badge bg-secondary">否</span>'}</td>
                <td>${user.is_active ? '<span class="badge bg-success">正常</span>' : '<span class="badge bg-danger">禁用</span>'}</td>
                <td>${new Date(user.created_at).toLocaleString()}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editUser(${user.id})"><i class="fas fa-edit"></i></button>
                    <button class="btn btn-sm ${user.is_active ? 'btn-outline-danger' : 'btn-outline-success'}" onclick="toggleUserStatus(${user.id}, ${user.is_active})">
                        <i class="fas ${user.is_active ? 'fa-ban' : 'fa-check'}"></i>
                    </button>
                </td>
            `;
            userTableBody.appendChild(row);
        });
        
        // 更新分页
        updatePagination('userPagination', result, loadUsers);
    } catch (error) {
        console.error('加载用户数据失败:', error);
        showAlert('加载失败', '获取用户数据失败', 'danger');
    }
}

// 加载项目管理数据
async function loadProjects(page = currentPage.projects) {
    try {
        currentPage.projects = page;
        const keyword = document.getElementById('projectSearchKeyword').value;
        const result = await ProjectAPI.getProjects(page, 20, keyword);
        
        // 更新项目表格
        const projectTableBody = document.getElementById('projectTableBody');
        projectTableBody.innerHTML = '';
        
        result.items.forEach(project => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${project.id}</td>
                <td title="${project.exclusive_id || ''}">${project.project_id || '-'}</td>
                <td>${project.name}</td>
                <td>${project.code}</td>
                <td>¥ ${project.price.toFixed(2)}</td>
                <td>${project.success_rate}%</td>
                <td>${project.available ? '<span class="badge bg-success">是</span>' : '<span class="badge bg-danger">否</span>'}</td>
                <td>${project.is_exclusive ? '<span class="badge bg-info">是</span>' : '<span class="badge bg-secondary">否</span>'}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editProject(${project.id})" title="编辑项目"><i class="fas fa-edit"></i></button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteProject(${project.id})" title="删除项目"><i class="fas fa-trash"></i></button>
                </td>
            `;
            projectTableBody.appendChild(row);
        });
        
        // 更新分页
        updatePagination('projectPagination', result, loadProjects);
    } catch (error) {
        console.error('加载项目数据失败:', error);
        showAlert('加载失败', '获取项目数据失败', 'danger');
    }
}

// 加载号码管理数据
async function loadNumbers(page = currentPage.numbers) {
    try {
        currentPage.numbers = page;
        const keyword = document.getElementById('numberSearchKeyword').value;
        const status = document.getElementById('numberStatusFilter').value;
        const result = await NumberAPI.getNumbers(page, 20, keyword, status);
        
        // 更新号码表格
        const numberTableBody = document.getElementById('numberTableBody');
        numberTableBody.innerHTML = '';
        
        result.items.forEach(number => {
            let statusBadge = '';
            switch (number.status) {
                case 'available':
                    statusBadge = '<span class="badge bg-success">可用</span>';
                    break;
                case 'used':
                    statusBadge = '<span class="badge bg-warning">已用</span>';
                    break;
                case 'released':
                    statusBadge = '<span class="badge bg-info">已释放</span>';
                    break;
                case 'blacklisted':
                    statusBadge = '<span class="badge bg-danger">黑名单</span>';
                    break;
                default:
                    statusBadge = '<span class="badge bg-secondary">未知</span>';
            }
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${number.id}</td>
                <td>${number.number}</td>
                <td>${statusBadge}</td>
                <td>${number.project ? number.project.name : '-'}</td>
                <td>${number.user ? number.user.username : '-'}</td>
                <td>${number.request_id || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editNumberStatus(${number.id})"><i class="fas fa-edit"></i></button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteNumber(${number.id})"><i class="fas fa-trash"></i></button>
                </td>
            `;
            numberTableBody.appendChild(row);
        });
        
        // 更新分页
        updatePagination('numberPagination', result, loadNumbers);
    } catch (error) {
        console.error('加载号码数据失败:', error);
        showAlert('加载失败', '获取号码数据失败', 'danger');
    }
}

// 加载通知管理数据
async function loadNotifications(page = currentPage.notifications) {
    try {
        currentPage.notifications = page;
        const result = await NotificationAPI.getNotifications(page, 20);
        
        // 更新通知表格
        const notificationTableBody = document.getElementById('notificationTableBody');
        notificationTableBody.innerHTML = '';
        
        result.items.forEach(notification => {
            const typeBadge = getNotificationTypeBadge(notification.type);
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${notification.id}</td>
                <td>${notification.title}</td>
                <td>${notification.content.length > 30 ? notification.content.substring(0, 30) + '...' : notification.content}</td>
                <td>${typeBadge}</td>
                <td>${notification.is_global ? '<span class="badge bg-success">是</span>' : '<span class="badge bg-secondary">否</span>'}</td>
                <td>${notification.user_id || '-'}</td>
                <td>${new Date(notification.created_at).toLocaleString()}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editNotification(${notification.id})"><i class="fas fa-edit"></i></button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteNotification(${notification.id})"><i class="fas fa-trash"></i></button>
                </td>
            `;
            notificationTableBody.appendChild(row);
        });
        
        // 更新分页
        updatePagination('notificationPagination', result, loadNotifications);
    } catch (error) {
        console.error('加载通知数据失败:', error);
        showAlert('加载失败', '获取通知数据失败', 'danger');
    }
}

// 加载系统设置数据
async function loadSettings() {
    try {
        const settings = await SettingsAPI.getSettings();
        
        // 填充设置表单
        document.getElementById('systemName').value = settings.system_name || '';
        document.getElementById('maintenanceMode').value = settings.maintenance_mode ? 'true' : 'false';
        document.getElementById('defaultPrice').value = settings.default_price || 0;
        document.getElementById('minTopup').value = settings.min_topup || 0;
        document.getElementById('maxTopup').value = settings.max_topup || 0;
        document.getElementById('smsTimeout').value = settings.sms_timeout || 60;
        document.getElementById('lowBalanceAlert').value = settings.low_balance_alert || 0;
        document.getElementById('numberPoolThreshold').value = settings.number_pool_threshold || 0;
    } catch (error) {
        console.error('加载设置失败:', error);
        showAlert('加载失败', '获取系统设置失败', 'danger');
    }
}

// 加载操作日志数据
async function loadLogs(page = currentPage.logs) {
    try {
        currentPage.logs = page;
        const result = await LogAPI.getLogs(page, 20);
        
        // 更新日志表格
        const logTableBody = document.getElementById('logTableBody');
        logTableBody.innerHTML = '';
        
        result.items.forEach(log => {
            let levelBadge = '';
            switch (log.level.toLowerCase()) {
                case 'info':
                    levelBadge = '<span class="badge bg-info">信息</span>';
                    break;
                case 'warning':
                    levelBadge = '<span class="badge bg-warning">警告</span>';
                    break;
                case 'error':
                    levelBadge = '<span class="badge bg-danger">错误</span>';
                    break;
                case 'debug':
                    levelBadge = '<span class="badge bg-secondary">调试</span>';
                    break;
                default:
                    levelBadge = `<span class="badge bg-secondary">${log.level}</span>`;
            }
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${log.id}</td>
                <td>${new Date(log.created_at).toLocaleString()}</td>
                <td>${levelBadge}</td>
                <td>${log.content}</td>
                <td>${log.user ? log.user.username : '-'}</td>
                <td>${log.ip_address || '-'}</td>
            `;
            logTableBody.appendChild(row);
        });
        
        // 更新分页
        updatePagination('logPagination', result, loadLogs);
    } catch (error) {
        console.error('加载日志失败:', error);
        showAlert('加载失败', '获取操作日志失败', 'danger');
    }
}

// 加载健康监控数据
async function loadHealth() {
    try {
        const health = await SystemAPI.getHealth();
        const metrics = await SystemAPI.getMetrics();
        
        // 更新健康状态卡片
        const healthStats = document.getElementById('healthStats');
        healthStats.innerHTML = `
            <div class="col-md-3 mb-3">
                <div class="card text-white ${health.status === 'ok' ? 'bg-success' : 'bg-danger'}">
                    <div class="card-body">
                        <h5 class="card-title">系统状态</h5>
                        <p class="card-text">${health.status === 'ok' ? '正常运行' : '故障'}</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="card bg-light">
                    <div class="card-body">
                        <h5 class="card-title">运行时间</h5>
                        <p class="card-text">${health.uptime_formatted}</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="card bg-light">
                    <div class="card-body">
                        <h5 class="card-title">环境</h5>
                        <p class="card-text">${health.environment}</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="card bg-light">
                    <div class="card-body">
                        <h5 class="card-title">版本</h5>
                        <p class="card-text">${health.version}</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4 mb-3">
                <div class="card text-white ${health.services.database === 'healthy' ? 'bg-success' : 'bg-danger'}">
                    <div class="card-body">
                        <h5 class="card-title">数据库</h5>
                        <p class="card-text">${health.services.database === 'healthy' ? '正常' : '故障'}</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4 mb-3">
                <div class="card bg-info text-white">
                    <div class="card-body">
                        <h5 class="card-title">CPU使用率</h5>
                        <p class="card-text">${health.system.cpu_usage}%</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4 mb-3">
                <div class="card bg-warning ${health.system.memory.percent > 80 ? 'text-white' : ''}">
                    <div class="card-body">
                        <h5 class="card-title">内存使用率</h5>
                        <p class="card-text">${health.system.memory.percent}%</p>
                    </div>
                </div>
            </div>
            <div class="col-md-6 mb-3">
                <div class="card bg-light">
                    <div class="card-body">
                        <h5 class="card-title">API请求总数</h5>
                        <p class="fs-4">${metrics.total_requests}</p>
                        <div class="progress">
                            <div class="progress-bar bg-success" role="progressbar" style="width: ${metrics.success_rate}%" aria-valuenow="${metrics.success_rate}" aria-valuemin="0" aria-valuemax="100">${metrics.success_rate.toFixed(1)}%</div>
                        </div>
                        <div class="d-flex justify-content-between mt-2">
                            <small>成功: ${metrics.successful_requests}</small>
                            <small>失败: ${metrics.failed_requests}</small>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6 mb-3">
                <div class="card bg-light">
                    <div class="card-body">
                        <h5 class="card-title">最常用端点</h5>
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>端点</th>
                                    <th>调用数</th>
                                    <th>成功率</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${metrics.endpoints.slice(0, 5).map(endpoint => `
                                    <tr>
                                        <td>${endpoint.endpoint}</td>
                                        <td>${endpoint.calls}</td>
                                        <td>
                                            <div class="progress" style="height: 5px;">
                                                <div class="progress-bar bg-success" role="progressbar" style="width: ${endpoint.success_rate}%"></div>
                                            </div>
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('加载健康监控数据失败:', error);
        showAlert('加载失败', '获取健康监控数据失败', 'danger');
    }
}

// 工具函数：更新分页器
function updatePagination(paginationId, data, loadFunction) {
    const pagination = document.getElementById(paginationId);
    if (!pagination) return;
    
    pagination.innerHTML = '';
    if (data.pages <= 1) return;
    
    // 上一页
    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${data.page <= 1 ? 'disabled' : ''}`;
    prevLi.innerHTML = `<a class="page-link" href="#" ${data.page > 1 ? `onclick="return ${loadFunction.name}(${data.page - 1})"` : ''}>上一页</a>`;
    pagination.appendChild(prevLi);
    
    // 页码
    const startPage = Math.max(1, data.page - 2);
    const endPage = Math.min(data.pages, data.page + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        const li = document.createElement('li');
        li.className = `page-item ${i === data.page ? 'active' : ''}`;
        li.innerHTML = `<a class="page-link" href="#" onclick="return ${loadFunction.name}(${i})">${i}</a>`;
        pagination.appendChild(li);
    }
    
    // 下一页
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${data.page >= data.pages ? 'disabled' : ''}`;
    nextLi.innerHTML = `<a class="page-link" href="#" ${data.page < data.pages ? `onclick="return ${loadFunction.name}(${data.page + 1})"` : ''}>下一页</a>`;
    pagination.appendChild(nextLi);
}

// 获取通知类型对应的标签
function getNotificationTypeBadge(type) {
    switch (type) {
        case 'info':
            return '<span class="badge bg-info">信息</span>';
        case 'warning':
            return '<span class="badge bg-warning">警告</span>';
        case 'error':
            return '<span class="badge bg-danger">错误</span>';
        case 'success':
            return '<span class="badge bg-success">成功</span>';
        default:
            return `<span class="badge bg-secondary">${type}</span>`;
    }
}

// 重置API指标
async function resetApiMetrics() {
    if (!confirm('确定要重置API指标吗？')) return;
    
    try {
        await SystemAPI.resetMetrics();
        showAlert('成功', 'API指标已重置', 'success');
        loadHealth();
    } catch (error) {
        console.error('重置API指标失败:', error);
        showAlert('操作失败', '重置API指标失败', 'danger');
    }
}

// 保存系统设置
async function saveSettings(e) {
    e.preventDefault();
    
    const settingsData = {
        system_name: document.getElementById('systemName').value,
        maintenance_mode: document.getElementById('maintenanceMode').value === 'true',
        default_price: parseFloat(document.getElementById('defaultPrice').value),
        min_topup: parseFloat(document.getElementById('minTopup').value),
        max_topup: parseFloat(document.getElementById('maxTopup').value),
        sms_timeout: parseInt(document.getElementById('smsTimeout').value),
        low_balance_alert: parseFloat(document.getElementById('lowBalanceAlert').value),
        number_pool_threshold: parseInt(document.getElementById('numberPoolThreshold').value)
    };
    
    try {
        await SettingsAPI.updateSettings(settingsData);
        showAlert('成功', '系统设置已保存', 'success');
    } catch (error) {
        console.error('保存设置失败:', error);
        showAlert('保存失败', error.message, 'danger');
    }
}

// 这些函数需要在全局作用域中定义，以便在HTML中直接调用
// 用户管理相关
function editUser(userId) {
    // 获取用户信息并显示在模态框中
    UserAPI.getUserDetail(userId)
        .then(response => {
            const user = response.user;
            document.getElementById('userId').value = user.id;
            document.getElementById('username').value = user.username;
            document.getElementById('email').value = user.email;
            document.getElementById('password').value = '';
            document.getElementById('balance').value = user.balance;
            document.getElementById('isAdmin').checked = user.is_admin;
            document.getElementById('isActive').checked = user.is_active;
            
            document.getElementById('userModalTitle').textContent = '编辑用户';
            const userModal = new bootstrap.Modal(document.getElementById('userModal'));
            userModal.show();
        })
        .catch(error => {
            console.error('获取用户信息失败:', error);
            showAlert('错误', '获取用户信息失败', 'danger');
        });
}

function toggleUserStatus(userId, isActive) {
    // 确认操作
    if (!confirm(`确定要${isActive ? '禁用' : '启用'}该用户吗？`)) return;
    
    // 更新用户状态
    UserAPI.updateUser(userId, { is_active: !isActive })
        .then(() => {
            showAlert('成功', `用户已${isActive ? '禁用' : '启用'}`, 'success');
            loadUsers(currentPage.users);
        })
        .catch(error => {
            console.error('更新用户状态失败:', error);
            showAlert('错误', '更新用户状态失败', 'danger');
        });
}

function showAddUserModal() {
    // 清空表单
    document.getElementById('userId').value = '';
    document.getElementById('username').value = '';
    document.getElementById('email').value = '';
    document.getElementById('password').value = '';
    document.getElementById('balance').value = '0';
    document.getElementById('isAdmin').checked = false;
    document.getElementById('isActive').checked = true;
    
    document.getElementById('userModalTitle').textContent = '新增用户';
    const userModal = new bootstrap.Modal(document.getElementById('userModal'));
    userModal.show();
}

// 项目管理相关
function editProject(projectId) {
    ProjectAPI.getProjects()
        .then(response => {
            const project = response.items.find(p => p.id === projectId);
            if (!project) throw new Error('项目不存在');
            
            document.getElementById('projectId').value = project.id;
            
            // 设置项目ID和专属项目ID（只读字段）
            document.getElementById('displayProjectId').value = project.project_id || '-';
            document.getElementById('displayExclusiveId').value = project.exclusive_id || '';
            
            // 根据是否为专属项目显示专属ID字段
            document.getElementById('exclusiveIdContainer').style.display = 
                project.is_exclusive ? 'block' : 'none';
            
            document.getElementById('projectName').value = project.name;
            document.getElementById('projectCode').value = project.code;
            document.getElementById('projectPrice').value = project.price;
            document.getElementById('successRate').value = project.success_rate;
            document.getElementById('projectDescription').value = project.description || '';
            document.getElementById('projectAvailable').checked = project.available;
            document.getElementById('isExclusive').checked = project.is_exclusive;
            
            // 添加专属项目checkbox的事件监听，控制专属ID字段的显示
            document.getElementById('isExclusive').onchange = function() {
                document.getElementById('exclusiveIdContainer').style.display = 
                    this.checked ? 'block' : 'none';
            };
            
            document.getElementById('projectModalTitle').textContent = '编辑项目';
            const projectModal = new bootstrap.Modal(document.getElementById('projectModal'));
            projectModal.show();
        })
        .catch(error => {
            console.error('获取项目信息失败:', error);
            showAlert('错误', '获取项目信息失败', 'danger');
        });
}

function deleteProject(projectId) {
    if (!confirm('确定要删除该项目吗？此操作不可逆！')) return;
    
    ProjectAPI.deleteProject(projectId)
        .then(() => {
            showAlert('成功', '项目已删除', 'success');
            loadProjects(currentPage.projects);
        })
        .catch(error => {
            console.error('删除项目失败:', error);
            showAlert('错误', '删除项目失败', 'danger');
        });
}

function showAddProjectModal() {
    // 清空表单
    document.getElementById('projectId').value = '';
    
    // 隐藏项目ID和专属项目ID字段（新增时不可见）
    document.getElementById('displayProjectId').value = '创建后自动生成';
    document.getElementById('displayExclusiveId').value = '创建后自动生成';
    document.getElementById('exclusiveIdContainer').style.display = 'none';
    
    document.getElementById('projectName').value = '';
    document.getElementById('projectCode').value = '';
    document.getElementById('projectPrice').value = '';
    document.getElementById('successRate').value = '0';
    document.getElementById('projectDescription').value = '';
    document.getElementById('projectAvailable').checked = true;
    document.getElementById('isExclusive').checked = false;
    
    // 添加专属项目checkbox的事件监听，控制专属ID字段的显示
    document.getElementById('isExclusive').onchange = function() {
        document.getElementById('exclusiveIdContainer').style.display = 
            this.checked ? 'block' : 'none';
    };
    
    document.getElementById('projectModalTitle').textContent = '新增项目';
    const projectModal = new bootstrap.Modal(document.getElementById('projectModal'));
    projectModal.show();
}

// 号码管理相关
function editNumberStatus(numberId) {
    // 获取号码列表中的当前号码
    NumberAPI.getNumbers()
        .then(response => {
            const number = response.items.find(n => n.id === numberId);
            if (!number) throw new Error('号码不存在');
            
            document.getElementById('numberId').value = number.id;
            document.getElementById('numberStatus').value = number.status;
            
            const numberModal = new bootstrap.Modal(document.getElementById('numberStatusModal'));
            numberModal.show();
        })
        .catch(error => {
            console.error('获取号码信息失败:', error);
            showAlert('错误', '获取号码信息失败', 'danger');
        });
}

function deleteNumber(numberId) {
    if (!confirm('确定要删除该号码吗？此操作不可逆！')) return;
    
    NumberAPI.deleteNumber(numberId)
        .then(() => {
            showAlert('成功', '号码已删除', 'success');
            loadNumbers(currentPage.numbers);
        })
        .catch(error => {
            console.error('删除号码失败:', error);
            showAlert('错误', '删除号码失败', 'danger');
        });
}

// 通知管理相关
function editNotification(notificationId) {
    NotificationAPI.getNotifications()
        .then(response => {
            const notification = response.items.find(n => n.id === notificationId);
            if (!notification) throw new Error('通知不存在');
            
            document.getElementById('notificationId').value = notification.id;
            document.getElementById('notificationTitle').value = notification.title;
            document.getElementById('notificationContent').value = notification.content;
            document.getElementById('notificationType').value = notification.type;
            document.getElementById('isGlobal').checked = notification.is_global;
            document.getElementById('notificationUserId').value = notification.user_id || '';
            
            // 根据是否全局通知控制用户ID输入框的显示
            toggleUserIdField();
            
            document.getElementById('notificationModalTitle').textContent = '编辑通知';
            const notificationModal = new bootstrap.Modal(document.getElementById('notificationModal'));
            notificationModal.show();
        })
        .catch(error => {
            console.error('获取通知信息失败:', error);
            showAlert('错误', '获取通知信息失败', 'danger');
        });
}

function deleteNotification(notificationId) {
    if (!confirm('确定要删除该通知吗？')) return;
    
    NotificationAPI.deleteNotification(notificationId)
        .then(() => {
            showAlert('成功', '通知已删除', 'success');
            loadNotifications(currentPage.notifications);
        })
        .catch(error => {
            console.error('删除通知失败:', error);
            showAlert('错误', '删除通知失败', 'danger');
        });
}

function showAddNotificationModal() {
    // 清空表单
    document.getElementById('notificationId').value = '';
    document.getElementById('notificationTitle').value = '';
    document.getElementById('notificationContent').value = '';
    document.getElementById('notificationType').value = 'info';
    document.getElementById('isGlobal').checked = true;
    document.getElementById('notificationUserId').value = '';
    
    // 根据是否全局通知控制用户ID输入框的显示
    toggleUserIdField();
    
    document.getElementById('notificationModalTitle').textContent = '新增通知';
    const notificationModal = new bootstrap.Modal(document.getElementById('notificationModal'));
    notificationModal.show();
}

// 工具函数：根据是否全局通知控制用户ID输入框的显示
function toggleUserIdField() {
    const isGlobal = document.getElementById('isGlobal').checked;
    document.getElementById('userIdContainer').style.display = isGlobal ? 'none' : 'block';
}

// 注册模态框内的事件
function registerModalEvents() {
    // 用户模态框
    document.getElementById('saveUserBtn').addEventListener('click', function() {
        const userId = document.getElementById('userId').value;
        const userData = {
            username: document.getElementById('username').value,
            email: document.getElementById('email').value,
            is_admin: document.getElementById('isAdmin').checked,
            is_active: document.getElementById('isActive').checked,
            balance: parseFloat(document.getElementById('balance').value)
        };
        
        const password = document.getElementById('password').value;
        if (password) {
            userData.password = password;
        }
        
        if (userId) {
            // 更新用户
            UserAPI.updateUser(userId, userData)
                .then(() => {
                    bootstrap.Modal.getInstance(document.getElementById('userModal')).hide();
                    showAlert('成功', '用户信息已更新', 'success');
                    loadUsers(currentPage.users);
                })
                .catch(error => {
                    console.error('更新用户失败:', error);
                    showAlert('错误', '更新用户失败: ' + error.message, 'danger');
                });
        } else {
            // 新建用户
            if (!password) {
                showAlert('错误', '新建用户必须设置密码', 'danger');
                return;
            }
            
            UserAPI.createUser(userData)
                .then(() => {
                    bootstrap.Modal.getInstance(document.getElementById('userModal')).hide();
                    showAlert('成功', '用户已创建', 'success');
                    loadUsers(1);
                })
                .catch(error => {
                    console.error('创建用户失败:', error);
                    showAlert('错误', '创建用户失败: ' + error.message, 'danger');
                });
        }
    });
    
    // 项目模态框
    document.getElementById('saveProjectBtn').addEventListener('click', function() {
        const projectId = document.getElementById('projectId').value;
        const projectData = {
            name: document.getElementById('projectName').value,
            code: document.getElementById('projectCode').value,
            price: parseFloat(document.getElementById('projectPrice').value),
            success_rate: parseFloat(document.getElementById('successRate').value),
            description: document.getElementById('projectDescription').value,
            available: document.getElementById('projectAvailable').checked,
            is_exclusive: document.getElementById('isExclusive').checked
        };
        
        if (projectId) {
            // 更新项目
            ProjectAPI.updateProject(projectId, projectData)
                .then(() => {
                    bootstrap.Modal.getInstance(document.getElementById('projectModal')).hide();
                    showAlert('成功', '项目信息已更新', 'success');
                    loadProjects(currentPage.projects);
                })
                .catch(error => {
                    console.error('更新项目失败:', error);
                    showAlert('错误', '更新项目失败: ' + error.message, 'danger');
                });
        } else {
            // 新建项目
            ProjectAPI.createProject(projectData)
                .then(() => {
                    bootstrap.Modal.getInstance(document.getElementById('projectModal')).hide();
                    showAlert('成功', '项目已创建', 'success');
                    loadProjects(1);
                })
                .catch(error => {
                    console.error('创建项目失败:', error);
                    showAlert('错误', '创建项目失败: ' + error.message, 'danger');
                });
        }
    });
    
    // 号码状态模态框
    document.getElementById('saveNumberStatusBtn').addEventListener('click', function() {
        const numberId = document.getElementById('numberId').value;
        const numberData = {
            status: document.getElementById('numberStatus').value
        };
        
        NumberAPI.updateNumber(numberId, numberData)
            .then(() => {
                bootstrap.Modal.getInstance(document.getElementById('numberStatusModal')).hide();
                showAlert('成功', '号码状态已更新', 'success');
                loadNumbers(currentPage.numbers);
            })
            .catch(error => {
                console.error('更新号码状态失败:', error);
                showAlert('错误', '更新号码状态失败: ' + error.message, 'danger');
            });
    });
    
    // 通知模态框
    document.getElementById('isGlobal').addEventListener('change', toggleUserIdField);
    
    document.getElementById('saveNotificationBtn').addEventListener('click', function() {
        const notificationId = document.getElementById('notificationId').value;
        const notificationData = {
            title: document.getElementById('notificationTitle').value,
            content: document.getElementById('notificationContent').value,
            type: document.getElementById('notificationType').value,
            is_global: document.getElementById('isGlobal').checked
        };
        
        if (!notificationData.is_global) {
            const userId = document.getElementById('notificationUserId').value;
            if (!userId) {
                showAlert('错误', '非全局通知必须指定用户ID', 'danger');
                return;
            }
            notificationData.user_id = parseInt(userId);
        }
        
        if (notificationId) {
            // 更新通知
            NotificationAPI.updateNotification(notificationId, notificationData)
                .then(() => {
                    bootstrap.Modal.getInstance(document.getElementById('notificationModal')).hide();
                    showAlert('成功', '通知信息已更新', 'success');
                    loadNotifications(currentPage.notifications);
                })
                .catch(error => {
                    console.error('更新通知失败:', error);
                    showAlert('错误', '更新通知失败: ' + error.message, 'danger');
                });
        } else {
            // 新建通知
            NotificationAPI.createNotification(notificationData)
                .then(() => {
                    bootstrap.Modal.getInstance(document.getElementById('notificationModal')).hide();
                    showAlert('成功', '通知已创建', 'success');
                    loadNotifications(1);
                })
                .catch(error => {
                    console.error('创建通知失败:', error);
                    showAlert('错误', '创建通知失败: ' + error.message, 'danger');
                });
        }
    });
}

// 工具函数：显示提示消息
function showAlert(title, message, type = 'info') {
    console.log(`显示提示: ${type} - ${title} - ${message}`);
    
    // 如果是登录相关的错误，显示在登录表单下方
    if (type === 'danger' && title === '登录失败') {
        // 创建错误提示
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger mt-3';
        alertDiv.innerHTML = `<i class="fas fa-exclamation-circle me-1"></i> ${message}`;
        
        // 在登录错误占位符中显示
        const errorContainer = document.getElementById('loginErrorPlaceholder');
        if (errorContainer) {
            console.log('在登录面板中显示错误');
            errorContainer.innerHTML = ''; // 清除旧消息
            errorContainer.appendChild(alertDiv);
            
            // 5秒后自动关闭
            setTimeout(() => {
                if (errorContainer.contains(alertDiv)) {
                    errorContainer.innerHTML = '';
                }
            }, 5000);
            return;
        } else {
            console.error('找不到登录错误占位符');
        }
    }
    
    // 创建一个Toast提示
    const toastContainer = document.createElement('div');
    toastContainer.className = 'position-fixed top-0 end-0 p-3';
    toastContainer.style.zIndex = '1050';
    
    // 根据类型选择不同背景色
    let bgColor = 'bg-info';
    if (type === 'success') bgColor = 'bg-success';
    if (type === 'danger') bgColor = 'bg-danger';
    if (type === 'warning') bgColor = 'bg-warning';
    
    toastContainer.innerHTML = `
        <div class="toast show" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header ${bgColor} text-white">
                <strong class="me-auto">${title}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    document.body.appendChild(toastContainer);
    
    // 3秒后自动关闭
    setTimeout(() => {
        if (document.body.contains(toastContainer)) {
            document.body.removeChild(toastContainer);
        }
    }, 3000);
} 