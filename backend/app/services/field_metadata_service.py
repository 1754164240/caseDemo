"""字段元数据服务 - 管理枚举值和联动规则"""

from typing import Dict, List, Optional
import requests
from app.core.config import settings


class FieldMetadataService:
    """字段元数据服务 - 管理枚举值和联动规则"""

    def __init__(self, automation_service):
        """
        初始化字段元数据服务

        Args:
            automation_service: 自动化平台服务实例
        """
        self.auto_svc = automation_service
        self._cache = {}  # 场景ID -> 字段元数据缓存

    def fetch_field_metadata(self, scene_id: str) -> Dict:
        """
        从自动化平台获取字段元数据

        Args:
            scene_id: 场景ID

        Returns:
            字段元数据（包含枚举值和联动规则）
        """
        # 检查缓存
        cache_key = f"metadata_{scene_id}"
        if cache_key in self._cache:
            print(f"[INFO] 从缓存获取场景 {scene_id} 的字段元数据")
            return self._cache[cache_key]

        # 调用自动化平台API
        url = f"{self.auto_svc.base_url}/ai/case/queryFieldMetadata"
        params = {"sceneId": scene_id}

        try:
            print(f"[INFO] 请求字段元数据: {url}")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            result = response.json()

            if result.get("success"):
                metadata = result.get("data", {})
                print(f"[INFO] 成功获取 {len(metadata.get('fields', []))} 个字段的元数据")

                # 缓存结果
                self._cache[cache_key] = metadata
                return metadata
            else:
                print(f"[WARNING] 获取字段元数据失败: {result.get('message')}")
                return self._get_empty_metadata()

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] 获取字段元数据请求异常: {e}")
            return self._get_empty_metadata()
        except Exception as e:
            print(f"[ERROR] 获取字段元数据异常: {type(e).__name__}: {e}")
            return self._get_empty_metadata()

    def _get_empty_metadata(self) -> Dict:
        """返回空的元数据结构"""
        return {
            "fields": [],
            "fieldGroups": []
        }

    def extract_linkage_rules(self, metadata: Dict) -> List[Dict]:
        """
        提取联动规则，用于AI Prompt

        Args:
            metadata: 字段元数据

        Returns:
            联动规则列表
        """
        rules = []

        for field in metadata.get('fields', []):
            field_row = field.get('row', '')
            field_name = field.get('rowName', field_row)

            # 提取枚举值联动规则
            if field.get('enumDependencies'):
                for dep in field['enumDependencies']:
                    rule = {
                        "field": field_row,
                        "fieldName": field_name,
                        "whenValue": dep.get('enumValue', ''),
                        "showFields": dep.get('showFields', []),
                        "hideFields": dep.get('hideFields', []),
                        "requiredFields": dep.get('requiredFields', [])
                    }
                    rules.append(rule)

            # 提取字段依赖规则
            if field.get('dependencies'):
                for dep in field['dependencies']:
                    rule = {
                        "field": field_row,
                        "fieldName": field_name,
                        "triggerField": dep.get('triggerField', ''),
                        "triggerValue": dep.get('triggerValue', ''),
                        "action": dep.get('action', 'show')
                    }
                    rules.append(rule)

        print(f"[INFO] 提取到 {len(rules)} 条联动规则")
        return rules

    def filter_enums_by_context(self, metadata: Dict, context: Dict) -> Dict:
        """
        根据上下文动态筛选枚举值（避免token超限）

        Args:
            metadata: 字段元数据
            context: 已选择的字段值 {field_name: value}

        Returns:
            筛选后的元数据
        """
        if not context:
            return metadata

        # 深拷贝避免修改原数据
        import copy
        filtered = copy.deepcopy(metadata)

        for field in filtered.get('fields', []):
            field_name = field['row']

            # 如果字段有依赖关系，检查触发条件
            if field.get('dependencies'):
                is_applicable = False

                for dep in field['dependencies']:
                    trigger_field = dep.get('triggerField', '')
                    trigger_value = dep.get('triggerValue', '')

                    # 检查上下文中是否有触发字段的值
                    if trigger_field in context:
                        if str(context[trigger_field]) == str(trigger_value):
                            is_applicable = True
                            break

                # 如果不满足触发条件，标记为不适用
                if not is_applicable:
                    field['_applicable'] = False
                    field['enums'] = []  # 清空枚举值
                    print(f"[DEBUG] 字段 {field_name} 不满足触发条件，已过滤枚举值")

        return filtered

    def find_field_metadata(self, metadata: Dict, field_name: str) -> Optional[Dict]:
        """
        查找指定字段的元数据

        Args:
            metadata: 字段元数据
            field_name: 字段名

        Returns:
            字段元数据，未找到返回None
        """
        for field in metadata.get('fields', []):
            if field.get('row') == field_name:
                return field
        return None

    def get_enum_values(self, metadata: Dict, field_name: str) -> List[Dict]:
        """
        获取字段的枚举值列表

        Args:
            metadata: 字段元数据
            field_name: 字段名

        Returns:
            枚举值列表 [{"value": "...", "label": "..."}]
        """
        field_meta = self.find_field_metadata(metadata, field_name)
        if field_meta and field_meta.get('enums'):
            return field_meta['enums']
        return []

    def is_field_required(self, metadata: Dict, field_name: str, context: Dict = None) -> bool:
        """
        判断字段是否必填（考虑联动规则）

        Args:
            metadata: 字段元数据
            field_name: 字段名
            context: 上下文字段值

        Returns:
            是否必填
        """
        field_meta = self.find_field_metadata(metadata, field_name)
        if not field_meta:
            return False

        # 基础必填属性
        if field_meta.get('required'):
            return True

        # 检查联动规则导致的必填
        if context:
            for other_field in metadata.get('fields', []):
                if not other_field.get('enumDependencies'):
                    continue

                other_field_value = context.get(other_field['row'])
                if not other_field_value:
                    continue

                # 检查是否触发了必填规则
                for dep in other_field['enumDependencies']:
                    if str(dep.get('enumValue')) == str(other_field_value):
                        if field_name in dep.get('requiredFields', []):
                            return True

        return False

    def clear_cache(self, scene_id: str = None):
        """
        清除缓存

        Args:
            scene_id: 场景ID，如果为None则清除所有缓存
        """
        if scene_id:
            cache_key = f"metadata_{scene_id}"
            if cache_key in self._cache:
                del self._cache[cache_key]
                print(f"[INFO] 已清除场景 {scene_id} 的元数据缓存")
        else:
            self._cache.clear()
            print(f"[INFO] 已清除所有元数据缓存")
