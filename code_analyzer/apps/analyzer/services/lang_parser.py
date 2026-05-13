import os
from tree_sitter import Parser, Language
import tree_sitter_python
import tree_sitter_javascript
import tree_sitter_php

class LangParser:
    '''Parse different language and create tree sitter dict for each
    '''
    _parser_list = {}

    def __init__(self):
        self._extractors = {
            'python': self._extractor_python,
            'javascript': self._extractor_javascript,
            'php': self._extractor_php,
        }

        self._languages = {
            'python': tree_sitter_python.language(),
            'javascript': tree_sitter_javascript.language(),
            'php': tree_sitter_php.language_php(),
        }

        print(self._languages)

        self._chunk_type = [
            "class_definition",
            "class_declaration",
            "function_definition",
            "function_declaration",
            "method_definition",
            "arrow_function",
            "interface_declaration",
            "trait_declaration",
        ]

    def handler(self, file_list: list):
        extracted = []
        for file_obj in file_list:
            try:
                parsed_set = self._parse_file(file_obj)
                if file_obj['language'] in self._extractors:
                    extracted.append(self._extractors[file_obj['language']](
                        parsed_set[-1].root_node, 
                        parsed_set[0]
                    ))
            except Exception as e:
                print(f"Error parsing file {file_obj.get('file')}: {e}")
                continue
        return [item for item in extracted if item is not None]

    def _parse_file(self, file_obj: dict):
        language = file_obj['language']
        if language not in self._parser_list.keys():
            try:
                # Try newer API: get_language returns a Language object that can be used directly
                parser = Parser()
                PY_LANGUAGE = Language(self._languages[language])
                parser.language = PY_LANGUAGE
                self._parser_list[language] = parser
                print("\n=== PARSER DEBUG ===")
                print("Language:", language)
                print("Parser object:", self._parser_list[language])
                print("Parser type:", type(self._parser_list[language]))
                print("Has parse:", hasattr(self._parser_list[language], "parse"))
                print("====================\n")
            except TypeError as e:
                print(f"Error loading parser for {language}: {e}")


        file_path = os.path.join(file_obj['dir'], file_obj['file'])
        with open(file_path, "rb") as f:
            code = f.read()
        return [{"dir": file_obj["dir"], "file": file_obj["file"]}, self._parser_list[language].parse(code)]
    
    def _extractor_javascript(self, node, file_name):
        if node.type == "program":
            dependencies = []
            chunks = []
            exports_list = []
            for child in node.children:
                if child.type == "import_statement":
                    source_node = child.child_by_field_name("source")
                    path = source_node.text.decode()
                    dependencies.append(path[1:-1])
                    continue

                if child.type == "export_statement":
                    source_node = child.child_by_field_name("identifier")
                    if source_node:
                        path = source_node.text.decode()
                        exports_list.append(path[1:-1])
                    continue
                
                if child.type in self._chunk_type:
                    function_name = child.child_by_field_name("name").text.decode()
                    code = child.text.decode()
                    chunk_type = child.type.split("_")
                    chunks.append({
                        "name": function_name,
                        "chunk_type": chunk_type[0],
                        "code": code[:4000]
                    })
                    continue
            if len(chunks) == 0:
                return
            
            return {
                "file_name": file_name['file'],
                "dependencies": dependencies,
                "dir": file_name['dir'],
                "chunks": chunks,
                "exports": exports_list
            }
        return

    def _extractor_python(self, node, file_name: str):
        if node.type == "module":
            dependencies = []
            chunks = []
            for child in node.children:
                if child.type == "decorated_definition":
                    for c in child.children:
                        if c.type in self._chunk_type:
                            name_node = c.child_by_field_name("name")
                            function_name = name_node.text.decode()
                            code = c.text.decode()
                            chunk_type = c.type.split("_")
                            chunks.append({
                                "name": function_name,
                                "chunk_type": chunk_type[0],
                                "code": code[:4000]
                            })
                            continue

                if child.type in ["import_statement", "import_from_statement"]:
                    names = ""
                    import_state = False
                    for c in child.children:
                        if c.type == "dotted_name":
                            c_name = c.text.decode()
                            if c_name in ["from", "import", ","]:
                                if c_name == "import":
                                    import_state = True
                                continue
                            if not import_state and names == "":
                                name = f"{c_name}."
                                import_state = True
                                continue
                            dependencies.append(f"{name}{c_name}")
                            continue
                    continue

                if child.type in self._chunk_type:
                    name_node = child.child_by_field_name("name")
                    function_name = name_node.text.decode()
                    code = child.text.decode()
                    chunk_type = child.type.split("_")
                    chunks.append({
                        "name": function_name,
                        "chunk_type": chunk_type[0],
                        "code": code[:4000]
                    })
                    continue

            if len(chunks) == 0:
                return
            
            return {
                "file_name": file_name['file'],
                "dir": file_name['dir'],
                "dependencies": dependencies,
                "chunks": chunks,
            }
        
        return

    def _extractor_php(self, node, file_name: str):
        if node.type == "program":
            dependencies = []
            chunks = []
            for child in node.children:
                if child.type == "namespace_use_declaration":
                    for use_child in child.children:
                        if use_child.type in [
                            "qualified_name",
                            "namespace_name"
                        ]:
                            dependencies.append(
                                use_child.text.decode()
                            )
                    continue

                if child.type in self._chunk_type:
                    name_node = child.child_by_field_name("name")
                    chunk_name = name_node.text.decode()
                    code = child.text.decode()
                    chunk_type = child.type.split("_")
                    chunks.append({
                        "name": chunk_name,
                        "chunk_type": chunk_type[0],
                        "code": code[:4000]
                    })
                    continue
            
            if len(chunks) == 0:
                return
            
            return {
                "file_name": file_name['file'],
                "dir": file_name['dir'],
                "dependencies": dependencies,
                "chunks": chunks,
            }
        return