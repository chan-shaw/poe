/**
 * 主要应用逻辑
 */

// 当文档加载完成时执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM 加载完成，初始化应用...');
    
    // 初始化事件监听器
    initEventListeners();
    
    // 从本地存储加载 Token
    const savedToken = localStorage.getItem('poe_api_token');
    if (savedToken) {
        document.getElementById('token').value = savedToken;
    }
    
    // 从本地存储加载语言设置
    const savedLanguage = localStorage.getItem('poe_language');
    if (savedLanguage) {
        document.getElementById('language').value = savedLanguage;
    }
    
    // 初始化密码显示/隐藏切换
    initPasswordToggle();
    
    // 初始化复制按钮
    initCopyButtons();
    
    console.log('应用初始化完成');
});

// 初始化事件监听器
function initEventListeners() {
    console.log('初始化事件监听器');
    
    // 测试按钮点击事件
    const testBtn = document.getElementById('test-btn');
    if (testBtn) {
        console.log('找到测试按钮，添加点击事件');
        testBtn.addEventListener('click', async function() {
            console.log('测试按钮被点击');
            const token = document.getElementById('token').value.trim();
            const language = document.getElementById('language').value;
            
            if (!token) {
                showToast('请输入 Poe API Token', 'error');
                return;
            }
            
            // 保存 Token 和语言设置到本地存储
            localStorage.setItem('poe_api_token', token);
            localStorage.setItem('poe_language', language);
            
            try {
                console.log('开始测试 API Token...');
                const result = await testApiToken(token, language);
                console.log('API 测试结果:', result);
                
                if (result.success) {
                    showToast('API Token 有效，已获取模型列表', 'success');
                    
                    // 初始化模型列表
                    initModelList(result.models);
                    
                    // 显示模型列表区域
                    const modelsSection = document.getElementById('models-section');
                    modelsSection.style.display = 'block';
                    
                    // 滚动到模型列表
                    modelsSection.scrollIntoView({
                        behavior: 'smooth'
                    });
                } else {
                    showToast(`API Token 无效: ${result.message || '未知错误'}`, 'error');
                }
            } catch (error) {
                console.error('测试 Token 失败:', error);
                showToast(`测试失败: ${error.message}`, 'error');
            }
        });
    } else {
        console.error('未找到测试按钮元素 #test-btn');
    }
    
    // 视图切换按钮点击事件
    const gridViewBtn = document.querySelector('[data-view="grid"]');
    const listViewBtn = document.querySelector('[data-view="list"]');
    
    if (gridViewBtn) {
        gridViewBtn.addEventListener('click', () => toggleViewMode('grid'));
    }
    
    if (listViewBtn) {
        listViewBtn.addEventListener('click', () => toggleViewMode('list'));
    }
    
    // 模型筛选下拉框变化事件
    const modelFilter = document.getElementById('model-filter');
    if (modelFilter) {
        modelFilter.addEventListener('change', (e) => {
            setFilter(e.target.value);
        });
    }
    
    // 搜索框输入事件
    const modelSearch = document.getElementById('model-search');
    if (modelSearch) {
        modelSearch.addEventListener('input', (e) => {
            setSearchQuery(e.target.value.trim());
        });
    }
}

// 初始化密码显示/隐藏切换
function initPasswordToggle() {
    const toggleBtn = document.querySelector('.toggle-password');
    const tokenInput = document.getElementById('token');
    
    if (toggleBtn && tokenInput) {
        toggleBtn.addEventListener('click', () => {
            const type = tokenInput.getAttribute('type') === 'password' ? 'text' : 'password';
            tokenInput.setAttribute('type', type);
            
            const icon = toggleBtn.querySelector('i');
            if (type === 'password') {
                icon.className = 'bi bi-eye';
            } else {
                icon.className = 'bi bi-eye-slash';
            }
        });
    }
}

// 初始化复制按钮
function initCopyButtons() {
    document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const code = btn.getAttribute('data-code');
            copyToClipboard(code);
        });
    });
}

