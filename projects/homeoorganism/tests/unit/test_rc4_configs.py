from dataclasses import dataclass, field
from pathlib import Path

from homeoorganism.config.loader import load_config
from homeoorganism.config.relocation_mode import RelocationMode
from homeoorganism.orchestration.matrix_runner import ExperimentMatrixRunner
from homeoorganism.orchestration.seed_set import SeedSet


def test_load_continuous_full_config():
    config = load_config(Path("configs/continuous_full.yaml"))
    assert config.experiment.mode == "continuous_full"
    assert config.experiment.lives_per_seed == 5
    assert config.experiment.life_max_ticks == 5000
    assert config.env.ecology_enabled is True
    assert config.env.relocation_mode == RelocationMode.CONTINUOUS_PERIODIC
    assert config.ecology.relocation_period_ticks == 1000
    assert config.ecology.relocation_probability == 0.5


def test_load_continuous_no_regen_config():
    config = load_config(Path("configs/continuous_no_regen.yaml"))
    assert config.experiment.mode == "continuous_no_regen"
    assert config.env.ecology_enabled is False
    assert config.env.relocation_mode == RelocationMode.CONTINUOUS_PERIODIC
    assert config.ecology.relocation_period_ticks == 1000
    assert config.ecology.relocation_probability == 0.5


def test_load_episodic_full_config():
    config = load_config(Path("configs/episodic_full.yaml"))
    assert config.experiment.mode == "episodic_full"
    assert config.env.relocation_mode == RelocationMode.EPISODIC_FIXED
    assert config.env.relocation_step == 150
    assert config.env.relocation_probability == 0.25
    assert config.env.ecology_enabled is False


def test_load_v1_baseline_full_config():
    config = load_config(Path("configs/v1_baseline_full.yaml"))
    assert config.experiment.mode == "v1_baseline_full"
    assert config.env.ecology_enabled is True
    assert config.env.relocation_mode == RelocationMode.CONTINUOUS_PERIODIC
    assert config.ecology.relocation_period_ticks == 1000
    assert config.ecology.relocation_probability == 0.5


def test_seed_files_parseable():
    pilot = SeedSet(Path("configs/seeds/pilot_rc4.txt")).load()
    official = SeedSet(Path("configs/seeds/official_rc4.txt")).load()
    assert pilot == (101, 202, 303, 404, 505)
    assert official == (101, 202, 303, 404, 505, 606, 707, 808, 909, 1010)
    assert len(set(pilot)) == len(pilot)
    assert len(set(official)) == len(official)


def test_matrix_runner_dispatches_by_mode(tmp_path: Path, monkeypatch):
    modes_seen = []
    monkeypatch.setattr(
        "homeoorganism.orchestration.matrix_runner.build_runtime",
        _build_runtime_factory(tmp_path, modes_seen),
    )
    runner = ExperimentMatrixRunner(
        config_path=Path("configs/continuous_full.yaml"),
        seeds_path=Path("configs/seeds/pilot_rc4.txt"),
        modes=("continuous_full", "episodic_full", "v1_baseline_full"),
        summary_name="summary.csv",
    )
    result = runner.run()
    _assert_mode_block(modes_seen, 0, "continuous_full")
    _assert_mode_block(modes_seen, 5, "episodic_full")
    _assert_mode_block(modes_seen, 10, "v1_baseline_full")
    assert result["run_count"] == 15
    assert result["modes"] == ["continuous_full", "episodic_full", "v1_baseline_full"]


def _build_runtime_factory(tmp_path: Path, modes_seen: list[tuple[str, str, str]]):
    def fake_build_runtime(config_path, settings, mode):
        run_dir = tmp_path / mode / settings.run_id
        modes_seen.append((config_path, settings.run_id, mode))
        return _fake_runtime(run_dir, mode)

    return fake_build_runtime


def _assert_mode_block(modes_seen: list[tuple[str, str, str]], start: int, expected: str):
    assert [mode for _, _, mode in modes_seen[start : start + 3]] == [expected, expected, expected]


def _fake_runtime(run_dir: Path, mode: str):
    if mode == "episodic_full":
        artifacts = _FakeEpisodicArtifacts(run_dir)
        return _FakeRuntime(_FakeEpisodicOrchestrator(artifacts), artifacts)
    artifacts = _FakeLifeArtifacts(run_dir)
    return _FakeRuntime(_FakeLifeOrchestrator(artifacts), artifacts)


@dataclass
class _FakeRuntime:
    orchestrator: object
    artifacts: object
    monitoring: object = field(default_factory=lambda: _FakeMonitoring())
    config: object = field(default_factory=lambda: _FakeConfig())


@dataclass(frozen=True)
class _FakeMonitoring:
    recorder: object = field(default_factory=lambda: _FakeRecorder())


@dataclass(frozen=True)
class _FakeRecorder:
    def close(self) -> None:
        return None


@dataclass(frozen=True)
class _FakeConfig:
    experiment: object = field(default_factory=lambda: _FakeExperiment())


@dataclass(frozen=True)
class _FakeExperiment:
    lives_per_seed: int = 5
    life_max_ticks: int = 5000


@dataclass(frozen=True)
class _FakeEpisodicArtifacts:
    root_dir: Path

    @property
    def metrics_path(self) -> Path:
        self.root_dir.mkdir(parents=True, exist_ok=True)
        path = self.root_dir / "metrics.csv"
        if not path.exists():
            path.write_text(
                "mode,phase,seed,survival_steps\n"
                "episodic_full,eval_seen,101,400\n",
                encoding="utf-8",
            )
        return path


@dataclass(frozen=True)
class _FakeLifeArtifacts:
    root_dir: Path

    @property
    def life_summaries_path(self) -> Path:
        self.root_dir.mkdir(parents=True, exist_ok=True)
        path = self.root_dir / "life_summaries.jsonl"
        if not path.exists():
            path.write_text(
                '{"life_id":1,"life_duration_ticks":5000,"end_reason":"max_ticks_reached","mode_transition_coherence":1.0,"mode_diversity":3}\n',
                encoding="utf-8",
            )
        return path


@dataclass(frozen=True)
class _FakeEpisodicOrchestrator:
    artifacts: _FakeEpisodicArtifacts

    def run_protocol(self, mode: str, train_episodes: int, eval_seen_episodes: int, eval_relocation_episodes: int) -> None:
        _ = (mode, train_episodes, eval_seen_episodes, eval_relocation_episodes)
        self.artifacts.metrics_path


@dataclass(frozen=True)
class _FakeLifeOrchestrator:
    artifacts: _FakeLifeArtifacts

    def run(self, mode: str, life_count: int, life_max_ticks: int) -> None:
        _ = (mode, life_count, life_max_ticks)
        self.artifacts.life_summaries_path
