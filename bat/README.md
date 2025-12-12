# 鎵瑰鐞嗚剼鏈鏄?

鏈枃浠跺す鍖呭惈椤圭洰鐨勬墍鏈夋壒澶勭悊鑴氭湰锛岀敤浜庣畝鍖栧紑鍙戝拰閮ㄧ讲娴佺▼銆?

## 馃摝 瀹夎鑴氭湰

### install-backend.bat
**鍔熻兘**: 瀹夎鍚庣 Python 渚濊禆

**浣跨敤鏂规硶**:
```bash
bat\install-backend.bat
```

**鎵ц鍐呭**:
- 杩涘叆 backend 鐩綍
- 鎵ц `pip install -r requirements.txt`
- 瀹夎鎵€鏈?Python 渚濊禆鍖?

---

### install-frontend.bat
**鍔熻兘**: 瀹夎鍓嶇 Node.js 渚濊禆

**浣跨敤鏂规硶**:
```bash
bat\install-frontend.bat
```

**鎵ц鍐呭**:
- 杩涘叆 frontend 鐩綍
- 鎵ц `npm install`
- 瀹夎鎵€鏈?Node.js 渚濊禆鍖?

---

### install-missing-deps.bat
**鍔熻兘**: 瀹夎缂哄け鐨勪緷璧栧寘

**浣跨敤鏂规硶**:
```bash
bat\install-missing-deps.bat
```

**鎵ц鍐呭**:
- 妫€鏌ュ苟瀹夎缂哄け鐨?Python 鍖?
- 淇渚濊禆闂

---

## 鈻讹笍 鍚姩鑴氭湰

### start-backend.bat
**鍔熻兘**: 鍚姩鍚庣鏈嶅姟

**浣跨敤鏂规硶**:
```bash
bat\start-backend.bat
```

**鎵ц鍐呭**:
- 杩涘叆 backend 鐩綍
- 鎵ц `python -m scripts.main`
- 鍚姩 FastAPI 鏈嶅姟锛坔ttp://localhost:8000锛?

---

### start-frontend.bat
**鍔熻兘**: 鍚姩鍓嶇鏈嶅姟

**浣跨敤鏂规硶**:
```bash
bat\start-frontend.bat
```

**鎵ц鍐呭**:
- 杩涘叆 frontend 鐩綍
- 鎵ц `npm run dev`
- 鍚姩 Vite 寮€鍙戞湇鍔″櫒锛坔ttp://localhost:5173锛?

---

## 馃敡 閰嶇疆鑴氭湰

### setup-env.bat
**鍔熻兘**: 閰嶇疆鐜鍙橀噺

**浣跨敤鏂规硶**:
```bash
bat\setup-env.bat
```

**鎵ц鍐呭**:
- 鍒涘缓 `.env` 鏂囦欢
- 閰嶇疆鏁版嵁搴撹繛鎺?
- 閰嶇疆 AI 妯″瀷鍙傛暟
- 閰嶇疆 Milvus 杩炴帴

---

### create-system-config-table.bat
**鍔熻兘**: 鍒涘缓绯荤粺閰嶇疆琛?

**浣跨敤鏂规硶**:
```bash
bat\create-system-config-table.bat
```

**鎵ц鍐呭**:
- 杩愯鏁版嵁搴撹縼绉昏剼鏈?
- 鍒涘缓 `system_config` 琛?
- 鐢ㄤ簬瀛樺偍绯荤粺閰嶇疆淇℃伅

---

### create-test-point-history-table.bat
**功能**: 初始化 `test_point_histories` 表, 记录测试点版本历史

**使用方法**:
```bash
bat\create-test-point-history-table.bat
```

**执行内容**:
- 运行 `backend/scripts/run_test_point_history_migration.py`
- 创建/更新 `test_point_histories` 表及索引
- 确保版本历史功能可用

---

## 馃懁 鐢ㄦ埛绠＄悊鑴氭湰

### create-test-user.bat
**鍔熻兘**: 鍒涘缓娴嬭瘯鐢ㄦ埛

**浣跨敤鏂规硶**:
```bash
bat\create-test-user.bat
```

**鎵ц鍐呭**:
- 杩愯鐢ㄦ埛鍒涘缓鑴氭湰
- 鍒涘缓娴嬭瘯璐﹀彿
- 鐢ㄤ簬寮€鍙戝拰娴嬭瘯

