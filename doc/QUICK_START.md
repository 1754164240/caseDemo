# 蹇€熷惎鍔ㄦ寚鍗?

## 鈿狅笍 閲嶈鎻愮ず

**棣栨浣跨敤蹇呰**:
1. 鉁?闇€瑕佸垱寤?*瓒呯骇绠＄悊鍛樿处鍙?*鎵嶈兘璁块棶绯荤粺閰嶇疆
2. 鉁?闇€瑕侀厤缃?**AI 妯″瀷 API Key** 鎵嶈兘浣跨敤 AI 鍔熻兘
3. 鉁?閰嶇疆淇敼鍚庨渶瑕?*閲嶅惎鍚庣**鎵嶈兘鐢熸晥

## 5 鍒嗛挓蹇€熷惎鍔?

### 鍓嶇疆鏉′欢

纭繚宸插畨瑁咃細
- 鉁?Python 3.10+ (鎺ㄨ崘 3.11 鎴?3.13)
- 鉁?Node.js 18+
- 鉁?Docker Desktop

> **閬囧埌闂锛?* 鏌ョ湅 [鏁呴殰鎺掗櫎鎸囧崡](./TROUBLESHOOTING.md)

### 姝ラ 1锛氬惎鍔ㄦ暟鎹簱锛? 鍒嗛挓锛?

鎵撳紑缁堢锛屽湪椤圭洰鏍圭洰褰曟墽琛岋細

```bash
docker-compose up -d
```

绛夊緟鎵€鏈夊鍣ㄥ惎鍔ㄥ畬鎴愩€?

### 姝ラ 2锛氶厤缃悗绔紙1 鍒嗛挓锛?

1. 澶嶅埗鐜鍙橀噺鏂囦欢锛?
```bash
cd backend
copy .env.example .env
```

2. 缂栬緫 `backend/.env` 鏂囦欢锛?*蹇呴』閰嶇疆 OpenAI API Key**锛?
```env
OPENAI_API_KEY=浣犵殑API瀵嗛挜
DATABASE_URL=postgresql+psycopg://testcase:testcase123@localhost:5432/test_case_db
```

鍏朵粬閰嶇疆鍙互淇濇寔榛樿銆?

> **閲嶈**: 鏁版嵁搴?URL 蹇呴』浣跨敤 `postgresql+psycopg://` 鏍煎紡锛圥ython 3.13 鍏煎锛?

### 姝ラ 3锛氬畨瑁呭悗绔緷璧栵紙1 鍒嗛挓锛?

鍙屽嚮杩愯锛?
```
install-backend.bat
```

鎴栨墜鍔ㄦ墽琛岋細
```bash
cd backend
pip install -r requirements.txt
```

### 姝ラ 4锛氬畨瑁呭墠绔緷璧栵紙1 鍒嗛挓锛?

鍙屽嚮杩愯锛?
```
install-frontend.bat
```

鎴栨墜鍔ㄦ墽琛岋細
```bash
cd frontend
npm install
```

### 姝ラ 5锛氬惎鍔ㄦ湇鍔★紙1 鍒嗛挓锛?

**鍚姩鍚庣**锛堟柊缁堢绐楀彛锛夛細
```
鍙屽嚮 start-backend.bat
```

鎴栨墜鍔ㄦ墽琛岋細
```bash
cd backend
python main.py
```

**鍚姩鍓嶇**锛堟柊缁堢绐楀彛锛夛細
```
鍙屽嚮 start-frontend.bat
```

鎴栨墜鍔ㄦ墽琛岋細
```bash
cd frontend
npm run dev
```

### 姝ラ 6锛氳闂郴缁?

鎵撳紑娴忚鍣ㄨ闂細
```
http://localhost:5173
```

## 棣栨浣跨敤

### 1. 鍒涘缓绠＄悊鍛樿处鍙?

**鏂规硶 1: 浣跨敤鑴氭湰鍒涘缓锛堟帹鑽愶級**

鍙屽嚮杩愯锛?
```
create-test-user.bat
```

杩欏皢鍒涘缓涓€涓秴绾х鐞嗗憳璐﹀彿锛?
- **鐢ㄦ埛鍚?*: `admin`
- **瀵嗙爜**: `admin123`
- **閭**: `admin@example.com`

**鏂规硶 2: 娉ㄥ唽鍚庤缃负瓒呯骇绠＄悊鍛?*

濡傛灉宸茬粡娉ㄥ唽浜嗚处鍙凤紝杩愯锛?
```
set-superuser.bat
```

鎸夋彁绀鸿緭鍏ョ敤鎴峰悕锛屽皢璇ョ敤鎴疯缃负瓒呯骇绠＄悊鍛樸€?

### 2. 鐧诲綍绯荤粺

浣跨敤绠＄悊鍛樿处鍙风櫥褰曪細
- 鐢ㄦ埛鍚? `admin`
- 瀵嗙爜: `admin123`

### 3. 閰嶇疆绯荤粺锛堥噸瑕侊紒锛?

**鍒涘缓閰嶇疆琛?*:
```
create-system-config-table.bat
```
**初始化版本历史表**:
```
create-test-point-history-table.bat
```
运行后会创建/更新 `test_point_histories` 表，确保测试点管理中的版本历史功能可用。


**閰嶇疆 AI 妯″瀷**:
1. 鐧诲綍鍚庣偣鍑诲乏渚ц彍鍗曠殑"绯荤粺绠＄悊"
2. 鍦?妯″瀷閰嶇疆"鍗＄墖涓～鍐欙細
   - **API Key**: 浣犵殑 API 瀵嗛挜
   - **API Base URL**: API 鍦板潃
   - **妯″瀷鍚嶇О**: 妯″瀷鍚嶇О

