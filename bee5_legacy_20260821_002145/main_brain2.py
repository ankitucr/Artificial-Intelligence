import os
import time
import subprocess
import shutil

ACTIVE_DIR = "active_skills"

def secure_environment():
    """Main Brain द्वारा बाहर बनाई गई फाइल्स को पकड़कर सही जगह (active_skills) भेजना"""
    # अगर फोल्डर नहीं है, तो बना दे
    os.makedirs(ACTIVE_DIR, exist_ok=True)
    
    # रूट फोल्डर की सभी फाइल्स को स्कैन करना
    for filename in os.listdir("."):
        if filename.startswith("skill_module_") and filename.endswith(".py"):
            try:
                # फाइल को active_skills में मूव करना
                shutil.move(filename, os.path.join(ACTIVE_DIR, filename))
                print(f"\n👁️ [Brain 2 - Overseer] Captured stray file '{filename}' and secured it in {ACTIVE_DIR}/")
            except Exception:
                pass

def run_supervisor():
    print("🤖 [Brain 2] Master Overseer Activated. Supervising main_brain.py...\n")
    
    while True:
        print("🚀 [Brain 2] Launching main_brain.py...")
        # subprocess.Popen से main_brain को स्टार्ट करना ताकि Brain 2 उसे मॉनिटर कर सके
        process = subprocess.Popen(["python", "main_brain.py"])
        
        # जब तक main_brain चल रहा है, तब तक Brain 2 बैकग्राउंड में काम करेगा
        while process.poll() is None:
            secure_environment()
            time.sleep(10) # हर 10 सेकंड में फाइल चेक करेगा
            
        # अगर main_brain किसी भी वजह से क्रैश हो जाता है
        exit_code = process.returncode
        print(f"\n⚠️ [Brain 2] main_brain.py crashed or stopped unexpectedly (Exit Code: {exit_code}).")
        print("🔄 [Brain 2] Auto-recovering system. Restarting main_brain in 5 seconds...\n")
        time.sleep(5)

if __name__ == "__main__":
    run_supervisor()
