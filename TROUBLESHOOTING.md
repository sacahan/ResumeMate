# 🔧 ResumeMate 部署疑難排解

## ❌ 常見問題與解決方案

### 問題 1: GitHub Actions 部署失敗

```
HttpError: Not Found
Get Pages site failed. Please verify that the repository has Pages enabled
```

**原因：** GitHub Pages 未啟用或未設定為使用 GitHub Actions

**解決方案：**

#### 方法 1: 手動啟用 (推薦)

1. 前往 `https://github.com/your-username/ResumeMate/settings/pages`
2. **Source** 選擇 `GitHub Actions`
3. 點選 `Save`
4. 前往 Actions 頁面手動觸發 workflow

#### 方法 2: 檢查權限

確保 repository 設定中：

- Actions 權限啟用
- Pages 功能可用 (公開 repo 或 Pro 帳戶)

---

### 問題 2: 部署成功但網站顯示 404

**可能原因：**

- 檔案路徑不正確
- index.html 不在根目錄
- GitHub Pages 快取問題

**解決方案：**

#### 檢查部署內容

1. 前往 repository → Actions
2. 查看最新的部署 log
3. 確認檔案已正確複製

#### 清除快取

```bash
# 強制重新部署
git commit --allow-empty -m "trigger deployment"
git push origin main
```

---

### 問題 3: iframe 無法載入 HuggingFace Space

**可能原因：**

- HTTPS/HTTP 混合內容問題
- iframe URL 不正確
- CORS 政策限制

**解決方案：**

#### 檢查 URL 格式

確保 iframe src 使用正確格式：

```html
<iframe src="https://sacahan-resumemate-chat.hf.space"></iframe>
```

#### 檢查 HuggingFace Space 狀態

1. 直接訪問 `https://sacahan-resumemate-chat.hf.space`
2. 確認 Space 正常運行
3. 檢查是否需要認證

---

### 問題 4: JSON 資料無法載入

**可能原因：**

- 檔案路徑錯誤
- CORS 限制
- 檔案格式問題

**解決方案：**

#### 檢查檔案結構

```
├── index.html
├── static/js/main.js
└── data/
    ├── resume-zh.json
    ├── resume-en.json
    └── version.json
```

#### 修正路徑

JavaScript 中使用相對路徑：

```javascript
fetch("./data/resume-zh.json"); // ✅ 正確
fetch("/data/resume-zh.json"); // ❌ 可能錯誤
```

---

## 🛠️ 除錯工具與命令

### 本地測試部署

```bash
# 本地構建並檢視
./scripts/build_and_deploy.sh

# 啟動本地伺服器測試
cd build
python -m http.server 8000
```

### 檢查 GitHub Actions 狀態

```bash
# 使用 GitHub CLI
gh workflow list
gh run list --workflow="Deploy to GitHub Pages"
gh run view [RUN_ID] --log
```

### 強制重新部署

```bash
# 清空提交觸發重新部署
git commit --allow-empty -m "force redeploy"
git push origin main

# 或手動觸發
gh workflow run "Deploy to GitHub Pages"
```

---

## 🔍 除錯檢查清單

### GitHub Pages 設定

- [ ] Pages 功能已啟用
- [ ] Source 設為 "GitHub Actions"
- [ ] Repository 為公開或有 Pro 帳戶

### GitHub Actions 權限

- [ ] `pages: write` 權限
- [ ] `id-token: write` 權限
- [ ] `contents: read` 權限

### 檔案結構

- [ ] `index.html` 在部署根目錄
- [ ] `static/js/main.js` 路徑正確
- [ ] `data/*.json` 檔案存在

### 網路與 URL

- [ ] HuggingFace Space URL 正確
- [ ] 所有資源使用 HTTPS
- [ ] 沒有 CORS 錯誤

---

## 📞 進階除錯

### 查看 GitHub Pages 構建狀態

1. Repository → Settings → Pages
2. 查看最新部署狀態和錯誤訊息

### 檢查瀏覽器開發者工具

1. 開啟網站按 F12
2. 查看 Console 錯誤訊息
3. 檢查 Network 請求失敗

### 使用備用部署方案

如果 GitHub Actions 持續失敗：

```bash
# 使用 Git Subtree 部署
./scripts/deploy_frontend_safe.sh

# 或本地構建手動上傳
./scripts/build_and_deploy.sh
```

---

## 🆘 獲取協助

如果問題持續存在：

1. 查看 GitHub Actions 完整 log
2. 檢查 repository Issues
3. 確認 GitHub Pages 服務狀態
4. 聯繫技術支援或社群
