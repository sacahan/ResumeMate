"""Git operations manager for CMS admin.

This module provides Git integration for the CMS admin interface,
enabling automatic commit and push of changes to trigger GitHub Pages deployment.

Usage:
    from src.backend.cms.git_manager import GitManager

    git_manager = GitManager()
    git_manager.check_ssh_config()  # Check SSH setup on startup
    git_manager.commit_changes(files, action="新增圖片", item_id="img_xxx")

Environment variables:
    CMS_GIT_AUTO_COMMIT: Enable auto commit (default: false)
    CMS_GIT_AUTO_PUSH: Enable auto push (default: false)
    CMS_GIT_COMMIT_PREFIX: Commit message prefix (default: [cms])
"""

import logging
import os
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class GitManager:
    """Manage Git operations for infographics changes.

    This class handles Git add, commit, and push operations for infographic
    file changes. It uses SSH authentication and skips pre-commit hooks
    with --no-verify flag.

    Attributes:
        repo_path: Path to the Git repository root.
        auto_commit: Whether to automatically commit changes.
        auto_push: Whether to automatically push after commit.
        commit_prefix: Prefix for commit messages.
    """

    def __init__(self, repo_path: Optional[Path] = None):
        """Initialize GitManager.

        Args:
            repo_path: Path to repository root. Defaults to project root.
        """
        self.repo_path = repo_path or Path(__file__).parent.parent.parent.parent
        self.auto_commit = os.getenv("CMS_GIT_AUTO_COMMIT", "false").lower() == "true"
        self.auto_push = os.getenv("CMS_GIT_AUTO_PUSH", "false").lower() == "true"
        self.commit_prefix = os.getenv("CMS_GIT_COMMIT_PREFIX", "[cms]")

    def _run_git_command(self, *args: str, timeout: int = 30) -> tuple[bool, str]:
        """Execute a git command and return success status and output.

        Args:
            *args: Git command arguments (without git prefix).
            timeout: Command timeout in seconds.

        Returns:
            Tuple of (success: bool, output: str).
        """
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output = result.stdout.strip()
            if result.stderr:
                output += "\n" + result.stderr.strip()
            return result.returncode == 0, output.strip()
        except subprocess.TimeoutExpired:
            return False, "Git command timed out"
        except FileNotFoundError:
            return False, "Git is not installed or not in PATH"
        except Exception as e:
            return False, f"Git command failed: {str(e)}"

    def check_ssh_config(self) -> dict[str, dict]:
        """Check SSH configuration for Git operations.

        Performs three checks:
        1. SSH key existence in ~/.ssh/
        2. Remote URL uses SSH format (git@github.com:...)
        3. SSH connection test to GitHub

        Returns:
            Dictionary with check results, each containing:
            - ok: bool - Whether the check passed
            - message: str - Status message
        """
        results = {
            "ssh_key": {"ok": False, "message": ""},
            "remote_url": {"ok": False, "message": ""},
            "ssh_connection": {"ok": False, "message": ""},
        }

        # Check 1: SSH key existence
        ssh_dir = Path.home() / ".ssh"
        ssh_keys = list(ssh_dir.glob("id_*")) if ssh_dir.exists() else []
        # Filter out .pub files to find private keys
        private_keys = [k for k in ssh_keys if not k.suffix == ".pub"]

        if private_keys:
            key_names = [k.name for k in private_keys]
            results["ssh_key"] = {
                "ok": True,
                "message": f"找到 SSH key: {', '.join(key_names)}",
            }
        else:
            results["ssh_key"] = {
                "ok": False,
                "message": "未找到 SSH key，請執行 ssh-keygen -t ed25519 -C 'your_email@example.com'",
            }

        # Check 2: Remote URL format
        success, remote_url = self._run_git_command("remote", "get-url", "origin")
        if success:
            if remote_url.startswith("git@") or remote_url.startswith("ssh://"):
                results["remote_url"] = {
                    "ok": True,
                    "message": f"Remote 使用 SSH URL: {remote_url}",
                }
            else:
                results["remote_url"] = {
                    "ok": False,
                    "message": f"Remote 使用 HTTPS URL: {remote_url}，建議改為 SSH URL",
                }
        else:
            results["remote_url"] = {
                "ok": False,
                "message": f"無法取得 remote URL: {remote_url}",
            }

        # Check 3: SSH connection test
        try:
            result = subprocess.run(
                ["ssh", "-T", "git@github.com"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            # GitHub returns exit code 1 with success message
            output = result.stdout + result.stderr
            if "successfully authenticated" in output.lower():
                results["ssh_connection"] = {
                    "ok": True,
                    "message": "SSH 連線測試成功",
                }
            elif result.returncode == 1 and "Hi " in output:
                # GitHub returns "Hi username!" on successful auth
                results["ssh_connection"] = {
                    "ok": True,
                    "message": f"SSH 連線測試成功: {output.strip()}",
                }
            else:
                results["ssh_connection"] = {
                    "ok": False,
                    "message": f"SSH 連線失敗: {output.strip()}",
                }
        except subprocess.TimeoutExpired:
            results["ssh_connection"] = {
                "ok": False,
                "message": "SSH 連線測試逾時",
            }
        except Exception as e:
            results["ssh_connection"] = {
                "ok": False,
                "message": f"SSH 連線測試錯誤: {str(e)}",
            }

        return results

    def get_status_report(self) -> str:
        """Generate a status report for logging on startup.

        Returns:
            Formatted status report string.
        """
        lines = ["Git 自動提交設定狀態:"]
        lines.append(f"  - 自動提交: {'✅ 啟用' if self.auto_commit else '❌ 停用'}")
        lines.append(f"  - 自動推送: {'✅ 啟用' if self.auto_push else '❌ 停用'}")
        lines.append(f"  - Commit 前綴: {self.commit_prefix}")

        if self.auto_commit or self.auto_push:
            lines.append("")
            lines.append("SSH 設定檢查:")
            checks = self.check_ssh_config()
            for name, result in checks.items():
                status = "✅" if result["ok"] else "⚠️"
                lines.append(f"  {status} {result['message']}")

            # Warn if any check failed but auto features are enabled
            failed_checks = [k for k, v in checks.items() if not v["ok"]]
            if failed_checks and self.auto_push:
                lines.append("")
                lines.append("⚠️  警告: SSH 設定有問題，自動推送可能會失敗")

        return "\n".join(lines)

    def commit_changes(
        self,
        files: list[str],
        action: str,
        item_id: str,
        title: str = "",
    ) -> tuple[bool, str]:
        """Commit and optionally push changes for specific files.

        Args:
            files: List of file paths to stage (relative or absolute).
            action: Action description (e.g., "新增圖片", "更新", "刪除").
            item_id: Item ID for commit message.
            title: Optional title for commit message.

        Returns:
            Tuple of (success: bool, message: str).
        """
        if not self.auto_commit:
            return True, "自動提交已停用"

        try:
            # Stage files (handle both existing and deleted files)
            staged_count = 0
            for file in files:
                # Use -A to handle both adds and deletes
                success, output = self._run_git_command("add", "-A", file)
                if success:
                    staged_count += 1
                else:
                    logger.warning(f"無法 stage 檔案 {file}: {output}")

            if staged_count == 0:
                return False, "沒有檔案被 staged"

            # Check if there are changes to commit
            success, status = self._run_git_command("status", "--porcelain")
            if success and not status.strip():
                return True, "沒有變更需要提交"

            # Create commit message
            display_name = title or item_id
            message = f"{self.commit_prefix} {action}: {display_name}"

            # Commit with --no-verify to skip pre-commit hooks
            success, output = self._run_git_command(
                "commit", "--no-verify", "-m", message
            )
            if not success:
                if "nothing to commit" in output:
                    return True, "沒有變更需要提交"
                return False, f"提交失敗: {output}"

            logger.info(f"Git commit 成功: {message}")

            # Push if enabled
            if self.auto_push:
                success, output = self._run_git_command("push", timeout=60)
                if not success:
                    return False, f"推送失敗: {output}"
                logger.info("Git push 成功")
                return True, "變更已提交並推送"

            return True, "變更已提交 (未推送)"

        except Exception as e:
            logger.error(f"Git 操作失敗: {e}")
            return False, f"Git 操作錯誤: {str(e)}"

    def get_relative_path(self, absolute_path: Path) -> str:
        """Convert absolute path to repository-relative path.

        Args:
            absolute_path: Absolute file path.

        Returns:
            Path relative to repository root.
        """
        try:
            return str(absolute_path.relative_to(self.repo_path))
        except ValueError:
            return str(absolute_path)
