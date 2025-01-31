import os
from openai import AsyncOpenAI
from together import AsyncTogether

client = AsyncTogether(
    base_url="https://api.scaleway.ai/v1",
    api_key=os.environ['TOGETHER_API_KEY'])

model = "meta-llama/Llama-3.3-70B-Instruct-Turbo"

async def get_option(query, correct_answer):
    completion = await client.chat.complete(
        model=model,
        messages=[{"role": "user", "content":
                  f"Напиши какой из вариантов ответов соответствует \
                данному правильному ответу:\n\
              Вопрос:{query}\n\
              Правильный ответ:{correct_answer}\n\
              напиши одно число - вариант ответа \
                  соответствующий правильному"}],
    )

    return completion.choices[0].message.content


def extract_sources(results):
    sources = []
    for res in results:
        if res["url"] and res["url"] not in sources:
            sources.append(res["url"])
    return sources


def check_if_options_exist(query):
    if '1.' in query or '1)' in query or '1 )' in query or ' 1 ' in query:
        return True
    return False

