"""Issue #48: a floating 'Back to top' button on every screen (AC-14).

The test harness cannot scroll or click in a browser, so these tests check that
the button is on each of the four screens with its label, exactly once. The
scroll itself is checked by hand in a real browser.
"""

from streamlit.testing.v1 import AppTest

LABEL = "Back to top"
SCREENS = ["Where the money comes from", "Growth", "Customers", "Sales reps"]


def _open_screen(index: int) -> AppTest:
    """Run streamlit_app.py showing one screen (its position in the navigation)."""

    def script(index):
        import runpy

        import streamlit as st

        pages = []
        real_page = st.Page

        def page(fn, **kwargs):
            pages.append(fn)
            return real_page(fn, **kwargs)

        class Chosen:
            def run(self):
                pages[index]()

        st.Page = page
        st.navigation = lambda *args, **kwargs: Chosen()
        runpy.run_path("streamlit_app.py")

    return AppTest.from_function(script, args=(index,), default_timeout=60).run()


def _back_to_top_elements(app: AppTest) -> list[str]:
    """Every button, link or text element on the screen that carries the label."""
    texts = [b.label for b in app.button]
    texts += [m.value for m in app.markdown]
    texts += [c.value for c in app.caption]
    return [t for t in texts if LABEL in t]


def test_ac14_back_to_top_button_on_every_screen(engine):
    # Given any of the four screens, when it loads, then a 'Back to top' button is
    # on the screen, once (not twice), so a viewer deep in a long page has one
    # click back to the top.
    problems = []
    for index, name in enumerate(SCREENS):
        app = _open_screen(index)
        assert not app.exception, f"{name} failed to load"
        count = len(_back_to_top_elements(app))
        if count != 1:
            problems.append(f"{name}: expected one '{LABEL}' button, found {count}")
    assert not problems, "; ".join(problems)
