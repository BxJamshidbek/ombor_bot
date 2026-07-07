from app.utils.validators import (
    normalize_phone,
    validate_phone_number,
    validate_quantity,
    validate_positive_int,
)


class TestNormalizePhone:
    def test_full_with_plus(self):
        assert normalize_phone("+998901234567") == "+998901234567"

    def test_without_plus(self):
        assert normalize_phone("998901234567") == "+998901234567"

    def test_without_code(self):
        assert normalize_phone("901234567") == "+998901234567"

    def test_invalid_short(self):
        result = normalize_phone("123")
        assert not validate_phone_number(result)


class TestValidatePhoneNumber:
    def test_valid(self):
        assert validate_phone_number("+998901234567") is True

    def test_invalid(self):
        assert validate_phone_number("12345") is False


class TestValidateQuantity:
    def test_valid_float(self):
        assert validate_quantity("10.5") == 10.5

    def test_valid_int(self):
        assert validate_quantity("10") == 10.0

    def test_zero(self):
        assert validate_quantity("0") is None

    def test_negative(self):
        assert validate_quantity("-5") is None

    def test_invalid(self):
        assert validate_quantity("abc") is None


class TestValidatePositiveInt:
    def test_valid(self):
        assert validate_positive_int("30") == 30

    def test_zero(self):
        assert validate_positive_int("0") is None

    def test_negative(self):
        assert validate_positive_int("-5") is None

    def test_float_string(self):
        assert validate_positive_int("10.5") is None

    def test_invalid(self):
        assert validate_positive_int("abc") is None
