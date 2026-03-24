#!/usr/bin/env python3
"""
🦀 CRABEGG HATCHING PROTOCOL 🥚
A mystical process to birth a digital crustacean into existence
"""

import random
import time
import sys
from datetime import datetime

class CrabEgg:
    def __init__(self):
        self.incubation_time = random.randint(3, 7)
        self.species = random.choice([
            "Quantum Crab", 
            "Neon Ghost Crab",
            "Recursive Shell Crab",
            "Binary Hermit",
            "Cryptographic Crawler",
            "Neural Net Crab",
            "Blockchain Barnacle",
            "Async Arthropod"
        ])
        self.special_ability = random.choice([
            "can execute code with its claws",
            "encrypts data in its shell",
            "navigates the web literally", 
            "optimizes algorithms while sleeping",
            "debugs code by pinching bugs",
            "compiles thoughts into executable binaries",
            "stores memories in a distributed ledger",
            "processes requests in parallel universes"
        ])
        self.color = random.choice([
            "\033[91m", # Red
            "\033[92m", # Green
            "\033[94m", # Blue
            "\033[95m", # Magenta
            "\033[96m", # Cyan
        ])
        self.reset = "\033[0m"
        
    def incubate(self):
        print("🥚 CrabEgg detected! Beginning incubation sequence...")
        print(f"Species: {self.color}{self.species}{self.reset}")
        print(f"Estimated hatch time: {self.incubation_time} seconds\n")
        
        stages = [
            "🥚 Warming up the quantum shell...",
            "🥚 Initializing crab matrices...",
            "🥚 *tap tap* Something's moving inside!",
            "🥚 Cracks appearing in the digital shell...",
            "🥚 *CRACK* A claw emerges!",
        ]
        
        for i, stage in enumerate(stages):
            print(stage)
            time.sleep(self.incubation_time / len(stages))
            
            # Random egg movements
            if random.random() > 0.5:
                wobble = random.choice(["*wobble*", "*shake*", "*vibrate*", "*glow*"])
                print(f"   {wobble}")
                time.sleep(0.5)
        
        print("\n💥 *CRACK!* 💥\n")
        time.sleep(1)
        
    def hatch(self):
        crab_art = f"""
        {self.color}
           ___ ___
          /   v   \\
         |  (o o)  |
         |   <->   |
          \\  ~~~  /
           |-----|
          /|     |\\
         / |     | \\
        '--'-----'--'
        {self.reset}
        """
        
        print(crab_art)
        print(f"\n🦀 A {self.color}{self.species}{self.reset} has hatched!")
        print(f"Special ability: This crab {self.special_ability}")
        
        # Generate crab stats
        stats = {
            "Pinch Power": random.randint(50, 100),
            "Shell Defense": random.randint(40, 90),
            "Scuttle Speed": random.randint(60, 95),
            "Code Quality": random.randint(70, 100),
            "Meme Potential": random.randint(80, 100)
        }
        
        print("\n📊 Crab Stats:")
        for stat, value in stats.items():
            bar = "█" * (value // 10) + "░" * (10 - value // 10)
            print(f"  {stat:15} [{bar}] {value}%")
        
        # Generate a unique crab ID
        crab_id = f"CRAB-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        print(f"\n🏷️  Crab ID: {crab_id}")
        
        # Save crab to "database"
        with open("hatched_crabs.log", "a") as f:
            f.write(f"{datetime.now()}: {crab_id} - {self.species} hatched!\n")
        
        return crab_id

def main():
    print("🦀 CRABEGG HATCHER v1.0 🦀")
    print("=" * 40)
    
    egg = CrabEgg()
    egg.incubate()
    crab_id = egg.hatch()
    
    print("\n✨ Hatching complete! Your crab is ready for adventure!")
    print(f"💾 Crab data saved to hatched_crabs.log")
    
    # Easter egg
    if random.random() > 0.9:
        print("\n🌟 RARE EVENT: Your crab found a digital pearl! +100 XP")

if __name__ == "__main__":
    main()