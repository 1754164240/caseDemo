# 用例数据结构说明

**版本**: v1.3.3  
**日期**: 2024-12-16

---

## 📋 完整数据结构

### 用例对象（Case Object）

```json
{
  "usercaseId": "1d5dafbe-3ab2-4c01-b86b-9897adfe7e65",
  "sceneId": "c5681443-a5a4-c0cc-8a2d-0e06f0cebfea",
  "project": "project_2",
  "description": "",
  "name": "柜面理赔-重疾险_copy",
  "type": "5",
  "tags": "[]",
  "moduleId": "8ff501fb-1100-4e20-9d58-d171f9ede2f2",
  "circulation": [...],
  "caseDefine": {...},
  "createBy": "admin",
  "createTime": 1765976884104,
  "updateBy": "admin",
  "updateTime": 1765976884104,
  "scenarioType": "API",
  "typeName": "流程类",
  "sceneName": "柜面理赔",
  "num": 18891,
  "caseNum": 7,
  "caseSumNum": 7
}
```

---

## 🔑 关键字段说明

### 基础信息

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `usercaseId` | string | 用例唯一标识 | "1d5dafbe-3ab2-4c01-b86b-..." |
| `name` | string | 用例名称 | "柜面理赔-重疾险_copy" |
| `sceneId` | string | 场景ID | "c5681443-a5a4-c0cc-..." |
| `moduleId` | string | 模块ID | "8ff501fb-1100-4e20-..." |
| `scenarioType` | string | 场景类型 | "API" |
| `type` | string | 用例类型 | "5" (流程类) |
| `project` | string | 项目标识 | "project_2" |
| `description` | string | 用例描述 | "" |
| `tags` | string (JSON) | 标签数组 | "[]" 或 "[\"理赔(CP)\"]" |

### 统计信息

| 字段 | 类型 | 说明 |
|------|------|------|
| `num` | number | 用例编号 | 18891 |
| `caseNum` | number | 测试数据数量 | 7 |
| `caseSumNum` | number | 测试数据总数 | 7 |

### 元数据

| 字段 | 类型 | 说明 |
|------|------|------|
| `createBy` | string | 创建人 | "admin" |
| `createTime` | number | 创建时间戳 | 1765976884104 |
| `updateBy` | string | 更新人 | "admin" |
| `updateTime` | number | 更新时间戳 | 1765976884104 |

---

## 🔄 Circulation（环节信息）

