
import os
import json
import asyncio
import tiktoken

from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

client = AsyncOpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

MODEL = os.getenv("MODEL_NAME", "openai/gpt-4o-mini")

encoding = tiktoken.get_encoding("cl100k_base")

SYSTEM_PROMPT = """
You are a helpful AI assistant.
Remember important user information.
Use conversation summaries when older messages are removed.
Never invent facts.
"""

# -------------------------------
# TOKEN BUDGET
# -------------------------------

TOKEN_BUDGET = {
    "system": 500,
    "history": 3000,
    "context": 2000,
    "output": 1000
}

LAST_N_TURNS = 4
SUMMARY_THRESHOLD = 2000


def count_tokens(text):
    return len(encoding.encode(str(text)))


def count_messages(messages):
    # Approximate token count including role names
    text = json.dumps(messages, ensure_ascii=False)
    return count_tokens(text)


def check_budget(system, history, context, output):

    counts = {
        "system": count_tokens(system),
        "history": count_messages(history),
        "context": count_tokens(context),
        "output": output
    }

    for category, used in counts.items():
        limit = TOKEN_BUDGET[category]

        if used > limit:
            raise ValueError(
                f"{category} budget exceeded: "
                f"{used}/{limit}"
            )

    total = sum(counts.values())

    if total > sum(TOKEN_BUDGET.values()):
        raise ValueError("Total token budget exceeded")

    print("Token budget check:", counts)

    return counts


# -------------------------------
# CONTEXT MANAGER
# -------------------------------

class ContextManager:

    def __init__(self):

        self.system_prompt = SYSTEM_PROMPT
        self.summary = ""

        self.history = []

        self.last_n_turns = LAST_N_TURNS

    def add_message(self, role, content):

        self.history.append({
            "role": role,
            "content": content
        })

    def sliding_window(self):

        max_messages = self.last_n_turns * 2

        if len(self.history) > max_messages:
            self.history = self.history[-max_messages:]

    async def summarize_old_messages(self):

        history_tokens = count_messages(self.history)

        if history_tokens <= SUMMARY_THRESHOLD:
            return

        print("\nHistory exceeds 2000 tokens.")
        print("Starting summarisation...")

        # Preserve the latest four complete turns
        keep_count = self.last_n_turns * 2

        old_messages = self.history[:-keep_count]
        recent_messages = self.history[-keep_count:]

        if not old_messages:
            return

        old_token_count = count_messages(old_messages)

        summarization_prompt = [
            {
                "role": "system",
                "content": (
                    "Summarise the conversation accurately. "
                    "Preserve names, order IDs, dates, preferences "
                    "and important facts. Do not invent information."
                )
            },
            {
                "role": "user",
                "content": (
                    "Previous summary:\n" + self.summary +
                    "\n\nOld conversation:\n" +
                    json.dumps(old_messages, ensure_ascii=False)
                )
            }
        ]

        # Check budget before summarisation API call
        check_budget(
            system=self.system_prompt,
            history=summarization_prompt,
            context=self.summary,
            output=1000
        )

        response = await client.chat.completions.create(
            model=MODEL,
            messages=summarization_prompt,
            max_tokens=1000
        )

        new_summary = response.choices[0].message.content

        # Keep previous facts and new summary together
        self.summary = (
            self.summary + "\n" + new_summary
        ).strip()

        self.history = recent_messages

        # Ensure summary fits context budget
        while count_tokens(self.summary) > TOKEN_BUDGET["context"]:
            self.summary = self.summary[:int(
                len(self.summary) * 0.8
            )]

        print("Old history tokens:", old_token_count)
        print("Summary tokens:", count_tokens(self.summary))
        print("Recent history tokens:", count_messages(self.history))

    async def prepare_context(self):

        await self.summarize_old_messages()

        self.sliding_window()

        # Ensure the history fits the allocated budget
        while count_messages(self.history) > TOKEN_BUDGET["history"]:
            self.history = self.history[2:]

        check_budget(
            system=self.system_prompt,
            history=self.history,
            context=self.summary,
            output=TOKEN_BUDGET["output"]
        )

        messages = [
            {
                "role": "system",
                "content": self.system_prompt
            }
        ]

        if self.summary:
            messages.append({
                "role": "system",
                "content": "Conversation summary:\n" + self.summary
            })

        messages.extend(self.history)

        return messages

    async def chat(self, user_message):

        self.add_message("user", user_message)

        messages = await self.prepare_context()

        response = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=TOKEN_BUDGET["output"]
        )

        reply = response.choices[0].message.content

        self.add_message("assistant", reply)

        return reply

    def save(self, filename="conversations/summary.json"):

        os.makedirs("conversations", exist_ok=True)

        data = {
            "summary": self.summary,
            "history": self.history
        }

        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

        print("\nConversation saved:", filename)


# -------------------------------
# 20-TURN DEMONSTRATION
# -------------------------------

async def main():

    manager = ContextManager()

    for turn in range(1, 21):

        if turn == 1:
            question = (
                "My name is Arun and my important order ID is 9999. "
                "Please remember these details."
            )

        else:
            question = (
                f"Turn {turn}: Explain one useful concept about "
                "Python, artificial intelligence, or machine learning. "
                "Give a detailed explanation with examples."
            )

        before = count_messages(manager.history)

        print("\n" + "=" * 55)
        print("TURN:", turn)
        print("History before trimming:", before)

        answer = await manager.chat(question)

        after = count_messages(manager.history)

        print("Assistant:", answer)
        print("History after trimming:", after)
        print("Summary tokens:", count_tokens(manager.summary))

    # Verify early facts
    print("\n--- IMPORTANT FACT VERIFICATION ---")
    print("Summary:", manager.summary)

    verification = await manager.chat(
        "What is my name and what is my important order ID?"
    )

    print("Verification response:", verification)

    manager.save()


if __name__ == "__main__":
    asyncio.run(main())
