# 模型名称下拉选择功能

## 功能说明

在模型配置管理页面，将"模型名称"字段从纯文本输入框改为**下拉选择框**，支持：

1. **预设模型列表**：提供常用AI模型的预设选项
2. **分组显示**：按提供商分组（OpenAI、智谱AI、通义千问等）
3. **搜索功能**：支持输入关键词快速筛选
4. **自定义输入**：支持手动输入自定义模型名称

## 修改文件

**前端文件**：`frontend/src/pages/ModelConfigs.tsx`

## 功能特性

### 1. 预设模型列表

支持以下主流AI模型：

#### OpenAI 系列
- GPT-4 Turbo (`gpt-4-turbo-preview`)
- GPT-4 (`gpt-4`)
- GPT-4 32K (`gpt-4-32k`)
- GPT-3.5 Turbo (`gpt-3.5-turbo`)
- GPT-3.5 Turbo 16K (`gpt-3.5-turbo-16k`)

#### 智谱AI 系列
- GLM-4 (`glm-4`)
- GLM-4-Plus (`glm-4-plus`)
- GLM-4-Air (`glm-4-air`)
- GLM-4-Flash (`glm-4-flash`)
- GLM-4.7 (`glm-4.7`)

#### 通义千问 系列
- Qwen-Max (`qwen-max`)
- Qwen-Plus (`qwen-plus`)
- Qwen-Turbo (`qwen-turbo`)

#### DeepSeek 系列
- DeepSeek-Chat (`deepseek-chat`)
- DeepSeek-Coder (`deepseek-coder`)

#### 文心一言 系列
- ERNIE-4.0 (`ernie-4.0`)
- ERNIE-3.5 (`ernie-3.5`)

#### Anthropic Claude 系列
- Claude 3 Opus (`claude-3-opus-20240229`)
- Claude 3 Sonnet (`claude-3-sonnet-20240229`)
- Claude 3 Haiku (`claude-3-haiku-20240307`)

### 2. 组件特性

```tsx
<Select
  showSearch            // 支持搜索
  placeholder="选择模型或手动输入"
  optionFilterProp="children"
  mode="tags"          // 支持自定义输入
  maxCount={1}         // 只能选择1个
  options={[...]}      // 预设模型列表
/>
```

**关键属性说明**：
- `showSearch`: 启用搜索框，可输入关键词筛选
- `mode="tags"`: 允许用户输入自定义值（如新发布的模型）
- `maxCount={1}`: 限制只能选择一个模型
- `optionFilterProp="children"`: 按选项文本内容搜索

### 3. 使用方式

#### 方式1：从预设列表选择
1. 点击下拉框
2. 浏览或搜索模型名称
3. 点击选择

#### 方式2：手动输入
1. 点击下拉框
2. 直接输入自定义模型名称（如 `gpt-5`）
3. 按回车确认

#### 方式3：搜索后选择
1. 点击下拉框
2. 输入关键词（如 "gpt"）
3. 从筛选结果中选择

## 用户体验改进

### 优化前
- ❌ 需要手动输入模型名称，容易拼写错误
- ❌ 不知道有哪些可用模型
- ❌ 不同提供商的模型难以区分

### 优化后
- ✅ 可视化选择，避免拼写错误
- ✅ 清晰展示所有主流模型
- ✅ 按提供商分组，易于查找
- ✅ 支持搜索和自定义输入，灵活性强

## 后续扩展建议

### 1. 根据Provider自动筛选

```tsx
const getModelsByProvider = (provider: string) => {
  const allModels = [...]; // 完整模型列表

  if (!provider) return allModels;

  return allModels.filter(m => m.group === providerMap[provider]);
};

<Form.Item
  noStyle
  shouldUpdate={(prev, curr) => prev.provider !== curr.provider}
>
  {({ getFieldValue }) => (
    <Form.Item name="model_name" label="模型名称">
      <Select options={getModelsByProvider(getFieldValue('provider'))} />
    </Form.Item>
  )}
</Form.Item>
```

### 2. 动态加载模型列表

从后端API获取最新的模型列表：

```tsx
const [availableModels, setAvailableModels] = useState([]);

useEffect(() => {
  fetch('/api/v1/models/available')
    .then(res => res.json())
    .then(data => setAvailableModels(data.models));
}, []);
```

### 3. 显示模型详细信息

鼠标悬停时显示模型的：
- 上下文长度
- 定价信息
- 特性说明

```tsx
{
  label: 'GPT-4 Turbo',
  value: 'gpt-4-turbo-preview',
  tooltip: '128K上下文，最新模型，性能最强'
}
```

## 测试验证

1. **创建新配置**
   - 从下拉列表选择模型
   - 手动输入自定义模型名称
   - 搜索功能是否正常

2. **编辑现有配置**
   - 已有模型名称是否正确显示
   - 可以切换到其他模型
   - 自定义模型名称可以保存

3. **表单验证**
   - 必填校验是否正常
   - 只能选择一个模型

## 注意事项

1. **兼容性**：保持与现有数据的兼容性，旧的自定义模型名称仍然有效
2. **验证**：模型名称仍然通过后端验证，前端仅提供便利
3. **更新**：模型列表需要定期更新（如有新模型发布）

---

**修改时间**: 2026-02-03
**状态**: 已实施
**影响范围**: 模型配置管理页面
