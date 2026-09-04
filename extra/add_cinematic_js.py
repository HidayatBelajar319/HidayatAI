import os

file_path = r'd:\TiTech Prabha Solution\Brahma Echo\Brahma Echo\Brahma Echo-AI---Lite-main\Brahma Echo-AI---Lite-main\assets\web_background\index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

js_additions = """
        // Cinematic Reactor Controls for Setup Wizard
        window.triggerPulse = function() {
            if (!window.glowMaterial) return;
            let originalIntensity = window.glowMaterial.uniforms.c.value;
            let originalScale = window.glowMesh ? window.glowMesh.scale.x : 1;
            
            let t = 0;
            let pulseInterval = setInterval(() => {
                t += 0.1;
                if (t <= 1) {
                    window.glowMaterial.uniforms.c.value = originalIntensity + (t * 0.5);
                    if (window.glowMesh) window.glowMesh.scale.setScalar(originalScale + (t * 0.2));
                } else if (t <= 2) {
                    let dt = t - 1;
                    window.glowMaterial.uniforms.c.value = originalIntensity + 0.5 - (dt * 0.5);
                    if (window.glowMesh) window.glowMesh.scale.setScalar(originalScale + 0.2 - (dt * 0.2));
                } else {
                    clearInterval(pulseInterval);
                    window.glowMaterial.uniforms.c.value = originalIntensity;
                    if (window.glowMesh) window.glowMesh.scale.setScalar(originalScale);
                }
            }, 16);
        };
        
        window.losePower = function() {
            if (!window.glowMaterial) return;
            let originalIntensity = window.glowMaterial.uniforms.c.value;
            window.glowMaterial.uniforms.c.value = 0.1;
            if (window.controls) window.controls.autoRotateSpeed = 0.5;
            
            setTimeout(() => {
                let t = 0;
                let recoverInterval = setInterval(() => {
                    t += 0.05;
                    if (t <= 1) {
                        window.glowMaterial.uniforms.c.value = 0.1 + (t * (originalIntensity - 0.1));
                        if (window.controls) window.controls.autoRotateSpeed = 0.5 + (t * 1.5);
                    } else {
                        clearInterval(recoverInterval);
                        window.glowMaterial.uniforms.c.value = originalIntensity;
                        if (window.controls) window.controls.autoRotateSpeed = 2.0;
                    }
                }, 16);
            }, 1000);
        };
        
        window.setReactorSpeed = function(speed) {
            if (window.controls) {
                window.controls.autoRotateSpeed = speed;
            }
        };
        
        window.dissolveReactor = function() {
            if (window.glowMaterial) window.glowMaterial.uniforms.c.value = 3.0;
            setTimeout(() => {
                if (window.glowMaterial) window.glowMaterial.uniforms.c.value = 1.0;
                window.setReactorSpeed(2.0);
            }, 500);
        };
"""

if 'triggerPulse' not in text:
    text = text.replace('</script>', js_additions + '\n</script>')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print('Added cinematic controls to index.html')
else:
    print('Cinematic controls already present')
