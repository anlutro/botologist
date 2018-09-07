from datetime import datetime
from freezegun import freeze_time
from botologist.util import time_until


@freeze_time("2018-02-03 20:00:00")
def test_time_until_returns_none_for_times_in_the_past():
    assert time_until(datetime(2018, 2, 3, 19)) == None
    assert time_until(datetime(2018, 2, 3, 20)) == None


@freeze_time("2018-02-03 20:00:00")
def test_time_until_returns_correct_estimates_for_same_day():
    assert time_until(datetime(2018, 2, 3, 20, 1)) == "1m"
    assert time_until(datetime(2018, 2, 3, 20, 59, 59)) in ("59m", "1h")
    assert time_until(datetime(2018, 2, 3, 21)) == "1h"
    assert time_until(datetime(2018, 2, 3, 21, 1)) == "1h 1m"
    assert time_until(datetime(2018, 2, 3, 21, 59, 59)) in ("1h 59m", "2h")
    assert time_until(datetime(2018, 2, 3, 22)) == "2h"
    assert time_until(datetime(2018, 2, 3, 22, 0, 1)) == "2h"
    assert time_until(datetime(2018, 2, 4, 1)) == "5h"


@freeze_time("2018-02-03 20:00:00")
def test_time_until_returns_correct_estimates_for_next_day():
    assert time_until(datetime(2018, 2, 4, 19)) == "23h"
    assert time_until(datetime(2018, 2, 4, 20)) == "1d"
    assert time_until(datetime(2018, 2, 4, 21)) == "1d 1h"
    assert time_until(datetime(2018, 2, 4, 21, 59, 59)) in ("1d 1h", "1d 2h")
