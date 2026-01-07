# 测试数据生成方案

## 一、现有流程

### 1.1 核心入口函数

**主流程函数**: `create_case_with_fields()` (`automation_service.py:671-834`)

### 1.2 完整业务流程（5个步骤）

#### 步骤1：获取场景用例列表
```
调用: get_scene_cases(scene_id)
API: GET /ai/case/queryBySceneId/{scene_id}
输出: 场景下所有可用用例列表 [{usercaseId, name, description, ...}]
```

#### 步骤2：AI选择最匹配用例
```
调用: select_best_case_by_ai(test_case_info, scene_cases)
逻辑:
  1. 构建prompt，包含测试用例信息(标题、描述、前置条件、步骤、预期结果)
  2. 调用AI服务分析并选择最佳模板
  3. 返回选中的用例ID和详细信息
```

#### 步骤3：获取用例详情
```
调用: get_case_detail(usercase_id)
API: GET /ai/case/queryCaseBody/{usercase_id}
输出: 用例完整信息，包含 caseDefine 结构:
  - header: 字段定义列表 [{rowName, row, type, flag, ...}]
  - body: 测试数据列表
  - circulation: 环节信息
```

#### 步骤4：AI生成测试数据
```
调用: generate_case_body_by_ai(header_fields, test_case_info, circulation)
逻辑:
  1. 解析header字段定义，提取字段名、类型、标识
  2. 构建prompt，注入测试用例信息
  3. 调用AI生成1-3条符合业务逻辑的测试数据
  4. 解析JSON响应，标准化格式:
     {
       "casezf": "1",
       "casedesc": "描述",
       "var": {字段名: 值, ...},
       "hoperesult": "成功结案",
       "iscaserun": False,
       "caseBodySN": 序号
     }
```

#### 步骤5：创建用例和明细
```
调用: create_case_and_body(name, module_id, scene_id, template_case_detail, ...)
API: POST /ai/case/createCaseAndBody
Payload结构:
  {
    "name": "用例名称",
    "moduleId": "模块ID",
    "sceneId": "场景ID",
    "scenarioType": "API",
    "description": "描述",
    "tags": "[]",
    "circulation": [...],      # 环节信息
    "caseDefine": {
      "header": [...],         # 字段定义
      "body": [...]            # AI生成的测试数据
    }
  }
输出: 创建成功的用例信息 {usercaseId, name, ...}
```

### 1.3 数据结构说明

#### 测试用例信息 (test_case_info)
```python
{
    "title": str,           # 用例标题
    "description": str,     # 描述
    "preconditions": str,   # 前置条件
    "test_steps": str,      # 测试步骤
    "expected_result": str, # 预期结果
    "test_type": str,       # 测试类型
    "priority": str         # 优先级
}
```

#### 字段定义 (header)
```python
{
    "rowName": "字段中文名",
    "row": "字段名",
    "type": "字段类型",
    "flag": "字段标识"
}
```

#### 测试数据 (body)
```python
{
    "casezf": "1",              # 用例作废标识
    "casedesc": "测试数据描述",
    "var": {"字段名": "值", ...},
    "hoperesult": "期望结果",
    "iscaserun": False,         # 是否运行
    "caseBodySN": 1             # 序号
}
```

