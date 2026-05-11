# 1. Asosiy imidjni ko'rsatamiz (Python 3.12 yoki o'zingizga keraklisi)
FROM python:3.12-slim

# 2. uv ni o'rnatish (bu qator sizda bor edi)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 3. Ishchi katalogni belgilash
WORKDIR /app

# 4. Loyiha fayllarini ko'chirish
COPY . .

# 5. uv yordamida kutubxonalarni o'rnatish
# --frozen lock fayldagi versiyalarni qat'iy saqlaydi
RUN uv sync

# 6. Virtual muhitni PATH ga qo'shish
#ENV PATH="/app/.venv/bin:$PATH"

# 7. Portni ochish
EXPOSE 8081