from articlesa.core.types import clean_url


def test_clean_url():
    assert clean_url('https://example.com') == 'https://example.com'
    assert clean_url('https://example.com/') == 'https://example.com/'
    assert clean_url('https://example.com/foo') == 'https://example.com/foo'
    assert clean_url('https://example.com/foo/') == 'https://example.com/foo/'
    assert clean_url('https://example.com/foo/bar') == 'https://example.com/foo/bar'
    assert clean_url('https://example.com/foo/bar/') == 'https://example.com/foo/bar/'
    assert clean_url('https://example.com/foo/bar/?baz=quux') == 'https://example.com/foo/bar/'
    assert clean_url('https://example.com/foo/bar/?baz=quux#quuz') == 'https://example.com/foo/bar/'
    assert clean_url('https://long.hostname.example.com/foo/bar?baz=quux#quuz') == 'https://long.hostname.example.com/foo/bar'
