/**
 * 接码平台管理后台 - 简化登录处理
 */
console.log('=====================================');
console.log('login.js 加载成功！登录模块初始化中...');
console.log('=====================================');

// 在页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('登录页面加载完成');
    
    // 检查是否已登录
    if (localStorage.getItem('adminToken')) {
        // 已有token，直接进入管理界面
        console.log('已有token，尝试使用现有登录状态');
        showAdminPanel();
    } else {
        console.log('未登录，显示登录界面');
        showLoginForm();
    }
    
    // 绑定登录按钮事件
    const loginBtn = document.getElementById('loginBtn');
    if (loginBtn) {
        loginBtn.addEventListener('click', handleLogin);
        console.log('登录按钮事件绑定完成 (login.js)');
    } else {
        console.error('找不到登录按钮');
    }
    
    // 绑定回车键登录
    const passwordInput = document.getElementById('adminPassword');
    if (passwordInput) {
        passwordInput.addEventListener('keyup', function(event) {
            if (event.key === "Enter") {
                handleLogin();
            }
        });
    }
});

// 显示登录表单
function showLoginForm() {
    // 确保登录面板可见
    const loginPanel = document.getElementById('loginPanel');
    if (loginPanel) {
        loginPanel.style.display = 'flex';
    }
    
    // 隐藏侧边栏
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.style.display = 'none';
    }
    
    // 聚焦用户名输入框
    setTimeout(function() {
        const usernameInput = document.getElementById('adminUsername');
        if (usernameInput) {
            usernameInput.focus();
        }
    }, 100);
}

// 显示管理面板
function showAdminPanel() {
    // 隐藏登录面板
    const loginPanel = document.getElementById('loginPanel');
    if (loginPanel) {
        loginPanel.style.display = 'none';
    }
    
    // 显示侧边栏
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.style.display = 'flex';
    }
    
    // 调整内容区域样式
    const content = document.querySelector('.content');
    if (content) {
        content.style.marginLeft = '220px';
    }
    
    // 显示默认内容区域（仪表盘）
    const dashboardSection = document.getElementById('dashboardSection');
    if (dashboardSection) {
        dashboardSection.classList.remove('d-none');
    }
}

// 处理登录
function handleLogin() {
    console.log('处理登录请求');
    alert('处理登录请求...');
    
    // 获取用户名和密码
    const username = document.getElementById('adminUsername').value;
    const password = document.getElementById('adminPassword').value;
    
    if (!username || !password) {
        alert('请输入用户名和密码');
        return;
    }
    
    // 简化登录逻辑，直接使用硬编码的账号密码
    if (username === 'admin' && password === 'admin123') {
        // 登录成功
        localStorage.setItem('adminToken', 'mock_token_for_testing');
        alert('登录成功！欢迎使用管理后台');
        showAdminPanel();
    } else {
        // 登录失败
        alert('用户名或密码错误');
        document.getElementById('adminPassword').value = '';
        document.getElementById('adminPassword').focus();
        
        // 显示错误消息
        const errorContainer = document.getElementById('loginErrorPlaceholder');
        if (errorContainer) {
            errorContainer.innerHTML = '<div class="alert alert-danger"><i class="fas fa-exclamation-circle me-1"></i> 用户名或密码错误</div>';
        }
    }
}

// 退出登录
function handleLogout() {
    localStorage.removeItem('adminToken');
    alert('已退出登录');
    showLoginForm();
} 