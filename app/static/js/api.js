/**
 * API 请求函数
 */

// 测试 API Token 并获取模型列表
async function testApiToken(token, language) {
    try {
        showLoading();
        const response = await fetch('/api/test-token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                token,
                language
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error?.message || errorData.message || '请求失败');
        }
        
        return await response.json();
    } catch (error) {
        console.error('测试 Token 失败:', error);
        throw error;
    } finally {
        hideLoading();
    }
}

// 测试单个模型
async function testModel(token, modelId) {
    try {
        showLoading();
        const response = await fetch('/api/test-model', {  // 修正 URL
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                token,
                model_id: modelId  // 修正参数名称，与后端匹配
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            return {
                success: false,
                error: errorData.error?.message || errorData.message || '请求失败',
                status_code: response.status,
                response_time: 0
            };
        }
        
        return await response.json();
    } catch (error) {
        console.error(`测试模型 ${modelId} 失败:`, error);
        return {
            success: false,
            error: error.message,
            status_code: 500,
            response_time: 0
        };
    } finally {
        hideLoading();
    }
}