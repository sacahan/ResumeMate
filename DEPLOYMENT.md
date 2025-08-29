# 🚀 ResumeMate 部署指南

本文檔提供三種安全的 GitHub Pages 部署方案，避免傳統分支切換的風險。

## ⚠️ 問題分析

原始的 `deploy_frontend.sh` 存在以下風險：

- 分支頻繁切換可能導致檔案遺失
- 工作區狀態混亂
- 難以追蹤部署版本
- 缺乏錯誤恢復機制

## 🎯 推薦方案

### 方案 1: GitHub Actions 自動部署 ⭐️ **推薦**

**優點：**

- 完全自動化，無需手動操作
- 不影響本地分支
- 支援版本控制和回滾
- 內建錯誤處理

**使用方式：**

```bash
# 只需推送到 main 分支
git add .
git commit -m "更新前端檔案"
git push origin main
# GitHub Actions 會自動部署到 Pages
```

**設定步驟：**

1. 檔案已創建：`.github/workflows/deploy-pages.yml`
2. 到 GitHub repo → Settings → Pages
3. 選擇 "GitHub Actions" 作為 Source
4. 推送任何前端更改到 main 分支即可觸發部署

---

### 方案 2: Git Subtree 安全部署

**優點：**

- 不切換分支，保持 main 分支穩定
- 使用 Git 官方功能
- 支援增量推送

**使用方式：**

```bash
./scripts/deploy_frontend_safe.sh
```

**腳本特色：**

- 檢查分支和工作區狀態
- 使用臨時提交，部署後自動清理
- 自動更新 iframe URL
- 詳細的錯誤提示

---

### 方案 3: 本地構建 + 手動/自動推送

**優點：**

- 最大靈活性
- 支援本地預覽
- 可自定義構建流程
- 支援多種推送方式

**使用方式：**

```bash
./scripts/build_and_deploy.sh
```

**功能特色：**

- 創建獨立的 build 目錄
- 自動更新生產環境配置
- 創建部署資訊檔案
- 支援 GitHub CLI 自動推送
- 支援手動上傳選項

## 📁 檔案結構

```
├── .github/workflows/
│   └── deploy-pages.yml          # GitHub Actions 工作流程
├── scripts/
│   ├── deploy_frontend_safe.sh   # Git subtree 安全部署
│   └── build_and_deploy.sh       # 本地構建腳本
└── src/frontend/
    ├── index.html                # 主頁面
    ├── static/js/main.js         # JavaScript 功能
    └── data/                     # JSON 資料檔案
        ├── resume-zh.json        # 中文履歷資料
        ├── resume-en.json        # 英文履歷資料
        └── version.json          # 版本資訊
```

## 🔧 使用建議

### 開發階段

- 使用 **方案 3** 進行本地構建和測試
- 運行 `build_and_deploy.sh` 檢查構建結果

### 生產部署

- 使用 **方案 1** 進行自動化部署
- 推送到 main 分支即可自動更新 GitHub Pages

### 緊急部署

- 使用 **方案 2** 進行手動安全部署
- 運行 `deploy_frontend_safe.sh` 快速推送

## 🛡️ 安全特性

所有方案都包含：

- ✅ 分支狀態檢查
- ✅ 工作區清潔驗證
- ✅ 自動 URL 更新
- ✅ 錯誤處理和恢復
- ✅ 臨時檔案清理
- ✅ 詳細日誌輸出

## 🌐 部署 URL

部署成功後，網站將在以下地址可用：

- **GitHub Pages**: `https://sacahan.github.io/ResumeMate`
- **自定義域名**: 可在 GitHub Pages 設定中配置

## 🔄 版本管理

- 所有 JSON 檔案支援版本控制
- 可透過更新 `version.json` 追蹤變更
- GitHub Actions 會記錄每次部署的提交 ID
