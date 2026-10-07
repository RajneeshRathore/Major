from langchain_core.callbacks import BaseCallbackHandler

stream_buffers = {}

class CoderStreamHandler(BaseCallbackHandler):
    def __init__(self, project_id):
        self.project_id = project_id
        if project_id not in stream_buffers:
            stream_buffers[project_id] = ""

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        if self.project_id not in stream_buffers:
            stream_buffers[self.project_id] = ""
        stream_buffers[self.project_id] += token

    def on_llm_end(self, response, **kwargs) -> None:
        # We can leave the buffer as is or append a finished marker
        pass


def cleanup_stream_buffer(project_id: str):
    """Remove a project's stream buffer to free memory."""
    if project_id in stream_buffers:
        del stream_buffers[project_id]
