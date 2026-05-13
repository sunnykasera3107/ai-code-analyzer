import json
import os
from dotenv import load_dotenv
from typing import TypedDict
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from .tools import repo_cloner, file_reader, scanner, code_analyzer, code_parser
import tracemalloc

tracemalloc.start()
load_dotenv()

class ProjectAnalyzer(TypedDict):
    repo_url: str
    repo_path: str | None
    scanned_doc: str | None
    project_doc_content: str | None
    projuct_documents_analysis: str | dict | None
    code_analysis: str | dict | None

# llm_model = ChatGroq(
#     model="meta-llama/llama-4-scout-17b-16e-instruct",
#     temperature=0.0
# )

llm_model = init_chat_model(
    model="gemma4",
    model_provider="ollama",
)

planner_agent = create_agent(
    model=llm_model,
    tools=[repo_cloner, scanner, file_reader, code_analyzer, code_parser]
)

def _planner_node(state: ProjectAnalyzer):
    print("\n=== CALLING AGENT ===")
    cloner_result = planner_agent.invoke({
        "messages": [("user", f"Clone {state['repo_url']} return only and only local repo path and no extra text.")]
    })
    print(f"\n=== AGENT RESPONSE ===")

    # Initialize repo_path if not set
    if 'repo_path' not in state:
        state['repo_path'] = None

    for i, msg in enumerate(cloner_result['messages']):
        if hasattr(msg, 'content'):
            if os.path.exists(msg.content):
                state['repo_path'] = msg.content
    
    last_msg = cloner_result['messages'][-1]
    print("\n=== LAST MESSAGE ===")
    
    if state['repo_path'] is None or state['repo_path'] == '':
        state['repo_path'] = str(last_msg.content).strip()
    
    # if os.path.exists(state['repo_path']):
    #     shutil.rmtree(state['repo_path'])
    
    return state

def _scanner_node(state: ProjectAnalyzer):
    print("\n=== Calling Scanner Node ===")
    
    # Initialize scanned_doc if not set
    if 'scanned_doc' not in state:
        state['scanned_doc'] = None

    scanner_result = planner_agent.invoke({
        "messages": [("user", f"Scan {state['repo_path']} return only and only file path and no extra text.")]
    },  tool_choice={"type": "tool", "name": "scanner"},)

    print("==== scanner complete ----")
    for i, msg in enumerate(scanner_result['messages']):
        print(f"==== scanner loop {i} ----")
        print(f"==== scanner loop {msg.content} ----")
        if os.path.exists(msg.content):
            state['scanned_doc'] = msg.content

    if hasattr(scanner_result['messages'][-1], 'content'):
        scanned_doc_path = scanner_result['messages'][-1].content.strip()
        if os.path.exists(scanned_doc_path):
            state['scanned_doc'] = scanned_doc_path
    
    print("\n=== Call Scanner Node End ===")
    return state

def _info_extractor(state: ProjectAnalyzer):
    print("\n=== Fetching project document ===")
    
    # Validate scanned_doc path exists
    if not state.get('scanned_doc') or not os.path.exists(state['scanned_doc']):
        print(f"ERROR: Invalid scanned_doc path: {state.get('scanned_doc')}")
        state['project_doc_content'] = ''
        return state
    
    doc_content = planner_agent.invoke({
        "messages": [("user", f'''Read the file at {state['scanned_doc']}  and stop immediately after getting the result.
Use only file_reader tool to read each documentation file.
Return only the response from file_reader tool.
                      Dont add any extra text to content. e.g. "The file reader tool has provided response"''')]
    }, tool_choice={"type": "tool", "name": "file_reader"},
    config={"recursion_limit": 5}
    )
    
    print("\n=== Fetch project document end ===")
    for i, msg in enumerate(doc_content['messages']):
        if msg.content != '' and len(msg.content) > 10:
            state['project_doc_content'] = msg.content
    return state

