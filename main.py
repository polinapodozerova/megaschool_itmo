"""
main
"""
import time
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from dotenv import load_dotenv
from tavily import AsyncTavilyClient

from utils.logger import setup_logger
from schemas.request import PredictionRequest, PredictionResponse
from option_extracter import get_option, extract_sources, check_if_options_exist

logger = None

load_dotenv()
client = AsyncTavilyClient(api_key=os.environ["TAVILY_API_KEY"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    global logger
    logger = await setup_logger()
    yield
    await logger.shutdown()


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    body = await request.body()
    await logger.info(
        f"Incoming request: {request.method} {request.url}\n"
        f"Request body: {body.decode()}"
    )

    response = await call_next(request)
    process_time = time.time() - start_time

    response_body = b""
    async for chunk in response.body_iterator:
        response_body += chunk

    await logger.info(
        f"Request completed: {request.method} {request.url}\n"
        f"Status: {response.status_code}\n"
        f"Response body: {response_body.decode()}\n"
        f"Duration: {process_time:.3f}s"
    )

    return Response(
        content=response_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
    )


@app.post("/api/request", response_model=PredictionResponse)
async def predict(body: PredictionRequest):
    try:
        await logger.info(f"Processing prediction request with id: {body.id}")
        query = body.query.replace("\n", " ")

        tavily_response = await client.search(query, include_answer=True, max_results=3)
        answer = tavily_response["answer"]
        results = tavily_response["results"]
        sources = extract_sources(results)
        await logger.info(f"Successfully processed request to tavily {body.id}")

        if check_if_options_exist(query):
            await logger.info(
                "Напиши какой из вариантов ответов соответствует "
                "данному правильному ответу:\n"
                f"Вопрос: {query}\n"
                f"Правильный ответ: {answer}\n"
                "напиши одно число - вариант ответа соответствующий правильному"
            )
            option = await get_option(query=query, correct_answer=answer)
            await logger.info(f"Successfully processed request to llama {body.id}")
        else:
            option = "null"

        response = PredictionResponse(
            id=body.id,
            answer=option,
            reasoning=answer,
            sources=sources,
        )
        return response

    except ValueError as e:
        error_msg = str(e)
        await logger.error(f"Validation error for request {body.id}: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        await logger.error(f"Internal error processing request {body.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")