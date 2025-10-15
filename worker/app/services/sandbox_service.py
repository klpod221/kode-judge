"""
Sandbox service for isolating and executing code submissions.
Handles compilation and execution in isolated environments.
"""
import subprocess
import logging
import shlex
from pathlib import Path
from typing import Dict, Any, Optional
from app.db.models import SubmissionStatus

logger = logging.getLogger(__name__)


class SandboxConfig:
    """Configuration for sandbox execution environment."""
    
    def __init__(
        self,
        isolate_binary: str = "/usr/local/bin/isolate",
        time_limit: int = 2,
        wall_time_limit: int = 5,
        memory_limit: int = 128000,
        processes: int = 128,
    ):
        """
        Initializes sandbox configuration.
        
        Args:
            isolate_binary: Path to isolate binary.
            time_limit: CPU time limit in seconds.
            wall_time_limit: Wall clock time limit in seconds.
            memory_limit: Memory limit in KB.
            processes: Maximum number of processes.
        """
        self.isolate_binary = isolate_binary
        self.time_limit = time_limit
        self.wall_time_limit = wall_time_limit
        self.memory_limit = memory_limit
        self.processes = processes


class SandboxService:
    """Manages code execution in isolated sandbox environment."""
    
    def __init__(self, config: SandboxConfig):
        """
        Initializes service with configuration.
        
        Args:
            config: Sandbox configuration instance.
        """
        self.config = config
        self.box_path: Optional[Path] = None
        self.box_id: Optional[str] = None
    
    def initialize(self) -> None:
        """
        Initializes sandbox environment.
        
        Raises:
            RuntimeError: If sandbox initialization fails.
        """
        init_cmd = [self.config.isolate_binary, "--init"]
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
            f"--time={self.config.time_limit}",
            f"--wall-time={self.config.wall_time_limit}",
            f"--mem={self.config.memory_limit}",
            f"--processes={self.config.processes}",
            "--stdout=compile_stdout.txt",
            "--stderr=compile_stderr.txt",
            "--run",
            "--",
        ]
        compile_cmd_list.extend(shlex.split(compile_command))
        
        logger.info(f"Compiling with command: {' '.join(compile_cmd_list)}")
        compile_result = subprocess.run(compile_cmd_list, capture_output=True, text=True)
        
        compile_stdout = (self.box_path / "compile_stdout.txt").read_text()
        compile_stderr = (self.box_path / "compile_stderr.txt").read_text()
        
        meta_dict = {}
        if compile_meta_file.exists():
            meta_data = compile_meta_file.read_text()
            meta_dict = dict(
                line.strip().split(":", 1) for line in meta_data.strip().split("\n")
            )
        
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
            f"--time={self.config.time_limit}",
            f"--wall-time={self.config.wall_time_limit}",
            f"--mem={self.config.memory_limit}",
            f"--processes={self.config.processes}",
            "--stdin=stdin.txt",
            "--stdout=stdout.txt",
            "--stderr=stderr.txt",
            "--run",
            "--",
        ]
        run_cmd_list.extend(shlex.split(run_command))
        
        logger.info(f"Executing with command: {' '.join(run_cmd_list)}")
        subprocess.run(run_cmd_list, capture_output=True, text=True)
        
        stdout_txt = (self.box_path / "stdout.txt").read_text()
        stderr_txt = (self.box_path / "stderr.txt").read_text()
        
        if language_name.lower() == "node.js":
            stderr_txt = stderr_txt.replace(
                "Warning: disabling flag --expose_wasm due to conflicting flags\n", ""
            )
        
        meta_dict = {}
        if meta_file.exists():
            meta_data = meta_file.read_text()
            meta_dict = dict(
                line.strip().split(":", 1) for line in meta_data.strip().split("\n")
            )
        
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
            logger.info(f"Sandbox cleaned up: {self.box_id}")