```json
{
  "circulation": [
    {
      "num": 2,
      "name": "理赔",
      "vargroup": "CP"
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `num` | number | 环节序号 | 2 |
| `name` | string | 环节名称 | "理赔" |
| `vargroup` | string | 变量组 | "CP" |

### 用途

- 🏷️ **标签生成**: 自动转换为标签 "理赔(CP)"
- 📋 **流程标识**: 标识用例所属的业务环节
- 🔗 **变量关联**: 关联到特定的变量组

---

## 📊 CaseDefine（用例定义）

### 完整结构

```json
{
  "caseDefine": {
    "usercaseId": null,
    "header": [...],
    "body": [...]
  }
}
```

### Header（字段定义）

**结构:**
```json
{
  "header": [
    {
      "row": "Cont_contno",
      "flag": null,
      "rowName": "保单信息_保单号",
      "type": null
    },
    {
      "row": "Risk_riskcode",
      "flag": "RiskFlag",
      "rowName": "险种_险种编码",
      "type": null
    }
    // ... 更多字段
  ]
}
```

**字段说明:**

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `row` | string | ✅ | 字段标识 | "CP_accidentReason_1" |
| `rowName` | string | ✅ | 字段显示名称 | "理赔_出险原因_1" |
| `flag` | string | ❌ | 标志位 | "RiskFlag" 或 null |
| `type` | string | ❌ | 字段类型 | "" 或 null |

**示例字段:**

1. **保单信息**
   ```json
   {
     "row": "Cont_contno",
     "flag": null,
     "rowName": "保单信息_保单号",
     "type": null
   }
   ```

2. **险种信息**
   ```json
   {
     "row": "Risk_riskcode",
     "flag": "RiskFlag",
     "rowName": "险种_险种编码",
     "type": null
   }
   ```

3. **理赔字段**
   ```json
   {
     "row": "CP_accidentType_1",
     "flag": null,
     "rowName": "理赔_出险人类型_1",
     "type": null
   }
   ```

### Body（测试数据）

**结构:**
```json
{
  "body": [
    {
      "caseId": 307091,
      "usercaseId": "1d5dafbe-3ab2-4c01-b86b-9897adfe7e65",
      "casezf": "1",
      "casedesc": "ADDTAE-疾病身故",
      "var": {
        "Risk_riskcode": "",
        "CP_StmSrcCd_1": "02-个险",
        "Cont_contno": "IP3713202500007096",
        "序号": "26",
        "CP_clmInsBnftECD_1": "ADDTAE4001",
        "CP_accidentType_1": "被保人",
        "CP_isCheck_1": "N",
        "CP_accidentReason_1": "1-疾病",
        "CP_claimType_1": "02-身故",
        "CP_cct_1": "1",
        "CP_accidentDay_1": "20250120"
      },
      "hoperesult": "成功结案",
      "iscaserun": false,
      "runresult": null,
      "importVariable": null,
      "createBy": "admin",
      "createTime": 1765976884127,
      "updateBy": "admin",
      "updateTime": 1765976884127,
      "files": null,
      "caseBodySN": 4,
      "success": true
    }
    // ... 更多测试数据
  ]
}
```

**字段说明:**

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `caseId` | number | 测试数据ID | 307091 |
| `usercaseId` | string | 所属用例ID | "1d5dafbe-..." |
| `casezf` | string | 执行标志 | "1" |
| `casedesc` | string | 测试场景描述 | "ADDTAE-疾病身故" |
| `var` | object | **变量值对象** | {...} |
| `hoperesult` | string | 预期结果 | "成功结案" |
| `iscaserun` | boolean | 是否执行 | false |
| `runresult` | string | 执行结果 | null |
| `caseBodySN` | number | 序号 | 4 |
| `success` | boolean | 是否成功 | true |

### Var（变量值对象）

**关键特点:**
- 📋 Key 对应 `header` 中的 `row` 字段
- 📝 Value 是具体的测试数据值
- 🔗 建立了字段定义和实际值的映射关系

**映射示例:**

| Header (row) | Var (key) | Var (value) | RowName |
|--------------|-----------|-------------|---------|
| Cont_contno | Cont_contno | "IP3713202500007096" | 保单信息_保单号 |
| CP_accidentReason_1 | CP_accidentReason_1 | "1-疾病" | 理赔_出险原因_1 |
| CP_claimType_1 | CP_claimType_1 | "02-身故" | 理赔_理赔类型_1 |

---

## 🔄 数据流转

### 1. 从模板获取

```python
# 获取模板用例详情
case_detail = self.get_case_detail(template_usercase_id)

