from homeogrid.app.run import build_runtime


def test_no_fast_ablation_disables_fast_memory():
    runtime = build_runtime("configs/full.yaml")
    runtime.orchestrator._apply_ablation("no_fast")
    assert runtime.orchestrator.agent.fast_memory.enabled is False
    runtime.orchestrator._restore_full_mode()
    assert runtime.orchestrator.agent.fast_memory.enabled is True


def test_no_slow_ablation_disables_slow_memory_during_run():
    runtime = build_runtime("configs/full.yaml")
    runtime.orchestrator._apply_ablation("no_slow")
    assert runtime.orchestrator.agent.slow_memory.enabled is False
    runtime.orchestrator._restore_full_mode()
    assert runtime.orchestrator.agent.slow_memory.enabled is True
