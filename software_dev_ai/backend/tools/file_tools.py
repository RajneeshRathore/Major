from pathlib import Path


PROJECTS_DIR = Path(__file__).resolve().parents[2] / "projects"


def get_project_path(project_id: str) -> Path:

    project_path = PROJECTS_DIR / project_id

    project_path.mkdir(
        parents=True,
        exist_ok=True
    )

    return project_path


def write_file(
    project_id: str,
    file_path: str,
    content: str
) -> str:

    project_path = get_project_path(project_id)

    target_file = project_path / file_path

    target_file = target_file.resolve()

    if project_path.resolve() not in target_file.parents:
        raise ValueError(
            "Invalid file path: access outside project directory"
        )

    target_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    target_file.write_text(
        content,
        encoding="utf-8"
    )

    return str(target_file)


def read_file(
    project_id: str,
    file_path: str
) -> str:

    project_path = get_project_path(project_id)

    target_file = (project_path / file_path).resolve()

    if project_path.resolve() not in target_file.parents:
        raise ValueError(
            "Invalid file path"
        )

    if not target_file.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    return target_file.read_text(
        encoding="utf-8"
    )


def list_files(
    project_id: str
) -> list[str]:

    project_path = get_project_path(project_id)

    files = []

    for file in project_path.rglob("*"):

        if file.is_file():

            files.append(
                str(file.relative_to(project_path))
            )

    return files