# 灏忕▼搴忓紑绁ㄦ櫤鑳戒綋 - 缁熶竴鍚庣鏈嶅姟

## 姒傝堪

**涓€涓湇鍔¤В鍐虫墍鏈夐棶棰樸€?* 鏁村悎浜嗚〃鍗曢獙璇併€佹覆鏌撻瑙堛€佸巻鍙叉煡璇€佹彁浜ょ敵璇峰叏閮?涓伐鍏枫€?
## 浣犵殑 API Key

```
ak-8Y5x8evzs6YO5CjvQSaMWHqhTL3vX9k2UYb2hQ85hA
```

**鐢ㄦ硶**锛氬湪鎵€鏈夎姹傜殑 Header 涓坊鍔?`X-API-Key: ak-8Y5x8evzs6YO5CjvQSaMWHqhTL3vX9k2UYb2hQ85hA`

## 4涓伐鍏风鐐?
| 绔偣 | 鏂规硶 | 鍔熻兘 |
|------|------|------|
| `/validate` | POST | 楠岃瘉4涓繀濉瓧娈靛畬鏁存€?|
| `/render` | POST | 鐢熸垚SVG琛ㄥ崟棰勮鍥?+ HTML鎻愪氦鎸夐挳 |
| `/query_history` | POST | 鏌ヨ鍘嗗彶寮€绁ㄨ褰曪紙mock/real鍙屾ā寮忥級 |
| `/submit_application` | POST | 鎻愪氦寮€绁ㄧ敵璇凤紙mock/real鍙屾ā寮忥級 |

## 3绉嶉儴缃叉柟寮忥紙浠庣畝鍒扮箒锛?
### 鏂瑰紡涓€锛氭湰鍦?Python 杩愯锛堟帹鑽愬厛娴嬭瘯锛?
```bash
# 1. 瀹夎渚濊禆
cd 00_缁熶竴鍚庣鏈嶅姟
pip install -r requirements.txt

# 2. 鍚姩
python main.py

# 3. 楠岃瘉
curl http://localhost:8000/health

# 4. 娴嬭瘯楠岃瘉鎺ュ彛
curl -X POST http://localhost:8000/validate \
  -H "X-API-Key: ak-8Y5x8evzs6YO5CjvQSaMWHqhTL3vX9k2UYb2hQ85hA" \
  -H "Content-Type: application/json" \
  -d '{"form_data":"{\"projectName\":\"鍏夋槑绉戝鍩嶾",\"amount\":\"50000\"}"}'
```

### 鏂瑰紡浜岋細Docker 閮ㄧ讲

```bash
docker build -t invoice-backend .
docker run -d --name invoice-backend -p 8000:8000 \
  -e SERVICE_HOST=http://浣犵殑IP:8000 \
  invoice-backend
```

