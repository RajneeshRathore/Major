from pydantic import BaseModel, Field


class DevelopmentTask(BaseModel):

    id: int = Field(
        description="Unique task number"
    )

    description: str = Field(
        description="Clear description of the development task"
    )


class DevelopmentPlan(BaseModel):

    project_type: str = Field(
        description="Type of software project"
    )

    technologies: list[str] = Field(
        description="Technologies and frameworks required"
    )

    components: list[str] = Field(
        description="Major components that need to be developed"
    )

    tasks: list[DevelopmentTask] = Field(
        description="Ordered development tasks"
    )

    testing_requirements: list[str] = Field(
        description="Tests that should be implemented"
    )