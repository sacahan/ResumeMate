"""Gradio-based admin interface for managing infographics.

Usage:
    python -m src.backend.infographics.admin_app

Environment variables:
    INFOGRAPHICS_ADMIN_USER: Admin username (default: admin)
    INFOGRAPHICS_ADMIN_PASS: Admin password (default: changeme)
    INFOGRAPHICS_ADMIN_HOST: Server host (default: 0.0.0.0)
    INFOGRAPHICS_ADMIN_PORT: Server port (default: 7861)
    INFOGRAPHICS_ADMIN_SHARE: Enable Gradio share (default: false)
"""

import logging
import os
import sys
import asyncio
import json
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

# ruff: noqa: E402
# Note: These imports must be after load_dotenv() to ensure environment variables are loaded
import gradio as gr

from src.backend.infographics import (
    GitManager,
    ImageProcessor,
    InfographicItem,
    InfographicsDataManager,
    InfographicAssistantAgent,
    ThumbnailConfig,
)
from src.backend.infographics.project_manager import ProjectDataManager
from src.backend.infographics.language_manager import LanguageDataManager
from src.backend.infographics.models import ProjectItem
from src.backend.logging_config import configure_logging

# Configure logging using project standard
configure_logging(
    console_level=os.getenv("LOG_CONSOLE_LEVEL", "INFO"),
    file_level=os.getenv("LOG_FILE_LEVEL", "DEBUG"),
    log_file=os.getenv("LOG_FILE"),
)
logger = logging.getLogger(__name__)

# Configuration
BASE_DIR = Path(__file__).parent.parent.parent.parent
IMAGES_DIR = BASE_DIR / "src" / "frontend" / "static" / "images" / "infographics"
DATA_FILE = BASE_DIR / "src" / "frontend" / "data" / "infographics.json"

