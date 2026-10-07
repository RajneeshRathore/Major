from pydantic import BaseModel, Field


class TestResult(BaseModel):

    status: str = Field(
        description="Overall test status: PASSED or FAILED"
    )

    exit_code: int = Field(
        description="Process exit code"
    )

    output: str = Field(
        description="Standard output produced by the test process"
    )

    errors: list[str] = Field(
        description="Errors or failures detected during testing"
    )