### 鏂瑰紡涓夛細鍏嶈垂浜戝钩鍙伴儴缃?
**Railway**锛堟帹鑽愶紝鍏嶈垂棰濆害澶熺敤锛夛細
1. 娉ㄥ唽 [railway.app](https://railway.app)
2. 杩炴帴 GitHub锛屼笂浼犳湰椤圭洰
3. Railway 鑷姩妫€娴?Dockerfile 骞堕儴缃?4. 鑾峰緱鍏綉 URL 濡?`https://invoice-backend.up.railway.app`
5. 璁剧疆鐜鍙橀噺 `SERVICE_HOST=https://invoice-backend.up.railway.app`

**Render**锛堝厤璐癸級锛?1. 娉ㄥ唽 [render.com](https://render.com)
2. 鏂板缓 Web Service锛岄€夋嫨 Docker
3. 閮ㄧ讲鍚庤幏寰?`https://xxx.onrender.com`

## 鍦?AgentArts 涓婁娇鐢?
1. 閮ㄧ讲鏈嶅姟鍚庯紝璁颁笅鍏綉鍦板潃锛堝 `https://invoice-backend.up.railway.app`锛?2. 鍦?AgentArts 鍒涘缓鎻掍欢鏃讹紝**瀵煎叆 `openapi.json`**
3. 淇敼鎻掍欢閰嶇疆涓殑 `servers[0].url` 涓轰綘鐨勫叕缃戝湴鍧€
4. 閰嶇疆 API Key 閴存潈锛圚eader: `X-API-Key`锛屽€硷細`ak-8Y5x8...`锛?5. 涓€涓彃浠跺寘鍚叏閮?涓伐鍏凤紝鏃犻渶鍒嗗埆鍒涘缓

## 鐜鍙橀噺

| 鍙橀噺 | 榛樿鍊?| 璇存槑 |
|------|--------|------|
| `BACKEND_MODE` | `mock` | `mock`=妯℃嫙鏁版嵁 / `real`=瀵规帴鐪熷疄鍚庣 |
| `SERVICE_HOST` | `http://localhost:8000` | 鏈嶅姟鍏綉鍦板潃 |
| `API_KEY` | 宸茬敓鎴?| 鎺ュ彛閴存潈瀵嗛挜 |
| `PORT` | `8000` | 鏈嶅姟绔彛 |
| `REAL_BACKEND_URL` | - | 鐪熷疄鍚庣API鍦板潃锛坮eal妯″紡蹇呭～锛?|

## 鍒囨崲鐪熷疄鍚庣

褰撲綘鐨勫姵鍔￠€氬悗绔?API 灏辩华鍚庯細

1. 璁剧疆鐜鍙橀噺锛?```
BACKEND_MODE=real
REAL_BACKEND_URL=https://浣犵殑鍔冲姟閫氬悗绔煙鍚?```

2. 閲嶅惎鏈嶅姟鍗冲彲銆俙/query_history` 鍜?`/submit_application` 浼氳嚜鍔ㄥ鎺ョ湡瀹?API

## 鏈湴娴嬭瘯绀轰緥

```bash
# 楠岃瘉琛ㄥ崟
curl -X POST http://localhost:8000/validate \
  -H "X-API-Key: ak-8Y5x8evzs6YO5CjvQSaMWHqhTL3vX9k2UYb2hQ85hA" \
  -H "Content-Type: application/json" \
  -d '{"form_data":"{\"projectName\":\"绂忕敯涓\",\"amount\":\"50000\",\"invoiceType\":\"鐢靛瓙涓撶エ\",\"proxyType\":\"1\"}"}'

# 娓叉煋琛ㄥ崟
curl -X POST http://localhost:8000/render \
  -H "X-API-Key: ak-8Y5x8evzs6YO5CjvQSaMWHqhTL3vX9k2UYb2hQ85hA" \
  -H "Content-Type: application/json" \
  -d '{"form_data":"{\"projectName\":\"绂忕敯涓\",\"amount\":\"50000\",\"invoiceType\":\"鐢靛瓙涓撶エ\",\"proxyType\":\"1\"}"}'

# 鏌ヨ鍘嗗彶
curl -X POST http://localhost:8000/query_history \
  -H "X-API-Key: ak-8Y5x8evzs6YO5CjvQSaMWHqhTL3vX9k2UYb2hQ85hA" \
  -H "Content-Type: application/json" \
  -d '{"project_name":"绂忕敯涓","time_range":"last_month"}'

# 鎻愪氦鐢宠
curl -X POST http://localhost:8000/submit_application \
  -H "X-API-Key: ak-8Y5x8evzs6YO5CjvQSaMWHqhTL3vX9k2UYb2hQ85hA" \
  -H "Content-Type: application/json" \
  -d '{"form_data":"{\"projectName\":\"绂忕敯涓\",\"amount\":\"50000\",\"invoiceType\":\"鐢靛瓙涓撶エ\",\"proxyType\":\"1\"}"}'
```
