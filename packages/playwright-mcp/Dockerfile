# Dedicated Playwright MCP image. Pinning @playwright/mcp and letting IT install
# its own matching browser avoids the version-pairing fights with prebuilt base
# images (chrome vs chrome-for-testing vs chromium-XXXX).
FROM node:20-bookworm

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
WORKDIR /app

# Install the MCP server globally so its bundled Playwright version is fixed.
RUN npm install -g @playwright/mcp@latest

# Install OS deps, then the exact browser THIS @playwright/mcp expects
# (it asks for "chrome-for-testing" specifically).
RUN npx -y playwright install-deps chromium
RUN playwright-mcp install-browser chrome-for-testing

EXPOSE 8931

CMD ["playwright-mcp", "--port", "8931", "--host", "0.0.0.0", \
     "--headless", "--isolated", "--allowed-hosts", "*", "--browser", "chromium"]
