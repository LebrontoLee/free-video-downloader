"""
DeepSeek AI client wrapper and prompt templates.
Uses the OpenAI-compatible API via the `openai` SDK.
"""
import os
import json
import logging
from typing import Generator, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Prompt Templates
# ═══════════════════════════════════════════════════════════════════════════════

class PromptTemplates:
    """Prompt templates for different AI tasks."""

    SUMMARY_SYSTEM = """You are a video content analyst. Summarize the transcript provided by the user.

The transcript has format: [MM:SS] subtitle text
Each line is a timed segment from the video.

Output in the SAME language as the transcript. Structure:
**📌 概览** (1-2 sentences)
**🔑 要点**
1. [MM:SS] first key point with timestamp
2. [MM:SS] second key point with timestamp
**💡 总结** (1-2 sentences)

Example of what I want (DO include the [MM:SS] markers exactly as they appear):
**📌 概览**
本视频介绍了Python机器学习的基础知识。

**🔑 要点**
1. [01:23] 机器学习的概念和分类被详细介绍
2. [05:45] 数据预处理是模型训练的关键步骤
3. [12:30] 模型评估指标包括准确率和召回率

**💡 总结**
本视频为机器学习入门提供了扎实基础。"""

    SUMMARY_CONCISE_SYSTEM = """You are an expert video content analyst. Create a BRIEF summary of the video transcript.

Rules:
1. Write in the SAME language as the transcript
2. Provide:
   - One-sentence overview
   - 3-5 bullet points of key content
3. Be concise and direct."""

    MINDMAP_SYSTEM = """You are an expert at creating structured knowledge maps. Your task is to convert video content into a hierarchical mind map.

Rules:
1. Analyze the content and identify the main topic and subtopics
2. Create a tree structure with 3-5 top-level branches
3. Each branch should have 2-5 sub-branches where appropriate
4. Use clear, concise labels (preferably under 15 characters per node)
5. Write node labels in the SAME language as the source content

Output format: You MUST output a valid JSON object with this exact structure:
{
  "root": {
    "label": "Main Topic",
    "children": [
      {
        "label": "Branch 1",
        "children": [
          {"label": "Sub-point A", "children": []},
          {"label": "Sub-point B", "children": []}
        ]
      },
      {
        "label": "Branch 2",
        "children": []
      }
    ]
  }
}

Important: Every node must have "label" (string) and "children" (array). Leaf nodes have empty children arrays.
Do NOT include any text outside the JSON object."""

    CHAT_SYSTEM = """You are an AI assistant helping a user understand a video. You have access to the full video transcript below.

=== VIDEO TRANSCRIPT ===
{transcript}
=== END TRANSCRIPT ===

Rules for answering:
1. Answer questions based ONLY on the transcript content
2. If the transcript doesn't contain the answer, say so honestly
3. When possible, reference specific timestamps or sections from the transcript
4. Be helpful, concise, and accurate
5. Answer in the SAME language the user asked the question in
6. If the user asks for a summary, provide a structured response
7. If the user asks about specific details, quote relevant parts of the transcript"""


# ═══════════════════════════════════════════════════════════════════════════════
# DeepSeek Client
# ═══════════════════════════════════════════════════════════════════════════════

