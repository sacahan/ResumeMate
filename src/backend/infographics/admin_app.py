"""Gradio-based admin interface for managing infographics.

Usage:
    python -m src.backend.infographics.admin_app

Or with custom credentials:
    INFOGRAPHICS_ADMIN_USER=admin INFOGRAPHICS_ADMIN_PASS=secret python -m src.backend.infographics.admin_app
"""

import logging
import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import gradio as gr

from src.backend.infographics import (
    ImageProcessor,
    InfographicItem,
    InfographicsDataManager,
    ThumbnailConfig,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BASE_DIR = Path(__file__).parent.parent.parent.parent
IMAGES_DIR = BASE_DIR / "src" / "frontend" / "static" / "images" / "infographics"
DATA_FILE = BASE_DIR / "src" / "frontend" / "data" / "infographics.json"

# Admin credentials from environment
ADMIN_USER = os.getenv("INFOGRAPHICS_ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("INFOGRAPHICS_ADMIN_PASS", "changeme")

# Initialize managers
data_manager = InfographicsDataManager(DATA_FILE)
image_processor = ImageProcessor(
    images_dir=IMAGES_DIR,
    config=ThumbnailConfig(max_width=400, max_height=300, quality=85, format="WEBP"),
)


def get_gallery_data() -> list[tuple[str, str]]:
    """Get data for gallery display: list of (image_path, caption)."""
    data = data_manager.load()
    result = []
    for img in data.images:
        # Construct full path for Gradio
        img_path = IMAGES_DIR / Path(img.url).name
        if img_path.exists():
            caption = f"{img.title_zh or img.title_en or 'Untitled'}\nID: {img.id}"
            result.append((str(img_path), caption))
    return result


def get_tags_list() -> str:
    """Get comma-separated list of all tags."""
    tags = data_manager.get_all_tags()
    return ", ".join(tags)


def get_item_details(item_id: str) -> tuple[str, str, str, str, str]:
    """Get details of an item by ID."""
    if not item_id:
        return "", "", "", "", ""

    item = data_manager.get_item(item_id)
    if not item:
        return "", "", "", "", ""

    return (
        item.title_zh,
        item.title_en,
        ", ".join(item.tags),
        item.source,
        item.id,
    )


def upload_image(
    image_file,
    title_zh: str,
    title_en: str,
    tags_str: str,
    source: str,
) -> tuple[str, list]:
    """Handle image upload."""
    if image_file is None:
        return "❌ 請選擇圖片檔案", get_gallery_data()

    try:
        # Parse tags
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]

        # Process the uploaded image
        item = image_processor.process_uploaded_image(
            source_path=image_file,
            title_zh=title_zh.strip(),
            title_en=title_en.strip(),
            tags=tags,
            source=source.strip(),
        )

        # Save to data file
        if data_manager.add_item(item):
            return f"✅ 圖片上傳成功！ID: {item.id}", get_gallery_data()
        else:
            return "❌ 儲存資料失敗", get_gallery_data()

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return f"❌ 上傳失敗: {str(e)}", get_gallery_data()


def update_item(
    item_id: str,
    title_zh: str,
    title_en: str,
    tags_str: str,
    source: str,
) -> tuple[str, list]:
    """Update an existing item."""
    if not item_id:
        return "❌ 請輸入項目 ID", get_gallery_data()

    item = data_manager.get_item(item_id)
    if not item:
        return f"❌ 找不到 ID: {item_id}", get_gallery_data()

    try:
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]

        updated_item = InfographicItem(
            id=item.id,
            url=item.url,
            thumbnail=item.thumbnail,
            title=title_zh or title_en,
            title_zh=title_zh.strip(),
            title_en=title_en.strip(),
            tags=tags,
            source=source.strip(),
            created_at=item.created_at,
        )

        if data_manager.update_item(updated_item):
            return f"✅ 更新成功！ID: {item_id}", get_gallery_data()
        else:
            return "❌ 更新失敗", get_gallery_data()

    except Exception as e:
        logger.error(f"Update failed: {e}")
        return f"❌ 更新失敗: {str(e)}", get_gallery_data()


def delete_item(item_id: str) -> tuple[str, list]:
    """Delete an item by ID."""
    if not item_id:
        return "❌ 請輸入項目 ID", get_gallery_data()

    item = data_manager.get_item(item_id)
    if not item:
        return f"❌ 找不到 ID: {item_id}", get_gallery_data()

    try:
        # Delete files
        image_processor.delete_image(item)

        # Delete from data
        if data_manager.delete_item(item_id):
            return f"✅ 刪除成功！ID: {item_id}", get_gallery_data()
        else:
            return "❌ 刪除失敗", get_gallery_data()

    except Exception as e:
        logger.error(f"Delete failed: {e}")
        return f"❌ 刪除失敗: {str(e)}", get_gallery_data()


def on_gallery_select(evt: gr.SelectData) -> str:
    """Handle gallery item selection to get item ID."""
    if evt.value and "caption" in evt.value:
        caption = evt.value["caption"]
        # Extract ID from caption
        if "ID:" in caption:
            item_id = caption.split("ID:")[-1].strip()
            return item_id
    return ""