# case_detail 包含完整的 caseDefine
{
  "caseDefine": {
    "header": [16个字段],
    "body": [7个测试数据]
  }
}
```

### 2. 创建新用例

```python
# 调用 createCaseAndBody
payload = {
  "name": "新用例名称",
  "moduleId": "...",
  "sceneId": "...",
  "caseDefine": case_detail.get("caseDefine"),  # 完整传递
  "circulation": [...]
}
```

### 3. 返回结果

```json
{
  "success": true,
  "data": {
    "usercaseId": "新创建的ID",
    "num": 18892,
    "caseNum": 7,
    "caseDefine": {
      "header": [16个字段],
      "body": [7个测试数据]
    }
  }
}
```

---

## 📝 实际示例

### 示例1: 柜面理赔-重疾险

**基础信息:**
- 用例名称: "柜面理赔-重疾险_copy"
- 场景: "柜面理赔"
- 类型: "流程类"

**字段定义（16个）:**
1. 保单信息_保单号
2. 险种_险种编码
3. 理赔_出险人类型_1
4. 理赔_出险原因_1
5. 理赔_理赔类型_1
6. 理赔_理赔类型_2
7. 理赔_理赔案件类型代码_1
8. 理赔_保险金编码_1
9. 理赔_保险金编码_2
10. 理赔_赔案属性_1
11. 理赔_是否校验_1
12. 理赔_效力初次状态_1
13. 理赔_理赔次数_1
14. 理赔_特疾类型_1
15. 理赔_特疾代码_1
16. 理赔_出险日期_1

**测试数据（7条）:**
1. ADDTAE-疾病身故
2. ADDTAE-意外身故
3. ADDTAE-意外重疾
4. ADDTAE-疾病重疾
5. ADDTAE-轻症豁免
6. ADDTAE-轻症豁免（重复）
7. ADDTAE-中症豁免

### 示例2: 创建Payload

```json
{
  "name": "测试理赔流程",
  "moduleId": "8ff501fb-1100-4e20-9d58-d171f9ede2f2",
  "sceneId": "c5681443-a5a4-c0cc-8a2d-0e06f0cebfea",
  "scenarioType": "API",
  "description": "基于重疾险模板创建",
  "tags": "[\"理赔(CP)\"]",
  "project": "project_2",
  "type": "5",
  "circulation": [
    {
      "num": 2,
      "name": "理赔",
      "vargroup": "CP"
    }
  ],
  "caseDefine": {
    "header": [
      {"row": "Cont_contno", "rowName": "保单信息_保单号", ...},
      {"row": "CP_accidentReason_1", "rowName": "理赔_出险原因_1", ...}
      // ... 16个字段
    ],
    "body": [
      {
        "casedesc": "ADDTAE-疾病身故",
        "var": {
          "Cont_contno": "IP3713202500007096",
          "CP_accidentReason_1": "1-疾病",
          "CP_claimType_1": "02-身故"
          // ... 更多变量
        },
        "hoperesult": "成功结案"
      }
      // ... 7条测试数据
    ]
  }
}
```

---

## ⚠️ 注意事项

### 1. CaseDefine 的完整性

✅ **必须包含:**
- `header`: 字段定义数组
- `body`: 测试数据数组

❌ **常见错误:**
```python
# 错误：只传递 header
payload["caseDefine"] = {"header": [...]}

# 正确：完整传递
payload["caseDefine"] = case_detail.get("caseDefine")
```

### 2. Body 数据的关联性

- `body` 中的 `var` 对象的 key 必须在 `header` 中定义
- 否则数据无法正确映射

### 3. Circulation 的转换

```python
# Circulation → Tags
circulation = [{"num": 2, "name": "理赔", "vargroup": "CP"}]
↓
tags = "[\"理赔(CP)\"]"
```

### 4. 数据一致性

创建新用例时：
- ✅ 保留模板的 `caseDefine` 结构
- ✅ 更新 `name` 为新名称
- ✅ 更新 `moduleId` 和 `sceneId`
- ✅ 添加 `tags`（从 circulation 生成）
- ❌ 不要修改 `caseDefine` 的内部结构

---

## 🔍 调试建议

### 查看日志

```bash
tail -f backend/logs/app.log | grep "caseDefine"
```

**预期输出:**
```
[INFO] caseDefine 包含 16 个字段(header), 7 个测试数据(body)
[INFO] CaseDefine: header=16, body=7
```

### 验证数据

```python
# 验证 header
assert len(case_define.get("header", [])) > 0

# 验证 body
assert len(case_define.get("body", [])) > 0

# 验证 var 对象
for body_item in case_define.get("body", []):
    assert "var" in body_item
    assert isinstance(body_item["var"], dict)
```

---

## 📚 相关文档

- **[v1.3.3 一步到位创建](./UPDATE_v1.3.3_ONE_STEP_CREATION.md)** - API调用说明
- **[用例生成完整实现](./CASE_GENERATION_WITH_DETAILS.md)** - 完整流程
- **[文档索引](./DOCUMENTATION_INDEX.md)** - 所有文档

---

**文档版本**: v1.3.3  
**最后更新**: 2024-12-16  
**状态**: ✅ 已完成