# Admin credentials from environment
ADMIN_USER = os.getenv("INFOGRAPHICS_ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("INFOGRAPHICS_ADMIN_PASS", "changeme")

# Admin server settings from environment
ADMIN_HOST = os.getenv("INFOGRAPHICS_ADMIN_HOST", "0.0.0.0")
ADMIN_PORT = int(os.getenv("INFOGRAPHICS_ADMIN_PORT", "7861"))
ADMIN_SHARE = os.getenv("INFOGRAPHICS_ADMIN_SHARE", "false").lower() == "true"

# Initialize managers
data_manager = InfographicsDataManager(DATA_FILE)
image_processor = ImageProcessor(
    images_dir=IMAGES_DIR,
    config=ThumbnailConfig(max_width=400, max_height=300, quality=85, format="WEBP"),
)
git_manager = GitManager(repo_path=BASE_DIR)
project_manager = ProjectDataManager(git_manager=git_manager)
language_manager = LanguageDataManager(git_manager=git_manager)


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


def ai_assist_metadata(title_zh: str) -> tuple[str, str]:
    """Get AI suggestions for English title and tags.

    Args:
        title_zh: Chinese title to process

    Returns:
        Tuple of (suggested_title_en, suggested_tags_str)
    """
    if not title_zh or not title_zh.strip():
        return "", ""

    try:
        existing_tags = data_manager.get_all_tags()
        agent = InfographicAssistantAgent(existing_tags=existing_tags)

        # Run async function in sync context
        result = asyncio.run(agent.suggest_metadata(title_zh.strip()))

        if result:
            title_en = result.title_en
            tags_str = ", ".join(result.suggested_tags)
            logger.info(
                f"AI assistance success for '{title_zh}': "
                f"en='{title_en}', tags='{tags_str}'"
            )
            return title_en, tags_str
        else:
            logger.warning(f"AI assistance returned None for '{title_zh}'")
            return "", ""

    except Exception as e:
        logger.error(f"AI assistance failed for '{title_zh}': {str(e)}")
        return "", ""


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
            status_msg = f"✅ 圖片上傳成功！ID: {item.id}"

            # Git commit and push
            files_to_commit = [
                git_manager.get_relative_path(DATA_FILE),
                git_manager.get_relative_path(IMAGES_DIR / Path(item.url).name),
                git_manager.get_relative_path(
                    IMAGES_DIR / "thumbnails" / Path(item.thumbnail).name
                ),
            ]
            git_success, git_msg = git_manager.commit_changes(
                files=files_to_commit,
                action="新增圖片",
                item_id=item.id,
                title=item.title_zh or item.title_en,
            )
            if git_manager.auto_commit:
                status_msg += f"\n📝 Git: {git_msg}"

            return status_msg, get_gallery_data()
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
            status_msg = f"✅ 更新成功！ID: {item_id}"

            # Git commit and push
            files_to_commit = [git_manager.get_relative_path(DATA_FILE)]
            git_success, git_msg = git_manager.commit_changes(
                files=files_to_commit,
                action="更新圖片",
                item_id=item_id,
                title=title_zh or title_en,
            )
            if git_manager.auto_commit:
                status_msg += f"\n📝 Git: {git_msg}"

            return status_msg, get_gallery_data()
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
        # Get file paths before deletion for git commit
        image_path = git_manager.get_relative_path(IMAGES_DIR / Path(item.url).name)
        thumbnail_path = git_manager.get_relative_path(
            IMAGES_DIR / "thumbnails" / Path(item.thumbnail).name
        )
        item_title = item.title_zh or item.title_en

        # Delete files
        image_processor.delete_image(item)

        # Delete from data
        if data_manager.delete_item(item_id):
            status_msg = f"✅ 刪除成功！ID: {item_id}"

            # Git commit and push
            files_to_commit = [
                git_manager.get_relative_path(DATA_FILE),
                image_path,
                thumbnail_path,
            ]
            git_success, git_msg = git_manager.commit_changes(
                files=files_to_commit,
                action="刪除圖片",
                item_id=item_id,
                title=item_title,
            )
            if git_manager.auto_commit:
                status_msg += f"\n📝 Git: {git_msg}"

            return status_msg, get_gallery_data()
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


def clear_upload_fields(image_file) -> tuple[str, str, str, str]:
    """Clear upload fields when image is cleared.

    Args:
        image_file: The uploaded image file (None when cleared)

    Returns:
        Tuple of empty strings for all upload fields
    """
    if image_file is None:
        return "", "", "", ""
    return gr.skip(), gr.skip(), gr.skip(), gr.skip()


# ============================================================================
# Project Management Functions
# ============================================================================


def get_projects_gallery() -> list[tuple[str, str]]:
    """Get projects for gallery display."""
    projects = project_manager.get_all_items()
    result = []
    for proj in projects:
        # Cover path is relative to frontend directory (e.g., "static/images/projects/cover.png")
        cover_path = BASE_DIR / "src" / "frontend" / proj.cover
        if cover_path.exists():
            caption = f"{proj.title_zh}\nID: {proj.id}"
            result.append((str(cover_path), caption))
        else:
            # If cover doesn't exist, log warning but continue
            logger.warning(f"Cover image not found for project {proj.id}: {cover_path}")
    return result


def get_project_details(project_id: str) -> tuple[str, str, str, str, str, str, str]:
    """Get project details by ID."""
    if not project_id:
        return "", "", "", "", "", "", ""

    proj = project_manager.get_item_by_id(project_id)
    if not proj:
        return "", "", "", "", "", "", ""

    return (
        proj.title_zh,
        proj.title_en,
        proj.desc_zh,
        proj.desc_en,
        ", ".join(proj.tags),
        proj.demoUrl,
        proj.githubUrl,
    )


def on_project_gallery_select(evt: gr.SelectData) -> str:
    """Handle project gallery selection."""
    if evt.value and "caption" in evt.value:
        caption = evt.value["caption"]
        if "ID:" in caption:
            project_id = caption.split("ID:")[-1].strip()
            return project_id
    return ""


def save_project(
    project_id: str,
    title_zh: str,
    title_en: str,
    desc_zh: str,
    desc_en: str,
    tags_str: str,
    demo_url: str,
    github_url: str,
    cover_image,
) -> tuple[str, list]:
    """Save or update a project."""
    try:
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]

        if not title_zh or not title_en:
            return "❌ 中文和英文標題為必填項目", get_projects_gallery()

        if project_id:
            # Update existing project
            project_manager.update_item(
                project_id,
                title_zh=title_zh,
                title_en=title_en,
                desc_zh=desc_zh,
                desc_en=desc_en,
                tags=tags,
                demoUrl=demo_url,
                githubUrl=github_url,
            )
            status_msg = "✅ 專案已更新！"
        else:
            # Create new project
            new_id = title_zh.replace(" ", "_").lower()
            cover_path = f"static/images/projects/{new_id}_cover.jpg"

            new_project = ProjectItem(
                id=new_id,
                title_zh=title_zh,
                title_en=title_en,
                desc_zh=desc_zh,
                desc_en=desc_en,
                tags=tags,
                cover=cover_path,
                demoUrl=demo_url,
                githubUrl=github_url,
            )
            project_manager.add_item(new_project)
            status_msg = f"✅ 新專案已新增！ID: {new_id}"

        return status_msg, get_projects_gallery()
    except Exception as e:
        logger.error(f"Save project failed: {e}")
        return f"❌ 儲存失敗: {str(e)}", get_projects_gallery()


