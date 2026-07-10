from app.utils.validators import (
    normalize_phone,
    validate_phone_number,
    validate_quantity,
    validate_positive_int,
    validate_full_name,
    validate_coordinates,
    build_google_maps_url,
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


class TestValidateFullName:
    def test_valid(self):
        assert validate_full_name("Ali Valiyev") == "Ali Valiyev"

    def test_strips_and_collapses_spaces(self):
        assert validate_full_name("  Ali   Valiyev  ") == "Ali Valiyev"

    def test_too_short(self):
        assert validate_full_name("A") is None

    def test_empty(self):
        assert validate_full_name("") is None

    def test_only_spaces(self):
        assert validate_full_name("    ") is None

    def test_too_long(self):
        assert validate_full_name("x" * 101) is None

    def test_exactly_max(self):
        assert validate_full_name("x" * 100) == "x" * 100


class TestValidateCoordinates:
    def test_valid(self):
        assert validate_coordinates(41.0, 69.0) is True

    def test_equator_and_prime_meridian(self):
        assert validate_coordinates(0.0, 0.0) is True

    def test_north_and_east_limits(self):
        assert validate_coordinates(90.0, 180.0) is True

    def test_south_and_west_limits(self):
        assert validate_coordinates(-90.0, -180.0) is True

    def test_latitude_over_90(self):
        assert validate_coordinates(91.0, 0.0) is False

    def test_latitude_under_minus_90(self):
        assert validate_coordinates(-91.0, 0.0) is False

    def test_longitude_over_180(self):
        assert validate_coordinates(0.0, 181.0) is False

    def test_longitude_under_minus_180(self):
        assert validate_coordinates(0.0, -181.0) is False

    def test_nan_latitude(self):
        assert validate_coordinates(float("nan"), 0.0) is False

    def test_infinity_latitude(self):
        assert validate_coordinates(float("inf"), 0.0) is False

    def test_nan_longitude(self):
        assert validate_coordinates(0.0, float("nan")) is False

    def test_infinity_longitude(self):
        assert validate_coordinates(0.0, float("-inf")) is False


class TestBuildGoogleMapsUrl:
    def test_basic_format(self):
        assert build_google_maps_url(41.1234567, 69.1234567) == "https://www.google.com/maps?q=41.1234567,69.1234567"

    def test_negative_coordinates(self):
        assert build_google_maps_url(-33.8688, 151.2093) == "https://www.google.com/maps?q=-33.8688000,151.2093000"

    def test_zero(self):
        assert build_google_maps_url(0.0, 0.0) == "https://www.google.com/maps?q=0.0000000,0.0000000"