### 1.4 现有流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                    create_case_with_fields()                    │
├─────────────────────────────────────────────────────────────────┤
│  步骤1: get_scene_cases(scene_id)                               │
│         ↓ 获取场景用例列表                                        │
│         ↓ (若无用例则抛出异常)                                     │
│                                                                  │
│  步骤2: select_best_case_by_ai(test_case_info, scene_cases)     │
│         ↓ AI选择最匹配模板                                        │
│         ↓ (无信息则使用第一个)                                     │
│                                                                  │
│  步骤3: get_case_detail(usercase_id)                            │
│         ↓ 获取模板详情                                            │
│         ↓ 提取 header, circulation                               │
│                                                                  │
│  步骤4: generate_case_body_by_ai(header, test_case_info)        │
│         ↓ AI生成测试数据                                          │
│         ↓ (返回 body 列表)                                        │
│         ↓ (若无header或信息则抛出异常)                              │
│                                                                  │
│  步骤5: create_case_and_body(..., template_case_detail)         │
│         ↓ 调用API创建用例和明细                                    │
│         ↓ 返回 {usercaseId, ...}                                 │
│                                                                  │
│  返回: {created_case, template_case, case_detail, fields,       │
│        new_usercase_id, scene_id, selected_template}            │
└─────────────────────────────────────────────────────────────────┘
```

### 1.5 关键API端点

| 端点 | 方法 | 用途 |
|------|------|------|
| `/ai/case/queryBySceneId/{scene_id}` | GET | 获取场景用例列表 |
| `/ai/case/queryCaseBody/{usercase_id}` | GET | 获取用例详情 |
| `/ai/case/createCaseAndBody` | POST | 创建用例和明细 |

### 1.6 现有问题

| 问题 | 原因 | 影响 |
|------|------|------|
| **枚举值无效** | AI不知道字段可选值范围，header中只有type没有enums | 运行时报错 |
| **字段联动错误** | AI不知道字段间的依赖关系 | 数据不一致 |
| **可选字段填了无效值** | 某些场景下字段不应有值，但AI全部填充 | 平台校验失败 |
| **token超限** | 枚举值太多，一次性传给AI会超出限制 | AI无法正确处理 |

---

## 二、优化方案

### 2.1 问题分析

| 问题 | 原因 | 影响 |
|------|------|------|
| **枚举值无效** | AI不知道字段可选值范围 | 运行时报错 |
| **字段联动错误** | AI不知道字段间的依赖关系 | 数据不一致 |
| **可选字段填了无效值** | 某些场景下字段不应有值 | 平台校验失败 |

**核心约束**：
- 自动化平台已有枚举值和联动规则的数据
- 但当前API没有返回这些信息
- 枚举值很多，需要按条件筛选，避免token超出限制

### 2.2 整体架构

```
┌──────────────────────────────────────────────────────────────────────┐
│                         自动化平台                                     │
│  ┌──────────────┐  ┌──────────────────────────────────────────────┐  │
│  │ 场景用例API    │  │ 字段元数据API (新)                           │  │
│  │ /queryBySceneId│  │ /ai/case/queryFieldMetadata?sceneId=xxx    │  │
│  │ /queryCaseBody │  │ 返回: header字段 + 枚举值 + 联动规则          │  │
│  └──────────────┘  └──────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────┐
│                      智能测试用例平台                                   │
│  ┌──────────────┐  ┌──────────────────────────────────────────────┐  │
│  │ 自动化服务     │  │ 枚举值缓存服务                                │  │
│  │               │  │ - 按场景缓存字段元数据                         │  │
│  │ create_case_  │  │ - 动态筛选枚举值（避免token超限）              │  │
│  │ with_fields() │  │ - 联动规则解析                                │  │
│  └──────────────┘  └──────────────────────────────────────────────┘  │
│                                    ↓                                  │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  步骤1: 获取场景用例                                             │ │
│  │  步骤2: AI选择模板                                               │ │
│  │  步骤3: 获取用例详情 + 字段元数据(枚举值+联动规则)                    │ │
│  │  步骤4: AI生成测试数据(带约束)                                     │ │
│  │  步骤5: 校验数据有效性                                            │ │
│  │  步骤6: 返回前端确认                                              │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                    ↓                                  │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  前端界面                                                        │ │
│  │  - 显示AI生成的测试数据                                           │ │
│  │  - 高亮显示有问题的字段（枚举值不匹配、联动错误）                      │ │
│  │  - 允许用户编辑修正                                               │ │
│  │  - 确认后提交到自动化平台                                          │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.3 新增自动化平台API

