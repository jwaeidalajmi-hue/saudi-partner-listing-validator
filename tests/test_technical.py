from app.technical import hash_distance, measure, tier_of


def test_resolution_tiers():
    assert tier_of(800, 600) == "below_hd"
    assert tier_of(1280, 720) == "hd"
    assert tier_of(1280, 960) == "hd"
    assert tier_of(1920, 1080) == "full_hd"
    assert tier_of(1080, 1920) == "full_hd"      # portrait Full HD
    assert tier_of(3840, 2160) == "4k"


def test_sharp_vs_blurry(photo):
    sharp = measure(photo())
    blurry = measure(photo(blur=8))
    assert sharp.sharpness > 100
    assert blurry.sharpness < 50


def test_dark_photo(photo):
    assert measure(photo(brightness=25)).brightness < 50


def test_black_and_white(photo):
    assert measure(photo(colour=(128, 128, 128))).saturation < 8


def test_orientation(photo):
    assert measure(photo(1080, 1440)).orientation == "portrait"
    assert measure(photo(1200, 1200)).orientation == "square"


def test_duplicate_hash(photo):
    a, b = measure(photo(seed=1)), measure(photo(seed=1))
    c = measure(photo(colour=(200, 60, 40), seed=5))
    assert hash_distance(a.phash, b.phash) == 0
    assert hash_distance(a.phash, c.phash) > 6
