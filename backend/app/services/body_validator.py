"""测试数据校验服务"""

from typing import Dict, List, Any


class BodyValidator:
    """测试数据校验服务 - 校验枚举值、联动规则、必填字段"""

    def __init__(self, field_metadata: Dict):
        """
        初始化校验器

        Args:
            field_metadata: 字段元数据（包含枚举值和联动规则）
        """
        self.metadata = field_metadata
        # 创建字段映射，方便快速查找
        self.fields_map = {
            field['row']: field
            for field in field_metadata.get('fields', [])
        }

    def validate(self, body_data: Dict) -> Dict:
        """
        校验单条body数据

        Args:
            body_data: 测试数据 {"casedesc": "...", "var": {...}}

        Returns:
            {
                "valid": True/False,
                "errors": [...],
                "warnings": [...],
                "suggestions": [...]
            }
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }

        var = body_data.get('var', {})
        if not var:
            result['warnings'].append({
                "type": "empty_data",
                "message": "测试数据为空"
            })
            return result

        # 1. 校验枚举值
        enum_errors = self._validate_enums(var)
        result['errors'].extend(enum_errors)

        # 2. 校验联动规则
        linkage_errors = self._validate_linkage(var)
        result['errors'].extend(linkage_errors)

        # 3. 校验必填字段
        required_errors = self._validate_required(var)
        result['errors'].extend(required_errors)

        # 4. 检查未知字段（警告）
        unknown_warnings = self._check_unknown_fields(var)
        result['warnings'].extend(unknown_warnings)

        # 设置最终校验结果
        if result['errors']:
            result['valid'] = False

        return result

    def _validate_enums(self, var: Dict) -> List[Dict]:
        """
        校验枚举值是否有效

        Args:
            var: 字段值字典

        Returns:
            错误列表
        """
        errors = []

        for field_name, value in var.items():
            # 跳过空值
            if value is None or value == '':
                continue

            # 查找字段元数据
            field = self.fields_map.get(field_name)
            if not field:
                continue

            # 检查是否有枚举值定义
            enums = field.get('enums')
            if not enums or len(enums) == 0:
                continue

            # 提取所有有效的枚举值
            enum_values = [str(e['value']) for e in enums]

            # 校验当前值是否在枚举范围内
            if str(value) not in enum_values:
                # 生成友好的建议
                suggestion_values = enum_values[:5]  # 最多显示5个
                if len(enum_values) > 5:
                    suggestion_str = f"{', '.join(suggestion_values)}... (共{len(enum_values)}个选项)"
                else:
                    suggestion_str = ', '.join(suggestion_values)

                errors.append({
                    "field": field_name,
                    "fieldName": field.get('rowName', field_name),
                    "value": value,
                    "type": "enum_invalid",
                    "message": f"值 '{value}' 不在有效范围内",
                    "suggestion": f"建议从以下值中选择: {suggestion_str}",
                    "validValues": enum_values
                })

        return errors

    def _validate_linkage(self, var: Dict) -> List[Dict]:
        """
        校验联动规则

        Args:
            var: 字段值字典

        Returns:
            错误列表
        """
        errors = []

        for field in self.metadata.get('fields', []):
            field_name = field['row']
            field_value = var.get(field_name)

            # 检查枚举值触发的联动规则
            if field.get('enumDependencies') and field_value:
                for dep in field['enumDependencies']:
                    # 如果当前字段值匹配触发值
                    if str(dep.get('enumValue')) != str(field_value):
                        continue

                    # 检查必填字段
                    for req_field in dep.get('requiredFields', []):
                        req_value = var.get(req_field)
                        if not req_value:
                            req_field_meta = self.fields_map.get(req_field, {})
                            errors.append({
                                "field": req_field,
                                "fieldName": req_field_meta.get('rowName', req_field),
                                "type": "linkage_required",
                                "message": f"当【{field.get('rowName', field_name)}】= {field_value} 时，此字段为必填",
                                "suggestion": "请填写一个有效值",
                                "triggerField": field_name,
                                "triggerValue": field_value
                            })

                    # 检查应该隐藏的字段
                    for hide_field in dep.get('hideFields', []):
                        hide_value = var.get(hide_field)
                        if hide_value:
                            hide_field_meta = self.fields_map.get(hide_field, {})
                            errors.append({
                                "field": hide_field,
                                "fieldName": hide_field_meta.get('rowName', hide_field),
                                "value": hide_value,
                                "type": "linkage_hide",
                                "message": f"当【{field.get('rowName', field_name)}】= {field_value} 时，此字段应为空",
                                "suggestion": "建议清空此字段",
                                "triggerField": field_name,
                                "triggerValue": field_value
                            })

            # 检查字段依赖（被其他字段触发显示）
            if field.get('dependencies'):
                for dep in field['dependencies']:
                    trigger_field = dep.get('triggerField')
                    trigger_value = dep.get('triggerValue')
                    action = dep.get('action', 'show')

                    trigger_field_value = var.get(trigger_field)

                    # 如果触发条件满足，字段应该有值
                    if action == 'show' and str(trigger_field_value) == str(trigger_value):
                        if not field_value and field.get('required'):
                            errors.append({
                                "field": field_name,
                                "fieldName": field.get('rowName', field_name),
                                "type": "linkage_required",
                                "message": f"当触发字段满足条件时，此字段应填写",
                                "suggestion": "请填写一个有效值",
                                "triggerField": trigger_field,
                                "triggerValue": trigger_value
                            })

        return errors

    def _validate_required(self, var: Dict) -> List[Dict]:
        """
        校验必填字段

        Args:
            var: 字段值字典

        Returns:
            错误列表
        """
        errors = []

        for field in self.metadata.get('fields', []):
            # 跳过非必填字段
            if not field.get('required'):
                continue

            field_name = field['row']
            field_value = var.get(field_name)

            # 检查是否为空
            if not field_value:
                errors.append({
                    "field": field_name,
                    "fieldName": field.get('rowName', field_name),
                    "type": "required",
                    "message": f"必填字段不能为空",
                    "suggestion": "请填写一个有效值"
                })

        return errors

    def _check_unknown_fields(self, var: Dict) -> List[Dict]:
        """
        检查未知字段（元数据中不存在的字段）

        Args:
            var: 字段值字典

        Returns:
            警告列表
        """
        warnings = []

        for field_name in var.keys():
            if field_name not in self.fields_map:
                warnings.append({
                    "field": field_name,
                    "type": "unknown_field",
                    "message": f"字段 '{field_name}' 在元数据中未定义"
                })

        return warnings

    def validate_all(self, body_list: List[Dict]) -> Dict:
        """
        批量校验所有body数据

        Args:
            body_list: 测试数据列表

        Returns:
            {
                "total": 总数,
                "valid_count": 有效数量,
                "invalid_count": 无效数量,
                "total_errors": 总错误数,
                "results": [每条数据的校验结果]
            }
        """
        if not body_list:
            return {
                "total": 0,
                "valid_count": 0,
                "invalid_count": 0,
                "total_errors": 0,
                "results": []
            }

        results = []

        for idx, body in enumerate(body_list):
            validation = self.validate(body)
            results.append({
                "index": idx,
                "casedesc": body.get('casedesc', f'测试数据{idx+1}'),
                "validation": validation
            })

        # 统计汇总
        valid_count = sum(1 for r in results if r['validation']['valid'])
        invalid_count = len(results) - valid_count
        total_errors = sum(len(r['validation']['errors']) for r in results)

        return {
            "total": len(body_list),
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "total_errors": total_errors,
            "results": results
        }

    def get_field_suggestions(self, field_name: str) -> Dict:
        """
        获取字段的建议值和约束信息

        Args:
            field_name: 字段名

        Returns:
            字段建议信息
        """
        field = self.fields_map.get(field_name)
        if not field:
            return {}

        suggestions = {
            "fieldName": field.get('rowName', field_name),
            "type": field.get('type', 'text'),
            "required": field.get('required', False),
            "enums": field.get('enums', []),
            "dependencies": field.get('dependencies', []),
            "description": field.get('description', '')
        }

        return suggestions