需要与自动化平台方确认新增字段元数据API：

```
GET /ai/case/queryFieldMetadata?sceneId={sceneId}

响应:
{
  "success": true,
  "data": {
    "sceneId": "xxx",
    "fields": [
      {
        "row": "CP_accidentType_1",
        "rowName": "理赔_出险人类型_1",
        "type": "select",
        "flag": "",
        "required": true,
        "enums": [                    // 枚举值列表
          {"value": "1", "label": "被保人"},
          {"value": "2", "label": "受益人"}
        ],
        "enumDependencies": [         // 枚举值联动规则
          {
            "enumValue": "1",         // 当选择此枚举值时
            "showFields": [           // 显示以下字段
              "CP_accidentReason_1",
              "CP_accidentDay_1"
            ],
            "hideFields": [],         // 隐藏以下字段
            "requiredFields": [       // 以下字段变为必填
              "CP_accidentReason_1"
            ]
          }
        ]
      },
      {
        "row": "CP_accidentReason_1",
        "rowName": "理赔_出险原因_1",
        "type": "select",
        "enums": [
          {"value": "1-疾病", "label": "疾病"},
          {"value": "2-意外", "label": "意外"}
        ],
        "dependencies": [             // 被其他字段触发的联动
          {
            "triggerField": "CP_accidentType_1",
            "triggerValue": "1",
            "action": "show"          // 联动触发时显示此字段
          }
        ]
      }
    ],
    "fieldGroups": [                  // 字段分组（用于条件显示）
      {
        "groupId": "accidentInfo",
        "fields": ["CP_accidentType_1", "CP_accidentReason_1", "CP_accidentDay_1"],
        "condition": "根据出险人类型显示"  // 分组描述
      }
    ]
  }
}
```

### 2.4 后端实现

#### 2.4.1 新增字段元数据服务

```python
# backend/app/services/field_metadata_service.py

class FieldMetadataService:
    """字段元数据服务 - 管理枚举值和联动规则"""

    def __init__(self, automation_service):
        self.auto_svc = automation_service
        self._cache = {}  # 场景ID -> 字段元数据缓存

    async def get_field_metadata(self, scene_id: str, context: Dict = None) -> Dict:
        """
        获取字段元数据，支持动态筛选枚举值

        Args:
            scene_id: 场景ID
            context: 上下文信息（如已选择的字段值），用于筛选枚举值
        """
        # 1. 检查缓存
        if scene_id in self._cache:
            return self._cache[scene_id]

        # 2. 调用自动化平台API
        metadata = await self._fetch_field_metadata(scene_id)

        # 3. 根据上下文动态筛选枚举值（避免token超限）
        if context:
            metadata = self._filter_enums_by_context(metadata, context)

        # 4. 缓存
        self._cache[scene_id] = metadata
        return metadata

    def _filter_enums_by_context(self, metadata: Dict, context: Dict) -> Dict:
        """
        根据上下文筛选枚举值

        例如：如果已知出险人类型是"被保人"，则只返回相关的出险原因
        """
        for field in metadata.get('fields', []):
            if field.get('row') in context:
                selected_value = context[field['row']]
                # 根据已选值筛选关联字段的枚举值
                for dep_field in metadata.get('fields', []):
                    if dep_field.get('dependencies'):
                        for dep in dep_field['dependencies']:
                            if dep['triggerField'] == field['row']:
                                if dep.get('triggerValue') == selected_value:
                                    # 保留完整的枚举值
                                    pass
                                else:
                                    # 标记为不适用（可选项为空）
                                    dep_field['_applicable'] = False
        return metadata

    def get_linkage_rules(self, metadata: Dict) -> List[Dict]:
        """提取联动规则，用于AI Prompt"""
        rules = []
        for field in metadata.get('fields', []):
            if field.get('enumDependencies'):
                for dep in field['enumDependencies']:
                    rules.append({
                        "field": field['row'],
                        "whenValue": dep['enumValue'],
                        "showFields": dep.get('showFields', []),
                        "hideFields": dep.get('hideFields', []),
                        "requiredFields": dep.get('requiredFields', [])
                    })
            if field.get('dependencies'):
                for dep in field['dependencies']:
                    rules.append({
                        "field": field['row'],
                        "triggerField": dep['triggerField'],
                        "triggerValue": dep['triggerValue'],
                        "action": dep.get('action', 'show')
                    })
        return rules
```

