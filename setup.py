from setuptools import setup, find_packages

setup(
    name="ai_agent_app",
    version="0.1.0",
    description="AI Agent Desktop Application",
    author="Project team ",
    author_email="your.email@example.com",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "PyQt6>=6.5.0",
        "openai>=1.0.0",
        "anthropic>=0.5.0",
        "google-generativeai>=0.3.0",  # For Gemini
        "mistralai>=0.0.7",            # For Mistral
        "deepseek>=0.0.1",             # For DeepSeek (check actual package name)
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "aiohttp>=3.8.0",
        "asyncio>=3.4.3",
        "pywin32>=306;platform_system=='Windows'",
        "psutil>=5.9.0",
        "QScintilla>=2.14.0",  # For code editor
        "qdarkstyle>=3.1.0",   # For dark theme
    ],
    entry_points={
        "console_scripts": [
            "ai-agent-app=app.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: Microsoft :: Windows",
    ],
)