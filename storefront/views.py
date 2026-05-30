import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST


PRODUCTS = [
    {
        "id": "harbor-quilted-crop-jacket",
        "title": "Harbor Quilted Crop Jacket",
        "price": "$118",
        "category": "Outerwear",
        "image": "storefront/jacket.png",
        "description": (
            "A deep teal, lightly insulated cropped jacket with a water-resistant "
            "shell, patch pockets, and easy room for layering over knits."
        ),
    },
    {
        "id": "sunwake-merino-crew",
        "title": "Sunwake Merino Crew",
        "price": "$86",
        "category": "Knitwear",
        "image": "storefront/sweater.png",
        "description": (
            "A soft marigold merino-blend sweater with a relaxed fit, ribbed "
            "trim, and breathable warmth for workdays or weekend travel."
        ),
    },
    {
        "id": "foundry-straight-jean",
        "title": "Foundry Straight Jean",
        "price": "$98",
        "category": "Denim",
        "image": "storefront/jeans.png",
        "description": (
            "Medium indigo straight-leg jeans with a high rise, sturdy denim, "
            "and a clean finish that works with sneakers, boots, or loafers."
        ),
    },
    {
        "id": "shoreline-poplin-shirt-dress",
        "title": "Shoreline Poplin Shirt Dress",
        "price": "$124",
        "category": "Dresses",
        "image": "storefront/shirt-dress.png",
        "description": (
            "A crisp white-and-navy striped poplin shirt dress with a tie waist, "
            "tailored collar, and breathable structure for warm days."
        ),
    },
]


@ensure_csrf_cookie
def index(request):
    return render(request, "storefront/index.html", {"products": PRODUCTS})


@require_POST
def chat(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Send a valid JSON body."}, status=400)

    message = str(payload.get("message", "")).strip()
    if not message:
        return JsonResponse({"error": "Message is required."}, status=400)

    history = _clean_history(payload.get("history", []))
    messages = [
        {"role": "system", "content": _advisor_prompt()},
        *history,
        {"role": "user", "content": message},
    ]

    try:
        reply = _ask_ollama(messages)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return JsonResponse(
            {"error": f"Ollama returned HTTP {exc.code}.", "detail": detail},
            status=502,
        )
    except URLError as exc:
        return JsonResponse(
            {
                "error": "Could not reach Ollama.",
                "detail": (
                    f"{exc.reason}. Confirm Ollama is running at "
                    f"{settings.OLLAMA_BASE_URL} and the model is available."
                ),
            },
            status=503,
        )
    except TimeoutError:
        return JsonResponse({"error": "Ollama timed out."}, status=504)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=502)

    return JsonResponse({"reply": reply})


def _clean_history(history):
    if not isinstance(history, list):
        return []

    cleaned = []
    for item in history[-8:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = str(item.get("content", "")).strip()
        if role in {"user", "assistant"} and content:
            cleaned.append({"role": role, "content": content[:1200]})
    return cleaned


def _advisor_prompt():
    product_lines = "\n".join(
        f"- Title: {product['title']}; Price: {product['price']}; "
        f"Description: {product['description']}"
        for product in PRODUCTS
    )
    return (
        "You are a concise, practical clothing product advisor for an online "
        "retailer. Recommend only products from the catalog below. Ask one "
        "brief follow-up question when the shopper has not shared enough about "
        "occasion, fit, climate, style, or budget. When recommending, explain "
        "why the item fits the shopper's needs and mention the price.\n\n"
        f"Catalog:\n{product_lines}"
    )


def _ask_ollama(messages):
    body = json.dumps(
        {
            "model": settings.OLLAMA_MODEL,
            "stream": False,
            "messages": messages,
            "options": {"temperature": 0.35},
        }
    ).encode("utf-8")
    request = Request(
        f"{settings.OLLAMA_BASE_URL}/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=settings.OLLAMA_TIMEOUT) as response:
        data = json.loads(response.read().decode("utf-8"))

    reply = data.get("message", {}).get("content", "").strip()
    if not reply:
        raise ValueError("Ollama returned an empty chat response.")
    return reply