#### 2.4.2 优化AI生成逻辑

```python
# backend/app/services/automation_service.py

async def generate_case_body_by_ai_v2(
    self,
    header_fields: List[Dict],
    test_case_info: Dict,
    circulation: List[Dict] = None,
    field_metadata: Dict = None,  # 新增：字段元数据
    linkage_rules: List[Dict] = None  # 新增：联动规则
) -> List[Dict]:
    """
    使用AI根据字段定义、枚举值和联动规则生成测试数据（v2版本）
    """

    # 构建增强的字段描述
    fields_desc = []
    for field in header_fields:
        row_name = field.get('rowName', field.get('row', ''))
        row = field.get('row', '')
        field_type = field.get('type', '')
        flag = field.get('flag', '')
        required = field.get('required', False)

        field_info = f"- {row_name} (字段名: {row}"
        if field_type:
            field_info += f", 类型: {field_type}"
        if flag:
            field_info += f", 标识: {flag}"
        if required:
            field_info += f", 必填"

        # 添加枚举值（如果字段元数据中有）
        if field_metadata:
            meta = self._find_field_metadata(field_metadata, row)
            if meta and meta.get('enums'):
                enums = meta['enums']
                # 枚举值太多时，限制显示数量
                if len(enums) > 10:
                    enum_str = ", ".join([f"{e['value']}({e['label']})" for e in enums[:5]])
                    enum_str += f"... 等共{len(enums)}个选项"
                else:
                    enum_str = ", ".join([f"{e['value']}({e['label']})" for e in enums])
                field_info += f", 可选值: [{enum_str}]"

        field_info += ")"
        fields_desc.append(field_info)

    fields_text = "\n".join(fields_desc)

    # 构建联动规则描述
    linkage_text = ""
    if linkage_rules:
        linkage_items = []
        for rule in linkage_rules:
            when_value = rule.get('whenValue', rule.get('triggerValue', ''))
            action = rule.get('action', '')
            show_fields = rule.get('showFields', [])
            hide_fields = rule.get('hideFields', [])
            required_fields = rule.get('requiredFields', [])

            if show_fields:
                linkage_items.append(
                    f"- 当字段【{rule['field']}】={when_value}时，显示字段: {', '.join(show_fields)}"
                )
            if hide_fields:
                linkage_items.append(
                    f"- 当字段【{rule['field']}】={when_value}时，隐藏字段: {', '.join(hide_fields)}"
                )
            if required_fields:
                linkage_items.append(
                    f"- 当字段【{rule['field']}】={when_value}时，以下字段变为必填: {', '.join(required_fields)}"
                )

        if linkage_items:
            linkage_text = "\n【字段联动规则】\n" + "\n".join(linkage_items)

    # 构建AI Prompt
    prompt = f"""你是一个自动化测试专家。请根据以下测试用例信息和字段定义（含枚举值和联动规则），生成1-3条合理的测试数据。

【测试用例信息】
标题：{test_case_info.get('title', '')}
描述：{test_case_info.get('description', '')}
前置条件：{test_case_info.get('preconditions', '')}
测试步骤：{test_case_info.get('test_steps', '')}
预期结果：{test_case_info.get('expected_result', '')}
测试类型：{test_case_info.get('test_type', '')}
优先级：{test_case_info.get('priority', '')}
{circulation_text if circulation else ''}

【字段定义】
{fields_text}
{linkage_text}

【要求】
1. 必须严格按照字段的枚举值范围生成数据，不能超出可选范围
2. 必须遵守字段联动规则：
   - 当触发条件满足时，确保联动字段的值符合规则
   - 当字段被隐藏时，不要填写该字段的值（保留空字符串或null）
   - 当字段变为必填时，确保填写有效值
3. 测试数据要真实、合理、符合业务逻辑
4. 生成1-3条测试数据
5. 日期格式使用 YYYYMMDD
6. 代码类字段要使用正确的业务代码

请以JSON格式返回...
"""
```

