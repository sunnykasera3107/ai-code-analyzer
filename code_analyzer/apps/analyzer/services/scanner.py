import json
import os
import yaml
from pathlib import Path

class Scanner:
    '''Scans all files in the given dir and prepare metadata list for each file.
    '''
    def __init__(self):
        with open("apps/analyzer/config.yaml", "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f)

    def handler(self, repo_dir: str):
        if not os.path.exists(repo_dir):
            raise FileExistsError("Directory does not exist.")
        
        report_filename = "scan_report.json"
        print("Scanned report")
        response = self._inner_items(repo_dir)
        scanned_file = os.path.join(repo_dir, report_filename)
        with open(scanned_file, "w") as f:
            json.dump(response, f)
        print("Scanned report saved", scanned_file)
        return scanned_file

    def _inner_items(self, directory: str):
        code = []
        project_doc = []
        items = [str(p.resolve()) for p in Path(directory).rglob("*") if p.is_file()]

        results = [self._process_item(item) for item in items]

        for result in results:
            if result is None:
                continue
            try:
                if result["is_code"]:
                    code.append(result)
                else:
                    project_doc.append(result)
            except Exception as e:
                print("Error Code: ", e)

        return {"project_doc": project_doc, "code_data": code}

    def _process_item(self, item_path):
        item = item_path.split("\\")[-1]
        directory = item_path.replace(f"\\{item}", "")
        if item in self._config['skips']:
            return
        
        response = ""
        if os.path.isdir(item_path):
            response = self._inner_items(item_path)
            return response
        else:
            extension = item.split(".")[-1]
            if extension in self._config['language'].keys():
                response = {
                    "file": item,
                    "dir": directory,
                    "file_path": item_path,
                    "size": os.path.getsize(item_path),
                    "language": self._config['language'][extension],
                    "is_code": True
                }
                return response
                # metadata.append(response)

            if item.lower() in ['requirements.txt', 'package.json', 'composer.json']:
                response = {
                    "file": item,
                    "dir": directory,
                    "file_path": item_path,
                    "size": os.path.getsize(item_path),
                    "is_code": False
                }
                return response
            
            return