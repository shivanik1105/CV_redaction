"""
Role-Specific Information Chatbot Template

This template allows you to quickly create chatbots for specific job roles
by providing a job description and supporting documents.

Usage:
1. Create a folder for your role (e.g., 'senior_python_dev')
2. Add these files:
   - job_description.txt (the JD)
   - client_info.txt (client details)
   - faqs.txt (common candidate questions)
   - .env (with API keys)
3. Run: python role_chatbot_template.py --role senior_python_dev
"""

from pathlib import Path
import os
import re
import sys
import argparse
from collections import OrderedDict
from typing import List, Dict, Optional

from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _split_chunks(text: str, chunk_size: int, overlap: int) -> List[str]:
    cleaned = _clean_text(text)
    if not cleaned:
        return []
    if chunk_size <= 0:
        return [cleaned]

    chunks: List[str] = []
    step = max(chunk_size - max(overlap, 0), 1)
    for start in range(0, len(cleaned), step):
        chunk = cleaned[start : start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        if start + chunk_size >= len(cleaned):
            break
    return chunks


def _keywords(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9]+", (text or "").lower()))


class RoleChatbot:
    def __init__(self, role_folder: Path):
        self.role_folder = role_folder
        
        # Load environment variables from role folder
        env_path = role_folder / ".env"
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
        
        # Get API key
        self.api_key = (
            os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
            or os.getenv("OPENAI_API_KEY")
        )
        
        if not self.api_key:
            raise RuntimeError(
                f"API key not found. Add GEMINI_API_KEY to {env_path}"
            )
        
        # Configuration
        self.gemini_base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        self.model_name = os.getenv("CHATBOT_MODEL", "gemini-2.5-flash-lite")
        self.max_history = int(os.getenv("MAX_HISTORY_MESSAGES", "10"))
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "1500"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
        self.max_context_chunks = int(os.getenv("MAX_CONTEXT_CHUNKS", "4"))
        
        # Initialize OpenAI client
        self.client = OpenAI(base_url=self.gemini_base_url, api_key=self.api_key)
        
        # Load role-specific content
        self.role_name = role_folder.name.replace("_", " ").title()
        self.job_description = self._load_file("job_description.txt")
        self.client_info = self._load_file("client_info.txt")
        self.faqs = self._load_file("faqs.txt")
        self.additional_info = self._load_file("additional_info.txt")
        
        # Create searchable chunks from all content
        all_content = "\n\n".join(filter(None, [
            f"JOB DESCRIPTION:\n{self.job_description}",
            f"CLIENT INFORMATION:\n{self.client_info}",
            f"FREQUENTLY ASKED QUESTIONS:\n{self.faqs}",
            f"ADDITIONAL INFORMATION:\n{self.additional_info}"
        ]))
        
        self.content_chunks = _split_chunks(all_content, self.chunk_size, self.chunk_overlap)
        
        # Build base system prompt
        self.base_prompt = self._build_base_prompt()
        
        # Response cache
        self.response_cache: OrderedDict[str, str] = OrderedDict()
        
        print(f"✓ Loaded chatbot for: {self.role_name}")
        print(f"✓ Content chunks: {len(self.content_chunks)}")
    
    def _load_file(self, filename: str) -> str:
        """Load a text file from the role folder."""
        file_path = self.role_folder / filename
        if not file_path.exists():
            return ""
        
        try:
            content = file_path.read_text(encoding="utf-8").strip()
            if content:
                print(f"✓ Loaded {filename}")
            return content
        except Exception as exc:
            print(f"⚠ Error reading {filename}: {exc}")
            return ""
    
    def _build_base_prompt(self) -> str:
        """Build the base system prompt for the chatbot."""
        prompt = (
            f"You are a helpful recruitment assistant providing information about a specific job role: {self.role_name}.\n\n"
            "Your responsibilities:\n"
            "- Answer candidate questions about the role, client, and application process\n"
            "- Be professional, friendly, and encouraging\n"
            "- Provide accurate information based on the provided context\n"
            "- If you don't know something, say so honestly\n"
            "- Encourage qualified candidates to apply\n"
            "- Keep responses concise and clear\n\n"
        )
        
        # Add brief overview if available
        if self.job_description:
            jd_preview = self.job_description[:500]
            prompt += f"Role Overview:\n{jd_preview}...\n\n"
        
        return prompt
    
    def _select_relevant_chunks(self, user_message: str) -> str:
        """Select the most relevant content chunks based on user query."""
        if not self.content_chunks:
            return ""
        
        query_terms = _keywords(user_message)
        if not query_terms:
            return "\n\n".join(self.content_chunks[:self.max_context_chunks])
        
        # Rank chunks by keyword overlap
        ranked: List[tuple[int, str]] = []
        for chunk in self.content_chunks:
            chunk_terms = _keywords(chunk)
            overlap = len(query_terms.intersection(chunk_terms))
            ranked.append((overlap, chunk))
        
        ranked.sort(key=lambda item: item[0], reverse=True)
        selected = [chunk for score, chunk in ranked if score > 0][:self.max_context_chunks]
        
        if not selected:
            selected = self.content_chunks[:2]
        
        return "\n\n".join(selected)
    
    def _normalize_history(self, history) -> List[Dict[str, str]]:
        """Normalize chat history to standard format."""
        if not history:
            return []
        
        normalized: List[Dict[str, str]] = []
        for item in history:
            if isinstance(item, dict):
                role = item.get("role")
                content = item.get("content")
                if role in {"user", "assistant"} and isinstance(content, str):
                    normalized.append({"role": role, "content": content})
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                user_msg, assistant_msg = item
                if isinstance(user_msg, str):
                    normalized.append({"role": "user", "content": user_msg})
                if isinstance(assistant_msg, str):
                    normalized.append({"role": "assistant", "content": assistant_msg})
        
        if self.max_history > 0:
            return normalized[-self.max_history:]
        return normalized
    
    def _build_system_prompt(self, user_message: str) -> str:
        """Build the complete system prompt with relevant context."""
        relevant_context = self._select_relevant_chunks(user_message)
        
        prompt = self.base_prompt
        if relevant_context:
            prompt += f"\n## Relevant Information:\n{relevant_context}\n"
        
        prompt += "\nProvide helpful, accurate information to assist the candidate."
        return prompt
    
    def chat(self, message, history):
        """Handle a chat message."""
        normalized_history = self._normalize_history(history)
        user_message = (message or "").strip()
        
        if not user_message:
            return "Please ask me anything about this role!"
        
        # Check cache
        cache_key = _clean_text(user_message).lower()
        if cache_key in self.response_cache:
            cached = self.response_cache.pop(cache_key)
            self.response_cache[cache_key] = cached
            return cached
        
        # Build messages
        messages = [
            {"role": "system", "content": self._build_system_prompt(user_message)},
            *normalized_history,
            {"role": "user", "content": user_message},
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.3,
                max_tokens=600,
                timeout=45,
            )
            
            content = response.choices[0].message.content
            final_content = content or "I apologize, I couldn't generate a response. Please try again."
            
            # Cache response
            self.response_cache[cache_key] = final_content
            while len(self.response_cache) > 50:
                self.response_cache.popitem(last=False)
            
            return final_content
            
        except Exception as exc:
            print(f"Chat error: {exc}")
            return "I encountered an issue. Please try asking your question again."


def build_interface(bot: RoleChatbot):
    """Build the Gradio interface."""
    title = f"💼 {bot.role_name} - Information Chatbot"
    description = (
        f"Ask me anything about this role! I can help with:\n"
        f"• Job requirements and responsibilities\n"
        f"• Client information and culture\n"
        f"• Application process and timeline\n"
        f"• Compensation and benefits\n"
        f"• Any other questions you may have"
    )
    
    try:
        interface = gr.ChatInterface(
            bot.chat,
            type="messages",
            title=title,
            description=description,
            examples=[
                "What are the main responsibilities?",
                "Tell me about the client",
                "What skills are required?",
                "What's the salary range?",
                "How do I apply?",
            ],
            theme=gr.themes.Soft(),
        )
    except TypeError:
        # Fallback for older Gradio versions
        interface = gr.ChatInterface(
            bot.chat,
            title=title,
            description=description,
        )
    
    return interface


def main():
    parser = argparse.ArgumentParser(description="Launch a role-specific chatbot")
    parser.add_argument(
        "--role",
        type=str,
        required=True,
        help="Name of the role folder (e.g., senior_python_dev)"
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help="Create a public shareable link"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Port to run the server on (default: 7860)"
    )
    
    args = parser.parse_args()
    
    # Determine role folder path
    if getattr(sys, "frozen", False):
        base_path = Path(sys.executable).parent
    else:
        base_path = Path(__file__).parent
    
    role_folder = base_path / "roles" / args.role
    
    if not role_folder.exists():
        print(f"❌ Role folder not found: {role_folder}")
        print(f"\nCreate it with:")
        print(f"  mkdir -p {role_folder}")
        print(f"  # Add job_description.txt, client_info.txt, faqs.txt, .env")
        sys.exit(1)
    
    # Initialize chatbot
    try:
        bot = RoleChatbot(role_folder)
    except Exception as exc:
        print(f"❌ Failed to initialize chatbot: {exc}")
        sys.exit(1)
    
    # Launch interface
    interface = build_interface(bot)
    print(f"\n🚀 Launching chatbot for: {bot.role_name}")
    print(f"📁 Role folder: {role_folder}")
    
    interface.launch(
        share=args.share,
        server_port=args.port,
        server_name="0.0.0.0"
    )


if __name__ == "__main__":
    main()
