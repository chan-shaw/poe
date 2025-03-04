/**
 * 模型相关函数
 */

// 存储模型数据
let allModels = [];
let testedModels = {};

// 当前分页状态
let currentPage = 1;
const itemsPerPage = 12;

// 当前视图模式
let currentViewMode = 'grid';

// 当前筛选条件
let currentFilter = 'all';
let searchQuery = '';

// 初始化模型列表
function initModelList(models) {
    allModels = models;
    renderModelList();
    updateStats();
}

// 添加缺失的 filterModels 函数
function filterModels(models, filter, query) {
    // 先应用搜索查询
    let filtered = models;
    
    if (query) {
        const lowerQuery = query.toLowerCase();
        filtered = filtered.filter(model => 
            model.name.toLowerCase().includes(lowerQuery) || 
            model.id.toLowerCase().includes(lowerQuery)
        );
    }
    
    // 再应用状态筛选
    if (filter !== 'all') {
        if (filter === 'tested') {
            filtered = filtered.filter(model => testedModels[model.id]);
        } else if (filter === 'healthy') {
            filtered = filtered.filter(model => 
                testedModels[model.id] && testedModels[model.id].success
            );
        } else if (filter === 'error') {
            filtered = filtered.filter(model => 
                testedModels[model.id] && !testedModels[model.id].success
            );
        }
    }
    
    return filtered;
}

// 添加缺失的 updateStats 函数
function updateStats() {
    // 更新统计数据
    const totalCount = allModels.length;
    const testedCount = Object.keys(testedModels).length;
    const healthyCount = Object.values(testedModels).filter(m => m.success).length;
    const errorCount = testedCount - healthyCount;
    
    // 更新页面上的统计数字
    document.getElementById('total-models').textContent = totalCount;
    document.getElementById('tested-models').textContent = testedCount;
    document.getElementById('healthy-models').textContent = healthyCount;
    document.getElementById('error-models').textContent = errorCount;
}

// 渲染模型列表
function renderModelList() {
    const modelListEl = document.getElementById('model-list');
    modelListEl.innerHTML = '';
    
    // 应用筛选和搜索
    let filteredModels = filterModels(allModels, currentFilter, searchQuery);
    
    // 应用分页
    const paginatedModels = paginate(filteredModels, currentPage, itemsPerPage);
    
    // 生成分页控件
    generatePagination(filteredModels.length, currentPage, itemsPerPage, (page) => {
        currentPage = page;
        renderModelList();
    });
    
    // 根据视图模式设置容器类
    modelListEl.className = currentViewMode === 'grid' ? 'model-grid-view' : 'model-list-view';
    
    // 移除了可能生成状态指示器的代码
    
    // 渲染模型卡片
    paginatedModels.forEach(model => {
        const modelCard = createModelCard(model);
        modelListEl.appendChild(modelCard);
    });
    
    // 如果没有模型，显示提示
    if (paginatedModels.length === 0) {
        const emptyMessage = document.createElement('div');
        emptyMessage.className = 'text-center text-muted py-5';
        emptyMessage.innerHTML = '<i class="bi bi-search me-2"></i>没有找到匹配的模型';
        modelListEl.appendChild(emptyMessage);
    }
}

