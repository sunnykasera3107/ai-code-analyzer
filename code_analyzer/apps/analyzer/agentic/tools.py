import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*allowed_objects.*")

import json
import os
from langchain.tools import tool
from apps.analyzer.services.cloner import Cloner
from apps.analyzer.services.scanner import Scanner
from apps.analyzer.services.analyzer import Analyzer
from apps.analyzer.services.lang_parser import LangParser
from apps.analyzer.services.embedder import Embedder
from apps.analyzer.services.storage import Storage

@tool
def repo_cloner(repo_url):
    '''Clones the git repository to local folder
    Args:
        repo_url: Repository URL for cloning
    Return: Local repository path
    '''
    _cloner = Cloner()
    repo_path = _cloner.handler(repo_url)
    repo_path = repo_path.replace("\\\\", "/").replace("\\", "/")
    return repo_path

@tool
def scanner(repo_dir):
    '''Scans all files of local repostory
    Args:
        repo_dir: Local repository path
    Return: scanned report file path
    '''
    _scanner = Scanner()
    response = _scanner.handler(repo_dir)
    print("response ascan:", response)
    return response

@tool
def file_reader(scanned_doc_path):
    '''Load the json file and extract document path from json
    then reads the document content and respond
    Args:
        scanned_doc_path: json file path
    Return: Content of project doc file.
    '''
    print("==== file reader ----", scanned_doc_path)
    with open(scanned_doc_path, "r", encoding='utf-8') as f:
        scan_data = json.load(f)
    
    items = scan_data['project_doc']
    print(items)
    file_list = [os.path.join(item['dir'], item['file']) for item in items]
    print(file_list)
    content = []
    for file in file_list:
        print(file)
        extension = file.split(".")[-1]
        print(extension)
        encoding_types = ['utf-8', 'utf-16', 'latin-1', 'ascii']
        for encoding_type in encoding_types:
            try:
                with open(file, "r", encoding=encoding_type) as f:
                    if extension == "json":
                        content.append(json.dumps(json.load(f)))
                    else:
                        file_content = f.read()
                        content.append(file_content)
                    print(content)
                    break
            except Exception as e:
                print(e)

    merged_content = " ".join(content)
    print("file_content", merged_content)
    response_content = _cleaner(merged_content)
    return response_content

@tool
def code_analyzer(repo_path):
    '''Analyzes code using various libs and store analysis report in folder
    Args:
        repo_path: repository path string
    Return: Content of given documents as text string
    '''
    analyzer = Analyzer()
    return analyzer.handler(repo_path)

@tool
def code_parser(scanned_doc_path):
    '''Read the json file on the given path.
    Fetch path of code files and read code as string.
    Parse the code using language parser.
    Arg:
        scanned_doc_path: json file path
    Return: code analysis doc path comma separated.
    '''
    with open(scanned_doc_path, "r") as f:
        doc_content = json.load(f)

    code_files_obj = doc_content['code_data']
    _parser = LangParser()
    parsed_data = _parser.handler(code_files_obj)

    _embedder = Embedder()
    embedded_data = _embedder.handler(parsed_data)

    code_analysis_doc = os.path.dirname(scanned_doc_path)
    collection_name = code_analysis_doc.split("/")[-1]
    
    _storage = Storage(collection_name)
    _storage.handler(embedded_data)

    with open(os.path.join(code_analysis_doc, 'code_analysis.json'), "w") as f:
        json.dump(parsed_data, f)
    return code_analysis_doc

def _cleaner(query):
    query = query.replace(r"(\\x00[A-Za-z0-9=\\n.#\s-]*)", "")
    query = query.replace("\n\n", "")
    query = query.replace("ÿþ#ÿþ", "")
    return query.replace(r"\n*", "")