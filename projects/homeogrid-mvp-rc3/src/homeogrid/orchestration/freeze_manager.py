"""Freeze protocol artifacts for a tagged build."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path


@dataclass(frozen=True)
class FreezeManager:
    tag_name: str
    config_paths: tuple[Path, ...]
    seed_paths: tuple[Path, ...]
    root_dir: Path = Path("artifacts") / "protocols"

    def freeze(self) -> dict[str, str]:
        self._ensure_clean_worktree()
        commit_sha = self._ensure_tag()
        target_dir = self.root_dir / self.tag_name
        copied = self._copy_payload(target_dir)
        manifest = self._manifest(commit_sha, copied)
        self._write_manifest(target_dir, manifest)
        return {
            "tag": self.tag_name,
            "commit": commit_sha,
            "output_dir": str(target_dir),
        }

    def _ensure_clean_worktree(self) -> None:
        status = self._git("status", "--short", "--", *self._tracked_paths())
        if status:
            raise ValueError("Working tree is dirty; commit or stash changes before freeze")

    def _ensure_tag(self) -> str:
        current = self._git("rev-parse", "HEAD")
        tagged = self._git("rev-parse", f"refs/tags/{self.tag_name}", check=False)
        if tagged == "":
            self._git("tag", self.tag_name)
            return current
        if tagged != current:
            raise ValueError(f"Tag {self.tag_name} points to {tagged}, expected {current}")
        return current

    def _copy_payload(self, target_dir: Path) -> list[Path]:
        copied = []
        copied.extend(self._copy_files(target_dir, self._root_files()))
        copied.extend(self._copy_files(target_dir / "configs", self.config_paths))
        copied.extend(self._copy_files(target_dir / "seeds", self.seed_paths))
        return copied

    def _root_files(self) -> tuple[Path, ...]:
        return (Path("README.md"), Path("requirements.lock"), Path("experiment_protocol.md"))

    def _tracked_paths(self) -> tuple[str, ...]:
        return ("src", "configs", "README.md", "experiment_protocol.md", "requirements.lock", "pyproject.toml")

    def _copy_files(self, target_dir: Path, files: tuple[Path, ...]) -> list[Path]:
        target_dir.mkdir(parents=True, exist_ok=True)
        copied = []
        for source in files:
            destination = target_dir / source.name
            shutil.copy2(source, destination)
            copied.append(destination)
        return copied

    def _manifest(self, commit_sha: str, copied: list[Path]) -> dict[str, object]:
        return {
            "tag": self.tag_name,
            "commit": commit_sha,
            "files": {str(path.relative_to(self.root_dir / self.tag_name)): self._hash_file(path) for path in copied},
        }

    def _write_manifest(self, target_dir: Path, manifest: dict[str, object]) -> None:
        path = target_dir / "manifest.json"
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    def _hash_file(self, path: Path) -> str:
        return sha256(path.read_bytes()).hexdigest()

    def _git(self, *args: str, check: bool = True) -> str:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            check=False,
            text=True,
        )
        if not check and result.returncode != 0:
            return ""
        if result.returncode != 0:
            raise ValueError(result.stderr.strip() or "git command failed")
        return result.stdout.strip()
