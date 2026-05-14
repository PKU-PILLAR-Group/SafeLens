import pytest

pytestmark = [pytest.mark.integration, pytest.mark.slow]


def test_real_model_downloads_are_not_part_of_default_unit_tests() -> None:
    pytest.skip("Real model download tests must opt into integration/slow markers.")
