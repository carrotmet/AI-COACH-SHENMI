/**
 * 星图403问题调试工具
 * 在浏览器控制台执行此脚本来诊断问题
 */

(function debugStar403() {
    console.log('=== 星图403问题诊断 ===\n');
    
    // 1. 检查token
    const token = localStorage.getItem('access_token');
    console.log('【1】Token检查:');
    if (!token) {
        console.error('✗ 未找到access_token，用户未登录');
        console.log('解决方案: 跳转到登录页面');
        return;
    }
    console.log('✓ Token存在:', token.substring(0, 20) + '...');
    
    // 2. 解析token
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        console.log('【2】Token解析:');
        console.log('  - 用户ID:', payload.sub);
        console.log('  - Token类型:', payload.type);
        console.log('  - 过期时间:', new Date(payload.exp * 1000).toLocaleString());
        
        if (payload.exp * 1000 < Date.now()) {
            console.error('✗ Token已过期');
            console.log('解决方案: 调用refresh token或重新登录');
        } else {
            console.log('✓ Token未过期');
        }
    } catch (e) {
        console.error('✗ Token格式无效:', e.message);
    }
    
    // 3. 测试API调用
    console.log('\n【3】API调用测试:');
    
    fetch('/api/v1/star/graph?depth=3', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Accept': 'application/json'
        }
    })
    .then(response => {
        console.log('  - 状态码:', response.status);
        console.log('  - 状态文本:', response.statusText);
        
        if (response.status === 403) {
            console.error('✗ 403 Forbidden - 权限不足');
            console.log('可能原因:');
            console.log('  1. 用户状态不是active');
            console.log('  2. Token被篡改');
            console.log('  3. 后端路由权限配置错误');
        } else if (response.status === 401) {
            console.error('✗ 401 Unauthorized - 未授权');
            console.log('可能原因:');
            console.log('  1. Token缺失');
            console.log('  2. Token无效');
            console.log('  3. Token过期');
        } else if (response.status === 200) {
            console.log('✓ API调用成功');
        }
        
        return response.json();
    })
    .then(data => {
        console.log('【4】响应数据:');
        console.log('  - code:', data.code);
        console.log('  - message:', data.message);
        if (data.data) {
            console.log('  - data:', data.data);
        }
    })
    .catch(error => {
        console.error('✗ 请求失败:', error.message);
    });
    
    console.log('\n=== 诊断完成 ===');
})();