#### 2.4.3 新增数据校验服务

```python
# backend/app/services/body_validator.py

class BodyValidator:
    """测试数据校验服务"""

    def __init__(self, field_metadata: Dict):
        self.metadata = field_metadata
        self.errors = []

    def validate(self, body_data: Dict) -> Dict:
        """
        校验单条body数据

        Returns:
            {
                "valid": True/False,
                "errors": [],                    # 错误列表
                "warnings": [],                  # 警告列表
                "suggestions": []                # 修正建议
            }
        """
        result = {"valid": True, "errors": [], "warnings": [], "suggestions": []}
        var = body_data.get('var', {})

        # 1. 校验枚举值
        for field in self.metadata.get('fields', []):
            field_name = field['row']
            value = var.get(field_name)

            if value and field.get('enums'):
                enum_values = [e['value'] for e in field['enums']]
                if value not in enum_values:
                    result['valid'] = False
                    result['errors'].append({
                        "field": field_name,
                        "value": value,
                        "message": f"值'{value}'不在枚举范围[{', '.join(enum_values[:5])}...]内",
                        "suggestion": f"建议修改为: {enum_values[0]}"
                    })

        # 2. 校验联动规则
        linkage_errors = self._validate_linkage(var)
        result['errors'].extend(linkage_errors)

        # 3. 校验必填字段
        required_errors = self._validate_required(var)
        result['errors'].extend(required_errors)

        if result['errors']:
            result['valid'] = False

        return result

    def _validate_linkage(self, var: Dict) -> List[Dict]:
        """校验联动规则"""
        errors = []
        for field in self.metadata.get('fields', []):
            if field.get('enumDependencies'):
                field_value = var.get(field['row'])
                for dep in field['enumDependencies']:
                    if dep['enumValue'] == field_value:
                        # 检查联动的必填字段
                        for req_field in dep.get('requiredFields', []):
                            req_value = var.get(req_field)
                            if not req_value:
                                errors.append({
                                    "field": req_field,
                                    "message": f"当{field['row']}={field_value}时，{req_field}为必填",
                                    "suggestion": f"建议设置一个有效值"
                                })
        return errors

    def _validate_required(self, var: Dict) -> List[Dict]:
        """校验必填字段"""
        errors = []
        for field in self.metadata.get('fields', []):
            if field.get('required'):
                field_value = var.get(field['row'])
                if not field_value:
                    errors.append({
                        "field": field['row'],
                        "message": f"必填字段{field['rowName']}不能为空",
                        "suggestion": "请填写一个有效值"
                    })
        return errors

    def validate_all(self, body_list: List[Dict]) -> Dict:
        """校验所有body数据"""
        results = []
        for idx, body in enumerate(body_list):
            validation = self.validate(body)
            results.append({
                "index": idx,
                "casedesc": body.get('casedesc', f'测试数据{idx+1}'),
                "validation": validation
            })

        # 汇总
        total_errors = sum(len(r['validation']['errors']) for r in results)
        return {
            "total": len(body_list),
            "valid_count": sum(1 for r in results if r['validation']['valid']),
            "invalid_count": total_errors,
            "results": results
        }
```

#### 2.4.4 主流程整合