def delete_project(project_id: str) -> tuple[str, list]:
    """Delete a project."""
    if not project_id:
        return "❌ 請選擇專案", get_projects_gallery()

    try:
        if project_manager.delete_item(project_id):
            return "✅ 專案已刪除", get_projects_gallery()
        else:
            return "❌ 專案不存在", get_projects_gallery()
    except Exception as e:
        logger.error(f"Delete project failed: {e}")
        return f"❌ 刪除失敗: {str(e)}", get_projects_gallery()


def clear_project_fields() -> tuple[str, str, str, str, str, str, str, str]:
    """Clear project form fields."""
    return "", "", "", "", "", "", "", ""


# ============================================================================
# Language Management Functions
# ============================================================================


def get_language_blocks() -> list[str]:
    """Get all language blocks."""
    return language_manager.get_block_keys()


def get_language_block_content(block_key: str, language: str) -> str:
    """Get content of a language block."""
    if not block_key:
        return ""

    block_data = language_manager.get_block(block_key, language)
    if block_data is None:
        return ""

    return json.dumps(block_data, ensure_ascii=False, indent=2)


def save_language_block(block_key: str, zh_content: str, en_content: str) -> str:
    """Save language block content."""
    try:
        if not block_key:
            return "❌ 請選擇語言區塊"

        # Parse zh-TW content
        try:
            zh_data = json.loads(zh_content) if zh_content else {}
        except json.JSONDecodeError as e:
            return f"❌ 中文內容格式錯誤: {str(e)}"

        # Parse en content
        try:
            en_data = json.loads(en_content) if en_content else {}
        except json.JSONDecodeError as e:
            return f"❌ 英文內容格式錯誤: {str(e)}"

        # Update blocks
        language_manager.update_block(
            block_key, zh_data, language="zh-TW", auto_sync=True
        )
        language_manager.update_block(block_key, en_data, language="en")

        return f"✅ 語言區塊已保存: {block_key}"
    except Exception as e:
        logger.error(f"Save language block failed: {e}")
        return f"❌ 儲存失敗: {str(e)}"


