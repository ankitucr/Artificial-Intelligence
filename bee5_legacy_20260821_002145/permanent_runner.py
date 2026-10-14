import os
import time
import subprocess
import threading

PERM_DIR = "permanent_skills"
os.makedirs(PERM_DIR, exist_ok=True)

# जो फाइलें रन हो चुकी हैं, उनकी लिस्ट (ताकि दोबारा रन न हों)
already_executed = set()
running_processes = {}

def stream_logs(process, skill_name):
    """फाइल के आउटपुट को साफ तरीके से स्क्रीन पर दिखाना"""
    for line in iter(process.stdout.readline, ''):
        if line:
            print(f"[{skill_name}] {line.strip()}")
            
    process.stdout.close()
    process.wait()
    print(f"🏁 [DONE] {skill_name} task completed.")
    # प्रोसेस को लिस्ट से हटा दें, लेकिन already_executed में रहने दें
    if skill_name in running_processes:
        del running_processes[skill_name]

def run_permanent_skills():
    skills = [f for f in os.listdir(PERM_DIR) if f.endswith(".py")]
    
    for skill in skills:
        # अगर यह फाइल पहले ही रन हो चुकी है, तो इसे इग्नोर करें (दोबारा रन नहीं होगी)
        if skill in already_executed:
            continue
            
        skill_path = os.path.join(PERM_DIR, skill)
        
        print(f"🚀 [EXECUTOR] Starting {skill}...")
        
        # text=True का इस्तेमाल किया है ताकि RuntimeWarning ना आए
        p = subprocess.Popen(
            ["python", skill_path], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            text=True, bufsize=1
        )
        
        running_processes[skill] = p
        already_executed.add(skill) # रिकॉर्ड में डाल दिया कि यह रन हो चुकी है
        
        # आउटपुट को स्क्रीन पर दिखाने के लिए बैकग्राउंड थ्रेड
        t = threading.Thread(target=stream_logs, args=(p, skill), daemon=True)
        t.start()

if __name__ == "__main__":
    print("==================================================")
    print("🌟 PERMANENT LOG VIEWER & EXECUTOR")
    print("Will run successful files ONLY ONCE and show logs.")
    print("==================================================\n")
    
    while True:
        run_permanent_skills()
        time.sleep(15) # हर 15 सेकंड में नए परमानेंट स्किल्स चेक करेगा
