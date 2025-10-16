"""
Sandbox service for isolating and executing code submissions.
Handles compilation and execution in isolated environments.
"""

import subprocess
import logging
import shlex
import os
import random
from pathlib import Path
from typing import Dict, Any, Optional
from app.db.models import SubmissionStatus

logger = logging.getLogger(__name__)


class SandboxConfig:
    """Configuration for sandbox execution environment."""

    def __init__(
        self,
        isolate_binary: str = "/usr/local/bin/isolate",
        cpu_time_limit: float = 2.0,
        cpu_extra_time: float = 0.5,
        wall_time_limit: float = 5.0,
        memory_limit: int = 128000,
        max_processes: int = 128,
        max_file_size: int = 10240,
        enable_per_process_time_limit: bool = False,
        enable_per_process_memory_limit: bool = False,
        redirect_stderr_to_stdout: bool = False,
        enable_network: bool = False,
    ):
        """
        Initializes sandbox configuration.

        Args:
            isolate_binary: Path to isolate binary.
            cpu_time_limit: CPU time limit in seconds.
            cpu_extra_time: Extra time before killing program when limit exceeded.
            wall_time_limit: Wall clock time limit in seconds.
            memory_limit: Memory limit in KB.
            max_processes: Maximum number of processes.
            max_file_size: Maximum file size in KB.
            enable_per_process_time_limit: Apply time limit per process/thread.
            enable_per_process_memory_limit: Apply memory limit per process/thread.
            redirect_stderr_to_stdout: Redirect stderr to stdout.
            enable_network: Enable network access.
        """
        self.isolate_binary = isolate_binary
        self.cpu_time_limit = cpu_time_limit
        self.cpu_extra_time = cpu_extra_time
        self.wall_time_limit = wall_time_limit
        self.memory_limit = memory_limit
        self.max_processes = max_processes
        self.max_file_size = max_file_size
        self.enable_per_process_time_limit = enable_per_process_time_limit
        self.enable_per_process_memory_limit = enable_per_process_memory_limit
        self.redirect_stderr_to_stdout = redirect_stderr_to_stdout
        self.enable_network = enable_network


