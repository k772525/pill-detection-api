#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GCP 字型安裝和管理腳本
支援多種字型來源和容錯機制
"""

import os
import sys
import requests
import logging
from pathlib import Path

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FontManager:
    """字型管理器"""
    
    def __init__(self, fonts_dir="fonts"):
        self.fonts_dir = Path(fonts_dir)
        self.fonts_dir.mkdir(exist_ok=True)
        
        # 字型下載配置
        self.font_configs = [
            {
                "name": "jf-openhuninn-2.1.ttf",
                "url": "https://github.com/justfont/open-huninn-font/releases/download/v2.1/jf-openhuninn-2.1.ttf",
                "description": "justfont 開源字型 (推薦)",
                "priority": 1
            },
            {
                "name": "NotoSansCJK-Regular.ttc", 
                "url": "https://github.com/googlefonts/noto-cjk/releases/download/Sans2.004/NotoSansCJK-Regular.ttc",
                "description": "Google Noto Sans CJK",
                "priority": 2
            },
            {
                "name": "SourceHanSansCN-Regular.otf",
                "url": "https://github.com/adobe-fonts/source-han-sans/releases/download/2.004R/SourceHanSansCN.zip",
                "description": "Adobe Source Han Sans (需解壓)",
                "priority": 3,
                "is_zip": True
            }
        ]
    
    def download_font(self, config):
        """下載單個字型檔案"""
        font_path = self.fonts_dir / config["name"]
        
        if font_path.exists():
            logger.info(f"✅ 字型已存在: {font_path}")
            return True
            
        try:
            logger.info(f"📥 下載 {config['description']}...")
            logger.info(f"🔗 URL: {config['url']}")
            
            response = requests.get(config["url"], stream=True, timeout=30)
            response.raise_for_status()
            
            # 檢查檔案大小
            total_size = int(response.headers.get('content-length', 0))
            logger.info(f"📊 檔案大小: {total_size / 1024 / 1024:.1f} MB")
            
            with open(font_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\r⏳ 下載進度: {progress:.1f}%", end="", flush=True)
            
            print()  # 換行
            logger.info(f"✅ 下載完成: {font_path}")
            logger.info(f"📁 檔案大小: {font_path.stat().st_size / 1024 / 1024:.1f} MB")
            return True
            
        except Exception as e:
            logger.error(f"❌ 下載失敗 {config['name']}: {str(e)}")
            if font_path.exists():
                font_path.unlink()  # 刪除不完整的檔案
            return False
    
    def create_fallback_links(self):
        """創建字型的備用連結"""
        target_font = self.fonts_dir / "jf-openhuninn-2.1.ttf"
        
        if target_font.exists():
            logger.info("✅ 主要字型檔案已存在")
            return True
        
        # 尋找可用的備用字型
        for config in sorted(self.font_configs, key=lambda x: x["priority"]):
            font_path = self.fonts_dir / config["name"]
            if font_path.exists():
                try:
                    # 創建符號連結
                    target_font.symlink_to(font_path.name)
                    logger.info(f"🔗 創建字型連結: {target_font} -> {font_path}")
                    return True
                except Exception as e:
                    logger.warning(f"⚠️ 無法創建連結: {str(e)}")
        
        return False
    
    def install_system_fonts(self):
        """安裝系統字型 (適用於 Debian/Ubuntu)"""
        try:
            import subprocess
            logger.info("📦 安裝系統中文字型...")
            
            # 更新套件列表並安裝字型
            commands = [
                ["apt-get", "update"],
                ["apt-get", "install", "-y", "fonts-noto-cjk", "fonts-wqy-zenhei", "fonts-wqy-microhei"]
            ]
            
            for cmd in commands:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"⚠️ 命令執行失敗: {' '.join(cmd)}")
                    logger.warning(f"錯誤: {result.stderr}")
                else:
                    logger.info(f"✅ 執行成功: {' '.join(cmd)}")
            
            # 更新字型快取
            subprocess.run(["fc-cache", "-fv"], capture_output=True)
            logger.info("✅ 系統字型安裝完成")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ 系統字型安裝失敗: {str(e)}")
            return False
    
    def verify_fonts(self):
        """驗證字型安裝"""
        logger.info("🔍 驗證字型安裝...")
        
        # 檢查目標字型
        target_font = self.fonts_dir / "jf-openhuninn-2.1.ttf"
        if target_font.exists():
            logger.info(f"✅ 主要字型: {target_font}")
            
            # 測試字型載入
            try:
                from PIL import ImageFont
                font = ImageFont.truetype(str(target_font), 24)
                logger.info("✅ 字型載入測試成功")
                return True
            except Exception as e:
                logger.error(f"❌ 字型載入測試失敗: {str(e)}")
                return False
        else:
            logger.error("❌ 主要字型檔案不存在")
            return False
    
    def install_all(self):
        """執行完整的字型安裝流程"""
        logger.info("🚀 開始字型安裝流程...")
        
        # 1. 嘗試安裝系統字型
        self.install_system_fonts()
        
        # 2. 下載自定義字型
        success_count = 0
        for config in self.font_configs:
            if self.download_font(config):
                success_count += 1
        
        logger.info(f"📊 成功下載 {success_count}/{len(self.font_configs)} 個字型")
        
        # 3. 創建備用連結
        if not self.create_fallback_links():
            logger.warning("⚠️ 無法創建主要字型連結")
        
        # 4. 驗證安裝
        if self.verify_fonts():
            logger.info("🎉 字型安裝完成並驗證成功！")
            return True
        else:
            logger.error("❌ 字型安裝驗證失敗")
            return False
    
    def list_available_fonts(self):
        """列出可用的字型"""
        logger.info("📋 可用字型列表:")
        for font_file in self.fonts_dir.glob("*.ttf"):
            size_mb = font_file.stat().st_size / 1024 / 1024
            logger.info(f"  📄 {font_file.name} ({size_mb:.1f} MB)")
        
        for font_file in self.fonts_dir.glob("*.ttc"):
            size_mb = font_file.stat().st_size / 1024 / 1024
            logger.info(f"  📄 {font_file.name} ({size_mb:.1f} MB)")

def main():
    """主函數"""
    print("🔤 GCP 中文字型安裝工具")
    print("=" * 50)
    
    font_manager = FontManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "list":
            font_manager.list_available_fonts()
        elif command == "verify":
            font_manager.verify_fonts()
        elif command == "install":
            font_manager.install_all()
        else:
            print("用法: python setup_fonts_gcp.py [install|list|verify]")
    else:
        # 預設執行安裝
        font_manager.install_all()

if __name__ == "__main__":
    main()