---

### set-superuser.bat
**鍔熻兘**: 璁剧疆瓒呯骇绠＄悊鍛?

**浣跨敤鏂规硶**:
```bash
bat\set-superuser.bat
```

**鎵ц鍐呭**:
- 鎻愮ず杈撳叆鐢ㄦ埛鍚?
- 灏嗘寚瀹氱敤鎴疯缃负瓒呯骇绠＄悊鍛?
- 鎺堜簣绯荤粺绠＄悊鏉冮檺

---

## 鉁?妫€鏌ヨ剼鏈?

### check-setup.bat
**鍔熻兘**: 妫€鏌ョ幆澧冮厤缃?

**浣跨敤鏂规硶**:
```bash
bat\check-setup.bat
```

**鎵ц鍐呭**:
- 妫€鏌?Python 鐗堟湰
- 妫€鏌?Node.js 鐗堟湰
- 妫€鏌?Docker 鐘舵€?
- 妫€鏌?.env 鏂囦欢
- 妫€鏌ユ暟鎹簱瀹瑰櫒
- 妫€鏌ヤ緷璧栧畨瑁?

---

### test-document-processing.bat
**鍔熻兘**: 娴嬭瘯鏂囨。澶勭悊鍔熻兘

**浣跨敤鏂规硶**:
```bash
bat\test-document-processing.bat
```

**鎵ц鍐呭**:
- 杩愯鏂囨。瑙ｆ瀽娴嬭瘯
- 娴嬭瘯 AI 鏈嶅姟
- 楠岃瘉鍔熻兘姝ｅ父

---

## 馃洜锔?淇鑴氭湰

### fix-backend.bat
**鍔熻兘**: 淇鍚庣闂

**浣跨敤鏂规硶**:
```bash
bat\fix-backend.bat
```

**鎵ц鍐呭**:
- 妫€鏌ュ苟淇鐜閰嶇疆
- 淇渚濊禆闂
- 閲嶆柊瀹夎蹇呰鐨勫寘

---

## 馃摑 浣跨敤寤鸿

### 棣栨瀹夎娴佺▼
```bash
# 1. 瀹夎鍚庣渚濊禆
bat\install-backend.bat

# 2. 瀹夎鍓嶇渚濊禆
bat\install-frontend.bat

# 3. 閰嶇疆鐜鍙橀噺
bat\setup-env.bat

# 4. 鍒涘缓绯荤粺閰嶇疆琛?
bat\create-system-config-table.bat

# 5. 初始化测试点版本历史表
bat\create-test-point-history-table.bat

# 6. 鍒涘缓娴嬭瘯鐢ㄦ埛
bat\create-test-user.bat

# 7. 璁剧疆瓒呯骇绠＄悊鍛?
bat\set-superuser.bat
```

### 鏃ュ父寮€鍙戞祦绋?
```bash
# 鍚姩鍚庣锛堢粓绔?锛?
bat\start-backend.bat

# 鍚姩鍓嶇锛堢粓绔?锛?
bat\start-frontend.bat
```

### 鐜妫€鏌?
```bash
# 妫€鏌ョ幆澧冮厤缃?
bat\check-setup.bat
```

---

## 鈿狅笍 娉ㄦ剰浜嬮」

1. **杩愯鏉冮檺**: 鏌愪簺鑴氭湰鍙兘闇€瑕佺鐞嗗憳鏉冮檺
2. **宸ヤ綔鐩綍**: 鎵€鏈夎剼鏈簲浠庨」鐩牴鐩綍杩愯
3. **璺緞闂**: 浣跨敤 `bat\` 鍓嶇紑璋冪敤鑴氭湰
4. **渚濊禆椤哄簭**: 鎸夌収鎺ㄨ崘椤哄簭鎵ц瀹夎鑴氭湰

---

## 馃敆 鐩稿叧鏂囨。

- [蹇€熷惎鍔ㄦ寚鍗梋(../doc/QUICK_START.md)
- [璇︾粏瀹夎鎸囧崡](../doc/README_SETUP.md)
- [闂鎺掓煡鎸囧崡](../doc/TROUBLESHOOTING.md)

