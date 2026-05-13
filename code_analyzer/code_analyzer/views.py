import json
import os
from django.shortcuts import render, redirect
from apps.analyzer.agentic import graph
from apps.analyzer.models import Repository
from apps.analyzer.services.storage import Storage
from apps.analyzer.services.embedder import Embedder

def home(request):
    user = request.user
    if not user.is_authenticated:
        return redirect('auth/login')
    
    if request.method == "POST":
        data = request.POST
        repo_url = data['repo_url']
        _pull_repo(request, repo_url)        
        response_data = _get_all_repository(user)
        return render(request, 'index.html', {
            "items": response_data
        })

    response_data = _get_all_repository(user)
    return render(request, 'index.html', {
        "items": response_data
    })


def repo_review(request, repo_name):
    user = request.user
    if not user.is_authenticated:
        return redirect('auth/login')
    
    methods_list = []
    if request.method == "POST":
        data = request.POST
        if 'pull_repo' in data:
            repo_url = data['repo_url']
            _pull_repo(request, repo_url)

        if 'search' in data and 'query' in data:
            query = data['query']
            embedder = Embedder()
            embeddings = embedder.encode(query)
            storage = Storage(repo_name)
            response = storage.finder({
                'embedding': embeddings,
                'number_of_results': 5
            })
            for i, dis in enumerate(response['distances'][0]):
                distance = (dis - 1) if dis > 1 else (dis)
                if distance > 0.5:
                    methods_list.append({
                        "id": response['ids'][0][i],
                        "code": response['documents'][0][i],
                    })

    repo = Repository.objects.filter(
        repo_name=repo_name
    ).first()

    if repo is None:
        return render(request, 'repository-review.html', {
            "error": "This repository not found in the record. Pull this repository again."
        })

    repo_path = os.path.join(os.getenv("LOCAL_DATA_PATH"), 'temp/git/')
    repo_path = os.path.join(repo_path, repo_name)

    scan_report_content = None
    scan_report_path = os.path.join(repo_path, 'scan_report.json')
    if os.path.exists(scan_report_path):
        with open(scan_report_path, 'r') as f:
            scan_report_content = json.load(f)

    backend, frontend, dependencies, database = None, None, None, None
    if scan_report_content is not None and 'doc_analysis' in scan_report_content:
        doc_analysis = (scan_report_content['doc_analysis'])
        doc_analysis = json.loads(doc_analysis.replace("```json", "").replace("```", ""))
        backend = doc_analysis['backend'] if type(doc_analysis['backend']) is list else doc_analysis['backend'].split(",")
        frontend = doc_analysis['frontend'] if type(doc_analysis['frontend']) is list else (doc_analysis['frontend'].split(",") if len(doc_analysis['frontend']) > 1 else None)
        dependencies = doc_analysis['dependencies']
        database = doc_analysis['database'] if type(doc_analysis['database']) is list else doc_analysis['database'].split(",")

    security_path = os.path.join(repo_path, 'reports/p_security-audit.json')
    report_items = []
    if os.path.exists(security_path):
        with open(security_path, 'r') as f:
            security_content = json.load(f)
        for item in security_content['results']:
            report_items.append({
                "type": item['extra']['severity'],
                "message": item['extra']['message'],
                "path": item['path'],
                "line": item['start']['line'],
                "category": item['extra']['metadata']['category'],
                "severity": item['extra']['metadata']['confidence'],
            })
   
    return render(request, 'repository-review.html', {
        "repo_name": repo_name,
        "repo_url": repo.repo_url,
        "backend": backend,
        "frontend": frontend,
        "dependencies": dependencies,
        "database": database,
        "report_items": report_items,
        "method_list": methods_list
    })

def _pull_repo(request, repo_url):
    user = request.user
    repo_name = repo_url.split("/")[-1].split(".")[0]
    repo_data = Repository.objects.filter(
        repo_name=repo_name,
        user=user
    ).first()
    if repo_data is None:
        repo = Repository()
        repo.repo_name = repo_name
        repo.repo_url = repo_url
        repo.user = user
        repo.save()
    extension = repo_url.split(".")[-1]
    if extension == "":
        repo_url = f"{repo_url}.git"
    graph.execute_graph(repo_url)


def _get_all_repository(user):
    repos = Repository.objects.filter(
        user=user
    )
    response_data = []
    for repo in repos:
        response_data.append({
            "id": repo.id,
            "repo_name": repo.repo_name,
            "repo_url": repo.repo_url,
        })

    return response_data