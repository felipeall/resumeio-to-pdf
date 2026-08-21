import pytest

from app.services.assets import find_chunk_names, find_rendering_core_url, find_worker_name

BUILDER_BUNDLE = (
    'c.u=e=>"chunk/"+(({184:"misc",3525:"pdf-preview-renderer",9148:"rendering-core"})[e]||e)'
    '+"."+({184:"0945f5e9412e9756",3525:"3917ea2d35a941e0",9148:"e0abc25e11002fd3"})[e]+".js"'
)
RENDERING_CORE = 'u=new Worker(new URL(e.p+e.u(961),e.b),{name:"rendering"});e.u=()=>"workers/rendering.be47e5a3.js"'
WORKER = (
    'd.u=e=>403===e?"workers/403.320a32cc6e386fcb17ce.js":972===e?"workers/972.151951a3f1e8ef2edf45.js"'
    ':"workers/vendors."+({36:"551c1290911e384152f8",138:"327b58d20d235ea59b9f"})[e]+".js"'
)


def test_find_rendering_core_url():
    assert find_rendering_core_url(BUILDER_BUNDLE) == (
        "https://resume.io/assets/chunk/rendering-core.e0abc25e11002fd3.js"
    )


def test_find_rendering_core_url_without_the_chunk():
    with pytest.raises(LookupError):
        find_rendering_core_url('c.u=e=>"chunk/"+(({184:"misc"})[e]||e)+"."+({184:"0945f5e9412e9756"})[e]+".js"')


def test_find_worker_name():
    assert find_worker_name(RENDERING_CORE) == "rendering.be47e5a3.js"


def test_find_worker_name_without_a_worker():
    with pytest.raises(LookupError):
        find_worker_name("u=new Worker(new URL(e.p+e.u(961),e.b))")


def test_find_chunk_names_covers_named_and_vendor_chunks():
    assert find_chunk_names(WORKER) == {
        "403.320a32cc6e386fcb17ce.js",
        "972.151951a3f1e8ef2edf45.js",
        "vendors.551c1290911e384152f8.js",
        "vendors.327b58d20d235ea59b9f.js",
    }
