// 前端配置文件
const CONFIG = {
    // API基础URL - AICOACH服务运行在8080端口
    API_BASE_URL: 'http://localhost:8080/api/v1',

    // 前端开发服务器端口
    DEV_PORT: 3001,

    // 请求超时时间（毫秒）
    TIMEOUT: 30000,

    // 是否启用调试模式
    DEBUG: true
};

// 导出配置
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}
