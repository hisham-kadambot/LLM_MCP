from fastapi import APIRouter, Depends
from ..auth import verify_jwt_token
from ..models import LLMParaphraseRequest, LLMParaphraseResponse
import language_tool_python

router = APIRouter(prefix="/llm", tags=["LLM"])

tool = language_tool_python.LanguageTool('en-US')

@router.post("/paraphrase", response_model=LLMParaphraseResponse, operation_id="llm_paraphrase_tool")
def llm_paraphrase_tool(
    request: LLMParaphraseRequest,
    username: str = Depends(verify_jwt_token)
) -> LLMParaphraseResponse:
    """
    Paraphrase the given text using a specified LLM model (now with grammar correction using LanguageTool).
    """
    matches = tool.check(request.text)
    corrected = language_tool_python.utils.correct(request.text, matches)
    return LLMParaphraseResponse(paraphrased_text=corrected) 