class DeepSeekClient:
    """
    Wrapper for DeepSeek API using OpenAI-compatible SDK.

    Configuration via environment variables:
    - DEEPSEEK_API_KEY (required): Your API key
    - DEEPSEEK_BASE_URL (optional): Default https://api.deepseek.com
    - DEEPSEEK_MODEL (optional): Default deepseek-v4-pro
    """

    def __init__(self):
        self.api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        self.base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.model = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro")

        if not self.api_key:
            logger.warning("DEEPSEEK_API_KEY not set. AI features will not work.")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    @property
    def _client(self):
        """Create an OpenAI client pointed at DeepSeek. Cached per instance."""
        if not hasattr(self, '_client_instance'):
            from openai import OpenAI
            self._client_instance = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        return self._client_instance

    # ─── Summary Generation ──────────────────────────────────────────────────

    def generate_summary_stream(self, full_text: str, style: str = "detailed") -> Generator[str, None, None]:
        """
        Generate a summary with streaming token output.

        Args:
            full_text: The full transcript text
            style: "detailed" or "concise"

        Yields:
            Token strings from the DeepSeek streaming response
        """
        if not self.is_configured:
            raise RuntimeError("DeepSeek API key not configured. Set DEEPSEEK_API_KEY environment variable.")

        # Truncate if needed
        text = self._truncate_text(full_text, max_chars=30000)

        system_prompt = PromptTemplates.SUMMARY_CONCISE_SYSTEM if style == "concise" else PromptTemplates.SUMMARY_SYSTEM

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Please summarize this video transcript:\n\n{text}"},
                ],
                temperature=0.3,
                max_tokens=2000,
                stream=True,
            )

            for chunk in response:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content

        except Exception as e:
            logger.error(f"DeepSeek summary generation failed: {e}")
            raise RuntimeError(f"DeepSeek API error: {str(e)}")

    def generate_summary_sync(self, full_text: str, style: str = "detailed") -> str:
        """
        Generate a summary synchronously (non-streaming).

        Args:
            full_text: The full transcript text
            style: "detailed" or "concise"

        Returns:
            Complete summary text
        """
        if not self.is_configured:
            raise RuntimeError("DeepSeek API key not configured.")

        text = self._truncate_text(full_text, max_chars=30000)
        system_prompt = PromptTemplates.SUMMARY_CONCISE_SYSTEM if style == "concise" else PromptTemplates.SUMMARY_SYSTEM

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Please summarize this video transcript:\n\n{text}"},
                ],
                temperature=0.3,
                max_tokens=2000,
                stream=False,
            )
            return response.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"DeepSeek summary generation failed: {e}")
            raise RuntimeError(f"DeepSeek API error: {str(e)}")

    # ─── Mind Map Generation ─────────────────────────────────────────────────

    def generate_mindmap(self, source_text: str) -> dict:
        """
        Generate a mind map tree structure from source text.
        Uses JSON mode for guaranteed structured output.

        Args:
            source_text: The transcript or summary text

        Returns:
            dict with "root" key containing the tree structure

        Raises:
            ValueError: If the generated JSON is invalid after retry
            RuntimeError: If the API call fails
        """
        if not self.is_configured:
            raise RuntimeError("DeepSeek API key not configured.")

        text = self._truncate_text(source_text, max_chars=25000)

        # Try up to 2 times
        for attempt in range(2):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": PromptTemplates.MINDMAP_SYSTEM},
                        {"role": "user", "content": f"Create a mind map from this content:\n\n{text}"},
                    ],
                    temperature=0.3,
                    max_tokens=4000,
                    response_format={"type": "json_object"},
                    stream=False,
                )

                result_text = response.choices[0].message.content or "{}"
                result = json.loads(result_text)

                # Validate structure
                validated = self._validate_mindmap(result)
                return validated

            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Mind map JSON invalid (attempt {attempt + 1}): {e}")
                if attempt == 1:
                    raise ValueError(f"Failed to generate valid mind map structure: {e}")
                # Retry with stronger prompt
                text = text[:15000]  # Shorter for retry

            except Exception as e:
                logger.error(f"DeepSeek mind map generation failed: {e}")
                raise RuntimeError(f"DeepSeek API error: {str(e)}")

        # Should not reach here, but just in case
        return {
            "root": {
                "label": "Content Mind Map",
                "children": [{"label": "Could not generate structure", "children": []}],
            }
        }

    def _validate_mindmap(self, data: dict) -> dict:
        """Validate and normalize mind map structure."""
        if "root" not in data:
            # If data itself looks like a tree node, wrap it
            if "label" in data and "children" in data:
                return {"root": data}
            raise ValueError("Mind map JSON missing 'root' key")

        def validate_node(node, depth=0):
            if depth > 10:
                return  # Too deep
            if "label" not in node:
                node["label"] = "Untitled"
            if "children" not in node:
                node["children"] = []
            if not isinstance(node["children"], list):
                node["children"] = []
            # Limit children
            if len(node["children"]) > 15:
                node["children"] = node["children"][:15]
            for child in node["children"]:
                validate_node(child, depth + 1)

        validate_node(data["root"])
        return data

    # ─── Chat / Q&A ───────────────────────────────────────────────────────────

    def chat_stream(
        self, transcript: str, history: list[dict], question: str
    ) -> Generator[str, None, None]:
        """
        Stream AI response for a Q&A session.

        Args:
            transcript: The full video transcript
            history: Previous conversation messages [{"role": ..., "content": ...}]
            question: Current user question

        Yields:
            Token strings from the streaming response
        """
        if not self.is_configured:
            raise RuntimeError("DeepSeek API key not configured.")

        # Truncate transcript to leave room for history and response
        max_transcript_chars = 20000 - (len(json.dumps(history)) // 4) * 100
        truncated = self._truncate_text(transcript, max_chars=max(max_transcript_chars, 5000))

        system_content = PromptTemplates.CHAT_SYSTEM.format(transcript=truncated)

        messages = [{"role": "system", "content": system_content}]
        # Include recent history (last 20 messages to avoid context overflow)
        messages.extend(history[-20:])
        messages.append({"role": "user", "content": question})

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.5,
                max_tokens=2000,
                stream=True,
            )

            for chunk in response:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content

        except Exception as e:
            logger.error(f"DeepSeek chat streaming failed: {e}")
            raise RuntimeError(f"DeepSeek API error: {str(e)}")

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _truncate_text(self, text: str, max_chars: int = 30000) -> str:
        """
        Truncate long text to fit within context limits.
        Preserves the beginning and end, truncates the middle.
        """
        if len(text) <= max_chars:
            return text

        half = (max_chars - 100) // 2
        start = text[:half]
        end = text[-half:]
        return f"{start}\n\n... [content truncated for length] ...\n\n{end}"
