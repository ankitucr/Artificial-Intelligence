with open("main_brainV3.py", "r") as f:
    code = f.read()

# Fix call_planner_with_fallback to handle None responses safely
old_func = """def call_planner_with_fallback(system_prompt: str, user_prompt: str) -> str:
    if groq_client:
        try:
            resp = groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                timeout=30
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f"⚠️ Groq Planner failed ({e}). Falling back to OpenRouter...")
    return call_openrouter(system_prompt, user_prompt)"""

new_func = """def call_planner_with_fallback(system_prompt: str, user_prompt: str) -> str:
    res = None
    if groq_client:
        try:
            resp = groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                timeout=30
            )
            res = resp.choices[0].message.content
        except Exception as e:
            print(f"⚠️ Groq Planner failed ({e}). Falling back to OpenRouter...")
    
    if not res:
        res = call_openrouter(system_prompt, user_prompt)
    
    return str(res).strip() if res else "Create a simple text processing utility using standard library.""""

if old_func in code:
    code = code.replace(old_func, new_func)
    with open("main_brainV3.py", "w") as f:
        f.write(code)
    print("✅ Planner fallback safety patch applied!")
else:
    print("⚠️ Function already modified or structure differed. Please check.")
