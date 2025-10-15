import subprocess
import os
import logging
import shlex
from pathlib import Path
from app.db_utils import (
    get_db_session,
    update_submission_status,
    update_submission_result,
)
from app.db.models import SubmissionStatus

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Configuration
ISOLATE_BINARY = "/usr/local/bin/isolate"
TIME_LIMIT = 2  # seconds
WALL_TIME_LIMIT = 5  # seconds
MEMORY_LIMIT = 128000  # KB


def process_submission(submission_data: dict, language_data: dict):
    submission_id = submission_data.get("id")
    source_code = submission_data.get("source_code", "")
    stdin = submission_data.get("stdin", "")
    language = language_data

    if not all([submission_id, source_code is not None, language]):
        return {"error": "Invalid submission data"}

    with get_db_session() as db:
        try:
            # Update submission status to 'processing'
            update_submission_status(db, submission_id, SubmissionStatus.PROCESSING)

            # Initialize sandbox
            init_cmd = [ISOLATE_BINARY, "--init"]
            result = subprocess.run(init_cmd, capture_output=True, text=True)

            # Extract box path from the output
            box_path_str = result.stdout.strip()
            box_path = Path(box_path_str) / "box"

            # Prepare source code file
            filename = language["file_name"] + language["file_extension"]
            source_file = box_path / filename
            source_file.write_text(source_code)

            # Prepare stdin
            stdin_file = Path(box_path) / "stdin.txt"
            stdin_file.write_text(stdin or "")

            # Compile if necessary
            if language.get("compile_command"):
                compile_cmd = language["compile_command"]

                compile_meta_file = Path(box_path) / "compile_meta.txt"
                compile_cmd_list = [
                    ISOLATE_BINARY,
                    f"--box-id={os.path.basename(box_path_str)}",
                    f"--meta={compile_meta_file}",
                    "--full-env",
                    f"--time={TIME_LIMIT}",
                    f"--wall-time={WALL_TIME_LIMIT}",
                    f"--mem={MEMORY_LIMIT}",
                    "--processes=128",
                    "--stdout=compile_stdout.txt",
                    "--stderr=compile_stderr.txt",
                    "--run",
                    "--",
                ]
                compile_cmd_list.extend(shlex.split(compile_cmd))
                logger.info(f"Compiling with command: {' '.join(compile_cmd_list)}")
                compile_result = subprocess.run(
                    compile_cmd_list, capture_output=True, text=True
                )

                # Check compilation result
                if compile_result.returncode != 0:
                    compile_stdout = (Path(box_path) / "compile_stdout.txt").read_text()
                    compile_stderr = (Path(box_path) / "compile_stderr.txt").read_text()
                    compile_meta_data = (compile_meta_file).read_text()

                    compile_meta_dict = dict(
                        line.strip().split(":")
                        for line in compile_meta_data.strip().split("\n")
                    )

                    update_submission_result(
                        db,
                        submission_id=submission_id,
                        status=SubmissionStatus.ERROR,
                        stdout=compile_stdout,
                        stderr=compile_stderr,
                        meta=compile_meta_dict,
                    )
                    return {
                        "result": "compile_error",
                        "stdout": compile_stdout,
                        "stderr": compile_stderr,
                        "meta": compile_meta_dict,
                    }

            # Run the code inside the sandbox
            run_cmd = language["run_command"]

            meta_file = Path(box_path) / "meta.txt"
            run_cmd_list = [
                ISOLATE_BINARY,
                f"--box-id={os.path.basename(box_path_str)}",
                f"--meta={meta_file}",
                "--full-env",
                f"--time={TIME_LIMIT}",
                f"--wall-time={WALL_TIME_LIMIT}",
                f"--mem={MEMORY_LIMIT}",
                "--processes=128",
                "--stdin=stdin.txt",
                "--stdout=stdout.txt",
                "--stderr=stderr.txt",
                "--run",
                "--",
            ]
            run_cmd_list.extend(shlex.split(run_cmd))
            subprocess.run(run_cmd_list, capture_output=True, text=True)

            # Analyze results
            stdout_txt = (Path(box_path) / "stdout.txt").read_text()
            stderr_txt = (Path(box_path) / "stderr.txt").read_text()
            meta_data = (meta_file).read_text()

            if language["name"].lower() == "node.js":
                stderr_txt = stderr_txt.replace(
                    "Warning: disabling flag --expose_wasm due to conflicting flags\n",
                    "",
                )

            meta_dict = dict(
                line.strip().split(":") for line in meta_data.strip().split("\n")
            )

            update_submission_result(
                db,
                submission_id=submission_id,
                status=SubmissionStatus.FINISHED,
                stdout=stdout_txt,
                stderr=stderr_txt,
                meta=meta_dict,
            )
            return {
                "result": "success",
                "stdout": stdout_txt,
                "stderr": stderr_txt,
                "meta": meta_dict,
            }

        except Exception as e:
            update_submission_result(
                db,
                submission_id=submission_id,
                status=SubmissionStatus.ERROR,
                stdout="",
                stderr=str(e),
                meta={"error": "Worker exception"},
            )
            return {"error": "Unexpected error", "details": str(e)}

        finally:
            # Cleanup the sandbox
            if box_path:
                cleanup_cmd = [
                    ISOLATE_BINARY,
                    f"--box-id={os.path.basename(box_path_str)}",
                    "--cleanup",
                ]
                subprocess.run(cleanup_cmd)
