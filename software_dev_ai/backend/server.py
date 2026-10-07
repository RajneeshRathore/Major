import sys
import os
import uuid
import json
import time
import threading
import traceback

from flask import Flask, request, jsonify, Response
from flask_cors import CORS

# Ensure the backend directory is on sys.path so agent imports work
sys.path.insert(0, os.path.dirname(__file__))

from graph import dev_graph
from tools.file_tools import list_files, read_file


# ─────────────────────────────────────────────
# FLASK APP
# ─────────────────────────────────────────────

from models import db, Project

app = Flask(__name__)
CORS(app)  # Allow frontend on a different port

# Configure SQLite Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///devagent.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create tables if they don't exist
with app.app_context():
    db.create_all()


# ─────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


# ─────────────────────────────────────────────
# GENERATE PROJECT
# ─────────────────────────────────────────────

@app.route("/api/generate", methods=["POST"])
def generate_project():
    """
    Accept a user requirement and start the multi-agent pipeline in the background.

    Request body (JSON):
        { "requirement": "Build a REST API for ..." }

    Response (JSON):
        { "project_id": "...", "status": "STARTED" }
    """
    data = request.get_json(force=True)
    requirement = data.get("requirement", "").strip()

    if not requirement:
        return jsonify({"error": "requirement is required"}), 400

    project_id = f"project_{uuid.uuid4().hex[:8]}"
    
    # Save a pending project to DB
    new_project = Project(id=project_id, name=f"Project {project_id}", status="STARTED")
    db.session.add(new_project)
    db.session.commit()

    initial_state = {
        "project_id": project_id,
        "user_requirement": requirement,
        "plan": {},
        "files": {},
        "test_result": {},
        "environment": {},
        "runtime_result": {},
        "review_result": "",
        "errors": [],
        "iteration": 0,
        "status": "STARTED",
    }

    def run_graph_in_background(app_obj, p_id, state):
        with app_obj.app_context():
            try:
                config = {"configurable": {"thread_id": p_id}}
                final_state = dev_graph.invoke(state, config=config)
                
                # Check if it was interrupted
                current_state = dev_graph.get_state(config)
                if current_state.next:
                    # It is interrupted (e.g. before 'wait_for_approval')
                    project = db.session.get(Project,p_id)
                    if project:
                        project.status = "WAITING_FOR_APPROVAL"
                        db.session.commit()
                    return

                # Otherwise it finished
                project = db.session.get(Project,p_id)
                if project:
                    project.status = final_state.get("status", "COMPLETED")
                    if final_state.get("plan") and final_state["plan"].get("project_type"):
                        project.name = final_state["plan"]["project_type"]
                    db.session.commit()
            except Exception as exc:
                traceback.print_exc()
                # Mark as failed in DB
                project = db.session.get(Project,p_id)
                if project:
                    project.status = "FAILED"
                    db.session.commit()
            finally:
                # Clean up stream buffer to prevent memory leak
                from utils.streaming import cleanup_stream_buffer
                cleanup_stream_buffer(p_id)

    # Start graph execution in background thread
    thread = threading.Thread(
        target=run_graph_in_background,
        args=(app, project_id, initial_state)
    )
    thread.start()

    return jsonify({
        "project_id": project_id,
        "status": "STARTED"
    })

# ─────────────────────────────────────────────
# PROJECT STATUS
# ─────────────────────────────────────────────

