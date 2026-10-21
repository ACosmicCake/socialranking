import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))


@pytest.fixture(scope="session")
def site(tmp_path_factory):
    """The static site, built once per test session."""
    import build_site
    return build_site.build(tmp_path_factory.mktemp("site"), base_path="")
