import pytest
from dataclass_dict_convert import UnknownFieldError  # type: ignore
from cyberham.tests.transform_models import (
    DC,
    DeepDC,
    basic_dc,
    basic_deep_dc,
    basic_item,
    incorrect_type_dc,
    incorrect_type_item,
    underloaded_item,
    overloaded_item,
)
from cyberham.dynamodb.types import data_to_item, item_to_data
from typing import Any


class TestTransform:
    def test_basic_dti(self) -> None:
        item = data_to_item(basic_dc)
        assert item == basic_item

    def test_basic_itd(self) -> None:
        dc = item_to_data(basic_item, DC)
        assert dc == basic_dc

    def test_built_itd(self) -> None:
        item: dict[str, Any] = {}
        item["string"] = "deeper word"
        ddc = item_to_data(item, DeepDC)
        assert ddc == basic_deep_dc

    def test_fail_type_error_dti(self) -> None:
        dc = data_to_item(incorrect_type_dc)
        assert dc == incorrect_type_item

    def test_fail_type_error_itd(self) -> None:
        item = item_to_data(incorrect_type_item, DC)
        assert item == incorrect_type_dc

    def test_fail_underloaded_itd(self) -> None:
        with pytest.raises(TypeError):
            _ = item_to_data(underloaded_item, DC)

    def test_fail_overloaded_itd(self) -> None:
        with pytest.raises(UnknownFieldError):
            _ = item_to_data(overloaded_item, DC)
