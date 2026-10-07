from typing import TypedDict,NotRequired

class DevelopmentState(TypedDict):
    project_id:NotRequired[str]
    user_requirement:NotRequired[str]
    plan:NotRequired[dict]
    files:NotRequired[dict]
    test_result:NotRequired[dict]
    environment: NotRequired[dict]
    runtime_result: NotRequired[dict]
    review_result:NotRequired[str]
    errors:NotRequired[list[str]]
    iteration:NotRequired[int]
    status:NotRequired[str]


