import logging
from unittest.mock import MagicMock

import pytest

from src.core.context import RomContext


@pytest.fixture
def mock_context():
    """Returns a mock RomContext."""
    mock = MagicMock(spec=RomContext)
    mock.is_eu_rom = False  # Default to CN port
    mock.logger = logging.getLogger("MockContext")
    return mock
