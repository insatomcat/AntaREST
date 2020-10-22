import json
import os

import pytest

from api_iso_antares.web import RequestHandler
from api_iso_antares.web.request_handler import RequestHandlerParameters
from api_iso_antares.web.server import create_server


def assert_url_content(
    request_handler: RequestHandler, url: str, expected_output: str
) -> None:
    app = create_server(request_handler)
    client = app.test_client()
    res = client.get(url)
    assert json.loads(res.data) == expected_output


def assert_with_errors(
    request_handler: RequestHandler, url: str, expected_output: dict
) -> None:
    url = url[10:]
    print(url)
    assert (
        request_handler.get(route=url, parameters=RequestHandlerParameters())
        == expected_output
    )


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url,expected_output",
    [],
)
def test_sta_mini(
    request_handler: RequestHandler, url: str, expected_output: str
) -> None:
    assert_url_content(
        request_handler=request_handler,
        url=url,
        expected_output=expected_output,
    )


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, expected_output",
    [
        ("/metadata/STA-mini/settings/generaldata/general/horizon", 2030),
        ("/metadata/STA-mini/settings/simulations", {}),
    ],
)
def test_sta_mini_settings(
    request_handler: RequestHandler, url: str, expected_output: str
):
    assert_with_errors(
        request_handler=request_handler,
        url=url,
        expected_output=expected_output,
    )
    assert_url_content(
        request_handler=request_handler,
        url=url,
        expected_output=expected_output,
    )


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, expected_output",
    [
        (
            "/metadata/STA-mini/layers/layers/activeLayer/showAllLayer",
            True,
        ),
        (
            "/metadata/STA-mini/layers/layers/layers/0",
            "All",
        ),
    ],
)
def test_sta_mini_layers_layers(
    request_handler: RequestHandler, url: str, expected_output: str
):

    assert_url_content(
        request_handler=request_handler,
        url=url,
        expected_output=expected_output,
    )


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, expected_output",
    [
        (
            "/metadata/STA-mini/desktop/.shellclassinfo/iconfile",
            "settings/resources/study.ico",
        ),
        (
            "/metadata/STA-mini/desktop/.shellclassinfo/infotip",
            "Antares Study7.0: STA-mini",
        ),
        ("/metadata/STA-mini/desktop/.shellclassinfo/iconindex", 0),
    ],
)
def test_sta_mini_desktop(
    request_handler: RequestHandler, url: str, expected_output: str
):
    assert_url_content(
        request_handler=request_handler,
        url=url,
        expected_output=expected_output,
    )


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, expected_output",
    [
        (
            "/metadata/STA-mini/study/antares/created",
            1480683452,
        ),
        (
            "/metadata/STA-mini/study/antares/author",
            "Andrea SGATTONI",
        ),
    ],
)
def test_sta_mini_study_antares(
    request_handler: RequestHandler, url: str, expected_output: str
):
    assert_url_content(
        request_handler=request_handler,
        url=url,
        expected_output=expected_output,
    )


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, expected_output",
    [
        (
            "/metadata/STA-mini/input/bindingconstraints/bindingconstraints",
            {},
        ),
        (
            "/metadata/STA-mini/input/hydro/series/de/mod.txt",
            f"file{os.sep}STA-mini{os.sep}input{os.sep}hydro{os.sep}series{os.sep}de{os.sep}mod.txt",
        ),
    ],
)
def test_sta_mini_input(
    request_handler: RequestHandler, url: str, expected_output: str
):
    assert_url_content(
        request_handler=request_handler,
        url=url,
        expected_output=expected_output,
    )


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, expected_output",
    [
        (
            "/metadata/STA-mini/output/20201014-1427eco/annualSystemCost.txt",
            f"file{os.sep}STA-mini{os.sep}output{os.sep}20201014-1427eco{os.sep}annualSystemCost.txt",
        ),
        (
            "/metadata/STA-mini/output/20201014-1422eco-hello/checkIntegrity.txt",
            f"file{os.sep}STA-mini{os.sep}output{os.sep}20201014-1422eco-hello{os.sep}checkIntegrity.txt",
        ),
        (
            "/metadata/STA-mini/output/20201014-1430adq/simulation-comments.txt",
            f"file{os.sep}STA-mini{os.sep}output{os.sep}20201014-1430adq{os.sep}simulation-comments.txt",
        ),
        (
            "/metadata/STA-mini/output/20201014-1425eco-goodbye/simulation.log",
            f"file{os.sep}STA-mini{os.sep}output{os.sep}20201014-1425eco-goodbye{os.sep}simulation.log",
        ),
        (
            "/metadata/STA-mini/output/20201014-1422eco-hello/about-the-study/areas.txt",
            f"file{os.sep}STA-mini{os.sep}output{os.sep}20201014-1422eco-hello{os.sep}about-the-study{os.sep}areas.txt",
        ),
        (
            "/metadata/STA-mini/output/20201014-1425eco-goodbye/about-the-study/comments.txt",
            f"file{os.sep}STA-mini{os.sep}output{os.sep}20201014-1425eco-goodbye{os.sep}about-the-study{os.sep}comments.txt",
        ),
        (
            "/metadata/STA-mini/output/20201014-1427eco/about-the-study/links.txt",
            f"file{os.sep}STA-mini{os.sep}output{os.sep}20201014-1427eco{os.sep}about-the-study{os.sep}links.txt",
        ),
        (
            "/metadata/STA-mini/output/20201014-1430adq/about-the-study/parameters/general/horizon",
            2030,
        ),
        (
            "/metadata/STA-mini/output/20201014-1422eco-hello/about-the-study/study/antares/author",
            "Andrea SGATTONI",
        ),
    ],
)
def test_sta_mini_output(
    request_handler: RequestHandler, url: str, expected_output: str
):
    assert_url_content(
        request_handler=request_handler,
        url=url,
        expected_output=expected_output,
    )