```python
# automation_service.py 中的 create_case_with_fields 优化版本

async def create_case_with_fields_v2(
    self,
    name: str,
    module_id: str,
    scene_id: str,
    scenario_type: str = "API",
    description: str = "",
    test_case_info: Optional[Dict[str, Any]] = None,
    need_human_confirm: bool = True  # 是否需要人工确认
) -> Dict[str, Any]:
    """
    基于AI匹配的模板一次性创建自动化用例和明细（v2版本）

    新增功能：
    - 获取字段元数据（枚举值+联动规则）
    - AI生成带约束的测试数据
    - 校验数据有效性
    - 支持人工确认流程
    """

    # 步骤1-3: 获取场景用例、AI选择、获取用例详情（保持不变）
    ...

    # 步骤3.5: 新增 - 获取字段元数据
    print(f"[INFO] 步骤3.5: 获取字段元数据（枚举值+联动规则）")
    field_metadata = await self._fetch_field_metadata(scene_id)
    linkage_rules = self._extract_linkage_rules(field_metadata)

    # 步骤4: AI生成测试数据（增强版）
    print(f"[INFO] 步骤4: 使用AI根据测试用例信息生成测试数据（带枚举约束）")

    example_body = None
    if case_detail and case_detail.get('caseDefine'):
        template_body = case_detail['caseDefine'].get('body') or []
        if template_body:
            example_body = template_body[0]

    generated_body = await self.generate_case_body_by_ai_v2(
        header_fields=header_fields,
        test_case_info=test_case_info,
        circulation=circulation,
        field_metadata=field_metadata,
        linkage_rules=linkage_rules,
        example_body=example_body
    )

    # 步骤4.5: 新增 - 校验生成的测试数据
    print(f"[INFO] 步骤4.5: 校验测试数据有效性")
    validator = BodyValidator(field_metadata)
    validation_result = validator.validate_all(generated_body)

    print(f"[INFO] 校验结果: {validation_result['valid_count']}/{validation_result['total']} 条数据有效")
    if validation_result['invalid_count'] > 0:
        for r in validation_result['results']:
            if r['validation']['errors']:
                print(f"[WARNING] 第{r['index']+1}条数据问题: {r['validation']['errors']}")

    # 步骤5: 判断是否需要人工确认
    if need_human_confirm and validation_result['invalid_count'] > 0:
        # 返回前端确认
        return {
            "status": "need_confirm",
            "message": f"生成{len(generated_body)}条数据，其中{validation_result['invalid_count']}条存在问题",
            "data": {
                "generated_body": generated_body,
                "validation_result": validation_result,
                "field_metadata": field_metadata,
                "case_detail": case_detail
            }
        }

    # 无问题或不需要确认，直接创建
    return await self._create_case_and_body_final(
        name=name,
        module_id=module_id,
        scene_id=scene_id,
        case_detail=case_detail,
        generated_body=generated_body,
        ...
    )
```

### 2.5 后端API接口设计

#### 2.5.1 新增后端API

```python
# backend/app/api/v1/endpoints/automation.py

@router.post("/create-with-confirm")
async def create_automation_case_with_confirm(
    request: CreateCaseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建自动化用例（支持人工确认流程）

    如果数据校验通过，直接创建用例
    如果数据有问题，返回确认页面数据让前端展示
    """
    automation_svc = get_automation_service(db)

    result = await automation_svc.create_case_with_fields_v2(
        name=request.name,
        module_id=request.module_id,
        scene_id=request.scene_id,
        test_case_info=request.test_case_info,
        need_human_confirm=request.need_human_confirm
    )

    if result.get('status') == 'need_confirm':
        # 返回确认数据
        return {
            "need_confirm": True,
            "confirm_data": {
                "generated_body": result['data']['generated_body'],
                "validation_result": result['data']['validation_result'],
                "field_metadata": result['data']['field_metadata'],
                "scene_id": request.scene_id,
                "module_id": request.module_id,
                "name": request.name
            }
        }

    return result

@router.post("/confirm-submit")
async def submit_confirmed_case(
    request: ConfirmSubmitRequest,
    db: Session = Depends(get_db)
):
    """
    人工确认后提交用例
    """
    automation_svc = get_automation_service(db)

    return await automation_svc._create_case_and_body_final(
        name=request.name,
        module_id=request.module_id,
        scene_id=request.scene_id,
        case_detail=request.case_detail,
        generated_body=request.corrected_body,
        ...
    )
```

