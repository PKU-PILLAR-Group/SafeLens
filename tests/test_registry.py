from SafeLens.core.registry import list_attributors, list_monitors, list_probes
from SafeLens.pipelines.runner import load_builtin_methods


def test_builtin_methods_register() -> None:
    load_builtin_methods()

    assert "dummy_probe" in list_probes()
    assert "linear_probe" in list_probes()
    assert "dummy_monitor" in list_monitors()
    assert "dummy_attributor" in list_attributors()
