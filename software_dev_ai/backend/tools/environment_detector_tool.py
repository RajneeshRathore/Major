from pathlib import Path


def detect_environment(project_path: Path):

    files = {
        file.name.lower()
        for file in project_path.rglob("*")
        if file.is_file()
    }

    # -------------------------
    # Python
    # -------------------------

    if (
        "pyproject.toml" in files
        or "requirements.txt" in files
        or "setup.py" in files
    ):

        return {
            "language": "python",
            "runtime": "python",
            "package_manager": "pip",
            "build_tool": "setuptools",
            "environment_type": "venv",
            "install_command": [
                "python",
                "-m",
                "pip",
                "install",
                "-r",
                "requirements.txt"
            ],
            "build_command": [],
            "test_command": [
                "python",
                "-m",
                "pytest"
            ]
        }

    # -------------------------
    # Node.js
    # -------------------------

    if "package.json" in files:

        if "pnpm-lock.yaml" in files:

            package_manager = "pnpm"

        elif "yarn.lock" in files:

            package_manager = "yarn"

        else:

            package_manager = "npm"

        return {
            "language": "javascript",
            "runtime": "node",
            "package_manager": package_manager,
            "build_tool": "npm",
            "environment_type": "node_modules",
            "install_command": [
                package_manager,
                "install"
            ],
            "build_command": [
                package_manager,
                "run",
                "build"
            ],
            "test_command": [
                package_manager,
                "test"
            ]
        }

    # -------------------------
    # Java / Maven
    # -------------------------

    if "pom.xml" in files:

        return {
            "language": "java",
            "runtime": "jdk",
            "package_manager": "maven",
            "build_tool": "maven",
            "environment_type": "maven",
            "install_command": [
                "mvn",
                "dependency:resolve"
            ],
            "build_command": [
                "mvn",
                "package"
            ],
            "test_command": [
                "mvn",
                "test"
            ]
        }

    # -------------------------
    # Java / Gradle
    # -------------------------

    if (
        "build.gradle" in files
        or "build.gradle.kts" in files
    ):

        return {
            "language": "java",
            "runtime": "jdk",
            "package_manager": "gradle",
            "build_tool": "gradle",
            "environment_type": "gradle",
            "install_command": [
                "gradle",
                "dependencies"
            ],
            "build_command": [
                "gradle",
                "build"
            ],
            "test_command": [
                "gradle",
                "test"
            ]
        }

    # -------------------------
    # Go
    # -------------------------

    if "go.mod" in files:
        return {
            "language": "go",
            "runtime": "go",
            "package_manager": "go modules",
            "build_tool": "go",
            "environment_type": "go",
            "install_command": ["go", "mod", "tidy"],
            "build_command": ["go", "build", "./..."],
            "test_command": ["go", "test", "./..."]
        }

    # -------------------------
    # Rust
    # -------------------------

    if "cargo.toml" in files:
        return {
            "language": "rust",
            "runtime": "rust",
            "package_manager": "cargo",
            "build_tool": "cargo",
            "environment_type": "cargo",
            "install_command": ["cargo", "fetch"],
            "build_command": ["cargo", "build"],
            "test_command": ["cargo", "test"]
        }

    # -------------------------
    # Fallback based on extensions
    # -------------------------

    has_py = any(f.endswith('.py') for f in files)
    has_js_ts = any(f.endswith(ext) for f in files for ext in ['.js', '.jsx', '.ts', '.tsx'])
    has_go = any(f.endswith('.go') for f in files)
    has_rs = any(f.endswith('.rs') for f in files)
    has_cpp = any(f.endswith(ext) for f in files for ext in ['.cpp', '.cc', '.c', '.h', '.hpp'])

    if has_py:
        return {
            "language": "python",
            "runtime": "python",
            "package_manager": "pip",
            "build_tool": "none",
            "environment_type": "venv",
            "install_command": [],
            "build_command": [],
            "test_command": []
        }
        
    if has_js_ts:
        return {
            "language": "javascript/typescript",
            "runtime": "node",
            "package_manager": "npm",
            "build_tool": "none",
            "environment_type": "none",
            "install_command": [],
            "build_command": [],
            "test_command": []
        }
        
    if has_go:
        return {
            "language": "go",
            "runtime": "go",
            "package_manager": "none",
            "build_tool": "go",
            "environment_type": "none",
            "install_command": [],
            "build_command": ["go", "build"],
            "test_command": ["go", "test"]
        }
        
    if has_rs:
        return {
            "language": "rust",
            "runtime": "rust",
            "package_manager": "cargo",
            "build_tool": "cargo",
            "environment_type": "none",
            "install_command": [],
            "build_command": ["cargo", "build"],
            "test_command": ["cargo", "test"]
        }
        
    if has_cpp:
        return {
            "language": "c/c++",
            "runtime": "native",
            "package_manager": "none",
            "build_tool": "make",
            "environment_type": "none",
            "install_command": [],
            "build_command": ["make"],
            "test_command": []
        }

    return {
        "language": "unknown",
        "runtime": "unknown",
        "package_manager": "none",
        "build_tool": "none",
        "environment_type": "none",
        "install_command": [],
        "build_command": [],
        "test_command": []
    }