@app.route("/api/projects/<project_id>/status", methods=["GET"])
def get_project_status(project_id):
    project = db.session.get(Project,project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
        
    config = {"configurable": {"thread_id": project_id}}
    
    plan = {}
    try:
        state_info = dev_graph.get_state(config)
        if state_info.values:
            plan = state_info.values.get("plan", {})
    except Exception:
        pass
        
    return jsonify({
        "project_id": project.id,
        "name": project.name,
        "status": project.status,
        "plan": plan
    })

# ─────────────────────────────────────────────
# APPROVE PLAN
# ─────────────────────────────────────────────

@app.route("/api/projects/<project_id>/approve", methods=["POST"])
def approve_plan(project_id):
    project = db.session.get(Project,project_id)
    if not project or project.status != "WAITING_FOR_APPROVAL":
        return jsonify({"error": "Project not found or not waiting for approval"}), 400
        
    project.status = "CODING"
    db.session.commit()
    
    def resume_graph(app_obj, p_id):
        with app_obj.app_context():
            try:
                config = {"configurable": {"thread_id": p_id}}
                final_state = dev_graph.invoke(None, config=config)
                
                # Update project status in DB
                proj = db.session.get(Project,p_id)
                if proj:
                    proj.status = final_state.get("status", "COMPLETED")
                    db.session.commit()
            except Exception as exc:
                traceback.print_exc()
                proj = db.session.get(Project,p_id)
                if proj:
                    proj.status = "FAILED"
                    db.session.commit()
            finally:
                # Clean up stream buffer to prevent memory leak
                from utils.streaming import cleanup_stream_buffer
                cleanup_stream_buffer(p_id)

    thread = threading.Thread(
        target=resume_graph,
        args=(app, project_id)
    )
    thread.start()
    
    return jsonify({"status": "CODING"})

# ─────────────────────────────────────────────
# RETRY / RESUME FAILED PROJECT
# ─────────────────────────────────────────────

@app.route("/api/projects/<project_id>/retry", methods=["POST"])
def retry_project(project_id):
    project = db.session.get(Project, project_id)
    if not project or project.status != "FAILED":
        return jsonify({"error": "Project not found or not failed"}), 400
        
    project.status = "CODING"
    db.session.commit()
    
    def retry_graph(app_obj, p_id):
        with app_obj.app_context():
            try:
                config = {"configurable": {"thread_id": p_id}}
                
                # Mock a reviewer response that triggers a retry by resetting iteration and saying NEEDS_REVISION
                dev_graph.update_state(
                    config, 
                    {"iteration": 0, "review_result": "NEEDS_REVISION", "status": "CODING"}, 
                    as_node="reviewer"
                )
                
                final_state = dev_graph.invoke(None, config=config)
                
                # Update project status in DB
                proj = db.session.get(Project, p_id)
                if proj:
                    proj.status = final_state.get("status", "COMPLETED")
                    db.session.commit()
            except Exception as exc:
                traceback.print_exc()
                proj = db.session.get(Project, p_id)
                if proj:
                    proj.status = "FAILED"
                    db.session.commit()
            finally:
                from utils.streaming import cleanup_stream_buffer
                cleanup_stream_buffer(p_id)

    thread = threading.Thread(
        target=retry_graph,
        args=(app, project_id)
    )
    thread.start()
    
    return jsonify({"status": "CODING"})

# ─────────────────────────────────────────────
# STREAMING PROGRESS
# ─────────────────────────────────────────────
from utils.streaming import stream_buffers

@app.route("/api/projects/<project_id>/stream", methods=["GET"])
def stream_project(project_id):
    def generate():
        last_idx = 0
        while True:
            with app.app_context():
                # Check if project finished coding
                project = db.session.get(Project,project_id)
                if not project or project.status not in ["CODING", "STARTED"]:
                    # Send whatever is left and stop
                    buffer = stream_buffers.get(project_id, "")
                    if last_idx < len(buffer):
                        chunk = buffer[last_idx:]
                        yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                    break
                    
                buffer = stream_buffers.get(project_id, "")
                if last_idx < len(buffer):
                    chunk = buffer[last_idx:]
                    last_idx = len(buffer)
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                    
            time.sleep(0.1)
            
    return Response(generate(), mimetype='text/event-stream')


# ─────────────────────────────────────────────
# LIST ALL PROJECTS
# ─────────────────────────────────────────────

@app.route("/api/projects", methods=["GET"])
def get_all_projects():
    """Return a list of all projects from the database."""
    try:
        projects = Project.query.order_by(Project.created_at.desc()).all()
        return jsonify({
            "projects": [
                {
                    "id": p.id,
                    "name": p.name,
                    "status": p.status,
                    "created_at": p.created_at.isoformat()
                } for p in projects
            ]
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ─────────────────────────────────────────────
# LIST PROJECT FILES
# ─────────────────────────────────────────────

@app.route("/api/projects/<project_id>/files", methods=["GET"])
def get_project_files(project_id):
    """Return a list of file paths inside the given project."""

    try:
        files = list_files(project_id)
        return jsonify({"project_id": project_id, "files": files})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ─────────────────────────────────────────────
# READ A PROJECT FILE
# ─────────────────────────────────────────────

@app.route("/api/projects/<project_id>/files/<path:file_path>", methods=["GET"])
def get_file_content(project_id, file_path):
    """Return the contents of a single file inside a project."""

    try:
        content = read_file(project_id, file_path)
        return jsonify({
            "project_id": project_id,
            "path": file_path,
            "content": content,
        })
    except FileNotFoundError:
        return jsonify({"error": f"File not found: {file_path}"}), 404
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    # use_reloader=False to prevent double-initialization of the graph and MemorySaver
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
