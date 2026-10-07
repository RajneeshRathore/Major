from pydantic import BaseModel, Field


class RuntimeResult(BaseModel):

    status: str = Field(
        description="Environment setup status"
    )

    environment_path: str = Field(
        description="Path to the created project environment"
    )

    output: str = Field(
        description="Command output"
    )

    errors: list[str] = Field(
        description="Errors encountered during setup"
    )