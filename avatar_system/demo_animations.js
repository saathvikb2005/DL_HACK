/*
Avatar Demo Script
=====================
Run this from the browser console to see all avatar animations and emotions in action.

Usage:
1. Open avatar_system/index.html in browser
2. Wait for avatar to load
3. Open browser console (F12)
4. Copy and paste this entire script
5. Watch the avatar perform all its animations!
*/

async function demoAvatarAnimations() {
    console.log("🎭 Starting Avatar Animation Demo...");
    
    // Helper function to wait
    const wait = (ms) => new Promise(resolve => setTimeout(resolve, ms));
    
    // Demo 1: Emotions
    console.log("\n1️⃣ EMOTIONS DEMO");
    await wait(1000);
    
    window.avatarSpeak("I'm feeling happy!", "happy");
    await wait(4000);
    
    window.avatarSpeak("This is concerning.", "concerned");
    await wait(4000);
    
    window.avatarSpeak("Urgent! Pay attention!", "urgent");
    await wait(4000);
    
    window.avatarSpeak("Stay calm, everything's fine.", "calm");
    await wait(4000);
    
    window.avatarSpeak("Oh, what a surprise!", "surprised");
    await wait(4000);
    
    // Demo 2: Gestures (if animator is available globally)
    const animator = window.getAnimator?.();
    if (animator) {
        console.log("\n2️⃣ GESTURES DEMO");
        await wait(1000);
        
        window.avatarSpeak("Let me show you a nod.", "neutral");
        animator.addGesture("nod");
        await wait(3000);
        
        window.avatarSpeak("And here's a wave!", "happy");
        animator.addGesture("wave");
        await wait(3000);
        
        window.avatarSpeak("I can point forward for emphasis.", "neutral");
        animator.addGesture("pointForward");
        await wait(3000);
        
        window.avatarSpeak("A hand to chest shows sincerity.", "concerned");
        animator.addGesture("handToChest");
        await wait(3000);
        
        window.avatarSpeak("Sometimes I shrug.", "thinking");
        animator.addGesture("shrug");
        await wait(3000);
        
        window.avatarSpeak("Thumbs up for approval!", "happy");
        animator.addGesture("thumbsUp");
        await wait(3000);
        
        window.avatarSpeak("And open arms to welcome you.", "calm");
        animator.addGesture("openArms");
        await wait(4000);
    }
    
    // Demo 3: Combined Emotions + Gestures
    console.log("\n3️⃣ COMBINED DEMO");
    await wait(1000);
    
    const scenarios = [
        {
            msg: "Hey there! Welcome to the wellness system!",
            emotion: "happy",
            gesture: "wave"
        },
        {
            msg: "Your posture needs some attention. Sit up straight!",
            emotion: "concerned",
            gesture: "handToChest"
        },
        {
            msg: "Alert! Poor air quality detected. Open a window now!",
            emotion: "urgent",
            gesture: "pointForward"
        },
        {
            msg: "Great job! You've earned a break. Rest well.",
            emotion: "happy",
            gesture: "thumbsUp"
        },
        {
            msg: "Take a deep breath. Everything will be okay.",
            emotion: "calm",
            gesture: "openArms"
        }
    ];
    
    for (const scene of scenarios) {
        window.avatarSpeak(scene.msg, scene.emotion);
        if (animator) {
            animator.addGesture(scene.gesture);
        }
        await wait(5000);
    }
    
    // Demo 4: Priority System
    console.log("\n4️⃣ PRIORITY SYSTEM DEMO");
    await wait(1000);
    
    window.avatarSpeak("This is a low priority message.", "neutral", 0);
    window.avatarSpeak("This is normal priority.", "neutral", 0);
    window.avatarSpeak("URGENT MESSAGE! I speak first!", "urgent", 2);
    window.avatarSpeak("Important, but not urgent.", "concerned", 1);
    
    await wait(15000);
    
    // Demo 5: Chat Responses
    console.log("\n5️⃣ CHAT INTERACTION DEMO");
    await wait(1000);
    
    window.avatarSpeak("You can chat with me! Try typing 'hello', 'I'm tired', or 'thanks'", "happy");
    await wait(5000);
    
    console.log("\n✅ Demo Complete!");
    console.log("Try interacting with the chat to see emotion-based responses!");
}

// Auto-run demo
console.log("🎬 Avatar Animation Demo Loaded!");
console.log("Run: demoAvatarAnimations()");
console.log("Or wait 3 seconds for auto-start...");

setTimeout(() => {
    demoAvatarAnimations();
}, 3000);