// 创建模型卡片
function createModelCard(model) {
    const modelCard = document.createElement('div');
    modelCard.className = 'model-card';
    modelCard.dataset.modelId = model.id;
    
    // 获取测试状态
    const testResult = testedModels[model.id] || null;
    const statusClass = testResult ? (testResult.success ? 'healthy' : 'error') : 'pending';
    const statusText = testResult ? (testResult.success ? '健康' : '异常') : '未测试';
    
    // 如果测试成功，添加特殊样式
    if (testResult && testResult.success) {
        modelCard.classList.add('model-card-success');
    } else if (testResult && !testResult.success) {
        modelCard.classList.add('model-card-error');
    }
    
    // 卡片内容
    modelCard.innerHTML = `
        <div class="model-header">
            <div class="model-info">
                <div class="model-name">${model.name}</div>
                <div class="model-id">${model.id}</div>
                <div class="model-status">
                    <span class="status-badge ${statusClass}">${statusText}</span>
                    ${testResult ? `<small>响应时间: ${formatResponseTime(testResult.response_time)}</small>` : ''}
                </div>
            </div>
            <div class="model-actions">
                <button class="btn btn-sm ${testResult && testResult.success ? 'btn-success' : 'btn-primary'} test-model-btn" data-model-id="${model.id}">
                    <i class="bi bi-lightning-charge"></i> ${testResult && testResult.success ? '已测试' : '测试'}
                </button>
                <button class="btn btn-sm btn-outline-secondary ms-2 copy-model-btn" data-model-id="${model.id}">
                    <i class="bi bi-clipboard"></i> 复制ID
                </button>
            </div>
        </div>
        ${testResult && testResult.response ? `
            <div class="model-response">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <small class="text-muted">响应内容:</small>
                    <button class="btn btn-sm btn-outline-secondary copy-response-btn" data-response="${encodeURIComponent(testResult.response)}">
                        <i class="bi bi-clipboard"></i> 复制
                    </button>
                </div>
                <pre>${testResult.response}</pre>
            </div>
            <button class="btn btn-sm btn-outline-primary w-100 mt-2 toggle-response-btn">
                <i class="bi bi-chevron-down"></i> 显示响应
            </button>
        ` : ''}
    `;
    
    // 添加事件监听器
    const testBtn = modelCard.querySelector('.test-model-btn');
    testBtn.addEventListener('click', () => testSingleModel(model.id));
    
    const copyBtn = modelCard.querySelector('.copy-model-btn');
    copyBtn.addEventListener('click', () => copyToClipboard(model.id));
    
    const toggleBtn = modelCard.querySelector('.toggle-response-btn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', (e) => {
            const responseEl = modelCard.querySelector('.model-response');
            if (responseEl.style.display === 'block') {
                responseEl.style.display = 'none';
                e.target.innerHTML = '<i class="bi bi-chevron-down"></i> 显示响应';
            } else {
                responseEl.style.display = 'block';
                e.target.innerHTML = '<i class="bi bi-chevron-up"></i> 隐藏响应';
            }
        });
    }
    
    const copyResponseBtn = modelCard.querySelector('.copy-response-btn');
    if (copyResponseBtn) {
        copyResponseBtn.addEventListener('click', () => {
            const response = decodeURIComponent(copyResponseBtn.dataset.response);
            copyToClipboard(response);
        });
    }
    
    return modelCard;
}

