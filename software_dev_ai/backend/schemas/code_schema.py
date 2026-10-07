from pydantic import BaseModel, Field


class GeneratedFile(BaseModel):

    path: str = Field(
        description="Relative path of the file inside the project"
    )

    content: str = Field(
        description="Complete source code of the file"
    )


class CodeGenerationResult(BaseModel):

    files: list[GeneratedFile] = Field(
        description="Files that need to be created or modified"
    )