
from pathlib import Path


# ============================================================
# PROJECT FILE DETECTION
# ============================================================

def _get_project_files(project_path: Path) -> set[str]:
    """
    Return all file names in the project.

    File names are converted to lowercase so environment
    detection works consistently across operating systems.
    """

    return {
        file.name.lower()
        for file in project_path.rglob("*")
        if file.is_file()
    }


# ============================================================
# BASE ENVIRONMENT
# ============================================================

def _base_environment(
    language: str,
    runtime: str,
    package_manager: str,
    build_tool: str,
    environment_type: str,
) -> dict:
    """
    Create a consistent environment configuration.
    """

    return {
        "language": language,
        "runtime": runtime,
        "package_manager": package_manager,
        "build_tool": build_tool,
        "environment_type": environment_type,
        "install_command": [],
        "build_command": [],
        "test_command": [],
    }


# ============================================================
# ENVIRONMENT DETECTOR
# ============================================================

def detect_environment(project_path: Path) -> dict:
    """
    Detect the project's programming language and tooling.

    Detection priority:

        1. Python
        2. Node.js / JavaScript / TypeScript
        3. Java / Maven
        4. Java / Gradle
        5. Go
        6. Rust
        7. C / C++ fallback

    Configuration files are preferred over source extensions.
    """

    project_path = Path(project_path)

    # --------------------------------------------------------
    # Validate project directory
    # --------------------------------------------------------

    if not project_path.exists():
        return _base_environment(
            language="unknown",
            runtime="unknown",
            package_manager="none",
            build_tool="none",
            environment_type="none",
        )

    files = _get_project_files(project_path)

    # ========================================================
    # PYTHON
    # ========================================================

    python_files = {
        "pyproject.toml",
        "requirements.txt",
        "setup.py",
        "setup.cfg",
        "pipfile",
    }

    if files.intersection(python_files):

        environment = _base_environment(
            language="python",
            runtime="python",
            package_manager="pip",
            build_tool="setuptools",
            environment_type="venv",
        )

        # ----------------------------------------------------
        # Dependencies
        # ----------------------------------------------------

        if "requirements.txt" in files:

            environment["install_command"] = [
                "python",
                "-m",
                "pip",
                "install",
                "-r",
                "requirements.txt",
            ]

        elif "pyproject.toml" in files:

            environment["install_command"] = [
                "python",
                "-m",
                "pip",
                "install",
                ".",
            ]

        elif "setup.py" in files or "setup.cfg" in files:

            environment["install_command"] = [
                "python",
                "-m",
                "pip",
                "install",
                ".",
            ]

        elif "pipfile" in files:

            environment["package_manager"] = "pipenv"

            environment["install_command"] = [
                "pipenv",
                "install",
            ]

        # ----------------------------------------------------
        # Python tests
        # ----------------------------------------------------

        environment["test_command"] = [
            "python",
            "-m",
            "pytest",
            "-v",
        ]

        return environment

    # ========================================================
    # NODE.JS / JAVASCRIPT / TYPESCRIPT
    # ========================================================

    if "package.json" in files:

        # ----------------------------------------------------
        # Detect package manager
        # ----------------------------------------------------

        if "pnpm-lock.yaml" in files:

            package_manager = "pnpm"

        elif "yarn.lock" in files:

            package_manager = "yarn"

        elif "bun.lockb" in files or "bun.lock" in files:

            package_manager = "bun"

        else:

            package_manager = "npm"

        environment = _base_environment(
            language="javascript",
            runtime="node",
            package_manager=package_manager,
            build_tool=package_manager,
            environment_type="node_modules",
        )

        # ----------------------------------------------------
        # Install dependencies
        # ----------------------------------------------------

        if package_manager == "npm":

            if "package-lock.json" in files:

                environment["install_command"] = [
                    "npm",
                    "ci",
                ]

            else:

                environment["install_command"] = [
                    "npm",
                    "install",
                ]

        elif package_manager == "pnpm":

            environment["install_command"] = [
                "pnpm",
                "install",
            ]

            if "pnpm-lock.yaml" in files:
                environment["install_command"].append(
                    "--frozen-lockfile"
                )

        elif package_manager == "yarn":

            environment["install_command"] = [
                "yarn",
                "install",
            ]

        elif package_manager == "bun":

            environment["install_command"] = [
                "bun",
                "install",
            ]

        # ----------------------------------------------------
        # Build
        # ----------------------------------------------------

        environment["build_command"] = [
            package_manager,
            "run",
            "build",
        ]

        # ----------------------------------------------------
        # Test
        # ----------------------------------------------------

        environment["test_command"] = [
            package_manager,
            "test",
        ]

        return environment

    # ========================================================
    # JAVA / MAVEN
    # ========================================================

    if "pom.xml" in files:

        environment = _base_environment(
            language="java",
            runtime="jdk",
            package_manager="maven",
            build_tool="maven",
            environment_type="maven",
        )

        # ----------------------------------------------------
        # Maven Wrapper
        # ----------------------------------------------------

        if "mvnw.cmd" in files:

            environment["install_command"] = [
                "mvnw.cmd",
                "dependency:resolve",
            ]

            environment["build_command"] = [
                "mvnw.cmd",
                "package",
            ]

            environment["test_command"] = [
                "mvnw.cmd",
                "test",
            ]

        elif "mvnw" in files:

            environment["install_command"] = [
                "./mvnw",
                "dependency:resolve",
            ]

            environment["build_command"] = [
                "./mvnw",
                "package",
            ]

            environment["test_command"] = [
                "./mvnw",
                "test",
            ]

        else:

            environment["install_command"] = [
                "mvn",
                "dependency:resolve",
            ]

            environment["build_command"] = [
                "mvn",
                "package",
            ]

            environment["test_command"] = [
                "mvn",
                "test",
            ]

        return environment

    # ========================================================
    # JAVA / GRADLE
    # ========================================================

    if (
        "build.gradle" in files
        or "build.gradle.kts" in files
    ):

        environment = _base_environment(
            language="java",
            runtime="jdk",
            package_manager="gradle",
            build_tool="gradle",
            environment_type="gradle",
        )

        # ----------------------------------------------------
        # Gradle Wrapper
        # ----------------------------------------------------

        if "gradlew.bat" in files:

            environment["install_command"] = [
                "gradlew.bat",
                "dependencies",
            ]

            environment["build_command"] = [
                "gradlew.bat",
                "build",
            ]

            environment["test_command"] = [
                "gradlew.bat",
                "test",
            ]

        elif "gradlew" in files:

            environment["install_command"] = [
                "./gradlew",
                "dependencies",
            ]

            environment["build_command"] = [
                "./gradlew",
                "build",
            ]

            environment["test_command"] = [
                "./gradlew",
                "test",
            ]

        else:

            environment["install_command"] = [
                "gradle",
                "dependencies",
            ]

            environment["build_command"] = [
                "gradle",
                "build",
            ]

            environment["test_command"] = [
                "gradle",
                "test",
            ]

        return environment

    # ========================================================
    # GO
    # ========================================================

    if "go.mod" in files:

        return {
            "language": "go",
            "runtime": "go",
            "package_manager": "go modules",
            "build_tool": "go",
            "environment_type": "go",
            "install_command": [
                "go",
                "mod",
                "download",
            ],
            "build_command": [
                "go",
                "build",
                "./...",
            ],
            "test_command": [
                "go",
                "test",
                "./...",
            ],
        }

    # ========================================================
    # RUST
    # ========================================================

    if "cargo.toml" in files:

        return {
            "language": "rust",
            "runtime": "rust",
            "package_manager": "cargo",
            "build_tool": "cargo",
            "environment_type": "cargo",
            "install_command": [
                "cargo",
                "fetch",
            ],
            "build_command": [
                "cargo",
                "build",
            ],
            "test_command": [
                "cargo",
                "test",
            ],
        }

    # ========================================================
    # SOURCE EXTENSION FALLBACK
    # ========================================================

    has_python = any(
        file.endswith(".py")
        for file in files
    )

    has_javascript = any(
        file.endswith(extension)
        for file in files
        for extension in (
            ".js",
            ".jsx",
            ".ts",
            ".tsx",
            ".mjs",
            ".cjs",
        )
    )

    has_go = any(
        file.endswith(".go")
        for file in files
    )

    has_rust = any(
        file.endswith(".rs")
        for file in files
    )

    has_cpp = any(
        file.endswith(extension)
        for file in files
        for extension in (
            ".cpp",
            ".cc",
            ".cxx",
            ".c",
            ".h",
            ".hpp",
        )
    )

    # --------------------------------------------------------
    # Python fallback
    # --------------------------------------------------------

    if has_python:

        return {
            "language": "python",
            "runtime": "python",
            "package_manager": "pip",
            "build_tool": "none",
            "environment_type": "venv",
            "install_command": [],
            "build_command": [],
            "test_command": [
                "python",
                "-m",
                "pytest",
                "-v",
            ],
        }

    # --------------------------------------------------------
    # JavaScript / TypeScript fallback
    # --------------------------------------------------------

    if has_javascript:

        return {
            "language": "javascript",
            "runtime": "node",
            "package_manager": "npm",
            "build_tool": "none",
            "environment_type": "node",
            "install_command": [],
            "build_command": [],
            "test_command": [],
        }

    # --------------------------------------------------------
    # Go fallback
    # --------------------------------------------------------

    if has_go:

        return {
            "language": "go",
            "runtime": "go",
            "package_manager": "none",
            "build_tool": "go",
            "environment_type": "none",
            "install_command": [],
            "build_command": [
                "go",
                "build",
                "./...",
            ],
            "test_command": [
                "go",
                "test",
                "./...",
            ],
        }

    # --------------------------------------------------------
    # Rust fallback
    # --------------------------------------------------------

    if has_rust:

        return {
            "language": "rust",
            "runtime": "rust",
            "package_manager": "cargo",
            "build_tool": "cargo",
            "environment_type": "none",
            "install_command": [],
            "build_command": [
                "cargo",
                "build",
            ],
            "test_command": [
                "cargo",
                "test",
            ],
        }

    # --------------------------------------------------------
    # C / C++ fallback
    # --------------------------------------------------------

    if has_cpp:

        return {
            "language": "c/c++",
            "runtime": "native",
            "package_manager": "none",
            "build_tool": "make",
            "environment_type": "none",
            "install_command": [],
            "build_command": [
                "make",
            ],
            "test_command": [],
        }

    # ========================================================
    # UNKNOWN
    # ========================================================

    return {
        "language": "unknown",
        "runtime": "unknown",
        "package_manager": "none",
        "build_tool": "none",
        "environment_type": "none",
        "install_command": [],
        "build_command": [],
        "test_command": [],
    }