### 2.6 前端确认界面

```tsx
// frontend/src/pages/TestCase/AutomationConfirm.tsx

interface Props {
  data: {
    generated_body: BodyItem[];
    validation_result: ValidationResult;
    field_metadata: FieldMetadata;
  };
  onConfirm: (correctedBody: BodyItem[]) => void;
  onCancel: () => void;
}

export const AutomationConfirm: React.FC<Props> = ({ data, onConfirm, onCancel }) => {
  const { generated_body, validation_result, field_metadata } = data;

  return (
    <div className="automation-confirm">
      <Alert
        type="warning"
        message="数据校验提示"
        description={`生成${generated_body.length}条数据中，有${validation_result.invalid_count}条存在问题，请检查修正`}
      />

      {generated_body.map((body, idx) => (
        <Card key={idx} title={body.casedesc} style={{ marginTop: 16 }}>
          <ValidationTag validation={validation_result.results[idx].validation} />

          <Table
            dataSource={Object.entries(body.var || {}).map(([field, value]) => ({
              field,
              value,
              metadata: findFieldMetadata(field_metadata, field)
            }))}
            columns={[
              { title: '字段', dataIndex: 'field' },
              {
                title: '值',
                dataIndex: 'value',
                render: (value, record) => (
                  <Form.Item>
                    <Input
                      value={value}
                      onChange={(e) => updateFieldValue(idx, record.field, e.target.value)}
                    />
                    {record.metadata?.enums && (
                      <Select
                        style={{ width: 200 }}
                        options={record.metadata.enums}
                        value={value}
                        onChange={(v) => updateFieldValue(idx, record.field, v)}
                      />
                    )}
                  </Form.Item>
                )
              },
              {
                title: '可选值',
                render: (_, record) => (
                  record.metadata?.enums ? (
                    <Space wrap>
                      {record.metadata.enums.slice(0, 5).map(e => (
                        <Tag
                          key={e.value}
                          color={e.value === record.value ? 'blue' : 'default'}
                        >
                          {e.value}({e.label})
                        </Tag>
                      ))}
                      {record.metadata.enums.length > 5 && (
                        <Tag>+{record.metadata.enums.length - 5}更多</Tag>
                      )}
                    </Space>
                  ) : '-'
                )
              }
            ]}
          />
        </Card>
      ))}

      <div style={{ marginTop: 16, textAlign: 'right' }}>
        <Button onClick={onCancel}>取消</Button>
        <Button type="primary" onClick={() => onConfirm(generated_body)}>
          确认提交
        </Button>
      </div>
    </div>
  );
};
```

### 2.7 优化后流程图

