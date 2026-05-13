import os
import subprocess

class Analyzer:
    def __init__(self):
        pass

    def handler(self, repo_path):
        os.makedirs(os.path.join(repo_path, "reports"), exist_ok=True)
        report_path = os.path.join(repo_path, "reports")
        return self._security_analyzer(repo_path, report_path)

    def _security_analyzer(self, repo_path, report_path):
        
        path_list = []
        for i in ['p_security-audit', 'p_ci', 'auto']:
        
            output_file = os.path.join(report_path, f"{i}.json")
            proc = subprocess.run(
                [
                    "semgrep",
                    "scan",
                    f"--config={i.replace("_", "/")}",
                    "--json",
                    "--output",
                    str(output_file),
                    repo_path
                ],
                capture_output=True,
                encoding="utf-8",
                text=True,
                errors="ignore"
            )

            if proc.returncode not in [0, 1]:
                print("\n=== SEMGREP STDOUT ===")
                print(proc.stdout)

                print("\n=== SEMGREP STDERR ===")
                print(proc.stderr)

                print("\n=== RETURN CODE ===")
                print(proc.returncode)
                raise Exception("Semgrep scan failed")
            
            path_list.append(output_file)

        return ','.join(path_list)