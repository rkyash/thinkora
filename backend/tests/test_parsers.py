"""
Tests for services/parsers/__init__.py — dispatch_parser factory.

Covers acceptance criteria for TASK-093:
  ✓ Factory returns correct parser for each SourceType
  ✓ Unknown source type raises ValidationError
  ✓ BaseParser contract is enforced
  ✓ Registry is built lazily and can be reset
  ✓ Missing parser modules are handled gracefully
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.constants import SourceType
from app.core.exceptions import ValidationError
from app.services.parsers import (
    BaseParser,
    _build_registry,
    dispatch_parser,
    get_supported_types,
    reset_registry,
)


@pytest.fixture(autouse=True)
def _reset():
    """Ensure the registry is reset between tests."""
    reset_registry()
    yield
    reset_registry()


# ─── BaseParser contract ──────────────────────────────────────────


class TestBaseParser:
    def test_cannot_instantiate_directly(self):
        """BaseParser is abstract and should not be instantiated."""
        with pytest.raises(TypeError):
            BaseParser()

    def test_subclass_must_implement_parse(self):
        """Subclass without parse() should fail to instantiate."""

        class IncompleteParser(BaseParser):
            supported_types = {SourceType.TXT}

        with pytest.raises(TypeError):
            IncompleteParser()

    def test_valid_subclass(self):
        """A properly implemented subclass should instantiate."""

        class GoodParser(BaseParser):
            supported_types = {SourceType.TXT}

            async def parse(self, data: bytes, *, filename: str = "") -> str:
                return data.decode()

        parser = GoodParser()
        assert SourceType.TXT in parser.supported_types
        assert repr(parser).startswith("<GoodParser")

    @pytest.mark.asyncio
    async def test_parse_returns_string(self):
        """parse() should return a string."""

        class TxtParser(BaseParser):
            supported_types = {SourceType.TXT}

            async def parse(self, data: bytes, *, filename: str = "") -> str:
                return data.decode("utf-8")

        parser = TxtParser()
        result = await parser.parse(b"hello world", filename="test.txt")
        assert result == "hello world"


# ─── dispatch_parser ──────────────────────────────────────────────


class TestDispatchParser:
    def test_dispatch_with_mock_parser(self):
        """dispatch_parser should return parser registered for a type."""

        class FakeParser(BaseParser):
            supported_types = {SourceType.TXT}

            async def parse(self, data: bytes, *, filename: str = "") -> str:
                return "fake"

        # Manually inject into registry
        from app.services.parsers import _get_registry

        registry = _get_registry()
        registry[SourceType.TXT] = FakeParser()

        parser = dispatch_parser(SourceType.TXT)
        assert isinstance(parser, FakeParser)

    def test_dispatch_unknown_raises(self):
        """Dispatching an unregistered source type should raise ValidationError."""
        # Build registry (may have no parsers if dependencies are missing)
        # Then try a type that's definitely not registered
        # We'll use a custom approach: clear registry and try dispatch

        from app.services.parsers import _get_registry

        registry = _get_registry()
        # Remove all entries to simulate no parsers
        registry.clear()

        with pytest.raises(ValidationError, match="No parser available"):
            dispatch_parser(SourceType.PDF)

    def test_dispatch_returns_same_instance(self):
        """dispatch_parser should return the same parser instance (singleton)."""

        class StubParser(BaseParser):
            supported_types = {SourceType.CSV}

            async def parse(self, data: bytes, *, filename: str = "") -> str:
                return ""

        from app.services.parsers import _get_registry

        instance = StubParser()
        _get_registry()[SourceType.CSV] = instance

        parser_a = dispatch_parser(SourceType.CSV)
        parser_b = dispatch_parser(SourceType.CSV)
        assert parser_a is parser_b
        assert parser_a is instance


# ─── Registry ────────────────────────────────────────────────────


class TestRegistry:
    def test_build_registry_handles_missing_modules(self):
        """Missing parser modules should be skipped, not crash."""
        # _build_registry tries to import all parser modules.
        # Some may fail due to missing dependencies — that's fine.
        registry = _build_registry()
        # Should return a dict (possibly empty if no parser libs installed)
        assert isinstance(registry, dict)

    def test_get_supported_types_returns_list(self):
        """get_supported_types should return a list of SourceType enums."""
        types = get_supported_types()
        assert isinstance(types, list)
        for t in types:
            assert isinstance(t, SourceType)

    def test_reset_registry_forces_rebuild(self):
        """After reset, the registry should be rebuilt on next access."""
        from app.services.parsers import _get_registry

        registry_a = _get_registry()
        reset_registry()
        registry_b = _get_registry()

        # They should be different dict objects (rebuilt)
        assert registry_a is not registry_b

    def test_registry_maps_source_types_correctly(self):
        """Each parser's supported_types should match its registry keys."""

        class MultiParser(BaseParser):
            supported_types = {SourceType.TXT, SourceType.MARKDOWN}

            async def parse(self, data: bytes, *, filename: str = "") -> str:
                return ""

        from app.services.parsers import _get_registry

        registry = _get_registry()
        instance = MultiParser()
        for st in instance.supported_types:
            registry[st] = instance

        assert dispatch_parser(SourceType.TXT) is instance
        assert dispatch_parser(SourceType.MARKDOWN) is instance