// 初始化批量测试模型选择
function initBatchModelSelection(models) {
    const batchModelList = document.getElementById('batch-model-list');
    if (!batchModelList) {
        console.error('未找到批量模型列表元素 #batch-model-list');
        return;
    }
    
    batchModelList.innerHTML = '';
    
    models.forEach(model => {
        const item = document.createElement('div');
        item.className = 'model-checkbox-item';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'form-check-input model-checkbox';
        checkbox.value = model.id;
        checkbox.id = `model-checkbox-${model.id}`;
        
        const label = document.createElement('label');
        label.className = 'form-check-label';
        label.htmlFor = `model-checkbox-${model.id}`;
        label.innerHTML = `<strong>${model.name}</strong> <small class="text-muted">${model.id}</small>`;
        
        const testBtn = document.createElement('button');
        testBtn.className = 'btn btn-sm btn-outline-primary model-test-btn';
        testBtn.innerHTML = '<i class="bi bi-lightning-charge"></i> 测试';
        testBtn.dataset.modelId = model.id;
        
        // 添加单个模型测试按钮的事件监听器
        testBtn.addEventListener('click', () => testSingleModel(model.id));
        
        item.appendChild(checkbox);
        item.appendChild(label);
        item.appendChild(testBtn);
        batchModelList.appendChild(item);
        
        // 添加复选框事件监听器
        checkbox.addEventListener('change', () => {
            updateSelectedCount();
            const batchTestBtn = document.getElementById('batch-test-btn');
            if (batchTestBtn) {
                batchTestBtn.disabled = document.querySelectorAll('.model-checkbox:checked').length === 0;
            }
        });
    });
    
    // 初始化选中计数
    updateSelectedCount();
}

// 更新选中模型计数
function updateSelectedCount() {
    const selectedCount = document.querySelectorAll('.model-checkbox:checked').length;
    const totalCount = document.querySelectorAll('.model-checkbox').length;
    
    const countElement = document.createElement('div');
    countElement.className = 'mt-2 text-muted';
    countElement.textContent = `已选择 ${selectedCount}/${totalCount} 个模型`;
    
    const oldCount = document.querySelector('.model-selection-container .text-muted');
    if (oldCount) {
        oldCount.remove();
    }
    
    const container = document.querySelector('.model-selection-container');
    if (container) {
        container.appendChild(countElement);
    }
}

// 开始批量测试
async function startBatchTest() {
    const token = document.getElementById('token').value.trim();
    const rateLimit = parseInt(document.getElementById('rate-limit').value) || 10;
    
    if (!token) {
        showToast('请输入 Poe API Token', 'error');
        return;
    }
    
    // 获取选中的模型
    const selectedModels = [];
    document.querySelectorAll('.model-checkbox:checked').forEach(checkbox => {
        selectedModels.push(checkbox.value);
    });
    
    if (selectedModels.length === 0) {
        showToast('请至少选择一个模型', 'warning');
        return;
    }
    
    // 显示进度条
    const progressContainer = document.getElementById('batch-progress-container');
    if (progressContainer) {
        progressContainer.style.display = 'block';
    }
    
    const batchTestBtn = document.getElementById('batch-test-btn');
    if (batchTestBtn) {
        batchTestBtn.disabled = true;
    }
    
    try {
        const results = await batchTestModels(token, selectedModels, rateLimit);
        const successCount = Object.values(results).filter(r => r.success).length;
        showToast(`批量测试完成: ${successCount}/${selectedModels.length} 成功`, 'success');
    } catch (error) {
        console.error('批量测试失败:', error);
        showToast(`批量测试失败: ${error.message}`, 'error');
    } finally {
        if (batchTestBtn) {
            batchTestBtn.disabled = false;
        }
    }
}

// 更新图表
function updateChart() {
    const ctx = document.getElementById('modelStatusChart');
    if (!ctx) return;
    
    const totalCount = allModels.length;
    const testedCount = Object.keys(testedModels).length;
    const healthyCount = Object.values(testedModels).filter(m => m.success).length;
    const errorCount = testedCount - healthyCount;
    const pendingCount = totalCount - testedCount;
    
    if (window.modelChart) {
        window.modelChart.destroy();
    }
    
    window.modelChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['健康', '异常', '未测试'],
            datasets: [{
                data: [healthyCount, errorCount, pendingCount],
                backgroundColor: [
                    'rgba(40, 167, 69, 0.7)',
                    'rgba(220, 53, 69, 0.7)',
                    'rgba(108, 117, 125, 0.7)'
                ],
                borderColor: [
                    'rgba(40, 167, 69, 1)',
                    'rgba(220, 53, 69, 1)',
                    'rgba(108, 117, 125, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// 导出测试结果为 JSON
function exportResults() {
    if (Object.keys(testedModels).length === 0) {
        showToast('没有可导出的测试结果', 'warning');
        return;
    }
    
    const exportData = {
        timestamp: new Date().toISOString(),
        results: testedModels
    };
    
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileName = `poe-api-test-results-${new Date().toISOString().slice(0, 10)}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileName);
    linkElement.click();
    
    showToast('测试结果已导出', 'success');
}