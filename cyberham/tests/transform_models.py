from dataclass_dict_convert import dataclass_dict_convert # type: ignore
from stringcase import camelcase # type: ignore
from dataclasses import dataclass
from typing import Any

@dataclass_dict_convert(dict_letter_case=camelcase) # type: ignore
@dataclass(kw_only=True)
class DeepDC:
    string: str


@dataclass_dict_convert(dict_letter_case=camelcase)  # type: ignore
@dataclass(kw_only=True)
class DC:
    integer: int
    string: str
    dictionary: dict[str, str]
    deep: DeepDC


_dict: dict[str, str] = {"from_key": "to_value"}
basic_deep_dc = DeepDC(string="deeper word")

basic_dc = DC(integer=9, string="word", dictionary=_dict, deep=basic_deep_dc)
basic_item: dict[str, Any] = {
    "integer": 9,
    "string": "word",
    "dictionary": _dict,
    "deep": {"string": "deeper word"},
}

incorrect_type_dc = DC(integer=True, string="word", dictionary=_dict, deep=basic_deep_dc)  # type: ignore
incorrect_type_item: dict[str, Any] = {
    "integer": True,
    "string": "word",
    "dictionary": _dict,
    "deep": {"string": "deeper word"},
}

underloaded_item: dict[str, Any] = {
    "string": "word",
    "dictionary": _dict,
    "deep": {"string": "deeper word"},
}

overloaded_item: dict[str, Any] = {
    "integer": 9,
    "string": "word",
    "dictionary": _dict,
    "deep": {"string": "deeper word"},
    "extra_attr": "oh noes",
}