class SandboxService:
    """Manages code execution in isolated sandbox environment."""

    def __init__(self, config: SandboxConfig, box_id: Optional[int] = None):
        """
        Initializes service with configuration.

        Args:
            config: Sandbox configuration instance.
            box_id: Isolate box ID to use. If None, will be auto-assigned.
        """
        self.config = config
        self.box_path: Optional[Path] = None
        self.assigned_box_id: Optional[int] = box_id
        self.box_id: Optional[str] = None

    @staticmethod
    def get_box_id_from_worker_name() -> Optional[int]:
        """
        Extracts box ID from RQ worker name.
        Assumes worker name format: worker-N where N is the box ID.

        Returns:
            Optional[int]: Box ID if extracted successfully, None otherwise.
        """
        worker_name = os.environ.get("RQ_WORKER_NAME", "")

        if worker_name.startswith("worker-"):
            try:
                return int(worker_name.split("-")[1])
            except (IndexError, ValueError):
                pass

        return None

    @staticmethod
    def get_available_box_id() -> int:
        """
        Gets an available box ID by checking which boxes are in use.
        Falls back to random ID if detection fails.

        Returns:
            int: An available box ID (0-999).
        """
        used_boxes = set()
        isolate_base = Path("/var/local/lib/isolate")

        if isolate_base.exists():
            for box_dir in isolate_base.iterdir():
                if box_dir.is_dir() and box_dir.name.isdigit():
                    used_boxes.add(int(box_dir.name))

        for box_id in range(1000):
            if box_id not in used_boxes:
                return box_id

        return random.randint(0, 999)

    def determine_box_id(self) -> int:
        """
        Determines which box ID to use for this execution.
        Priority: assigned_box_id > worker_name > available_box

        Returns:
            int: Box ID to use.
        """
        if self.assigned_box_id is not None:
            return self.assigned_box_id

        worker_box_id = self.get_box_id_from_worker_name()
        if worker_box_id is not None:
            return worker_box_id

        box_id = self.get_available_box_id()
        logger.info(f"Using auto-assigned box ID {box_id}")
        return box_id

    def initialize(self) -> None:
        """
        Initializes sandbox environment with determined box ID.

        Raises:
            RuntimeError: If sandbox initialization fails.
        """
        determined_box_id = self.determine_box_id()
        init_cmd = [
            self.config.isolate_binary,
            f"--box-id={determined_box_id}",
            "--init",
        ]
        result = subprocess.run(init_cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Failed to initialize sandbox: {result.stderr}")

        box_path_str = result.stdout.strip()
        self.box_path = Path(box_path_str) / "box"
        self.box_id = Path(box_path_str).name
        logger.info(f"Sandbox initialized: {self.box_path}")

    def prepare_source_file(
        self, source_code: str, filename: str, extension: str
    ) -> Path:
        """
        Writes source code to file in sandbox.

        Args:
            source_code: The source code content.
            filename: Base filename without extension.
            extension: File extension.

        Returns:
            Path: Path to created source file.
        """
        full_filename = filename + extension
        source_file = self.box_path / full_filename
        source_file.write_text(source_code)
        return source_file

    def prepare_stdin(self, stdin: str) -> Path:
        """
        Writes stdin data to file in sandbox.

        Args:
            stdin: Standard input content.

        Returns:
            Path: Path to stdin file.
        """
        stdin_file = self.box_path / "stdin.txt"
        stdin_file.write_text(stdin or "")
        return stdin_file

    def compile(self, compile_command: str) -> Dict[str, Any]:
        """
        Compiles source code in sandbox.

        Args:
            compile_command: Shell command for compilation.

        Returns:
            Dict[str, Any]: Compilation result with status, stdout, stderr, and meta.
        """
        compile_meta_file = self.box_path / "compile_meta.txt"

        compile_cmd_list = [
            self.config.isolate_binary,
            f"--box-id={self.box_id}",
            f"--meta={compile_meta_file}",
            "--full-env",
            f"--time={self.config.cpu_time_limit}",
            f"--extra-time={self.config.cpu_extra_time}",
            f"--wall-time={self.config.wall_time_limit}",
            f"--mem={self.config.memory_limit}",
            f"--processes={self.config.max_processes}",
            f"--fsize={self.config.max_file_size}",
        ]

        if self.config.enable_per_process_time_limit:
            compile_cmd_list.append("--cg-timing")

        if self.config.enable_per_process_memory_limit:
            compile_cmd_list.append("--cg-mem")

        if self.config.enable_network:
            compile_cmd_list.append("--share-net")

        compile_cmd_list.extend(
            [
                "--stdout=compile_stdout.txt",
                "--stderr=compile_stderr.txt",
                "--run",
                "--",
            ]
        )
        compile_cmd_list.extend(shlex.split(compile_command))

        logger.info(f"Compiling with command: {' '.join(compile_cmd_list)}")
        compile_result = subprocess.run(
            compile_cmd_list, capture_output=True, text=True
        )

        compile_stdout_file = self.box_path / "compile_stdout.txt"
        compile_stderr_file = self.box_path / "compile_stderr.txt"

        compile_stdout = (
            compile_stdout_file.read_text() if compile_stdout_file.exists() else ""
        )
        compile_stderr = (
            compile_stderr_file.read_text() if compile_stderr_file.exists() else ""
        )

        meta_dict = {}
        if compile_meta_file.exists():
            meta_data = compile_meta_file.read_text()
            for line in meta_data.strip().split("\n"):
                if ":" in line:
                    key, value = line.strip().split(":", 1)
                    meta_dict[key] = value

        return {
            "success": compile_result.returncode == 0,
            "stdout": compile_stdout,
            "stderr": compile_stderr,
            "meta": meta_dict,
        }

    def execute(self, run_command: str, language_name: str = "") -> Dict[str, Any]:
        """
        Executes code in sandbox.

        Args:
            run_command: Shell command for execution.
            language_name: Name of programming language (for filtering output).

        Returns:
            Dict[str, Any]: Execution result with stdout, stderr, and meta.
        """
        meta_file = self.box_path / "meta.txt"

        run_cmd_list = [
            self.config.isolate_binary,
            f"--box-id={self.box_id}",
            f"--meta={meta_file}",
            "--full-env",
            f"--time={self.config.cpu_time_limit}",
            f"--extra-time={self.config.cpu_extra_time}",
            f"--wall-time={self.config.wall_time_limit}",
            f"--mem={self.config.memory_limit}",
            f"--processes={self.config.max_processes}",
            f"--fsize={self.config.max_file_size}",
        ]

        if self.config.enable_per_process_time_limit:
            run_cmd_list.append("--cg-timing")

        if self.config.enable_per_process_memory_limit:
            run_cmd_list.append("--cg-mem")

        if self.config.enable_network:
            run_cmd_list.append("--share-net")

        run_cmd_list.extend(
            [
                "--stdin=stdin.txt",
                "--stdout=stdout.txt",
            ]
        )

        if self.config.redirect_stderr_to_stdout:
            run_cmd_list.append("--stderr=stdout.txt")
        else:
            run_cmd_list.append("--stderr=stderr.txt")

        run_cmd_list.extend(
            [
                "--run",
                "--",
            ]
        )
        run_cmd_list.extend(shlex.split(run_command))

        logger.info(f"Executing with command: {' '.join(run_cmd_list)}")
        subprocess.run(run_cmd_list, capture_output=True, text=True)

        stdout_file = self.box_path / "stdout.txt"
        stderr_file = self.box_path / "stderr.txt"

        stdout_txt = stdout_file.read_text() if stdout_file.exists() else ""
        stderr_txt = (
            ""
            if self.config.redirect_stderr_to_stdout
            else (stderr_file.read_text() if stderr_file.exists() else "")
        )

        if (
            language_name.lower() == "node.js"
            and not self.config.redirect_stderr_to_stdout
        ):
            stderr_txt = stderr_txt.replace(
                "Warning: disabling flag --expose_wasm due to conflicting flags\n", ""
            )

        meta_dict = {}
        if meta_file.exists():
            meta_data = meta_file.read_text()
            for line in meta_data.strip().split("\n"):
                if ":" in line:
                    key, value = line.strip().split(":", 1)
                    meta_dict[key] = value

        return {
            "stdout": stdout_txt,
            "stderr": stderr_txt,
            "meta": meta_dict,
        }

    def cleanup(self) -> None:
        """Cleans up sandbox environment."""
        if self.box_id:
            cleanup_cmd = [
                self.config.isolate_binary,
                f"--box-id={self.box_id}",
                "--cleanup",
            ]
            subprocess.run(cleanup_cmd, capture_output=True)
