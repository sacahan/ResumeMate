"""Unit tests for the InfographicAssistantAgent."""

import pytest

from src.backend.cms import InfographicAssistantAgent


class TestInfographicAssistantAgent:
    """Tests for the AI assistant agent."""

    def test_agent_initialization(self):
        """Test that agent initializes with default settings."""
        existing_tags = ["Architecture", "AI", "CICD"]
        agent = InfographicAssistantAgent(existing_tags=existing_tags)

        assert agent.existing_tags == existing_tags
        assert agent.llm_model is not None
        assert agent.model_settings is not None
        assert agent.sdk_agent is not None

    def test_agent_initialization_empty_tags(self):
        """Test agent initialization with empty tag list."""
        agent = InfographicAssistantAgent(existing_tags=[])

        assert agent.existing_tags == []

    def test_agent_initialization_none_tags(self):
        """Test agent initialization with None tags."""
        agent = InfographicAssistantAgent(existing_tags=None)

        assert agent.existing_tags == []

    def test_instructions_contain_tags(self):
        """Test that instructions contain the existing tags."""
        existing_tags = ["Architecture", "AI", "CICD", "Design Pattern"]
        agent = InfographicAssistantAgent(existing_tags=existing_tags)

        instructions = agent._build_instructions()

        for tag in existing_tags:
            assert tag in instructions

    def test_instructions_format(self):
        """Test that instructions have proper structure."""
        agent = InfographicAssistantAgent()

        instructions = agent._build_instructions()

        assert "圖表元數據助理" in instructions
        assert "角色定位" in instructions
        assert "核心任務" in instructions
        assert "翻譯指南" in instructions
        assert "標籤建議規則" in instructions


@pytest.mark.asyncio
class TestInfographicAssistantAgentAsync:
    """Async tests for the AI assistant agent."""

    async def test_suggest_metadata_empty_title(self):
        """Test suggest_metadata with empty title."""
        agent = InfographicAssistantAgent()

        with pytest.raises(ValueError, match="cannot be empty"):
            await agent.suggest_metadata("")

    async def test_suggest_metadata_none_title(self):
        """Test suggest_metadata with None title."""
        agent = InfographicAssistantAgent()

        with pytest.raises(ValueError, match="cannot be empty"):
            await agent.suggest_metadata(None)

    async def test_suggest_metadata_whitespace_title(self):
        """Test suggest_metadata with whitespace-only title."""
        agent = InfographicAssistantAgent()

        with pytest.raises(ValueError, match="cannot be empty"):
            await agent.suggest_metadata("   ")

    # Note: Full async tests with actual API calls would require:
    # - Valid GitHub Copilot API token
    # - Network connectivity
    # - Should be run separately as integration tests