def _doc_analyzer(state: ProjectAnalyzer):
    print("\n=== Analyze project document ===")
    # Project document analyzer
    project_doc_content = state['project_doc_content']
    doc_analysis = planner_agent.invoke({
        "messages": [
            (
                "user",
                f'''Extract technical stack from follwing content:
                {project_doc_content}
                Return JSON: {{"backend": "...", "frontend": "...", "dependencies": [...], "database": "...", "additional_info": "..."}}
                Return only JSON. No markdown. No explanations.'''
            )
        ]
    })

    state['projuct_documents_analysis'] = doc_analysis["messages"][-1].content
    
    # Validate scanned_doc path before writing
    if state.get('scanned_doc') and os.path.exists(state['scanned_doc']):
        try:
            with open(state['scanned_doc'], "r") as f:
                scanned_doc = json.load(f)

            scanned_doc.update({"doc_analysis": state['projuct_documents_analysis']})
            with open(state['scanned_doc'], "w") as f:        
                json.dump(scanned_doc, f)
        except Exception as e:
            print(f"Error writing doc analysis: {e}")
    else:
        print(f"ERROR: Cannot write to scanned_doc: {state.get('scanned_doc')}")

    print("\n=== Analyze project document end ===")
    return state

def _code_analyzer(state: ProjectAnalyzer):
    # Code analysizer
    print("\n=== Analyze code ===")
    analyzer_response = planner_agent.invoke({
        "messages": [("user", f"Analyze code file at: {state['repo_path']} return only report path and no extra text ")]
    })
    state['analyzer_response'] = analyzer_response['messages'][-1].content
    print("\n=== Analyze code end ===")
    return state

def _code_parser(state: ProjectAnalyzer):
    # Code Parser
    print("\n=== Parse code ===")
    scanned_doc_path = state.get('scanned_doc')
    
    # Validate scanned_doc path
    if not scanned_doc_path or not os.path.exists(scanned_doc_path):
        print(f"ERROR: Invalid scanned_doc_path: {scanned_doc_path}")
        state['code_parsed'] = ''
        return state
    
    code_parsed = planner_agent.invoke({
        "messages": [("user", f'''Read the file at {scanned_doc_path} using the code_parser tool.
                      Extract all file paths from the JSON.
                      Make chunks based on class, function etc.
                      Store the all parsing in another json file 
                      Return only the file contents.''')]
    })
    state['code_parsed'] = code_parsed['messages'][-1].content
    print("\n=== Parse code end ===")
    return state

def execute_graph(repo_url):
    
    try:
        _graph = StateGraph(ProjectAnalyzer)
        _graph.add_node("planner", _planner_node)
        _graph.add_node("scanner", _scanner_node)
        _graph.add_node("extractor", _info_extractor)
        _graph.add_node("doc_analyzer", _doc_analyzer)
        _graph.add_node("code_analyzer", _code_analyzer)
        _graph.add_node("code_parser", _code_parser)
        _graph.add_edge(START, 'planner')
        _graph.add_edge('planner', 'scanner')
        _graph.add_edge('scanner', 'extractor')
        _graph.add_edge('extractor', 'doc_analyzer')
        _graph.add_edge('doc_analyzer', 'code_analyzer')
        _graph.add_edge('code_analyzer', 'code_parser')
        _graph.add_edge('code_parser', END)
        _compiled = _graph.compile()
        response = _compiled.invoke({
            "repo_url": repo_url
        })

        print(response)
        return response
    except Exception as e:
        import traceback
        print("Graph Invoke Error: ", e)
        print("\n=== Full Traceback ===")
        traceback.print_exc()
        print("=== End Traceback ===")

if __name__ == "__main__":
    # Get snapshot to see memory allocation
    current, peak = tracemalloc.get_traced_memory()
    print(f"Current memory: {current / 1024 / 1024:.1f} MB")
    print(f"Peak memory: {peak / 1024 / 1024:.1f} MB")
    tracemalloc.stop()