// 更新模型卡片状态
function updateModelCardStatus(modelId, result) {
    testedModels[modelId] = result;
    
    const modelCard = document.querySelector(`.model-card[data-model-id="${modelId}"]`);
    if (!modelCard) return;
    
    // 更新卡片样式
    if (result.success) {
        modelCard.classList.add('model-card-success');
        modelCard.classList.remove('model-card-error');
    } else {
        modelCard.classList.add('model-card-error');
        modelCard.classList.remove('model-card-success');
    }
    
    const statusBadge = modelCard.querySelector('.status-badge');
    const statusText = result.success ? '健康' : '异常';
    const statusClass = result.success ? 'healthy' : 'error';
    
    statusBadge.textContent = statusText;
    statusBadge.className = `status-badge ${statusClass}`;
    
    // 更新测试按钮样式
    const testBtn = modelCard.querySelector('.test-model-btn');
    if (testBtn) {
        if (result.success) {
            testBtn.className = 'btn btn-sm btn-success test-model-btn';
            testBtn.innerHTML = '<i class="bi bi-check-circle"></i> 已测试';
        } else {
            testBtn.className = 'btn btn-sm btn-danger test-model-btn';
            testBtn.innerHTML = '<i class="bi bi-exclamation-triangle"></i> 重试';
        }
    }
    
    // 添加响应时间
    const modelStatus = modelCard.querySelector('.model-status');
    let responseTimeEl = modelStatus.querySelector('small');
    
    if (!responseTimeEl) {
        responseTimeEl = document.createElement('small');
        modelStatus.appendChild(responseTimeEl);
    }
    
    responseTimeEl.textContent = `响应时间: ${formatResponseTime(result.response_time)}`;
    
    // 如果有响应内容，添加或更新响应区域
    if (result.response) {
        let responseArea = modelCard.querySelector('.model-response');
        let toggleBtn = modelCard.querySelector('.toggle-response-btn');
        
        if (!responseArea) {
            // 创建响应区域
            responseArea = document.createElement('div');
            responseArea.className = 'model-response';
            responseArea.innerHTML = `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <small class="text-muted">响应内容:</small>
                    <button class="btn btn-sm btn-outline-secondary copy-response-btn" data-response="${encodeURIComponent(result.response)}">
                        <i class="bi bi-clipboard"></i> 复制
                    </button>
                </div>
                <pre>${result.response}</pre>
            `;
            
            // 创建切换按钮
            toggleBtn = document.createElement('button');
            toggleBtn.className = 'btn btn-sm btn-outline-primary w-100 mt-2 toggle-response-btn';
            toggleBtn.innerHTML = '<i class="bi bi-chevron-down"></i> 显示响应';
            
            // 添加到卡片
            modelCard.appendChild(responseArea);
            modelCard.appendChild(toggleBtn);
            
            // 添加事件监听器
            toggleBtn.addEventListener('click', (e) => {
                if (responseArea.style.display === 'block') {
                    responseArea.style.display = 'none';
                    e.target.innerHTML = '<i class="bi bi-chevron-down"></i> 显示响应';
                } else {
                    responseArea.style.display = 'block';
                    e.target.innerHTML = '<i class="bi bi-chevron-up"></i> 隐藏响应';
                }
            });
            
            const copyResponseBtn = responseArea.querySelector('.copy-response-btn');
            copyResponseBtn.addEventListener('click', () => {
                const response = decodeURIComponent(copyResponseBtn.dataset.response);
                copyToClipboard(response);
            });
        } else {
            // 更新现有响应区域
            const pre = responseArea.querySelector('pre');
            pre.textContent = result.response;
            
            const copyResponseBtn = responseArea.querySelector('.copy-response-btn');
            copyResponseBtn.dataset.response = encodeURIComponent(result.response);
        }
    }
}

// 测试单个模型
async function testSingleModel(modelId) {
    const token = document.getElementById('token').value.trim();
    
    if (!token) {
        showToast('请输入 Poe API Token', 'error');
        return;
    }
    
    try {
        const result = await testModel(token, modelId);
        updateModelCardStatus(modelId, result);
        updateStats();
        
        if (result.success) {
            showToast(`模型 ${modelId} 测试成功`, 'success');
        } else {
            showToast(`模型 ${modelId} 测试失败: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error(`测试模型 ${modelId} 失败:`, error);
        showToast(`测试失败: ${error.message}`, 'error');
    }
}

// 批量测试模型
async function startBatchModelTests() {
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
    document.getElementById('batch-progress-container').style.display = 'block';
    document.getElementById('batch-test-btn').disabled = true;
    
    try {
        const results = await batchTestModels(token, selectedModels, rateLimit);
        showToast(`批量测试完成: ${Object.values(results).filter(r => r.success).length}/${selectedModels.length} 成功`, 'success');
    } catch (error) {
        console.error('批量测试失败:', error);
        showToast(`批量测试失败: ${error.message}`, 'error');
    } finally {
        document.getElementById('batch-test-btn').disabled = false;
    }
}

// 切换视图模式
function toggleViewMode(mode) {
    currentViewMode = mode;
    
    // 更新按钮状态
    document.getElementById('grid-view-btn').classList.toggle('active', mode === 'grid');
    document.getElementById('list-view-btn').classList.toggle('active', mode === 'list');
    
    // 重新渲染列表
    renderModelList();
}

// 设置筛选条件
function setFilter(filter) {
    currentFilter = filter;
    currentPage = 1;
    
    // 更新按钮状态
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.filter === filter);
    });
    
    // 重新渲染列表
    renderModelList();
}

// 设置搜索查询
function setSearchQuery(query) {
    searchQuery = query;
    currentPage = 1;
    renderModelList();
}