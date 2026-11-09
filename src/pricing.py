from decimal import Decimal

BASE_PRICE = Decimal("15.00")
SURCHARGE_3D = Decimal("5.00")
SURCHARGE_ENHANCED_SOUND = Decimal("3.00")
OLD_MOVIE_DISCOUNT = Decimal("0.80")


def two_years_before(day):
    try:
        return day.replace(year=day.year - 2)
    except ValueError:
        return day.replace(year=day.year - 2, day=28)


def ticket_price(supports_3d, has_enhanced_sound, release_date, screening_date):
    price = BASE_PRICE
    if supports_3d:
        price += SURCHARGE_3D
    if has_enhanced_sound:
        price += SURCHARGE_ENHANCED_SOUND
    if release_date < two_years_before(screening_date):
        price *= OLD_MOVIE_DISCOUNT
    return price.quantize(Decimal("0.01"))