**绀轰緥閰嶇疆锛圡odelScope锛?*:
```
API Key: ms-xxxxxxxxxxxxx
API Base URL: https://api-inference.modelscope.cn/v1/chat/completions
妯″瀷鍚嶇О: deepseek-ai/DeepSeek-V3.1
```

3. 鐐瑰嚮"淇濆瓨閰嶇疆"
4. **閲嶅惎鍚庣**浣块厤缃敓鏁?

> **娉ㄦ剰**: 濡傛灉涓嶉厤缃?API Key锛岀郴缁熶細浣跨敤妯℃嫙鏁版嵁锛屾棤娉曠湡姝ｄ娇鐢?AI 鍔熻兘

### 4. 涓婁紶闇€姹傛枃妗?
- 杩涘叆"闇€姹傜鐞?
- 鐐瑰嚮"涓婁紶闇€姹?
- 濉啓鏍囬鍜屾弿杩?
- 閫夋嫨鏂囨。鏂囦欢锛堟敮鎸?DOCX銆丳DF銆乀XT銆乆LS銆乆LSX锛?
- 鐐瑰嚮涓婁紶

### 4. 鏌ョ湅娴嬭瘯鐐?
- 绛夊緟绯荤粺澶勭悊锛堜細鏀跺埌閫氱煡锛?
- 杩涘叆"鐢ㄤ緥绠＄悊" 鈫?"娴嬭瘯鐐?
- 鏌ョ湅 AI 鐢熸垚鐨勬祴璇曠偣

### 5. 鐢熸垚娴嬭瘯鐢ㄤ緥
- 鍦ㄦ祴璇曠偣鍒楄〃涓偣鍑?鐢熸垚鐢ㄤ緥"
- 绛夊緟鐢熸垚瀹屾垚锛堜細鏀跺埌閫氱煡锛?
- 鍒囨崲鍒?娴嬭瘯鐢ㄤ緥"鏍囩鏌ョ湅

## 甯歌闂

### Q1: Docker 瀹瑰櫒鍚姩澶辫触锛?
**A:** 纭繚 Docker Desktop 姝ｅ湪杩愯锛岀鍙?5432 鍜?19530 鏈鍗犵敤銆?

### Q2: 鍚庣鍚姩澶辫触锛?
**A:** 妫€鏌ワ細
1. Python 鐗堟湰鏄惁 3.10+
2. 渚濊禆鏄惁瀹夎瀹屾垚
3. `.env` 鏂囦欢鏄惁閰嶇疆姝ｇ‘
4. Docker 瀹瑰櫒鏄惁姝ｅ湪杩愯

### Q3: 鍓嶇鍚姩澶辫触锛?
**A:** 妫€鏌ワ細
1. Node.js 鐗堟湰鏄惁 18+
2. 渚濊禆鏄惁瀹夎瀹屾垚锛坄npm install`锛?
3. 绔彛 5173 鏄惁琚崰鐢?

### Q4: AI 鐢熸垚澶辫触锛?
**A:** 妫€鏌ワ細
1. OpenAI API Key 鏄惁姝ｇ‘閰嶇疆
2. API Key 鏄惁鏈夋晥
3. 缃戠粶鏄惁鍙互璁块棶 OpenAI API

### Q5: WebSocket 杩炴帴澶辫触锛?
**A:** 纭繚鍚庣鏈嶅姟姝ｅ湪杩愯锛屽埛鏂伴〉闈㈤噸鏂拌繛鎺ャ€?

## 鏈嶅姟鍦板潃

| 鏈嶅姟 | 鍦板潃 | 璇存槑 |
|------|------|------|
| 鍓嶇 | http://localhost:5173 | React 搴旂敤 |
| 鍚庣 | http://localhost:8000 | FastAPI 鏈嶅姟 |
| API 鏂囨。 | http://localhost:8000/docs | Swagger UI |
| PostgreSQL | localhost:5432 | 鏁版嵁搴?|
| Milvus | localhost:19530 | 鍚戦噺鏁版嵁搴?|

## 榛樿閰嶇疆

### 鏁版嵁搴?
- 鐢ㄦ埛鍚? `testcase`
- 瀵嗙爜: `testcase123`
- 鏁版嵁搴? `test_case_db`

### Milvus
- Host: `localhost`
- Port: `19530`

## 鍋滄鏈嶅姟

### 鍋滄鍓嶅悗绔?
鍦ㄨ繍琛岀殑缁堢绐楀彛鎸?`Ctrl + C`

### 鍋滄鏁版嵁搴?
```bash
docker-compose down
```

### 瀹屽叏娓呯悊锛堝寘鎷暟鎹級
```bash
docker-compose down -v
```

## 涓嬩竴姝?

- 馃摉 闃呰 [README.md](./readme.md) 浜嗚В璇︾粏鍔熻兘
- 馃摎 闃呰 [README_SETUP.md](./README_SETUP.md) 浜嗚В璇︾粏閰嶇疆
- 馃攳 闃呰 [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md) 浜嗚В椤圭洰缁撴瀯

## 鎶€鏈敮鎸?

閬囧埌闂锛?
1. 妫€鏌ユ湰鏂囨。鐨?甯歌闂"閮ㄥ垎
2. 鏌ョ湅缁堢鐨勯敊璇俊鎭?
3. 妫€鏌?Docker 瀹瑰櫒鐘舵€侊細`docker-compose ps`
4. 鏌ョ湅瀹瑰櫒鏃ュ織锛歚docker-compose logs`

绁濅娇鐢ㄦ剦蹇紒馃帀