def create_admin_interface():
    """Create the Gradio admin interface."""

    custom_css = """
    .gradio-container {
        max-width: 1200px !important;
    }
    .gallery-item {
        cursor: pointer;
    }
    """

    with gr.Blocks(
        title="Infographics Admin",
        css=custom_css,
        theme=gr.themes.Soft(primary_hue="orange"),
    ) as app:
        gr.Markdown("# 📊 圖表管理後台")
        gr.Markdown("管理 infographics.html 頁面顯示的圖表內容")

        with gr.Tabs():
            # Upload Tab
            with gr.Tab("📤 上傳圖片"):
                with gr.Row():
                    with gr.Column(scale=1):
                        upload_image_input = gr.Image(
                            label="選擇圖片",
                            type="filepath",
                            height=300,
                        )
                        upload_title_zh = gr.Textbox(
                            label="中文標題",
                            placeholder="輸入中文標題",
                        )
                        upload_title_en = gr.Textbox(
                            label="英文標題",
                            placeholder="Enter English title",
                        )
                        upload_tags = gr.Textbox(
                            label="標籤（逗號分隔）",
                            placeholder="AI, Data, Visualization",
                        )
                        upload_source = gr.Textbox(
                            label="來源",
                            placeholder="圖片來源或出處",
                        )
                        upload_btn = gr.Button("上傳", variant="primary")

                    with gr.Column(scale=1):
                        upload_status = gr.Textbox(
                            label="狀態",
                            interactive=False,
                        )
                        existing_tags = gr.Textbox(
                            label="現有標籤",
                            value=get_tags_list,
                            interactive=False,
                        )

            # Manage Tab
            with gr.Tab("📝 管理圖片"):
                with gr.Row():
                    with gr.Column(scale=2):
                        gallery = gr.Gallery(
                            label="圖片列表（點擊選擇）",
                            value=get_gallery_data,
                            columns=3,
                            height=400,
                            object_fit="contain",
                            allow_preview=True,
                        )

                    with gr.Column(scale=1):
                        selected_id = gr.Textbox(
                            label="選擇的項目 ID",
                            placeholder="從圖片列表選擇或手動輸入",
                        )
                        load_btn = gr.Button("載入詳情")

                        edit_title_zh = gr.Textbox(label="中文標題")
                        edit_title_en = gr.Textbox(label="英文標題")
                        edit_tags = gr.Textbox(label="標籤（逗號分隔）")
                        edit_source = gr.Textbox(label="來源")

                        with gr.Row():
                            update_btn = gr.Button("更新", variant="primary")
                            delete_btn = gr.Button("刪除", variant="stop")

                        manage_status = gr.Textbox(
                            label="狀態",
                            interactive=False,
                        )

            # Stats Tab
            with gr.Tab("📈 統計"):
                with gr.Row():
                    stats_display = gr.Markdown()

                refresh_stats_btn = gr.Button("刷新統計")

                def get_stats():
                    data = data_manager.load()
                    tags = data_manager.get_all_tags()
                    return f"""
### 總覽
- **圖片總數**: {len(data.images)}
- **標籤總數**: {len(tags)}
- **最後更新**: {data.lastUpdated}

### 標籤分布
{chr(10).join([f'- **{tag}**: {len(data_manager.get_items_by_tag(tag))} 張' for tag in tags[:15]])}
"""

                refresh_stats_btn.click(fn=get_stats, outputs=stats_display)
                app.load(fn=get_stats, outputs=stats_display)

        # Event handlers
        upload_btn.click(
            fn=upload_image,
            inputs=[
                upload_image_input,
                upload_title_zh,
                upload_title_en,
                upload_tags,
                upload_source,
            ],
            outputs=[upload_status, gallery],
        ).then(fn=get_tags_list, outputs=existing_tags)

        gallery.select(fn=on_gallery_select, outputs=selected_id)

        load_btn.click(
            fn=get_item_details,
            inputs=selected_id,
            outputs=[
                edit_title_zh,
                edit_title_en,
                edit_tags,
                edit_source,
                selected_id,
            ],
        )

        update_btn.click(
            fn=update_item,
            inputs=[
                selected_id,
                edit_title_zh,
                edit_title_en,
                edit_tags,
                edit_source,
            ],
            outputs=[manage_status, gallery],
        )

        delete_btn.click(
            fn=delete_item,
            inputs=selected_id,
            outputs=[manage_status, gallery],
        )

    return app


def main():
    """Main entry point for the admin interface."""
    logger.info("Starting Infographics Admin Interface")
    logger.info(f"Images directory: {IMAGES_DIR}")
    logger.info(f"Data file: {DATA_FILE}")

    app = create_admin_interface()

    # Launch with authentication
    app.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=False,
        auth=(ADMIN_USER, ADMIN_PASS),
        auth_message="請輸入管理員帳號密碼",
    )


if __name__ == "__main__":
    main()
