import os
import time
import subprocess
import shutil

ACTIVE_DIR = "active_skills"
PERM_DIR = "permanent_skills"

# फोल्डर्स क्रिएट करना
os.makedirs(ACTIVE_DIR, exist_ok=True)
os.makedirs(PERM_DIR, exist_ok=True)

def test_and_sort_skills():
    skills = [f for f in os.listdir(ACTIVE_DIR) if f.endswith(".py")]
    
    for skill in skills:
        skill_path = os.path.join(ACTIVE_DIR, skill)
        print(f"🧪 [SORTER] Testing new skill: {skill}...")
        
        # फाइल को एक बार रन करके चेक करना
        result = subprocess.run(["python", skill_path], capture_output=True, text=True)
        
        if result.returncode == 0:
            # फाइल सक्सेसफुल है! इसे permanent_skills में भेजें
            perm_path = os.path.join(PERM_DIR, skill)
            shutil.move(skill_path, perm_path)
            print(f"✅ [SUCCESS] Moved {skill} to {PERM_DIR}/ folder.")
        else:
            # फाइल में एरर है, इसे यहीं छोड़ दें ताकि AI इसे बाद में फिक्स कर सके या आप खुद देख सकें
            print(f"❌ [FAILED] {skill} has errors. Left in {ACTIVE_DIR}/")

if __name__ == "__main__":
    print("=========================================")
    print("🕵️  SKILL SORTER ACTIVATED")
    print("Moving successful files to 'permanent_skills/'")
    print("=========================================\n")
    
    while True:
        test_and_sort_skills()
        time.sleep(10) # हर 10 सेकंड में नई फाइल्स चेक करेगा
