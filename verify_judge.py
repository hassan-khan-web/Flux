import asyncio
import os
import json
from app.services.llm_judge import llm_judge

async def test_judge():
    print("--- Testing LLM Judge Robustness ---")
    
    # Test cases for JSON extraction
    test_contents = [
        '{"score": 0.9, "reasoning": "Great content"}',
        'The score is {"score": 0.85, "reasoning": "Found in middle"}',
        '```json\n{"score": 0.7, "reasoning": "In markdown block"}\n```',
        'No JSON here but the score is 0.95',
        'Score is 85% and it is good'
    ]
    
    for content in test_contents:
        print(f"\nTesting Content: {content[:50]}...")
        # We manually simulate the API response handling part of _call_api
        try:
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(content)
        except:
            result = {}
            
        if "score" not in result:
            scores = re.findall(r'(\d+\.\d+|\d+)', content)
            if scores:
                val = float(scores[0])
                result["score"] = val if val <= 1.0 else val/100.0
            else:
                result["score"] = 0.0
        
        print(f"Resulting Score: {result.get('score')}")

    # Real API Test (Only if key exists)
    if os.getenv("OPENROUTER_API_KEY"):
        print("\n--- Running REAL API Test ---")
        rel = await llm_judge.evaluate_relevance("Python programming", ["Python is a high-level, general-purpose programming language."])
        print(f"Relevance Result: {rel}")
    else:
        print("\nSkipping real API test - No Key found.")

if __name__ == "__main__":
    asyncio.run(test_judge())