```
┌──────────────────────────────────────────────────────────────────────┐
│                    create_case_with_fields_v2()                       │
├──────────────────────────────────────────────────────────────────────┤
│  步骤1: get_scene_cases(scene_id)                                    │
│         ↓ 获取场景用例列表                                            │
│                                                                      │
│  步骤2: select_best_case_by_ai(test_case_info, scene_cases)          │
│         ↓ AI选择最匹配模板                                            │
│                                                                      │
│  步骤3: get_case_detail(usercase_id)                                 │
│         ↓ 获取模板详情，提取 header, circulation                      │
│                                                                      │
│  步骤3.5: 新增 - 获取字段元数据                                        │
│         ↓ _fetch_field_metadata(scene_id)                            │
│         ↓ 获取枚举值 + 联动规则                                        │
│                                                                      │
│  步骤4: generate_case_body_by_ai_v2(...)                             │
│         ↓ AI生成测试数据（带枚举约束 + 联动规则）                        │
│                                                                      │
│  步骤4.5: 新增 - 校验数据有效性                                        │
│         ↓ validator.validate_all(generated_body)                     │
│         ↓ 检查枚举值、联动规则、必填字段                                │
│                                                                      │
│  步骤5: 判断是否需要人工确认                                           │
│         ↓ 无问题或不需要确认 → 直接创建用例                             │
│         ↓ 有问题且需要确认 → 返回前端展示                               │
│                                                                      │
│  前端确认流程:                                                        │
│         - 显示AI生成的数据                                             │
│         - 高亮显示有问题的字段                                         │
│         - 用户编辑修正                                                 │
│         - 确认后调用 confirm-submit API                               │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.8 关键技术点

#### 2.8.1 枚举值太多时的处理策略

```python
def _filter_enums_by_context(self, metadata: Dict, context: Dict) -> Dict:
    """
    动态筛选枚举值，避免token超限

    策略：
    1. 先传入核心字段的枚举值（如业务线、渠道）
    2. 根据已选值，逐步补充关联字段的枚举值
    3. AI生成时，先让AI选择核心字段，再根据选择补充后续
    """
    pass
```

#### 2.8.2 联动规则的两步生成策略

```python
async def generate_body_with_linkage(
    self,
    header_fields,
    test_case_info,
    field_metadata
):
    """
    分两步处理联动关系：

    第一步：生成核心字段的值（不含联动）
    第二步：根据已选值，动态补充枚举值，生成联动字段
    """
    # Step 1: 生成不依赖其他字段的字段值
    step1_result = await self._generate_independent_fields(...)

    # Step 2: 根据step1结果，筛选枚举值，生成联动字段
    filtered_metadata = self._filter_enums_by_context(
        field_metadata,
        step1_result
    )

    step2_result = await self._generate_dependent_fields(
        filtered_metadata,
        step1_result
    )

    return self._merge_results(step1_result, step2_result)
```

---

## 三、实施步骤

| 阶段 | 内容 | 工作量 |
|------|------|--------|
| **阶段1** | 与自动化平台方确认字段元数据API | 1天 |
| **阶段2** | 新增 `field_metadata_service.py` 和 `body_validator.py` | 2天 |
| **阶段3** | 优化 `generate_case_body_by_ai` 添加枚举约束 | 1天 |
| **阶段4** | 新增后端API `create-with-confirm` 和 `confirm-submit` | 1天 |
| **阶段5** | 前端确认界面开发 | 2天 |
| **阶段6** | 联调测试 | 2天 |

---

## 四、功能清单

### 4.1 AI生成时约束枚举值
- [ ] 从自动化平台获取字段枚举值
- [ ] 在AI Prompt中添加枚举值约束
- [ ] 枚举值过多时动态筛选

### 4.2 AI生成时处理联动关系
- [ ] 从自动化平台获取联动规则
- [ ] 在AI Prompt中添加联动规则说明
- [ ] 实现联动规则的两步生成策略

### 4.3 生成后校验数据有效性
- [ ] 实现 BodyValidator 校验服务
- [ ] 校验枚举值是否有效
- [ ] 校验联动规则是否满足
- [ ] 校验必填字段是否填写

### 4.4 前端界面人工确认
- [ ] 显示AI生成的测试数据
- [ ] 高亮显示有问题的字段
- [ ] 展示可选值下拉框
- [ ] 允许用户编辑修正
- [ ] 确认后提交到自动化平台

---

## 五、相关文档

- [自动化平台集成](./AUTOMATION_PLATFORM_INTEGRATION.md)
- [AI智能生成测试数据](./AI_GENERATE_BODY_DATA.md)
- [用例数据结构说明](./CASE_DATA_STRUCTURE.md)