def create_admin_interface():
    """Create the Gradio admin interface."""

    custom_css = """
    .gradio-container {
        max-width: 1200px !important;
    }
    .gallery-item {
        cursor: pointer;
    }
    .gallery-container {
        max-height: 700px !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 8px;
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
                        ai_assist_btn = gr.Button("🤖 AI 輔助", variant="secondary")
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
                            rows=2,
                            height="700px",
                            object_fit="contain",
                            allow_preview=True,
                            elem_classes="gallery-container",
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

            # Projects Tab
            with gr.Tab("🎨 專案管理"):
                with gr.Row():
                    with gr.Column(scale=2):
                        projects_gallery = gr.Gallery(
                            label="專案列表（點擊選擇）",
                            value=get_projects_gallery,
                            columns=3,
                            rows=2,
                            height="600px",
                            object_fit="contain",
                            allow_preview=True,
                        )

                    with gr.Column(scale=1):
                        project_id = gr.Textbox(
                            label="專案 ID",
                            placeholder="自動生成或選擇現有專案",
                            interactive=False,
                        )
                        project_title_zh = gr.Textbox(
                            label="中文標題*", placeholder="輸入中文標題"
                        )
                        project_title_en = gr.Textbox(
                            label="英文標題*", placeholder="Enter title"
                        )
                        project_desc_zh = gr.TextArea(label="中文描述", lines=3)
                        project_desc_en = gr.TextArea(
                            label="English Description", lines=3
                        )
                        project_tags = gr.Textbox(
                            label="標籤（逗號分隔）",
                            placeholder="React, Python, AI",
                        )
                        project_demo_url = gr.Textbox(
                            label="演示 URL", placeholder="https://..."
                        )
                        project_github_url = gr.Textbox(
                            label="GitHub URL", placeholder="https://..."
                        )

                        with gr.Row():
                            project_load_btn = gr.Button("載入詳情")
                            project_save_btn = gr.Button("儲存", variant="primary")
                            project_delete_btn = gr.Button("刪除", variant="stop")
                            project_new_btn = gr.Button("新增", variant="secondary")

                        project_status = gr.Textbox(label="狀態", interactive=False)

            # Languages Tab
            with gr.Tab("🌐 多語言管理"):
                with gr.Row():
                    block_selector = gr.Dropdown(
                        label="語言區塊",
                        choices=get_language_blocks(),
                        interactive=True,
                    )
                    load_block_btn = gr.Button("載入內容")

                with gr.Row():
                    with gr.Column():
                        zh_tw_editor = gr.TextArea(
                            label="中文 (繁體)",
                            lines=15,
                            placeholder="JSON 格式內容",
                            max_lines=30,
                        )

                    with gr.Column():
                        en_editor = gr.TextArea(
                            label="English",
                            lines=15,
                            placeholder="JSON format content",
                            max_lines=30,
                        )

                with gr.Row():
                    lang_save_btn = gr.Button("保存並同步", variant="primary")
                    lang_status = gr.Textbox(label="狀態", interactive=False)

                gr.Markdown(
                    "💡 **提示**: 編輯中文內容時，結構變更會自動同步到英文版本"
                )

        # Event handlers
        ai_assist_btn.click(
            fn=ai_assist_metadata,
            inputs=upload_title_zh,
            outputs=[upload_title_en, upload_tags],
        )

        upload_image_input.change(
            fn=clear_upload_fields,
            inputs=upload_image_input,
            outputs=[upload_title_zh, upload_title_en, upload_tags, upload_source],
        )

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

        # Project management events
        projects_gallery.select(fn=on_project_gallery_select, outputs=project_id)

        project_load_btn.click(
            fn=get_project_details,
            inputs=project_id,
            outputs=[
                project_title_zh,
                project_title_en,
                project_desc_zh,
                project_desc_en,
                project_tags,
                project_demo_url,
                project_github_url,
            ],
        )

        project_save_btn.click(
            fn=save_project,
            inputs=[
                project_id,
                project_title_zh,
                project_title_en,
                project_desc_zh,
                project_desc_en,
                project_tags,
                project_demo_url,
                project_github_url,
                gr.State(None),  # cover_image - placeholder
            ],
            outputs=[project_status, projects_gallery],
        )

        project_delete_btn.click(
            fn=delete_project,
            inputs=project_id,
            outputs=[project_status, projects_gallery],
        )

        project_new_btn.click(
            fn=clear_project_fields,
            outputs=[
                project_id,
                project_title_zh,
                project_title_en,
                project_desc_zh,
                project_desc_en,
                project_tags,
                project_demo_url,
                project_github_url,
            ],
        )

        # Language management events
        load_block_btn.click(
            fn=lambda block: (
                get_language_block_content(block, "zh-TW"),
                get_language_block_content(block, "en"),
            ),
            inputs=block_selector,
            outputs=[zh_tw_editor, en_editor],
        )

        lang_save_btn.click(
            fn=save_language_block,
            inputs=[block_selector, zh_tw_editor, en_editor],
            outputs=lang_status,
        )

    return app


def main():
    """Main entry point for the admin interface."""
    logger.info("Starting Infographics Admin Interface")
    logger.info(f"Server: http://{ADMIN_HOST}:{ADMIN_PORT}")
    logger.info(f"Share mode: {ADMIN_SHARE}")
    logger.info(f"Images directory: {IMAGES_DIR}")
    logger.info(f"Data file: {DATA_FILE}")

    # Log Git auto-commit status and SSH configuration
    logger.info("\n" + git_manager.get_status_report())

    app = create_admin_interface()

    # Launch with authentication
    app.launch(
        server_name=ADMIN_HOST,
        server_port=ADMIN_PORT,
        share=ADMIN_SHARE,
        auth=(ADMIN_USER, ADMIN_PASS),
        auth_message="請輸入管理員帳號密碼",
    )


if __name__ == "__main__":
    main()
