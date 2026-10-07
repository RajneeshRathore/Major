from pydantic import BaseModel, Field


class EnvironmentConfig(BaseModel):

    language: str = Field(
        description="Primary programming language"
    )

    runtime: str = Field(
        description="Runtime or platform used by the project"
    )

    package_manager: str = Field(
        description="Package or dependency manager"
    )

    build_tool: str = Field(
        description="Build tool used by the project"
    )

    environment_type: str = Field(
        description="Type of isolated project environment"
    )

    install_command: list[str] = Field(
        description="Command used to install dependencies"
    )

    build_command: list[str] = Field(
        description="Command used to build the project"
    )

    test_command: list[str] = Field(
        description="Command used to run tests"
    )