import pytest
import pandas as pd

from main import Crawler, FIXED_COL_NAMES, DYNAMIC_COL_NAMES


@pytest.fixture
def mock_project_info():
    return ["1"] * (len(FIXED_COL_NAMES) + 4 * len(DYNAMIC_COL_NAMES))


def test_crawler_output(mock_project_info):
    crawler = Crawler()
    filename = "test/test.xlsx"

    crawler.output(filename)
    df = pd.read_excel(filename)
    assert len(df.columns) == len(FIXED_COL_NAMES) + 1

    crawler.project_infos = [mock_project_info]
    crawler.output(filename)
    df = pd.read_excel(filename)
    expected = len(mock_project_info) + 1
    assert len(df.columns) == expected
