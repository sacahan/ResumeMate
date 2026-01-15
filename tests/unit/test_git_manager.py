"""Unit tests for GitManager class.

Tests Git operations for infographics admin, mocking subprocess calls
to avoid actual Git operations during testing.
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.backend.cms.git_manager import GitManager


class TestGitManagerInit:
    """Tests for GitManager initialization."""

    def test_default_initialization(self):
        """Test default values when no environment variables are set."""
        with patch.dict(
            "os.environ",
            {
                "CMS_GIT_AUTO_COMMIT": "false",
                "CMS_GIT_AUTO_PUSH": "false",
            },
            clear=False,
        ):
            manager = GitManager()
            assert manager.auto_commit is False
            assert manager.auto_push is False
            assert manager.commit_prefix == "[cms]"

    def test_enabled_auto_commit(self):
        """Test auto_commit enabled via environment variable."""
        with patch.dict(
            "os.environ",
            {"CMS_GIT_AUTO_COMMIT": "true"},
            clear=False,
        ):
            manager = GitManager()
            assert manager.auto_commit is True

    def test_enabled_auto_push(self):
        """Test auto_push enabled via environment variable."""
        with patch.dict(
            "os.environ",
            {"CMS_GIT_AUTO_PUSH": "true"},
            clear=False,
        ):
            manager = GitManager()
            assert manager.auto_push is True

    def test_custom_commit_prefix(self):
        """Test custom commit prefix via environment variable."""
        with patch.dict(
            "os.environ",
            {"CMS_GIT_COMMIT_PREFIX": "[custom]"},
            clear=False,
        ):
            manager = GitManager()
            assert manager.commit_prefix == "[custom]"

    def test_custom_repo_path(self, tmp_path):
        """Test custom repository path."""
        manager = GitManager(repo_path=tmp_path)
        assert manager.repo_path == tmp_path


class TestRunGitCommand:
    """Tests for _run_git_command method."""

    def test_successful_command(self):
        """Test successful git command execution."""
        manager = GitManager()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="success output",
                stderr="",
            )
            success, output = manager._run_git_command("status")

            assert success is True
            assert "success output" in output
            mock_run.assert_called_once()

    def test_failed_command(self):
        """Test failed git command execution."""
        manager = GitManager()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="error: command failed",
            )
            success, output = manager._run_git_command("status")

            assert success is False
            assert "error" in output

    def test_command_timeout(self):
        """Test git command timeout handling."""
        manager = GitManager()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=30)
            success, output = manager._run_git_command("push")

            assert success is False
            assert "timed out" in output.lower()

    def test_git_not_installed(self):
        """Test handling when git is not installed."""
        manager = GitManager()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            success, output = manager._run_git_command("status")

            assert success is False
            assert "not installed" in output.lower()


class TestCheckSshConfig:
    """Tests for check_ssh_config method."""

    def test_ssh_key_found(self, tmp_path):
        """Test SSH key detection when key exists."""
        # Create mock SSH directory with key
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "id_ed25519").touch()
        (ssh_dir / "id_ed25519.pub").touch()

        manager = GitManager()

        with patch.object(Path, "home", return_value=tmp_path):
            results = manager.check_ssh_config()

        assert results["ssh_key"]["ok"] is True
        assert "id_ed25519" in results["ssh_key"]["message"]

    def test_ssh_key_not_found(self, tmp_path):
        """Test SSH key detection when no key exists."""
        # Create empty SSH directory
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()

        manager = GitManager()

        with patch.object(Path, "home", return_value=tmp_path):
            results = manager.check_ssh_config()

        assert results["ssh_key"]["ok"] is False
        assert "ssh-keygen" in results["ssh_key"]["message"]

    def test_remote_url_ssh(self):
        """Test remote URL check with SSH URL."""
        manager = GitManager()

        with patch.object(
            manager,
            "_run_git_command",
            return_value=(True, "git@github.com:user/repo.git"),
        ):
            with patch.object(Path, "home", return_value=Path("/tmp")):
                with patch("subprocess.run"):
                    results = manager.check_ssh_config()

        assert results["remote_url"]["ok"] is True
        assert "SSH URL" in results["remote_url"]["message"]

    def test_remote_url_https(self):
        """Test remote URL check with HTTPS URL."""
        manager = GitManager()

        with patch.object(
            manager,
            "_run_git_command",
            return_value=(True, "https://github.com/user/repo.git"),
        ):
            with patch.object(Path, "home", return_value=Path("/tmp")):
                with patch("subprocess.run"):
                    results = manager.check_ssh_config()

        assert results["remote_url"]["ok"] is False
        assert "HTTPS" in results["remote_url"]["message"]


class TestCommitChanges:
    """Tests for commit_changes method."""

    def test_auto_commit_disabled(self):
        """Test that commit is skipped when auto_commit is disabled."""
        with patch.dict(
            "os.environ",
            {"INFOGRAPHICS_GIT_AUTO_COMMIT": "false"},
            clear=False,
        ):
            manager = GitManager()
            success, message = manager.commit_changes(
                files=["test.json"],
                action="新增",
                item_id="img_123",
            )

            assert success is True
            assert "停用" in message

    def test_successful_commit_without_push(self):
        """Test successful commit without push."""
        with patch.dict(
            "os.environ",
            {
                "INFOGRAPHICS_GIT_AUTO_COMMIT": "true",
                "INFOGRAPHICS_GIT_AUTO_PUSH": "false",
            },
            clear=False,
        ):
            manager = GitManager()

            with patch.object(manager, "_run_git_command") as mock_cmd:
                # Setup mock responses
                mock_cmd.side_effect = [
                    (True, ""),  # git add
                    (True, "M test.json"),  # git status
                    (True, "committed"),  # git commit
                ]

                success, message = manager.commit_changes(
                    files=["test.json"],
                    action="新增",
                    item_id="img_123",
                )

                assert success is True
                assert "已提交" in message
                assert "未推送" in message

    def test_successful_commit_with_push(self):
        """Test successful commit with push."""
        with patch.dict(
            "os.environ",
            {
                "INFOGRAPHICS_GIT_AUTO_COMMIT": "true",
                "INFOGRAPHICS_GIT_AUTO_PUSH": "true",
            },
            clear=False,
        ):
            manager = GitManager()

            with patch.object(manager, "_run_git_command") as mock_cmd:
                mock_cmd.side_effect = [
                    (True, ""),  # git add
                    (True, "M test.json"),  # git status
                    (True, "committed"),  # git commit
                    (True, "pushed"),  # git push
                ]

                success, message = manager.commit_changes(
                    files=["test.json"],
                    action="新增",
                    item_id="img_123",
                )

                assert success is True
                assert "已提交並推送" in message

    def test_commit_failure(self):
        """Test handling of commit failure."""
        with patch.dict(
            "os.environ",
            {"INFOGRAPHICS_GIT_AUTO_COMMIT": "true"},
            clear=False,
        ):
            manager = GitManager()

            with patch.object(manager, "_run_git_command") as mock_cmd:
                mock_cmd.side_effect = [
                    (True, ""),  # git add
                    (True, "M test.json"),  # git status
                    (False, "error: commit failed"),  # git commit
                ]

                success, message = manager.commit_changes(
                    files=["test.json"],
                    action="新增",
                    item_id="img_123",
                )

                assert success is False
                assert "失敗" in message

    def test_push_failure(self):
        """Test handling of push failure."""
        with patch.dict(
            "os.environ",
            {
                "INFOGRAPHICS_GIT_AUTO_COMMIT": "true",
                "INFOGRAPHICS_GIT_AUTO_PUSH": "true",
            },
            clear=False,
        ):
            manager = GitManager()

            with patch.object(manager, "_run_git_command") as mock_cmd:
                mock_cmd.side_effect = [
                    (True, ""),  # git add
                    (True, "M test.json"),  # git status
                    (True, "committed"),  # git commit
                    (False, "error: push failed"),  # git push
                ]

                success, message = manager.commit_changes(
                    files=["test.json"],
                    action="新增",
                    item_id="img_123",
                )

                assert success is False
                assert "推送失敗" in message

    def test_no_changes_to_commit(self):
        """Test handling when there are no changes to commit."""
        with patch.dict(
            "os.environ",
            {"INFOGRAPHICS_GIT_AUTO_COMMIT": "true"},
            clear=False,
        ):
            manager = GitManager()

            with patch.object(manager, "_run_git_command") as mock_cmd:
                mock_cmd.side_effect = [
                    (True, ""),  # git add
                    (True, ""),  # git status (empty = no changes)
                ]

                success, message = manager.commit_changes(
                    files=["test.json"],
                    action="新增",
                    item_id="img_123",
                )

                assert success is True
                assert "沒有變更" in message


class TestGetRelativePath:
    """Tests for get_relative_path method."""

    def test_path_within_repo(self, tmp_path):
        """Test converting absolute path within repo to relative."""
        manager = GitManager(repo_path=tmp_path)
        absolute_path = tmp_path / "src" / "file.json"

        relative = manager.get_relative_path(absolute_path)

        assert relative == "src/file.json"

    def test_path_outside_repo(self, tmp_path):
        """Test handling path outside repository."""
        manager = GitManager(repo_path=tmp_path)
        outside_path = Path("/some/other/path/file.json")

        relative = manager.get_relative_path(outside_path)

        # Should return the original path as string
        assert relative == str(outside_path)


class TestGetStatusReport:
    """Tests for get_status_report method."""

    def test_status_report_disabled(self):
        """Test status report when auto features are disabled."""
        with patch.dict(
            "os.environ",
            {
                "INFOGRAPHICS_GIT_AUTO_COMMIT": "false",
                "INFOGRAPHICS_GIT_AUTO_PUSH": "false",
            },
            clear=False,
        ):
            manager = GitManager()
            report = manager.get_status_report()

            assert "停用" in report
            assert "自動提交" in report
            assert "自動推送" in report

    def test_status_report_enabled(self):
        """Test status report when auto features are enabled."""
        with patch.dict(
            "os.environ",
            {
                "INFOGRAPHICS_GIT_AUTO_COMMIT": "true",
                "INFOGRAPHICS_GIT_AUTO_PUSH": "true",
            },
            clear=False,
        ):
            manager = GitManager()

            with patch.object(manager, "check_ssh_config") as mock_check:
                mock_check.return_value = {
                    "ssh_key": {"ok": True, "message": "Found SSH key"},
                    "remote_url": {"ok": True, "message": "Using SSH URL"},
                    "ssh_connection": {"ok": True, "message": "Connection OK"},
                }
                report = manager.get_status_report()

            assert "啟用" in report
            assert "SSH 設定檢查" in report
