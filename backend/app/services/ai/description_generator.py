"""
AI Product Description Generator
Uses LLM providers (Gemini / Groq / Mistral / OpenAI) with intelligent fallback
to generate Amazon-grade, SEO-friendly, high-converting product descriptions.
Integrated with Redis caching for performance and $0 API spend.
"""
from __future__ import annotations

import logging
from typing import Any

from .ai_cache import ai_cache
from .fallback_manager import AIFallbackManager

logger = logging.getLogger("shopzone_ai.desc_generator")

FALLBACK_TEMPLATES = {
    "electronics": (
        "Experience cutting-edge performance with the {name}. Engineered for tech enthusiasts, "
        "it delivers exceptional speed, premium build quality, and unmatched daily reliability. "
        "Key Highlights:\n"
        "• High-precision engineering and durable premium construction\n"
        "• Intuitive plug-and-play compatibility across modern devices\n"
        "• Energy-efficient architecture engineered for extended longevity\n"
        "• Backed by manufacturer warranty and express customer support."
    ),
    "fashion": (
        "Elevate your signature wardrobe with the {name}. Crafted from ultra-comfortable, "
        "breathable fabrics that drape effortlessly for all-day confidence. "
        "Key Highlights:\n"
        "• Premium bio-washed combed fabric for skin-friendly softness\n"
        "• Fade-resistant dye and reinforced precision stitching\n"
        "• Versatile silhouette suitable for office, casual, and evening styling\n"
        "• Easy machine wash care with wrinkle-resistant finish."
    ),
    "jewellery": (
        "Make an unforgettable statement with the {name}. Exquisitely designed with "
        "intricate artisanal detailing and sparkling accents that capture ambient light. "
        "Key Highlights:\n"
        "• Skin-friendly hypoallergenic metals with anti-tarnish protective coating\n"
        "• Brilliant precision-cut stones delivering captivating luster\n"
        "• Secure ergonomic clasp for comfortable, confident daily wear\n"
        "• Delivered in a luxury gift box ready for festive celebrations."
    ),
    "general": (
        "Discover elevated quality with the {name}. Designed to combine functionality, "
        "enduring durability, and modern aesthetics into an essential everyday product. "
        "Key Highlights:\n"
        "• Premium materials tested for long-lasting everyday durability\n"
        "• Thoughtfully designed for optimal ergonomics and user satisfaction\n"
        "• Verified quality assured by GenZ Zone standards\n"
        "• 100% genuine product with easy returns and hassle-free delivery."
    ),
}


class ProductDescriptionGenerator:
    """
    Generates compelling e-commerce product descriptions using LLMs or robust copy templates.
    """

    def __init__(self, fallback_manager: AIFallbackManager | None = None):
        self.fallback_manager = fallback_manager or AIFallbackManager()

    async def generate_description(
        self,
        name: str,
        category: str,
        price: float | None = None,
        keywords: list[str] | None = None,
        tone: str = "persuasive and professional",
    ) -> dict[str, Any]:
        """
        Generate an Amazon-style product description.
        Checks Redis cache first, then calls LLM fallback chain, with template safety fallback.
        """
        clean_name = name.strip()
        clean_cat = category.strip()

        # 1. Check Redis cache
        cached = ai_cache.get_cached_description(clean_name, clean_cat)
        if cached:
            return {**cached, "cached": True}

        # 2. Build prompt for LLM
        price_text = f"₹{price:,.2f} INR" if price is not None else "Competitive pricing"
        kw_text = ", ".join(keywords) if keywords else "premium quality, durability, modern design"

        system_instruction = (
            "You are an elite Amazon e-commerce senior copywriter and SEO specialist. "
            "Your objective is to generate an engaging, conversion-optimized, professional product description "
            "that highlights key benefits, materials, features, and target occasions."
        )

        user_prompt = (
            f"Write an Amazon-standard product description for:\n"
            f"- Product Title: {clean_name}\n"
            f"- Category: {clean_cat}\n"
            f"- Pricing: {price_text}\n"
            f"- Key Highlights / Keywords: {kw_text}\n"
            f"- Tone: {tone}\n\n"
            f"Format requirements:\n"
            f"1. A compelling 2-sentence opening hook.\n"
            f"2. 4 concise bullet points detailing Key Features & Benefits (use '• ').\n"
            f"3. A closing call-to-action sentence.\n"
            f"Keep total length under 180 words. Never mention competitor brands."
        )

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt},
        ]

        provider = "local_template"
        model = "ecommerce-v1"
        description_text = ""

        try:
            res = await self.fallback_manager.generate_chat_with_fallback(messages)
            content = res.get("content", "").strip()
            if content:
                description_text = content
                provider = res.get("successful_provider", "ai")
                model = res.get("model", "")
        except Exception as err:
            logger.warning("LLMs failed for description generation: %s. Using template fallback.", err)

        # 3. Template fallback if LLMs were offline / no keys
        if not description_text:
            cat_key = clean_cat.lower()
            template = (
                FALLBACK_TEMPLATES.get(cat_key)
                or next((v for k, v in FALLBACK_TEMPLATES.items() if k in cat_key), None)
                or FALLBACK_TEMPLATES["general"]
            )
            description_text = template.format(name=clean_name)
            provider = "GenZ Zone Copywriter Engine"
            model = "template-v1"

        # Extract bullet points
        bullets = [
            line.replace("•", "").strip()
            for line in description_text.splitlines()
            if line.strip().startswith("•") or line.strip().startswith("-")
        ]

        result = {
            "name": clean_name,
            "category": clean_cat,
            "description": description_text,
            "bullet_points": bullets[:5],
            "provider": provider,
            "model": model,
            "cached": False,
        }

        # Cache in Redis and record call
        ai_cache.set_cached_description(clean_name, clean_cat, result)
        ai_cache.record_ai_call(provider, model)

        return result

description_generator = ProductDescriptionGenerator()


async def generate_ai_product_description(
    name: str,
    category: str,
    price: float | None = None,
    keywords: list[str] | None = None,
    tone: str = "persuasive and professional",
) -> dict[str, Any]:
    return await description_generator.generate_description(
        name=name, category=category, price=price, keywords=keywords, tone=tone
    )
